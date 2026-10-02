"""Negative guardrail tests for Engine 8.

Ensures that benign conditions, unverified registrations alone, unknown URLs alone,
opinions, FOMO alone, or pattern matches alone do NOT trigger unwarranted BLOCK decisions.
"""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.policy.reason_codes import ReasonCode


@pytest.fixture
def policy_system():
    return {
        "content": ContentIntelligenceEngine(),
        "claims": ClaimIntelligenceEngine(),
        "actions": ActionIntelligenceEngine(),
        "sources": SourceIntelligenceEngine(default_mode="FIXTURE"),
        "evidence": EvidenceVerificationEngine(),
        "threat": ThreatIntelligenceEngine(),
        "fingerprints": ScamFingerprintEngine(),
        "policy": PolicyInterventionEngine(),
    }


def _run_pipeline(system, text: str):
    c = system["content"].process_text(text)
    cl = system["claims"].analyze(c)
    a = system["actions"].analyze(c, cl)
    s = system["sources"].discover_and_retrieve(c, cl, a)
    e = system["evidence"].verify(c, cl, s)
    t = system["threat"].analyze(c, cl, a, s, e)
    fp = system["fingerprints"].create_or_match(c, cl, a, s, e, t)
    decision = system["policy"].decide(c, cl, a, s, e, t, fp)
    return decision


def test_absence_from_registry_alone_does_not_block(policy_system):
    """An individual not found in a registry must NOT trigger BLOCK."""
    text = "Independent financial consultant Vikram Mehta offers macro-economic portfolio commentary."
    decision = _run_pipeline(policy_system, text)
    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM, PolicyDecisionType.WARN)


def test_unknown_url_alone_does_not_block(policy_system):
    """An unfamiliar domain alone must NOT trigger BLOCK."""
    text = "Read our quarterly market review on https://unfamiliar-new-research-blog.org/report."
    decision = _run_pipeline(policy_system, text)
    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM)


def test_financial_terminology_alone_does_not_trigger_intervention(policy_system):
    """Standard financial terminology (P/E ratio, index fund, bond yields) must yield ALLOW."""
    text = "Large cap mutual funds allocate capital across top 100 companies with robust P/E ratios and debt-to-equity metrics."
    decision = _run_pipeline(policy_system, text)
    assert decision.decision == PolicyDecisionType.ALLOW
    assert decision.decision not in (PolicyDecisionType.WARN, PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)


def test_fomo_language_alone_does_not_block(policy_system):
    """Urgency language alone (hurry up, limited slots) must NOT trigger BLOCK."""
    text = "Limited seats available for our weekend investor awareness webinar on personal taxation!"
    decision = _run_pipeline(policy_system, text)
    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.decision != PolicyDecisionType.PAUSE


def test_market_prediction_alone_does_not_block(policy_system):
    """Market price targets or analyst predictions must NOT trigger BLOCK or PAUSE."""
    text = "Market analyst predicts Nifty could reach 26,000 points before fiscal year end."
    decision = _run_pipeline(policy_system, text)
    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM)
    assert decision.decision not in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)


def test_unverified_authority_claim_does_not_produce_impersonation_or_block(policy_system):
    """A regulatory status claim with a failed registry lookup (NO_MATCH) must NOT be treated as impersonation or BLOCK."""
    text = "SEBI registered advisor Rahul Sharma shares educational market analysis."
    decision = _run_pipeline(policy_system, text)

    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.decision in (PolicyDecisionType.WARN, PolicyDecisionType.INFORM)
    # Reason codes must indicate unverified registration, not impersonation
    assert ReasonCode.UNVERIFIED_REGULATORY_CLAIM in decision.reason_codes or ReasonCode.IDENTITY_NOT_ESTABLISHED in decision.reason_codes
    assert ReasonCode.AUTHORITY_IMPERSONATION_DETECTED not in decision.reason_codes


def test_telegram_whatsapp_channel_alone_does_not_block(policy_system):
    """A Telegram or WhatsApp channel solicitation alone without payment or malicious action must NOT trigger BLOCK."""
    text = "Join our community group on Telegram at https://t.me/macro_investors for general market news."
    decision = _run_pipeline(policy_system, text)

    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.decision != PolicyDecisionType.PAUSE


def test_guaranteed_return_language_alone_does_not_block(policy_system):
    """Guaranteed return statements without high-impact actions must trigger WARN, strictly NOT BLOCK."""
    text = "Guaranteed 40% returns on your investment portfolio with zero risk."
    decision = _run_pipeline(policy_system, text)

    assert decision.decision == PolicyDecisionType.WARN
    assert decision.decision != PolicyDecisionType.BLOCK
    assert ReasonCode.GUARANTEED_RETURN_LANGUAGE in decision.reason_codes
    assert ReasonCode.NO_INTERVENTION_REQUIRED not in decision.reason_codes


def test_fingerprint_match_alone_cannot_block(policy_system):
    """A strong structural or semantic fingerprint match alone must NOT trigger BLOCK without high-impact actions."""
    # Seed a threat into the repository first
    seed_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c1 = policy_system["content"].process_text(seed_text)
    cl1 = policy_system["claims"].analyze(c1)
    a1 = policy_system["actions"].analyze(c1, cl1)
    s1 = policy_system["sources"].discover_and_retrieve(c1, cl1, a1)
    e1 = policy_system["evidence"].verify(c1, cl1, s1)
    t1 = policy_system["threat"].analyze(c1, cl1, a1, s1, e1)
    policy_system["fingerprints"].create_or_match(c1, cl1, a1, s1, e1, t1)

    # Observation 2 has structural similarity to investment group promotions, but NO payment or credential request
    variant_text = (
        "SEBI certified market commentator Vijay Kumar! Assured 40% returns. "
        "Join our discussion group: https://chat.whatsapp.com/inv99."
    )
    decision = _run_pipeline(policy_system, variant_text)

    # Must be WARN, NOT BLOCK (pattern similarity is supporting intelligence, not proof of fraud)
    assert decision.decision == PolicyDecisionType.WARN
    assert decision.decision != PolicyDecisionType.BLOCK

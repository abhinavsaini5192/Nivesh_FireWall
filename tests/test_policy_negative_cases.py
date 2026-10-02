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
    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM)
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

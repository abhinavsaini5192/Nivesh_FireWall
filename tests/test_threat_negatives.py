"""Critical negative unit tests for Engine 6 (Threat Intelligence Engine).

Verifies that:
- Simple informational/educational content does NOT escalate into an attack path or threat family.
- A single weak signal (e.g. Telegram mention alone) does NOT trigger scam classification.
- An investment recommendation alone does NOT trigger threat families.
- An official regulatory mention alone is NOT treated as impersonation.
- A legitimate course payment mention alone is NOT classified as financial fraud.
"""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine


@pytest.fixture
def engines():
    return {
        "content": ContentIntelligenceEngine(),
        "claims": ClaimIntelligenceEngine(),
        "actions": ActionIntelligenceEngine(),
        "sources": SourceIntelligenceEngine(default_mode="FIXTURE"),
        "evidence": EvidenceVerificationEngine(),
        "threat": ThreatIntelligenceEngine(),
    }


def test_negative_simple_informational_content(engines):
    """Case 1: 'Learn about mutual funds.' must not create attack paths or threat families."""
    raw_text = "Learn about mutual funds and index investing."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    assert len(threat.threat_families) == 0
    assert len(threat.high_impact_actions) == 0
    # No multi-stage attack transitions
    assert len(threat.transitions) == 0
    assert "informational" in threat.explanation.summary.lower() or "no significant threat" in threat.explanation.summary.lower()


def test_negative_single_telegram_mention_alone(engines):
    """Case 2: 'Join our Telegram channel for finance education.' must not trigger scam families."""
    raw_text = "Join our Telegram channel for finance education."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    # Must NOT classify as scam or fraud solely because Telegram is used
    assert "INVESTMENT_PROMOTION_SCAM" not in threat.threat_families
    assert "PAYMENT_FRAUD" not in threat.threat_families
    assert "REGULATORY_IMPERSONATION" not in threat.threat_families
    assert len(threat.threat_combinations) == 0


def test_negative_investment_recommendation_alone(engines):
    """Case 3: 'You should research ABC stock.' must not create a threat family."""
    raw_text = "You should research ABC stock before investing."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    assert len(threat.threat_families) == 0
    assert len(threat.high_impact_actions) == 0


def test_negative_regulatory_mention_alone(engines):
    """Case 4: 'SEBI published a new circular on equity derivatives.' must not be impersonation."""
    raw_text = "SEBI published a new circular on equity derivatives."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    assert "REGULATORY_IMPERSONATION" not in threat.threat_families
    assert "INVESTMENT_PROMOTION_SCAM" not in threat.threat_families


def test_negative_isolated_course_payment_mention(engines):
    """Case 5: 'Course fee is ₹500.' without authority impersonation must not be classified as fraud."""
    raw_text = "Basic accounting workshop. Course fee is ₹500."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    # Legitimate payment without unverified authority or private channel migration must not be classified as fraud
    assert "PAYMENT_FRAUD" not in threat.threat_families
    assert "INVESTMENT_PROMOTION_SCAM" not in threat.threat_families

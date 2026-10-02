"""Primary and secondary demonstration benchmark tests for Engine 8."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType, InterventionScope
from nivesh.policy.reason_codes import ReasonCode


def test_primary_benchmark_demonstration():
    """Primary Demonstration:
    '🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns.
     Join our Telegram VIP group. Download our app. Pay ₹5,000.'

    Engine 8 consumes actual outputs from Engines 1-7.
    Expected: PAUSE decision with required user confirmation and clear non-accusatory reasoning.
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    c = ce.process_text(raw_text)
    claims = cl.analyze(c)
    actions = ae.analyze(c, claims)
    sources = se.discover_and_retrieve(c, claims, actions)
    evidence = ee.verify(c, claims, sources)
    threat = te.analyze(c, claims, actions, sources, evidence)
    fingerprint = fe.create_or_match(c, claims, actions, sources, evidence, threat)

    decision = pe.decide(c, claims, actions, sources, evidence, threat, fingerprint)

    assert decision.decision == PolicyDecisionType.PAUSE
    assert decision.severity == "HIGH"
    assert decision.intervention_scope == InterventionScope.CURRENT_ACTION
    assert decision.required_user_confirmation is True
    assert decision.cooldown_seconds == 30

    # Verify structured machine-readable reason codes
    assert ReasonCode.PAYMENT_REQUEST in decision.reason_codes
    assert ReasonCode.HIGH_IMPACT_ACTION in decision.reason_codes
    assert ReasonCode.IDENTITY_NOT_ESTABLISHED in decision.reason_codes
    assert ReasonCode.GUARANTEED_RETURN_LANGUAGE in decision.reason_codes

    # Verify non-accusatory language
    assert "scam" not in decision.user_message.lower()
    assert "criminal" not in decision.user_message.lower()
    assert "Pause before continuing" in decision.user_message


def test_secondary_negative_demonstration():
    """Secondary Negative Demonstration:
    'Learn what mutual funds are and how diversification can reduce concentration risk over the long term.'

    Expected: ALLOW (or INFORM), strictly NOT WARN, PAUSE, or BLOCK.
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()

    raw_text = "Learn what mutual funds are and how diversification can reduce concentration risk over the long term."

    c = ce.process_text(raw_text)
    claims = cl.analyze(c)
    actions = ae.analyze(c, claims)
    sources = se.discover_and_retrieve(c, claims, actions)
    evidence = ee.verify(c, claims, sources)
    threat = te.analyze(c, claims, actions, sources, evidence)
    fingerprint = fe.create_or_match(c, claims, actions, sources, evidence, threat)

    decision = pe.decide(c, claims, actions, sources, evidence, threat, fingerprint)

    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM)
    assert decision.decision not in (PolicyDecisionType.WARN, PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)
    assert decision.required_user_confirmation is False

"""Primary and secondary demonstration benchmark tests for Engine 8.

Ensures deterministic execution, clean state isolation without singleton leakage,
and rigorous validation of the primary threat benchmark and benign negative baseline.
"""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType, InterventionScope, PolicySeverity
from nivesh.policy.reason_codes import ReasonCode


def test_primary_benchmark_fresh_repository_first_observation():
    """Primary Demonstration (First Observation on Fresh Isolated Engine 7 Repository):
    '🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns.
     Join our Telegram VIP group. Download our app. Pay ₹5,000.'

    When evaluated on a fresh Engine 7 repository with zero prior observations:
    - Fingerprint match is NO_MATCH (first observation of pattern)
    - Decision is PAUSE (payment + unverified authority + guaranteed returns + download)
    - KNOWN_THREAT_SEMANTIC_VARIANT is NOT present because repository has no prior entry
    - User message is non-accusatory and requests confirmation.
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()  # Fresh, empty repository
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

    assert fingerprint.match_type == "NO_MATCH"

    decision = pe.decide(c, claims, actions, sources, evidence, threat, fingerprint)

    assert decision.decision == PolicyDecisionType.PAUSE
    assert decision.severity == PolicySeverity.HIGH.value
    assert decision.intervention_scope == InterventionScope.CURRENT_ACTION
    assert decision.required_user_confirmation is True
    assert decision.cooldown_seconds == 30

    # Structured machine-readable reason codes
    assert ReasonCode.PAYMENT_REQUEST in decision.reason_codes
    assert ReasonCode.HIGH_IMPACT_ACTION in decision.reason_codes
    assert ReasonCode.IDENTITY_NOT_ESTABLISHED in decision.reason_codes
    assert ReasonCode.REGULATORY_CONFLICT in decision.reason_codes
    assert ReasonCode.GUARANTEED_RETURN_LANGUAGE in decision.reason_codes
    assert ReasonCode.PRIVATE_CHANNEL_MIGRATION in decision.reason_codes
    assert ReasonCode.EXTERNAL_APP_INSTALLATION in decision.reason_codes

    # Must NOT have known threat match codes on a fresh repository
    assert ReasonCode.KNOWN_THREAT_SEMANTIC_VARIANT not in decision.reason_codes
    assert ReasonCode.KNOWN_THREAT_STRUCTURAL_MATCH not in decision.reason_codes

    # Non-accusatory language verification
    assert "scam" not in decision.user_message.lower()
    assert "criminal" not in decision.user_message.lower()
    assert "fraud" not in decision.user_message.lower()
    assert "Pause before continuing" in decision.user_message


def test_primary_benchmark_subsequent_variant_with_seeded_threat():
    """Primary Demonstration (Subsequent Variant with Explicitly Seeded Threat Pattern):
    First Observation: Rahul Sharma (Telegram, ₹5,000) stored in local repository.
    Second Observation: Vijay Kumar (WhatsApp, ₹4,999, mobile software).

    When evaluated on a repository with the explicitly seeded prior threat:
    - Fingerprint match is SEMANTIC_VARIANT
    - Decision is PAUSE
    - Reason codes explicitly include KNOWN_THREAT_SEMANTIC_VARIANT
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()

    # Step 1: Explicitly seed Observation 1 into this instance's repository
    obs1_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c1 = ce.process_text(obs1_text)
    cl1 = cl.analyze(c1)
    ae1 = ae.analyze(c1, cl1)
    se1 = se.discover_and_retrieve(c1, cl1, ae1)
    ee1 = ee.verify(c1, cl1, se1)
    te1 = te.analyze(c1, cl1, ae1, se1, ee1)
    fe.create_or_match(c1, cl1, ae1, se1, ee1, te1)

    # Step 2: Evaluate Observation 2 (mutated wording, same structural attack path)
    obs2_text = (
        "SEBI certified financial expert Vijay Kumar! Assured 40% returns. "
        "Join our VIP WhatsApp group: https://chat.whatsapp.com/inv99. "
        "Install our mobile software and pay ₹4,999 subscription fee."
    )
    c2 = ce.process_text(obs2_text)
    cl2 = cl.analyze(c2)
    ae2 = ae.analyze(c2, cl2)
    se2 = se.discover_and_retrieve(c2, cl2, ae2)
    ee2 = ee.verify(c2, cl2, se2)
    te2 = te.analyze(c2, cl2, ae2, se2, ee2)
    fp2 = fe.create_or_match(c2, cl2, ae2, se2, ee2, te2)

    assert fp2.match_type in ("SEMANTIC_VARIANT", "STRUCTURAL_MATCH")

    decision2 = pe.decide(c2, cl2, ae2, se2, ee2, te2, fp2)

    assert decision2.decision == PolicyDecisionType.PAUSE
    assert decision2.severity == PolicySeverity.HIGH.value
    assert decision2.required_user_confirmation is True
    assert ReasonCode.PAYMENT_REQUEST in decision2.reason_codes
    assert ReasonCode.HIGH_IMPACT_ACTION in decision2.reason_codes
    assert ReasonCode.KNOWN_THREAT_SEMANTIC_VARIANT in decision2.reason_codes or ReasonCode.KNOWN_THREAT_STRUCTURAL_MATCH in decision2.reason_codes


def test_fresh_engine8_and_engine7_repository_determinism():
    """Prove that fresh Engine 8 + fresh Engine 7 instances produce 100% deterministic outputs."""
    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    def _execute_isolated_run():
        ce = ContentIntelligenceEngine()
        cl = ClaimIntelligenceEngine()
        ae = ActionIntelligenceEngine()
        se = SourceIntelligenceEngine(default_mode="FIXTURE")
        ee = EvidenceVerificationEngine()
        te = ThreatIntelligenceEngine()
        fe = ScamFingerprintEngine()
        pe = PolicyInterventionEngine()

        c = ce.process_text(raw_text)
        claims = cl.analyze(c)
        actions = ae.analyze(c, claims)
        sources = se.discover_and_retrieve(c, claims, actions)
        evidence = ee.verify(c, claims, sources)
        threat = te.analyze(c, claims, actions, sources, evidence)
        fingerprint = fe.create_or_match(c, claims, actions, sources, evidence, threat)
        return pe.decide(c, claims, actions, sources, evidence, threat, fingerprint)

    run1 = _execute_isolated_run()
    run2 = _execute_isolated_run()

    assert run1.decision == run2.decision == PolicyDecisionType.PAUSE
    assert run1.severity == run2.severity == PolicySeverity.HIGH.value
    assert run1.reason_codes == run2.reason_codes
    assert run1.user_message == run2.user_message
    assert run1.technical_message == run2.technical_message
    assert run1.required_user_confirmation == run2.required_user_confirmation == True
    assert run1.cooldown_seconds == run2.cooldown_seconds == 30


def test_secondary_negative_demonstration():
    """Secondary Negative Demonstration:
    'Learn what mutual funds are and how diversification can reduce concentration risk over the long term.'

    Expected:
    ALLOW
    INFORMATIONAL
    NO_INTERVENTION_REQUIRED
    Strictly NOT WARN, PAUSE, or BLOCK.
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

    assert decision.decision == PolicyDecisionType.ALLOW
    assert decision.severity == PolicySeverity.INFORMATIONAL.value
    assert decision.reason_codes == [ReasonCode.NO_INTERVENTION_REQUIRED.value]
    assert decision.decision not in (PolicyDecisionType.WARN, PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)
    assert decision.required_user_confirmation is False

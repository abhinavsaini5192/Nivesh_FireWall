"""Full 8-Engine End-to-End Integration Tests.

Validates complete data flow and provenance across:
Engine 1 (Content)
  -> Engine 2 (Claims)
  -> Engine 3 (Actions)
  -> Engine 4 (Sources)
  -> Engine 5 (Evidence)
  -> Engine 6 (Threat / Attack Path)
  -> Engine 7 (Scam Fingerprint & Collective Intelligence)
  -> Engine 8 (Policy & Intervention)
  -> PolicyDecision
"""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType, PolicyContext


def test_full_8_engine_end_to_end_pipeline():
    """Execute complete 1 -> 8 pipeline on benchmark content and verify provenance continuity."""
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

    # 1. Engine 1
    content = ce.process_text(raw_text)
    assert content.normalized.text is not None

    # 2. Engine 2
    claims = cl.analyze(content)
    assert len(claims.claims) >= 2

    # 3. Engine 3
    actions = ae.analyze(content, claims)
    assert len(actions.actions) >= 3

    # 4. Engine 4
    sources = se.discover_and_retrieve(content, claims, actions)
    assert len(sources.claim_sources) > 0

    # 5. Engine 5
    evidence = ee.verify(content, claims, sources)
    assert len(evidence.verifications) >= 2

    # 6. Engine 6
    threat = te.analyze(content, claims, actions, sources, evidence)
    assert len(threat.attack_path.nodes) >= 3

    # 7. Engine 7
    fingerprint = fe.create_or_match(content, claims, actions, sources, evidence, threat)
    assert fingerprint.fingerprint.fingerprint_id == "SFP-001"

    # 8. Engine 8
    decision = pe.decide(content, claims, actions, sources, evidence, threat, fingerprint)

    # Verify Decision Properties
    assert decision.decision == PolicyDecisionType.PAUSE
    assert decision.severity == "HIGH"
    assert decision.required_user_confirmation is True
    assert decision.cooldown_seconds == 30

    # Verify Provenance Continuity Across All 8 Engines
    assert set(decision.relevant_claim_ids) == {c.claim_id for c in claims.claims}
    assert set(decision.relevant_action_ids) == {a.action_id for a in actions.actions}
    assert set(decision.relevant_source_ids) == {doc.document_id for cs in sources.claim_sources for doc in cs.documents}
    assert len(decision.relevant_evidence_ids) == len(evidence.verifications)
    assert decision.relevant_fingerprint_id == fingerprint.fingerprint.fingerprint_id
    assert decision.policy_version == "8.0.0"

    # Verify User Override Demotion Flow
    context_override = PolicyContext(user_override=True)
    decision_override = pe.decide(content, claims, actions, sources, evidence, threat, fingerprint, context=context_override)
    assert decision_override.decision == PolicyDecisionType.WARN
    assert decision_override.required_user_confirmation is False


def test_full_8_engine_pipeline_benign_informational_content():
    """Execute complete 1 -> 8 pipeline on purely benign informational content."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()

    raw_text = "Learn what mutual funds are and how diversification protects your capital over the long term."

    content = ce.process_text(raw_text)
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)
    sources = se.discover_and_retrieve(content, claims, actions)
    evidence = ee.verify(content, claims, sources)
    threat = te.analyze(content, claims, actions, sources, evidence)
    fingerprint = fe.create_or_match(content, claims, actions, sources, evidence, threat)
    decision = pe.decide(content, claims, actions, sources, evidence, threat, fingerprint)

    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM)
    assert decision.required_user_confirmation is False
    assert decision.severity in ("NONE", "LOW")

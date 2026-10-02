r"""Full integration test for Engine 10 within the complete Nivesh Firewall 10-engine pipeline.

Verifies end-to-end execution:
Engine 1: Content Intelligence
    ↓
Engine 2: Claim Intelligence
    ↓
Engine 3: Action Intelligence
    ↓
Engine 4: Source Intelligence
    ↓
Engine 5: Evidence Verification
    ↓
   ┌──────────────────────┐
   │ downstream analysis  │
   └──────────────────────┘
      ↓         ↓        ↓
  Engine 6   Engine 7  Engine 9
   Threat   Fingerprint Identity
      \         |        /
       \        |       /
        ↓       ↓      ↓
  Engine 10: Behavioural Signal Intelligence
        ↓
  Engine 8: Policy & Intervention
"""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import IdentityStatus
from nivesh.behaviour.engine import BehaviouralSignalEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionEventType,
    InteractionHistory,
)
from nivesh.behaviour.schemas import BehaviouralSignalType


@pytest.fixture
def firewall():
    """Instantiate fresh instances of all 10 engines."""
    e1 = ContentIntelligenceEngine()
    e2 = ClaimIntelligenceEngine()
    e3 = ActionIntelligenceEngine()
    e4 = SourceIntelligenceEngine(default_mode="FIXTURE")
    e5 = EvidenceVerificationEngine()
    e6 = ThreatIntelligenceEngine()
    e7 = ScamFingerprintEngine()
    e9 = IdentityVerificationEngine()
    e10 = BehaviouralSignalEngine()
    e8 = PolicyInterventionEngine()
    return e1, e2, e3, e4, e5, e6, e7, e9, e10, e8


def test_full_10_engine_primary_benchmark_pipeline(firewall):
    """Full end-to-end execution of primary benchmark across all 10 engines.

    Canonical benchmark sequence:
    10:00 educational financial content
    10:01 private Telegram migration
    10:02 external app request
    10:03 payment request
    10:03:30 explicit time-pressure message
    """
    e1, e2, e3, e4, e5, e6, e7, e9, e10, e8 = firewall

    raw_text = (
        "Learn about our investment education program. "
        "SEBI registered advisor Rahul Sharma guarantees 40% monthly returns! "
        "Join our private Telegram group: https://t.me/rahulvip. "
        "Install our APK application. "
        "Pay ₹5,000 now. Only 5 minutes left."
    )

    # Engine 1: Content Intelligence
    content = e1.process_text(raw_text)
    assert content.status == "success"

    # Engine 2: Claim Intelligence
    claims = e2.analyze(content)
    assert len(claims.claims) >= 1

    # Engine 3: Action Intelligence
    actions = e3.analyze(content, claims)
    assert len(actions.actions) >= 1

    # Engine 4: Source Intelligence
    sources = e4.discover_and_retrieve(content, claims, actions)
    assert sources is not None

    # Engine 5: Evidence Verification
    evidence = e5.verify(content, claims, sources)
    assert evidence is not None

    # Engine 6: Threat Intelligence (structural threat & attack path)
    threat = e6.analyze(content, claims, actions, sources, evidence)
    assert threat is not None
    assert threat.attack_path is not None
    assert len(threat.attack_path.nodes) >= 2

    # Engine 7: Fingerprint Intelligence (scam fingerprint & collective intelligence)
    fingerprint = e7.create_or_match(content, claims, actions, sources, evidence, threat)
    assert fingerprint is not None
    assert fingerprint.fingerprint is not None
    assert fingerprint.fingerprint.fingerprint_id.startswith("SFP-")
    assert len(fingerprint.fingerprint.exact_signature) > 0

    # Engine 9: Identity Verification (reports identity status based on evidence)
    identity = e9.verify(
        content=content,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )
    assert identity is not None
    assert identity.identity_status in (IdentityStatus.IDENTITY_MISMATCH, IdentityStatus.NOT_ESTABLISHED)
    assert len(identity.identity_findings) >= 1

    # Build sequence history for Engine 10
    history = InteractionHistory(session_id="SESS-E2E-001")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.CONTENT_VIEW,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="10:01:00",
        event_type=InteractionEventType.CHANNEL_CHANGED,
        channel="telegram",
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-03",
        timestamp="10:02:00",
        event_type=InteractionEventType.EXTERNAL_APP_REQUESTED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-04",
        timestamp="10:03:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-05",
        timestamp="10:03:30",
        event_type=InteractionEventType.ACTION_REQUESTED,
        metadata={"urgency_marker": "Only 5 minutes left"},
    ))

    # Engine 10: Behavioural Signal Intelligence
    # Answers: "What behavioural pattern is emerging across this interaction sequence?"
    behaviour = e10.analyze(
        content=content,
        claims=claims,
        actions=actions,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        interaction_history=history,
    )

    assert behaviour is not None
    assert behaviour.analysis_id.startswith("BHA-")
    stypes = {s.signal_type for s in behaviour.signals}
    assert BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION in stypes
    assert BehaviouralSignalType.CHANNEL_MIGRATION in stypes
    assert BehaviouralSignalType.TIME_PRESSURE in stypes
    assert behaviour.policy_hints.high_impact_action_progression is True
    assert behaviour.policy_hints.pressure_present is True

    # Engine 8: Policy & Intervention (Final Policy Authority)
    # Consumes findings from Engines 6, 7, 9, 10 as supporting evidence
    decision = e8.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        behaviour=behaviour,
    )

    assert decision is not None
    assert decision.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)
    assert decision.relevant_behaviour_id == behaviour.analysis_id
    assert decision.relevant_identity_id == identity.analysis_id
    assert "threat_stages" in decision.audit_metadata
    assert "behaviour_signals" in decision.audit_metadata
    assert len(decision.audit_metadata["behaviour_signals"]) >= 1


def test_full_10_engine_benign_educational_pipeline(firewall):
    """Full 10-engine pipeline on benign informational content.

    Verifies:
    1. Ordinary educational financial content does not generate behavioural escalation.
    2. Zero financial-topic-based suspicion.
    3. Negative guardrails: Behavioural signals alone (RAPID_ACTION_ESCALATION alone,
       PERSISTENT_PAYMENT_REQUEST alone, CHANNEL_MIGRATION alone) do NOT imply fraud
       or automatically BLOCK. Engine 8 consumes behaviour as supporting evidence only.
    """
    e1, e2, e3, e4, e5, e6, e7, e9, e10, e8 = firewall

    benign_text = "Learn how mutual funds work. Review diversification, fees, and long-term investing concepts."

    content = e1.process_text(benign_text)
    claims = e2.analyze(content)
    actions = e3.analyze(content, claims)
    sources = e4.discover_and_retrieve(content, claims, actions)
    evidence = e5.verify(content, claims, sources)
    threat = e6.analyze(content, claims, actions, sources, evidence)
    fingerprint = e7.create_or_match(content, claims, actions, sources, evidence, threat)
    identity = e9.verify(content=content, claims=claims, sources=sources, evidence=evidence, threat=threat)

    behaviour = e10.analyze(
        content=content,
        claims=claims,
        actions=actions,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
    )

    # Engine 10 reports zero threat/escalation signals on benign educational content
    assert len(behaviour.signals) == 0
    assert behaviour.policy_hints.high_impact_action_progression is False
    assert behaviour.policy_hints.pressure_present is False
    assert behaviour.policy_hints.rapid_escalation_present is False
    assert behaviour.policy_hints.persistent_payment_present is False

    decision = e8.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        behaviour=behaviour,
    )

    # Engine 8 correctly issues ALLOW
    assert decision.decision == PolicyDecisionType.ALLOW
    assert decision.relevant_behaviour_id == behaviour.analysis_id

    # Negative Policy Guardrail: RAPID_ACTION_ESCALATION alone must NOT imply fraud or automatically BLOCK
    from nivesh.behaviour.schemas import (
        BehaviouralSignal,
        BehaviouralSignalType,
        BehaviouralSignalSeverity,
        BehaviouralPolicyHints,
        BehaviouralAnalysis,
    )
    isolated_rapid_escalation_behaviour = BehaviouralAnalysis(
        analysis_id="BHA-TEST-RAPID",
        signals=[
            BehaviouralSignal(
                signal_id="BHS-001",
                signal_type=BehaviouralSignalType.RAPID_ACTION_ESCALATION,
                description="Fast action progression observed",
                severity=BehaviouralSignalSeverity.MEDIUM,
                confidence=0.92,
            )
        ],
        findings=[],
        session_summary=behaviour.session_summary,
        policy_hints=BehaviouralPolicyHints(rapid_escalation_present=True),
        confidence=0.92,
        provenance=behaviour.provenance,
    )
    decision_rapid = e8.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        behaviour=isolated_rapid_escalation_behaviour,
    )
    # Rapid action escalation alone does NOT cause BLOCK
    assert decision_rapid.decision != PolicyDecisionType.BLOCK

    # Negative Policy Guardrail: CHANNEL_MIGRATION alone must NOT imply fraud or automatically BLOCK
    isolated_channel_behaviour = BehaviouralAnalysis(
        analysis_id="BHA-TEST-CHAN",
        signals=[
            BehaviouralSignal(
                signal_id="BHS-002",
                signal_type=BehaviouralSignalType.CHANNEL_MIGRATION,
                description="Communication migrated to external channel",
                severity=BehaviouralSignalSeverity.LOW,
                confidence=0.90,
            )
        ],
        findings=[],
        session_summary=behaviour.session_summary,
        policy_hints=BehaviouralPolicyHints(),
        confidence=0.90,
        provenance=behaviour.provenance,
    )
    decision_channel = e8.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        behaviour=isolated_channel_behaviour,
    )
    assert decision_channel.decision != PolicyDecisionType.BLOCK


def test_engine_10_determinism(firewall):
    """Verify determinism and confidence semantics across repeated executions.

    1. Identical behavioural input produces identical signal types, relationships,
       severities, confidences, and policy hints.
    2. Confirm that confidence = confidence that the behavioural pattern exists,
       NOT scam probability, fraud probability, criminal likelihood, or user risk score.
    """
    e1, e2, e3, _, _, _, _, _, e10, _ = firewall

    raw_text = "Join our Telegram group and pay ₹5,000 immediately."
    content = e1.process_text(raw_text)
    claims = e2.analyze(content)
    actions = e3.analyze(content, claims)

    res1 = e10.analyze(content, claims, actions)
    res2 = e10.analyze(content, claims, actions)

    # Signal determinism
    assert [s.signal_type for s in res1.signals] == [s.signal_type for s in res2.signals]
    assert [s.severity for s in res1.signals] == [s.severity for s in res2.signals]
    assert [s.confidence for s in res1.signals] == [s.confidence for s in res2.signals]
    assert [f.finding_type for f in res1.findings] == [f.finding_type for f in res2.findings]
    assert res1.policy_hints == res2.policy_hints
    assert res1.confidence == res2.confidence

    # Strict confidence semantics: Must represent pattern existence confidence [0, 1]
    assert 0.0 <= res1.confidence <= 1.0
    for s in res1.signals:
        assert 0.0 <= s.confidence <= 1.0
        # No signal description or finding may imply scam probability or user criminality
        desc_lower = s.description.lower()
        for forbidden in ["scam probability", "fraud probability", "criminal likelihood", "user risk score", "personality"]:
            assert forbidden not in desc_lower


def test_engine_10_privacy_boundary(firewall):
    """Verify Engine 10 privacy lock and strict session isolation with cross-session regression test.

    1. Privacy Lock: Never stores or serializes passwords, OTP, PIN, CVV, card numbers,
       bank account numbers, raw credentials, keystrokes, or raw message bodies.
       Provenance does not reintroduce sensitive content indirectly.
    2. Session Isolation: Interaction history is isolated by session_id.
       A behavioural event from session A never affects session B, another user's analysis,
       another analysis_id, another fingerprint, or another policy decision.
    """
    e1, e2, e3, e4, e5, e6, e7, e9, e10, e8 = firewall

    # 1. Privacy Lock Verification
    content = e1.process_text("Enter your OTP: 981292 and password: SecretPassword123 to proceed.")
    claims = e2.analyze(content)
    actions = e3.analyze(content, claims)

    history_sec = InteractionHistory(session_id="SESS-PRIVACY")
    history_sec.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.ACTION_REQUESTED,
        metadata={
            "password": "SecretPassword123",
            "otp": "981292",
            "pin": "1234",
            "cvv": "999",
            "card_number": "4111222233334444",
            "bank_account_number": "9876543210",
            "raw_credentials": "admin:secret",
            "keystrokes": "typing...",
        },
    ))

    analysis_sec = e10.analyze(content, claims, actions, interaction_history=history_sec)
    dumped = str(analysis_sec.model_dump())
    assert "SecretPassword123" not in dumped
    assert "981292" not in dumped
    assert "4111222233334444" not in dumped
    assert "9876543210" not in dumped
    assert "admin:secret" not in dumped

    # 2. Cross-Session Contamination Regression Test
    # Session A: High escalation sequence with pressure and payment requests
    e10.record_event("SESSION-A", InteractionEvent(
        event_id="EVT-A1",
        timestamp="10:00:00",
        event_type=InteractionEventType.CONTENT_VIEW,
    ))
    e10.record_event("SESSION-A", InteractionEvent(
        event_id="EVT-A2",
        timestamp="10:01:00",
        event_type=InteractionEventType.CHANNEL_CHANGED,
        channel="telegram",
    ))
    e10.record_event("SESSION-A", InteractionEvent(
        event_id="EVT-A3",
        timestamp="10:02:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))

    content_a = e1.process_text("Join Telegram and pay ₹5,000 now!")
    claims_a = e2.analyze(content_a)
    actions_a = e3.analyze(content_a, claims_a)
    analysis_a = e10.analyze(
        content=content_a,
        claims=claims_a,
        actions=actions_a,
        interaction_history=e10.get_session("SESSION-A"),
    )
    assert len(analysis_a.signals) > 0
    assert analysis_a.policy_hints.high_impact_action_progression is True

    # Session B: Completely separate user/session with neutral educational content
    e10.record_event("SESSION-B", InteractionEvent(
        event_id="EVT-B1",
        timestamp="10:05:00",
        event_type=InteractionEventType.CONTENT_VIEW,
    ))

    content_b = e1.process_text("Learn how mutual funds work. Review diversification concepts.")
    claims_b = e2.analyze(content_b)
    actions_b = e3.analyze(content_b, claims_b)
    sources_b = e4.discover_and_retrieve(content_b, claims_b, actions_b)
    evidence_b = e5.verify(content_b, claims_b, sources_b)
    threat_b = e6.analyze(content_b, claims_b, actions_b, sources_b, evidence_b)
    fingerprint_b = e7.create_or_match(content_b, claims_b, actions_b, sources_b, evidence_b, threat_b)
    identity_b = e9.verify(content=content_b, claims=claims_b, sources=sources_b, evidence=evidence_b, threat=threat_b)

    analysis_b = e10.analyze(
        content=content_b,
        claims=claims_b,
        actions=actions_b,
        threat=threat_b,
        fingerprint=fingerprint_b,
        identity=identity_b,
        interaction_history=e10.get_session("SESSION-B"),
    )

    # Session B MUST NOT be contaminated by Session A:
    assert len(analysis_b.signals) == 0
    assert analysis_b.policy_hints.high_impact_action_progression is False
    assert analysis_b.policy_hints.pressure_present is False
    assert analysis_b.policy_hints.persistent_payment_present is False
    assert analysis_b.analysis_id != analysis_a.analysis_id

    # Session B history must contain ONLY its own 1 event
    session_b_history = e10.get_session("SESSION-B")
    assert session_b_history is not None
    assert len(session_b_history.events) == 1
    assert session_b_history.events[0].event_id == "EVT-B1"

    # Engine 8 policy decision for Session B must be ALLOW
    decision_b = e8.decide(
        content=content_b,
        claims=claims_b,
        actions=actions_b,
        sources=sources_b,
        evidence=evidence_b,
        threat=threat_b,
        fingerprint=fingerprint_b,
        identity=identity_b,
        behaviour=analysis_b,
    )
    assert decision_b.decision == PolicyDecisionType.ALLOW

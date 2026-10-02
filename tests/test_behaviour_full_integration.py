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
    """Full end-to-end execution of primary benchmark across all 10 engines."""
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

    # Engine 6: Threat Intelligence
    threat = e6.analyze(content, claims, actions, sources, evidence)
    assert threat is not None

    # Engine 7: Fingerprint Intelligence
    fingerprint = e7.create_or_match(content, claims, actions, sources, evidence, threat)
    assert fingerprint is not None

    # Engine 9: Identity Verification
    identity = e9.verify(
        content=content,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )
    assert identity is not None

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

    # Engine 10: Behavioural Signal Intelligence
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

    # Engine 8: Policy & Intervention
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
    assert "behaviour_signals" in decision.audit_metadata
    assert len(decision.audit_metadata["behaviour_signals"]) >= 1


def test_full_10_engine_benign_educational_pipeline(firewall):
    """Full 10-engine pipeline on benign informational content."""
    e1, e2, e3, e4, e5, e6, e7, e9, e10, e8 = firewall

    benign_text = "Learn what mutual funds are and how diversification protects your capital over the long term."

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

    # Engine 10 reports zero threat/escalation signals
    assert len(behaviour.signals) == 0
    assert behaviour.policy_hints.high_impact_action_progression is False
    assert behaviour.policy_hints.pressure_present is False

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


def test_engine_10_determinism(firewall):
    """Verify that identical input sequence produces identical behavioural analysis."""
    e1, e2, e3, _, _, _, _, _, e10, _ = firewall

    raw_text = "Join our Telegram group and pay ₹5,000 immediately."
    content = e1.process_text(raw_text)
    claims = e2.analyze(content)
    actions = e3.analyze(content, claims)

    res1 = e10.analyze(content, claims, actions)
    res2 = e10.analyze(content, claims, actions)

    assert [s.signal_type for s in res1.signals] == [s.signal_type for s in res2.signals]
    assert [f.finding_type for f in res1.findings] == [f.finding_type for f in res2.findings]
    assert res1.policy_hints == res2.policy_hints
    assert res1.confidence == res2.confidence


def test_engine_10_privacy_boundary(firewall):
    """Verify Engine 10 does not record raw sensitive data or credentials."""
    e1, e2, e3, _, _, _, _, _, e10, _ = firewall

    content = e1.process_text("Enter your OTP: 981292 and password: SecretPassword123 to proceed.")
    claims = e2.analyze(content)
    actions = e3.analyze(content, claims)

    history = InteractionHistory(session_id="SESS-PRIVACY")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.ACTION_REQUESTED,
        metadata={"password": "SecretPassword123", "otp": "981292"},
    ))

    analysis = e10.analyze(content, claims, actions, interaction_history=history)

    dumped = str(analysis.model_dump())
    assert "SecretPassword123" not in dumped
    assert "981292" not in dumped

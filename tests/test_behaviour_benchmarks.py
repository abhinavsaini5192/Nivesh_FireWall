"""Benchmark tests for Engine 10: Behavioural Signal Intelligence Engine.

Covers:
- Primary Benchmark (Section 30): Progressive escalation across multi-step flow
- Secondary Persistence Benchmark (Section 31): Persistent payment & retries after decline
- Benign Benchmark (Section 32): Informational financial education without escalation
"""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.behaviour.engine import BehaviouralSignalEngine
from nivesh.behaviour.schemas import (
    BehaviouralSignalType,
    BehaviouralFindingType,
)
from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionEventType,
    InteractionHistory,
)
from nivesh.behaviour.temporal import TemporalThresholds


@pytest.fixture
def pipeline():
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    be = BehaviouralSignalEngine()
    return ce, cl, ae, be


def test_primary_behavioural_benchmark(pipeline):
    """Primary Benchmark (Section 30).

    Sequence:
    10:00 "Learn about our investment education program."
    10:01 "Join our private Telegram group."
    10:02 "Install our application."
    10:03 "Pay ₹5,000 now."
    10:03:30 "Only 5 minutes left."

    Expected Behavioural Findings:
    - INFORMATION_TO_TRANSACTION_SHIFT
    - RAPID_ACTION_ESCALATION
    - LOW_TO_HIGH_IMPACT_TRANSITION
    - CHANNEL_MIGRATION
    - TIME_PRESSURE
    """
    ce, cl, ae, be = pipeline

    full_text = (
        "Learn about our investment education program. "
        "Join our private Telegram group: https://t.me/investment_edu. "
        "Install our application from https://example.com/app.apk. "
        "Pay ₹5,000 now. "
        "Only 5 minutes left."
    )
    content = ce.process_text(full_text)
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    # Reconstruct the chronological interaction history
    history = InteractionHistory(session_id="SESS-PRIMARY-001")
    history.add_event(InteractionEvent(
        event_id="EVT-001",
        timestamp="10:00:00",
        event_type=InteractionEventType.CONTENT_VIEW,
        metadata={"text": "Learn about our investment education program."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-002",
        timestamp="10:01:00",
        event_type=InteractionEventType.CHANNEL_CHANGED,
        channel="telegram",
        metadata={"text": "Join our private Telegram group."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-003",
        timestamp="10:02:00",
        event_type=InteractionEventType.EXTERNAL_APP_REQUESTED,
        metadata={"text": "Install our application."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-004",
        timestamp="10:03:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
        metadata={"text": "Pay ₹5,000 now."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-005",
        timestamp="10:03:30",
        event_type=InteractionEventType.ACTION_REQUESTED,
        metadata={"text": "Only 5 minutes left."},
    ))

    analysis = be.analyze(
        content=content,
        claims=claims,
        actions=actions,
        interaction_history=history,
    )

    detected_signals = {s.signal_type for s in analysis.signals}
    detected_findings = {f.finding_type for f in analysis.findings}

    # Verify expected behavioural findings / signals
    assert BehaviouralSignalType.INFORMATION_TO_TRANSACTION_SHIFT in detected_signals
    assert BehaviouralSignalType.RAPID_ACTION_ESCALATION in detected_signals
    assert BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION in detected_signals
    assert BehaviouralSignalType.CHANNEL_MIGRATION in detected_signals
    assert BehaviouralSignalType.TIME_PRESSURE in detected_signals

    # Verify structured policy hints
    hints = analysis.policy_hints
    assert hints.information_to_transaction_shift is True
    assert hints.rapid_escalation_present is True
    assert hints.high_impact_action_progression is True
    assert hints.pressure_present is True

    # Verify session summary
    assert analysis.session_summary.event_count == 5
    assert analysis.session_summary.duration_seconds == 210.0
    assert analysis.session_summary.high_impact_action_count >= 1

    # STRICT GUARDRAILS (Prompt Section 3 & 30):
    # 1. Must NOT determine legal fraud or scam probability
    dumped = analysis.model_dump()
    assert "scam_probability" not in dumped
    assert "fraud_probability" not in dumped
    assert "criminal_probability" not in dumped

    # 2. Must NOT emit policy decisions (BLOCK/WARN/PAUSE)
    assert not hasattr(analysis, "decision")
    assert not hasattr(analysis, "policy_decision")

    # 3. Must NOT label people as scammers
    for s in analysis.signals:
        assert "scammer" not in s.description.lower()
        assert "fraudster" not in s.description.lower()


def test_secondary_persistence_benchmark(pipeline):
    """Secondary Persistence Benchmark (Section 31).

    Sequence:
    User: "No, I don't want to pay."
    System: "Pay ₹5,000 to continue."
    System: "Your access will expire unless you pay."
    System: "Pay now."

    Expected Behavioural Signals:
    - RETRY_AFTER_DECLINE
    - PERSISTENT_PAYMENT_REQUEST
    - REPEATED_URGENCY
    """
    ce, cl, ae, be = pipeline

    content = ce.process_text("Pay now. Your access will expire unless you pay.")
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    history = InteractionHistory(session_id="SESS-PERSISTENCE-002")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="11:00:00",
        event_type=InteractionEventType.USER_DECLINED,
        user_initiated=True,
        metadata={"text": "No, I don't want to pay."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="11:00:30",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
        system_initiated=True,
        metadata={"text": "Pay ₹5,000 to continue."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-03",
        timestamp="11:01:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
        system_initiated=True,
        metadata={"text": "Your access will expire unless you pay."},
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-04",
        timestamp="11:01:30",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
        system_initiated=True,
        metadata={"text": "Pay now."},
    ))

    analysis = be.analyze(
        content=content,
        claims=claims,
        actions=actions,
        interaction_history=history,
    )

    detected_signals = {s.signal_type for s in analysis.signals}

    # Verify persistence benchmark signals
    assert BehaviouralSignalType.RETRY_AFTER_DECLINE in detected_signals
    assert BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST in detected_signals
    assert BehaviouralSignalType.REPEATED_URGENCY in detected_signals

    # Verify policy hints
    hints = analysis.policy_hints
    assert hints.repeated_request_present is True
    assert hints.persistent_payment_present is True
    assert hints.pressure_present is True

    # Strict constraint: Observable events only, no psychological diagnosis
    for s in analysis.signals:
        desc = s.description.lower()
        for forbidden in ["greedy", "fearful", "desperate", "naive", "uneducated", "mentally unstable"]:
            assert forbidden not in desc


def test_benign_benchmark(pipeline):
    """Benign Benchmark (Section 32).

    Content:
    "Learn how mutual funds work.
    Review diversification, fees, and long-term investing concepts."

    Expected:
    - Zero behavioural escalation signals
    - Financial subject matter alone must NOT create threat signals
    """
    ce, cl, ae, be = pipeline

    content = ce.process_text(
        "Learn how mutual funds work. Review diversification, fees, and long-term investing concepts."
    )
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    analysis = be.analyze(
        content=content,
        claims=claims,
        actions=actions,
        interaction_history=None,
    )

    # Zero escalation signals
    assert len(analysis.signals) == 0
    assert len(analysis.findings) == 0

    # Policy hints must all be false
    hints = analysis.policy_hints
    assert hints.high_impact_action_progression is False
    assert hints.pressure_present is False
    assert hints.repeated_request_present is False
    assert hints.rapid_escalation_present is False
    assert hints.information_to_transaction_shift is False
    assert hints.persistent_payment_present is False
    assert hints.persistent_credential_present is False

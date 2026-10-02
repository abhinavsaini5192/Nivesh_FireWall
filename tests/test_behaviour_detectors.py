"""Tests for Engine 10 detectors: pressure, escalation, persistence, and channel migration.

Verifies behavioral signal generation, configurable threshold adherence,
and strict negative constraints (no scammer labels, no psychological inferences).
"""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.behaviour.schemas import (
    BehaviouralSignalType,
    BehaviouralSignalSeverity,
)
from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionEventType,
    InteractionHistory,
)
from nivesh.behaviour.temporal import TemporalThresholds
from nivesh.behaviour.pressure_detector import PressureDetector
from nivesh.behaviour.escalation_detector import EscalationDetector
from nivesh.behaviour.persistence_detector import PersistenceDetector
from nivesh.behaviour.channel_detector import ChannelDetector


@pytest.fixture
def engines():
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    return ce, cl, ae


# ==============================================================================
# Pressure Detector Tests
# ==============================================================================

def test_pressure_detector_single_time_pressure(engines):
    """Verify single urgency phrase produces TIME_PRESSURE but NOT REPEATED_URGENCY."""
    ce, cl, _ = engines
    content = ce.process_text("Act now to secure your spot in our program.")
    claims = cl.analyze(content)

    detector = PressureDetector()
    signals = detector.detect(content, claims)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.TIME_PRESSURE in stypes
    # Negative constraint: single phrase must NOT be labeled repeated urgency
    assert BehaviouralSignalType.REPEATED_URGENCY not in stypes

    # Negative constraint: no scammer labels
    for s in signals:
        assert "scam" not in s.signal_type.value.lower()
        assert "fraud" not in s.description.lower()


def test_pressure_detector_fomo_pressure(engines):
    """Verify FOMO language produces FOMO_PRESSURE."""
    ce, cl, _ = engines
    content = ce.process_text("Don't miss this exclusive opportunity, only 2 spots left!")
    claims = cl.analyze(content)

    detector = PressureDetector()
    signals = detector.detect(content, claims)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.FOMO_PRESSURE in stypes


def test_pressure_detector_repeated_urgency(engines):
    """Verify multiple urgency phrases across content/history produce REPEATED_URGENCY."""
    ce, cl, _ = engines
    content = ce.process_text("Act now! Only 2 minutes left! Pay immediately before offer expires!")
    claims = cl.analyze(content)

    detector = PressureDetector()
    signals = detector.detect(content, claims)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.TIME_PRESSURE in stypes
    assert BehaviouralSignalType.REPEATED_URGENCY in stypes


# ==============================================================================
# Escalation Detector Tests
# ==============================================================================

def test_escalation_detector_information_to_transaction_shift(engines):
    """Verify transition from educational introduction to payment request."""
    ce, cl, ae = engines
    content = ce.process_text(
        "Learn about our investment education program. Review stock market basics. Then pay ₹5,000 now."
    )
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    detector = EscalationDetector()
    signals = detector.detect(content, claims, actions)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.INFORMATION_TO_TRANSACTION_SHIFT in stypes
    assert BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION in stypes


def test_escalation_detector_rapid_action_escalation(engines):
    """Verify rapid escalation detected when timing satisfies configured threshold."""
    ce, cl, ae = engines
    content = ce.process_text("Learn about investing and pay ₹5,000.")
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    history = InteractionHistory(session_id="SESS-ESC-01")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.CONTENT_VIEW,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="10:02:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))

    # Rapid escalation threshold = 300s (5 mins); duration = 120s (2 mins)
    detector = EscalationDetector(TemporalThresholds(rapid_escalation_seconds_threshold=300.0))
    signals = detector.detect(content, claims, actions, interaction_history=history)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.RAPID_ACTION_ESCALATION in stypes


def test_escalation_detector_negative_slow_interval(engines):
    """Verify rapid escalation is NOT flagged when time difference exceeds threshold."""
    ce, cl, ae = engines
    content = ce.process_text("Learn about investing and pay ₹5,000.")
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    history = InteractionHistory(session_id="SESS-ESC-02")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.CONTENT_VIEW,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="10:45:00",  # 45 minutes later
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))

    detector = EscalationDetector(TemporalThresholds(rapid_escalation_seconds_threshold=300.0))
    signals = detector.detect(content, claims, actions, interaction_history=history)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.RAPID_ACTION_ESCALATION not in stypes


# ==============================================================================
# Persistence Detector Tests
# ==============================================================================

def test_persistence_detector_retry_after_decline(engines):
    """Verify retry after explicit decline generates RETRY_AFTER_DECLINE."""
    _, _, ae = engines

    history = InteractionHistory(session_id="SESS-PER-01")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="10:01:00",
        event_type=InteractionEventType.USER_DECLINED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-03",
        timestamp="10:02:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))

    detector = PersistenceDetector()
    signals = detector.detect(interaction_history=history)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.RETRY_AFTER_DECLINE in stypes
    assert BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST in stypes


def test_persistence_detector_negative_single_message_no_history():
    """Negative rule: Do NOT infer repetition or retries from a single interaction without history."""
    detector = PersistenceDetector()
    signals = detector.detect(interaction_history=None)
    assert len(signals) == 0

    history_single = InteractionHistory(session_id="SESS-PER-SINGLE")
    history_single.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))
    signals_single = detector.detect(interaction_history=history_single)
    assert len(signals_single) == 0


def test_persistence_detector_user_override_and_repeated_warning_override():
    """Verify all 5 user response patterns (HESITATION, DECLINE, OVERRIDE, WARNING_OVERRIDE, REPEATED_WARNING_OVERRIDE).

    Strict neutrality constraint: All 5 are observable interaction events only,
    never psychological or character judgments (fearful, greedy, naive, impulsive,
    desperate, uneducated, untrustworthy, etc.).
    """
    history = InteractionHistory(session_id="SESS-PER-OVR")
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.USER_HESITATION,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="10:00:15",
        event_type=InteractionEventType.USER_DECLINED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-03",
        timestamp="10:00:30",
        event_type=InteractionEventType.WARNING_SHOWN,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-04",
        timestamp="10:00:45",
        event_type=InteractionEventType.USER_OVERRIDE,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-05",
        timestamp="10:01:00",
        event_type=InteractionEventType.WARNING_SHOWN,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-06",
        timestamp="10:01:30",
        event_type=InteractionEventType.USER_OVERRIDE,
    ))

    detector = PersistenceDetector()
    signals = detector.detect(interaction_history=history)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.USER_HESITATION in stypes
    assert BehaviouralSignalType.USER_DECLINE in stypes
    assert BehaviouralSignalType.WARNING_OVERRIDE in stypes
    assert BehaviouralSignalType.REPEATED_WARNING_OVERRIDE in stypes

    # Strict constraint: Override description does NOT judge user character, intelligence, or rationality
    forbidden_terms = [
        "fearful", "greedy", "naive", "impulsive", "desperate",
        "uneducated", "untrustworthy", "careless", "irrational",
        "foolish", "vulnerable", "criminal", "personality", "mental state"
    ]
    for s in signals:
        desc = s.description.lower()
        for forbidden in forbidden_terms:
            assert forbidden not in desc, f"Forbidden psychological term '{forbidden}' found in description: {desc}"


# ==============================================================================
# Channel Detector Tests
# ==============================================================================

def test_channel_detector_migration_to_telegram(engines):
    """Verify migration from web to Telegram is detected objectively."""
    ce, cl, ae = engines
    content = ce.process_text("Visit our website and join our private Telegram group: https://t.me/investvip")
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    detector = ChannelDetector()
    signals = detector.detect(content, actions)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.CHANNEL_MIGRATION in stypes
    assert BehaviouralSignalType.PRIVATE_CHANNEL_ESCALATION in stypes


def test_channel_detector_negative_neutral_telegram_reference(engines):
    """Negative rule: Telegram mention alone without migration does not create threat labels."""
    ce, _, ae = engines
    content = ce.process_text("Learn about our educational articles published on various platforms.")
    actions = ae.analyze(content)

    detector = ChannelDetector()
    signals = detector.detect(content, actions)

    stypes = {s.signal_type for s in signals}
    assert BehaviouralSignalType.CHANNEL_MIGRATION not in stypes
    assert BehaviouralSignalType.PRIVATE_CHANNEL_ESCALATION not in stypes

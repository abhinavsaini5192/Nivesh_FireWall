"""Tests for Engine 10 Behavioural Signal Intelligence schemas and event models.

Verifies typing, Pydantic validation, serialization, privacy sanitization,
and strict non-psychological boundaries.
"""

import pytest
from datetime import datetime, timezone
from nivesh.behaviour.schemas import (
    BehaviouralSignalType,
    BehaviouralFindingType,
    BehaviouralSignalSeverity,
    BehaviouralSignal,
    BehaviouralFinding,
    SessionBehaviourSummary,
    BehaviouralPolicyHints,
    BehaviouralProvenance,
    BehaviouralAnalysis,
    ENGINE_VERSION,
)
from nivesh.behaviour.event_model import (
    InteractionEventType,
    InteractionEvent,
    InteractionHistory,
    FORBIDDEN_METADATA_KEYS,
)
from nivesh.behaviour.temporal import (
    TemporalThresholds,
    parse_timestamp,
    compute_duration_seconds,
    is_rapid_interval,
)


def test_behavioural_signal_types_taxonomy():
    """Verify controlled taxonomy covers pressure, escalation, persistence, and channels."""
    pressure_types = {
        BehaviouralSignalType.URGENCY_ESCALATION,
        BehaviouralSignalType.REPEATED_URGENCY,
        BehaviouralSignalType.TIME_PRESSURE,
        BehaviouralSignalType.FOMO_PRESSURE,
    }
    escalation_types = {
        BehaviouralSignalType.PROGRESSIVE_COMMITMENT,
        BehaviouralSignalType.RAPID_ACTION_ESCALATION,
        BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION,
        BehaviouralSignalType.INFORMATION_TO_TRANSACTION_SHIFT,
    }
    persistence_types = {
        BehaviouralSignalType.REPEATED_ACTION_REQUEST,
        BehaviouralSignalType.RETRY_AFTER_DECLINE,
        BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST,
        BehaviouralSignalType.PERSISTENT_CREDENTIAL_REQUEST,
    }
    channel_types = {
        BehaviouralSignalType.CHANNEL_MIGRATION,
        BehaviouralSignalType.RAPID_CHANNEL_MIGRATION,
        BehaviouralSignalType.PRIVATE_CHANNEL_ESCALATION,
    }
    user_types = {
        BehaviouralSignalType.USER_HESITATION,
        BehaviouralSignalType.USER_DECLINE,
        BehaviouralSignalType.USER_OVERRIDE,
        BehaviouralSignalType.WARNING_OVERRIDE,
        BehaviouralSignalType.REPEATED_WARNING_OVERRIDE,
    }

    all_defined = {t for t in BehaviouralSignalType}
    expected = pressure_types | escalation_types | persistence_types | channel_types | user_types
    assert expected.issubset(all_defined)


def test_interaction_event_privacy_sanitization():
    """Verify forbidden sensitive keys (passwords, OTPs, PINs, card numbers) are automatically stripped."""
    event = InteractionEvent(
        event_id="EVT-001",
        timestamp="2026-10-02T10:00:00Z",
        event_type=InteractionEventType.ACTION_REQUESTED,
        action_id="ACT-001",
        metadata={
            "safe_key": "safe_value",
            "password": "secret_password_123",
            "OTP": "992812",
            "pin": "1234",
            "card_number": "4111222233334444",
            "cvv": "999",
            "keystrokes": "user_typed_keys",
        },
    )

    # Allowed key remains
    assert event.metadata["safe_key"] == "safe_value"

    # All forbidden keys must be stripped
    for forbidden in FORBIDDEN_METADATA_KEYS:
        assert forbidden not in event.metadata
        assert forbidden.upper() not in event.metadata


def test_interaction_history_ordering_and_recomputation():
    """Verify InteractionHistory properly sequences events and computes boundaries."""
    history = InteractionHistory(session_id="SESS-101")
    assert history.event_count == 0
    assert history.started_at is None
    assert history.last_event_at is None

    evt1 = InteractionEvent(
        event_id="EVT-001",
        timestamp="2026-10-02T10:00:00Z",
        event_type=InteractionEventType.CONTENT_VIEW,
    )
    evt2 = InteractionEvent(
        event_id="EVT-002",
        timestamp="2026-10-02T10:01:00Z",
        event_type=InteractionEventType.CHANNEL_CHANGED,
        channel="telegram",
    )
    evt3 = InteractionEvent(
        event_id="EVT-003",
        timestamp="2026-10-02T10:03:00Z",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    )

    history.add_event(evt1)
    history.add_event(evt2)
    history.add_event(evt3)

    assert history.event_count == 3
    assert history.started_at == "2026-10-02T10:00:00Z"
    assert history.last_event_at == "2026-10-02T10:03:00Z"

    sorted_evts = history.get_sorted_events()
    assert [e.event_id for e in sorted_evts] == ["EVT-001", "EVT-002", "EVT-003"]
    assert len(history.filter_by_type(InteractionEventType.PAYMENT_REQUESTED)) == 1


def test_temporal_thresholds_and_intervals():
    """Verify temporal calculations, clock string parsing, and configurable thresholds."""
    thresholds = TemporalThresholds(
        rapid_escalation_seconds_threshold=300.0,
        rapid_channel_migration_seconds_threshold=180.0,
    )

    assert thresholds.rapid_escalation_seconds_threshold == 300.0
    assert thresholds.rapid_channel_migration_seconds_threshold == 180.0

    # Clock strings
    dt1 = parse_timestamp("10:00")
    dt2 = parse_timestamp("10:03:30")
    assert dt1 is not None
    assert dt2 is not None

    dur = compute_duration_seconds("10:00", "10:03:30")
    assert dur == 210.0

    # Interval checks
    assert is_rapid_interval("10:00", "10:03:30", threshold_seconds=300.0) is True
    assert is_rapid_interval("10:00", "10:03:30", threshold_seconds=180.0) is False


def test_behavioural_analysis_serialization():
    """Verify BehaviouralAnalysis schema validates and serializes to dict/json cleanly."""
    signal = BehaviouralSignal(
        signal_id="BHS-001",
        signal_type=BehaviouralSignalType.TIME_PRESSURE,
        description="Time pressure observed in prompts.",
        severity=BehaviouralSignalSeverity.MEDIUM,
        confidence=0.92,
        evidence=["Urgency detected: 'Only 5 minutes left'"],
    )
    finding = BehaviouralFinding(
        finding_id="BHF-001",
        finding_type=BehaviouralFindingType.TIME_PRESSURE,
        description="Time-limited urgency demands observed.",
        basis="Content or prompt commands user to act before an immediate time limit.",
        supporting_signal_ids=["BHS-001"],
        confidence=0.92,
    )
    summary = SessionBehaviourSummary(
        session_id="SESS-001",
        event_count=3,
        action_count=2,
        high_impact_action_count=1,
    )
    hints = BehaviouralPolicyHints(
        pressure_present=True,
        high_impact_action_progression=True,
    )
    provenance = BehaviouralProvenance(
        engine_version=ENGINE_VERSION,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        content_id="CNT-001",
        claims_count=2,
        actions_count=2,
        events_count=3,
    )

    analysis = BehaviouralAnalysis(
        analysis_id="BHA-001",
        signals=[signal],
        findings=[finding],
        session_summary=summary,
        policy_hints=hints,
        confidence=0.92,
        provenance=provenance,
    )

    dumped = analysis.model_dump()
    assert dumped["analysis_id"] == "BHA-001"
    assert dumped["signals"][0]["signal_type"] == "TIME_PRESSURE"
    assert dumped["findings"][0]["finding_type"] == "TIME_PRESSURE"
    assert dumped["policy_hints"]["pressure_present"] is True
    assert dumped["policy_hints"]["high_impact_action_progression"] is True
    assert dumped["confidence"] == 0.92


def test_confidence_boundary_not_scam_probability():
    """Confirm confidence is bounded between 0.0 and 1.0 and does NOT assert fraud probability."""
    with pytest.raises(Exception):
        # Invalid confidence > 1.0 must fail validation
        BehaviouralSignal(
            signal_id="BHS-ERR",
            signal_type=BehaviouralSignalType.TIME_PRESSURE,
            description="Invalid confidence",
            confidence=1.5,
        )

    with pytest.raises(Exception):
        # Invalid confidence < 0.0 must fail validation
        BehaviouralSignal(
            signal_id="BHS-ERR",
            signal_type=BehaviouralSignalType.TIME_PRESSURE,
            description="Invalid confidence",
            confidence=-0.1,
        )

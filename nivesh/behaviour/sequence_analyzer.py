"""Sequence analyzer coordinating all behavioural detectors for Engine 10.

Aggregates pressure, escalation, persistence, and channel detectors. Builds
session summary, structured policy hints, and findings.
"""

from typing import Optional, Any
from nivesh.behaviour.schemas import (
    BehaviouralSignal,
    BehaviouralFinding,
    BehaviouralSignalType,
    SessionBehaviourSummary,
    BehaviouralPolicyHints,
)
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType, InteractionHistory
from nivesh.behaviour.temporal import (
    TemporalThresholds,
    DEFAULT_TEMPORAL_THRESHOLDS,
    compute_duration_seconds,
)
from nivesh.behaviour.pressure_detector import PressureDetector
from nivesh.behaviour.escalation_detector import EscalationDetector, HIGH_IMPACT_ACTION_TYPES, HIGH_IMPACT_CATEGORIES
from nivesh.behaviour.persistence_detector import PersistenceDetector
from nivesh.behaviour.channel_detector import ChannelDetector
from nivesh.behaviour.findings import FindingsBuilder
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis


class SequenceAnalyzer:
    """Coordinates multi-modal sequence evaluation across content, actions, and history."""

    def __init__(self, thresholds: Optional[TemporalThresholds] = None):
        self.thresholds = thresholds or DEFAULT_TEMPORAL_THRESHOLDS
        self.pressure_detector = PressureDetector(self.thresholds)
        self.escalation_detector = EscalationDetector(self.thresholds)
        self.persistence_detector = PersistenceDetector(self.thresholds)
        self.channel_detector = ChannelDetector(self.thresholds)

    def analyze_sequence(
        self,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None,
        actions: Optional[ActionAnalysis] = None,
        interaction_history: Optional[InteractionHistory] = None,
    ) -> tuple[list[BehaviouralSignal], list[BehaviouralFinding], SessionBehaviourSummary, BehaviouralPolicyHints, float]:
        """Run all detectors, compose summary, policy hints, and pattern confidence."""
        signals: list[BehaviouralSignal] = []

        # 1. Detect pressure and urgency
        signals.extend(self.pressure_detector.detect(content, claims, interaction_history))

        # 2. Detect action escalation and commitment
        signals.extend(self.escalation_detector.detect(content, claims, actions, interaction_history))

        # 3. Detect persistence and retries
        signals.extend(self.persistence_detector.detect(actions, interaction_history))

        # 4. Detect channel migrations
        signals.extend(self.channel_detector.detect(content, actions, interaction_history))

        # Deduplicate signals by signal_type and primary target/description
        deduped_signals: list[BehaviouralSignal] = []
        seen_types: set[str] = set()
        for s in signals:
            key = f"{s.signal_type.value}:{s.description}"
            if key not in seen_types:
                seen_types.add(key)
                deduped_signals.append(s)

        # 5. Build structured findings
        findings = FindingsBuilder.build_findings(deduped_signals)

        # 6. Compose SessionBehaviourSummary
        session_summary = self._build_session_summary(actions, interaction_history, deduped_signals)

        # 7. Compose BehaviouralPolicyHints
        policy_hints = self._build_policy_hints(deduped_signals)

        # 8. Compute pattern confidence
        # Strict rule: Represents confidence that observed behavioral patterns exist, NOT scam probability
        pattern_confidence = max((s.confidence for s in deduped_signals), default=0.0)

        return deduped_signals, findings, session_summary, policy_hints, round(pattern_confidence, 2)

    def _build_session_summary(
        self,
        actions: Optional[ActionAnalysis],
        history: Optional[InteractionHistory],
        signals: list[BehaviouralSignal],
    ) -> SessionBehaviourSummary:
        """Calculate statistical and sequence descriptors without trustworthiness scoring."""
        events: list[InteractionEvent] = history.get_sorted_events() if history else []
        event_count = len(events)
        action_count = len(actions.actions) if actions and actions.actions else 0

        # High impact action count
        high_impact_count = 0
        if actions and actions.actions:
            for a in actions.actions:
                if a.action_type in HIGH_IMPACT_ACTION_TYPES or str(a.category) in HIGH_IMPACT_CATEGORIES:
                    high_impact_count += 1
        for e in events:
            if e.event_type in (
                InteractionEventType.PAYMENT_REQUESTED,
                InteractionEventType.CREDENTIAL_REQUESTED,
                InteractionEventType.EXTERNAL_APP_REQUESTED,
            ):
                high_impact_count += 1

        # Channel changes
        distinct_channels: list[str] = []
        for e in events:
            if e.channel and (not distinct_channels or distinct_channels[-1] != e.channel.lower()):
                distinct_channels.append(e.channel.lower())
        channel_changes = max(0, len(distinct_channels) - 1)

        # Warning & override counts
        warning_count = sum(1 for e in events if e.event_type == InteractionEventType.WARNING_SHOWN)
        override_count = sum(1 for e in events if e.event_type == InteractionEventType.USER_OVERRIDE)

        # Duration
        duration_seconds: Optional[float] = None
        if events and len(events) >= 2:
            duration_seconds = compute_duration_seconds(events[0].timestamp, events[-1].timestamp)

        # Sequence summary
        seq_summary: list[str] = []
        for e in events:
            detail = f"{e.timestamp}: {e.event_type.value}"
            if e.channel:
                detail += f" [channel={e.channel}]"
            if e.action_id:
                detail += f" [action={e.action_id}]"
            seq_summary.append(detail)

        return SessionBehaviourSummary(
            session_id=history.session_id if history else None,
            event_count=event_count,
            duration_seconds=duration_seconds,
            action_count=action_count,
            high_impact_action_count=high_impact_count,
            channel_changes=channel_changes,
            warning_count=warning_count,
            override_count=override_count,
            behavioural_signals=[s.signal_type.value for s in signals],
            sequence_summary=seq_summary,
        )

    def _build_policy_hints(self, signals: list[BehaviouralSignal]) -> BehaviouralPolicyHints:
        """Map observed signal types directly into objective boolean observations."""
        stypes = {s.signal_type for s in signals}
        return BehaviouralPolicyHints(
            high_impact_action_progression=(
                BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION in stypes
                or BehaviouralSignalType.PROGRESSIVE_COMMITMENT in stypes
            ),
            pressure_present=(
                BehaviouralSignalType.TIME_PRESSURE in stypes
                or BehaviouralSignalType.FOMO_PRESSURE in stypes
                or BehaviouralSignalType.REPEATED_URGENCY in stypes
            ),
            repeated_request_present=(
                BehaviouralSignalType.REPEATED_ACTION_REQUEST in stypes
                or BehaviouralSignalType.RETRY_AFTER_DECLINE in stypes
                or BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST in stypes
                or BehaviouralSignalType.PERSISTENT_CREDENTIAL_REQUEST in stypes
            ),
            user_override_present=(
                BehaviouralSignalType.USER_OVERRIDE in stypes
                or BehaviouralSignalType.WARNING_OVERRIDE in stypes
                or BehaviouralSignalType.REPEATED_WARNING_OVERRIDE in stypes
            ),
            rapid_escalation_present=(
                BehaviouralSignalType.RAPID_ACTION_ESCALATION in stypes
                or BehaviouralSignalType.RAPID_CHANNEL_MIGRATION in stypes
            ),
            information_to_transaction_shift=(
                BehaviouralSignalType.INFORMATION_TO_TRANSACTION_SHIFT in stypes
            ),
            persistent_payment_present=(
                BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST in stypes
                or BehaviouralSignalType.RETRY_AFTER_DECLINE in stypes
            ),
            persistent_credential_present=(
                BehaviouralSignalType.PERSISTENT_CREDENTIAL_REQUEST in stypes
            ),
        )

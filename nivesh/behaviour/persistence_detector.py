"""Persistence and retry detection for Engine 10: Behavioural Signal Intelligence.

Detects repeated requests, retries after user decline, persistent payment requests,
and user override patterns across interaction events.
Follows strict negative constraints: never infers repetition from a single interaction
and never makes psychological or competency judgments on users.
"""

from typing import Optional
from collections import Counter
from nivesh.behaviour.schemas import (
    BehaviouralSignal,
    BehaviouralSignalType,
    BehaviouralSignalSeverity,
)
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType, InteractionHistory
from nivesh.behaviour.temporal import TemporalThresholds, DEFAULT_TEMPORAL_THRESHOLDS
from nivesh.schemas.actions import ActionAnalysis


class PersistenceDetector:
    """Detects persistence patterns: retries after decline, repeated action/payment requests, overrides."""

    def __init__(self, thresholds: Optional[TemporalThresholds] = None):
        self.thresholds = thresholds or DEFAULT_TEMPORAL_THRESHOLDS

    def detect(
        self,
        actions: Optional[ActionAnalysis] = None,
        interaction_history: Optional[InteractionHistory] = None,
    ) -> list[BehaviouralSignal]:
        """Analyze event history for persistence and user response patterns.

        Requires actual multi-event history to detect repetition. Returns empty
        if interaction_history is absent or contains only a single event.
        """
        signals: list[BehaviouralSignal] = []
        if not interaction_history or len(interaction_history.events) < 2:
            # Strict rule: Do not infer repetition from a single message/event
            return signals

        events = interaction_history.get_sorted_events()

        # 1. Count event occurrences by type
        type_counts = Counter(e.event_type for e in events)

        # 2. Check for USER_DECLINE and RETRY_AFTER_DECLINE
        decline_indices = [
            i for i, e in enumerate(events)
            if e.event_type == InteractionEventType.USER_DECLINED
        ]

        if decline_indices:
            # Check if any request event followed a decline
            retry_events: list[InteractionEvent] = []
            for d_idx in decline_indices:
                subsequent = events[d_idx + 1:]
                for sub in subsequent:
                    if sub.event_type in (
                        InteractionEventType.PAYMENT_REQUESTED,
                        InteractionEventType.ACTION_REQUESTED,
                        InteractionEventType.CREDENTIAL_REQUESTED,
                        InteractionEventType.EXTERNAL_APP_REQUESTED,
                    ):
                        retry_events.append(sub)

            if retry_events:
                signals.append(
                    BehaviouralSignal(
                        signal_id=f"BHS-PER-RTR-{len(signals) + 1:03d}",
                        signal_type=BehaviouralSignalType.RETRY_AFTER_DECLINE,
                        description="Action or payment request was repeated after explicit user decline was recorded",
                        severity=BehaviouralSignalSeverity.HIGH,
                        confidence=0.96,
                        event_ids=[e.event_id for e in retry_events if e.event_id],
                        action_ids=[e.action_id for e in retry_events if e.action_id],
                        evidence=[
                            f"User declined at step {decline_indices[0]}, followed by {len(retry_events)} subsequent request(s)"
                        ],
                    )
                )

        # 3. PERSISTENT_PAYMENT_REQUEST (Payment requested >= repeated_request_threshold times)
        payment_events = [
            e for e in events if e.event_type == InteractionEventType.PAYMENT_REQUESTED
        ]
        if len(payment_events) >= self.thresholds.repeated_request_threshold:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PER-PAY-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST,
                    description=f"Payment was requested {len(payment_events)} times across the interaction history",
                    severity=BehaviouralSignalSeverity.HIGH,
                    confidence=0.95,
                    event_ids=[e.event_id for e in payment_events if e.event_id],
                    action_ids=[e.action_id for e in payment_events if e.action_id],
                    evidence=[
                        f"Observed {len(payment_events)} payment request events (threshold: {self.thresholds.repeated_request_threshold})"
                    ],
                    metadata={"occurrence_count": len(payment_events)},
                )
            )

        # 4. PERSISTENT_CREDENTIAL_REQUEST (Credentials requested >= repeated_request_threshold times)
        cred_events = [
            e for e in events if e.event_type == InteractionEventType.CREDENTIAL_REQUESTED
        ]
        if len(cred_events) >= self.thresholds.repeated_request_threshold:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PER-CRD-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.PERSISTENT_CREDENTIAL_REQUEST,
                    description=f"Credential/authentication disclosure requested {len(cred_events)} times",
                    severity=BehaviouralSignalSeverity.HIGH,
                    confidence=0.95,
                    event_ids=[e.event_id for e in cred_events if e.event_id],
                    action_ids=[e.action_id for e in cred_events if e.action_id],
                    evidence=[
                        f"Observed {len(cred_events)} credential request events (threshold: {self.thresholds.repeated_request_threshold})"
                    ],
                    metadata={"occurrence_count": len(cred_events)},
                )
            )

        # 5. REPEATED_ACTION_REQUEST (Same action_id or multiple generic action requests)
        action_id_counts = Counter(e.action_id for e in events if e.action_id)
        repeated_action_ids = [
            act_id for act_id, cnt in action_id_counts.items()
            if cnt >= self.thresholds.repeated_request_threshold
        ]
        if repeated_action_ids:
            matching_events = [e for e in events if e.action_id in repeated_action_ids]
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PER-ACT-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.REPEATED_ACTION_REQUEST,
                    description=f"Identical action requested repeatedly across sequence: {', '.join(repeated_action_ids)}",
                    severity=BehaviouralSignalSeverity.MEDIUM,
                    confidence=0.91,
                    event_ids=[e.event_id for e in matching_events if e.event_id],
                    action_ids=repeated_action_ids,
                    evidence=[f"Action {act_id} repeated {action_id_counts[act_id]} times" for act_id in repeated_action_ids],
                )
            )

        # 6. User response patterns (USER_OVERRIDE, WARNING_OVERRIDE, REPEATED_WARNING_OVERRIDE)
        override_events = [
            e for e in events if e.event_type == InteractionEventType.USER_OVERRIDE
        ]
        warning_events = [
            e for e in events if e.event_type == InteractionEventType.WARNING_SHOWN
        ]

        if override_events:
            has_warning_preceding = any(
                any(events[j].event_type == InteractionEventType.WARNING_SHOWN for j in range(i))
                for i, e in enumerate(events) if e.event_type == InteractionEventType.USER_OVERRIDE
            )
            # Signal: USER_OVERRIDE / WARNING_OVERRIDE
            signal_type = (
                BehaviouralSignalType.WARNING_OVERRIDE if has_warning_preceding
                else BehaviouralSignalType.USER_OVERRIDE
            )
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PER-OVR-{len(signals) + 1:03d}",
                    signal_type=signal_type,
                    description=f"User continued interaction after policy intervention/warning was presented ({len(override_events)} recorded)",
                    severity=BehaviouralSignalSeverity.LOW,
                    confidence=0.95,
                    event_ids=[e.event_id for e in override_events if e.event_id],
                    evidence=[
                        f"Observed {len(override_events)} override event(s) following {len(warning_events)} warning(s)"
                    ],
                )
            )

            # Signal: REPEATED_WARNING_OVERRIDE
            if len(override_events) >= 2 and len(warning_events) >= 2:
                signals.append(
                    BehaviouralSignal(
                        signal_id=f"BHS-PER-RPO-{len(signals) + 1:03d}",
                        signal_type=BehaviouralSignalType.REPEATED_WARNING_OVERRIDE,
                        description=f"User repeatedly continued past multiple warnings ({len(override_events)} overrides recorded)",
                        severity=BehaviouralSignalSeverity.MEDIUM,
                        confidence=0.96,
                        event_ids=[e.event_id for e in override_events if e.event_id],
                        evidence=[f"Sequence contains {len(override_events)} warning overrides"],
                    )
                )

        return signals

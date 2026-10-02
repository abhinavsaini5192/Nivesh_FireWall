"""Escalation detection for Engine 10: Behavioural Signal Intelligence.

Detects progressive commitment, low-to-high impact transitions, rapid action escalation,
and information-to-transaction shifts across interaction sequences.
"""

from typing import Optional, Sequence
import re
from nivesh.behaviour.schemas import (
    BehaviouralSignal,
    BehaviouralSignalType,
    BehaviouralSignalSeverity,
)
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType, InteractionHistory
from nivesh.behaviour.temporal import (
    TemporalThresholds,
    DEFAULT_TEMPORAL_THRESHOLDS,
    compute_duration_seconds,
)
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction, ActionCategory


# Impact tier mapping for ActionCategory
CATEGORY_IMPACT_TIER: dict[str, int] = {
    "INFORMATIONAL": 0,
    "NAVIGATION": 1,
    "COMMUNICATION": 1,
    "CHANNEL_MIGRATION": 2,
    "SOFTWARE_INSTALLATION": 3,
    "DATA_DISCLOSURE": 3,
    "CREDENTIAL_ACCESS": 4,
    "ACCOUNT_AUTHORIZATION": 4,
    "FINANCIAL_TRANSACTION": 5,
}

HIGH_IMPACT_CATEGORIES = frozenset({
    "SOFTWARE_INSTALLATION",
    "DATA_DISCLOSURE",
    "CREDENTIAL_ACCESS",
    "ACCOUNT_AUTHORIZATION",
    "FINANCIAL_TRANSACTION",
})

HIGH_IMPACT_ACTION_TYPES = frozenset({
    "PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY", "WITHDRAW_MONEY",
    "BUY", "SELL", "ENTER_CREDENTIALS", "SHARE_OTP", "CONNECT_BANK",
    "AUTHORIZE_ACCESS", "INSTALL", "DOWNLOAD",
})

LOW_IMPACT_ACTION_TYPES = frozenset({
    "CLICK_LINK", "OPEN_WEBSITE", "JOIN_CHANNEL", "JOIN_GROUP",
    "FOLLOW_ACCOUNT", "MESSAGE_PERSON", "CALL_PERSON", "CONTACT",
    "SHARE", "FORWARD",
})

INFORMATIONAL_KEYWORDS = re.compile(
    r"\b(?:learn|education|program|guide|course|overview|basics|concepts|understand|mutual funds?|research|webinar)\b",
    re.IGNORECASE,
)


class EscalationDetector:
    """Detects progressive action escalation, transitions, and commitment."""

    def __init__(self, thresholds: Optional[TemporalThresholds] = None):
        self.thresholds = thresholds or DEFAULT_TEMPORAL_THRESHOLDS

    def detect(
        self,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None,
        actions: Optional[ActionAnalysis] = None,
        interaction_history: Optional[InteractionHistory] = None,
    ) -> list[BehaviouralSignal]:
        """Identify escalation patterns across current actions and historical sequence."""
        signals: list[BehaviouralSignal] = []

        # Gather ordered action items
        action_items: list[CanonicalAction] = actions.actions if actions and actions.actions else []
        action_ids = [a.action_id for a in action_items if a.action_id]

        # Gather historical events
        events: list[InteractionEvent] = (
            interaction_history.get_sorted_events() if interaction_history else []
        )

        has_low_impact = False
        has_high_impact = False
        low_action_ids: list[str] = []
        high_action_ids: list[str] = []

        # Check action items
        for a in action_items:
            tier = CATEGORY_IMPACT_TIER.get(str(a.category), 0)
            if a.action_type in HIGH_IMPACT_ACTION_TYPES or str(a.category) in HIGH_IMPACT_CATEGORIES or tier >= 3:
                has_high_impact = True
                if a.action_id:
                    high_action_ids.append(a.action_id)
            elif a.action_type in LOW_IMPACT_ACTION_TYPES or tier <= 2:
                has_low_impact = True
                if a.action_id:
                    low_action_ids.append(a.action_id)

        # Check events
        for e in events:
            if e.event_type in (
                InteractionEventType.PAYMENT_REQUESTED,
                InteractionEventType.CREDENTIAL_REQUESTED,
                InteractionEventType.EXTERNAL_APP_REQUESTED,
            ):
                has_high_impact = True
                if e.action_id and e.action_id not in high_action_ids:
                    high_action_ids.append(e.action_id)
            elif e.event_type in (
                InteractionEventType.CONTENT_VIEW,
                InteractionEventType.CLAIM_PRESENTED,
                InteractionEventType.CHANNEL_CHANGED,
            ):
                has_low_impact = True
                if e.action_id and e.action_id not in low_action_ids:
                    low_action_ids.append(e.action_id)

        # Content text inspection for educational/informational start
        content_text = ""
        if content:
            if hasattr(content, "normalized") and hasattr(content.normalized, "text") and content.normalized.text:
                content_text = content.normalized.text
            elif hasattr(content, "raw") and hasattr(content.raw, "text") and content.raw.text:
                content_text = content.raw.text
            elif hasattr(content, "text"):
                content_text = str(getattr(content, "text") or "")
        has_informational_content = bool(INFORMATIONAL_KEYWORDS.search(content_text))
        if has_informational_content:
            has_low_impact = True

        # Signal: LOW_TO_HIGH_IMPACT_TRANSITION
        # Requires evidence of low-impact preceding or co-occurring with high-impact
        if has_low_impact and has_high_impact:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-ESC-L2H-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION,
                    description="Interaction progresses from low-impact actions/information to high-impact commitments (financial/credentials/software)",
                    severity=BehaviouralSignalSeverity.HIGH,
                    confidence=0.92,
                    event_ids=[e.event_id for e in events if e.event_id],
                    action_ids=list(dict.fromkeys(low_action_ids + high_action_ids)),
                    evidence=[
                        f"Low impact steps: {len(low_action_ids) or ('informational content' if has_informational_content else 1)}",
                        f"High impact steps: {len(high_action_ids) or 1}",
                    ],
                )
            )

        # Signal: INFORMATION_TO_TRANSACTION_SHIFT
        # Content or earlier steps were educational/informational, followed by payment or financial transaction
        has_financial_target = (
            any(
                a.action_type in ("PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY", "BUY", "SELL")
                or str(a.category) == "FINANCIAL_TRANSACTION"
                for a in action_items
            )
            or any(e.event_type == InteractionEventType.PAYMENT_REQUESTED for e in events)
            or bool(re.search(r"\b(?:pay|payment|deposit|transfer|₹|\$)\b", content_text, re.IGNORECASE))
        )

        if has_informational_content and has_financial_target:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-ESC-I2T-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.INFORMATION_TO_TRANSACTION_SHIFT,
                    description="Interaction initiated with informational/educational presentation then shifted to transaction/financial request",
                    severity=BehaviouralSignalSeverity.HIGH,
                    confidence=0.93,
                    event_ids=[e.event_id for e in events if e.event_id],
                    action_ids=list(dict.fromkeys(action_ids)),
                    evidence=[
                        "Initial stage presented educational/program material",
                        "Subsequent stage requested financial transaction or payment",
                    ],
                )
            )

        # Signal: PROGRESSIVE_COMMITMENT
        # Evaluates multiple distinct tiers stepped in order (>= 3 categories stepped up)
        tiers_seen: list[int] = []
        if has_informational_content:
            tiers_seen.append(0)
        for a in action_items:
            tier = CATEGORY_IMPACT_TIER.get(str(a.category), 1)
            tiers_seen.append(tier)
        for e in events:
            if e.event_type == InteractionEventType.CONTENT_VIEW:
                tiers_seen.append(0)
            elif e.event_type == InteractionEventType.CHANNEL_CHANGED:
                tiers_seen.append(2)
            elif e.event_type == InteractionEventType.EXTERNAL_APP_REQUESTED:
                tiers_seen.append(3)
            elif e.event_type == InteractionEventType.CREDENTIAL_REQUESTED:
                tiers_seen.append(4)
            elif e.event_type == InteractionEventType.PAYMENT_REQUESTED:
                tiers_seen.append(5)

        unique_tiers_in_order: list[int] = []
        for t in tiers_seen:
            if not unique_tiers_in_order or t != unique_tiers_in_order[-1]:
                unique_tiers_in_order.append(t)

        is_increasing = (
            len(unique_tiers_in_order) >= 3
            and all(unique_tiers_in_order[i] <= unique_tiers_in_order[i + 1] for i in range(len(unique_tiers_in_order) - 1))
            and unique_tiers_in_order[-1] > unique_tiers_in_order[0]
        )

        if is_increasing:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-ESC-PRG-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.PROGRESSIVE_COMMITMENT,
                    description="Stepwise progressive commitment observed through successive increasing action tiers",
                    severity=BehaviouralSignalSeverity.MEDIUM,
                    confidence=0.90,
                    event_ids=[e.event_id for e in events if e.event_id],
                    action_ids=list(dict.fromkeys(action_ids)),
                    evidence=[f"Tiers transitioned: {' -> '.join(str(t) for t in unique_tiers_in_order)}"],
                )
            )

        # Signal: RAPID_ACTION_ESCALATION
        # When timing data shows the transition to high impact happened within rapid_escalation_seconds_threshold
        if has_high_impact and len(events) >= 2:
            start_ts = events[0].timestamp
            # Find timestamp of first high-impact event
            high_ts: Optional[str] = None
            for e in events:
                if e.event_type in (
                    InteractionEventType.PAYMENT_REQUESTED,
                    InteractionEventType.CREDENTIAL_REQUESTED,
                    InteractionEventType.EXTERNAL_APP_REQUESTED,
                ):
                    high_ts = e.timestamp
                    break
            if not high_ts:
                # If high impact was from current action and events represent sequence up to now
                high_ts = events[-1].timestamp

            duration = compute_duration_seconds(start_ts, high_ts)
            if duration is not None and duration <= self.thresholds.rapid_escalation_seconds_threshold:
                signals.append(
                    BehaviouralSignal(
                        signal_id=f"BHS-ESC-RPD-{len(signals) + 1:03d}",
                        signal_type=BehaviouralSignalType.RAPID_ACTION_ESCALATION,
                        description=f"Action escalated to high-impact commitment in {duration:.1f}s (threshold: {self.thresholds.rapid_escalation_seconds_threshold:.0f}s)",
                        severity=BehaviouralSignalSeverity.HIGH,
                        confidence=0.94,
                        event_ids=[e.event_id for e in events if e.event_id],
                        action_ids=list(dict.fromkeys(high_action_ids or action_ids)),
                        evidence=[
                            f"Elapsed time: {duration:.1f}s between initial event ({start_ts}) and high-impact action ({high_ts})",
                            f"Rapid escalation threshold: {self.thresholds.rapid_escalation_seconds_threshold:.0f}s",
                        ],
                    )
                )

        return signals

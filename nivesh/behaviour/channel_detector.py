"""Channel migration detection for Engine 10: Behavioural Signal Intelligence.

Detects channel migration, rapid channel transitions, and escalation to private
or unmonitored communication platforms across content and interaction history.
Follows strict negative constraints: using Telegram/WhatsApp by itself is not
labeled suspicious or criminal; only the migration pattern is described objectively.
"""

from typing import Optional
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
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction


PRIVATE_CHANNELS = frozenset({"telegram", "whatsapp", "signal", "dm", "private_chat", "phone", "call"})
PUBLIC_CHANNELS = frozenset({"web", "website", "youtube", "twitter", "x", "instagram", "facebook", "linkedin", "email"})

CHANNEL_KEYWORDS = {
    "telegram": re.compile(r"\b(?:telegram|t\.me)\b", re.IGNORECASE),
    "whatsapp": re.compile(r"\b(?:whatsapp|wa\.me)\b", re.IGNORECASE),
    "signal": re.compile(r"\bsignal\b", re.IGNORECASE),
    "phone": re.compile(r"\b(?:call|phone|sms)\b", re.IGNORECASE),
    "web": re.compile(r"\b(?:website|portal|browser|web)\b", re.IGNORECASE),
}


class ChannelDetector:
    """Detects channel transitions: migration, rapid migration, and private channel escalation."""

    def __init__(self, thresholds: Optional[TemporalThresholds] = None):
        self.thresholds = thresholds or DEFAULT_TEMPORAL_THRESHOLDS

    def detect(
        self,
        content: NormalizedContent,
        actions: Optional[ActionAnalysis] = None,
        interaction_history: Optional[InteractionHistory] = None,
    ) -> list[BehaviouralSignal]:
        """Identify channel migration patterns across interaction events and content."""
        signals: list[BehaviouralSignal] = []

        channels_observed: list[str] = []
        channel_events: list[InteractionEvent] = []

        # 1. Historical events
        if interaction_history and interaction_history.events:
            for e in interaction_history.get_sorted_events():
                ch = e.channel or (e.metadata.get("channel") if e.metadata else None)
                if ch:
                    ch_norm = str(ch).lower()
                    if not channels_observed or channels_observed[-1] != ch_norm:
                        channels_observed.append(ch_norm)
                    channel_events.append(e)

        # 2. Originating content channel vs requested action channels
        content_channel = "web"
        if content and hasattr(content, "source_type") and content.source_type:
            content_channel = str(content.source_type).lower()
        if content and hasattr(content, "platform") and content.platform:
            content_channel = str(content.platform).lower()

        if not channels_observed:
            channels_observed.append(content_channel)

        action_channels: list[str] = []
        action_ids: list[str] = []
        if actions and actions.actions:
            for a in actions.actions:
                if a.action_id:
                    action_ids.append(a.action_id)
                # Check target or parameters
                target_str = str(a.target or "").lower()
                for ch_name, pat in CHANNEL_KEYWORDS.items():
                    if pat.search(target_str):
                        action_channels.append(ch_name)
                if str(a.category) == "CHANNEL_MIGRATION" or a.action_type in ("JOIN_CHANNEL", "JOIN_GROUP"):
                    content_text = ""
                    if content:
                        if hasattr(content, "normalized") and hasattr(content.normalized, "text") and content.normalized.text:
                            content_text = content.normalized.text
                        elif hasattr(content, "raw") and hasattr(content.raw, "text") and content.raw.text:
                            content_text = content.raw.text
                        elif hasattr(content, "text"):
                            content_text = str(getattr(content, "text") or "")
                    for ch_name, pat in CHANNEL_KEYWORDS.items():
                        if pat.search(content_text):
                            action_channels.append(ch_name)

        for ch in action_channels:
            if not channels_observed or channels_observed[-1] != ch:
                channels_observed.append(ch)

        # Signal: CHANNEL_MIGRATION
        distinct_channels = list(dict.fromkeys(channels_observed))
        has_migration = len(distinct_channels) >= 2 or any(
            a.action_type in ("JOIN_CHANNEL", "JOIN_GROUP") or str(a.category) == "CHANNEL_MIGRATION"
            for a in (actions.actions if actions and actions.actions else [])
        )

        if has_migration:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-CHN-MIG-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.CHANNEL_MIGRATION,
                    description=f"Interaction transitions across communication channels: {' -> '.join(distinct_channels) if len(distinct_channels) >= 2 else 'external channel migration requested'}",
                    severity=BehaviouralSignalSeverity.MEDIUM,
                    confidence=0.91,
                    event_ids=[e.event_id for e in channel_events if e.event_id],
                    action_ids=action_ids,
                    evidence=[
                        f"Observed channels: {', '.join(distinct_channels) if distinct_channels else 'channel switch'}"
                    ],
                )
            )

        # Signal: PRIVATE_CHANNEL_ESCALATION
        # When moving from a public/web context to a private channel (Telegram, WhatsApp, Signal, etc.)
        has_private = any(ch in PRIVATE_CHANNELS for ch in distinct_channels)
        has_public_origin = any(ch in PUBLIC_CHANNELS for ch in distinct_channels) or content_channel in PUBLIC_CHANNELS
        if has_private and has_public_origin:
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-CHN-PRV-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.PRIVATE_CHANNEL_ESCALATION,
                    description="Interaction directed user from public/web setting to private messaging channel",
                    severity=BehaviouralSignalSeverity.MEDIUM,
                    confidence=0.89,
                    event_ids=[e.event_id for e in channel_events if e.event_id],
                    action_ids=action_ids,
                    evidence=["Channel transition directs to private messaging platform"],
                )
            )

        # Signal: RAPID_CHANNEL_MIGRATION
        # When timing in event history shows channel change within threshold
        if len(channel_events) >= 2 and len(distinct_channels) >= 2:
            first_ch_ts = channel_events[0].timestamp
            second_ch_ts = channel_events[-1].timestamp
            duration = compute_duration_seconds(first_ch_ts, second_ch_ts)
            if duration is not None and duration <= self.thresholds.rapid_channel_migration_seconds_threshold:
                signals.append(
                    BehaviouralSignal(
                        signal_id=f"BHS-CHN-RPD-{len(signals) + 1:03d}",
                        signal_type=BehaviouralSignalType.RAPID_CHANNEL_MIGRATION,
                        description=f"Channel migration occurred rapidly within {duration:.1f}s (threshold: {self.thresholds.rapid_channel_migration_seconds_threshold:.0f}s)",
                        severity=BehaviouralSignalSeverity.HIGH,
                        confidence=0.93,
                        event_ids=[e.event_id for e in channel_events if e.event_id],
                        action_ids=action_ids,
                        evidence=[
                            f"Channel transition took {duration:.1f}s between {first_ch_ts} and {second_ch_ts}"
                        ],
                    )
                )

        return signals

"""Interaction event model for Engine 10: Behavioural Signal Intelligence Engine.

Provides typed, privacy-preserving event structures and session history
tracking for sequence analysis across financial interactions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class InteractionEventType(str, Enum):
    """Supported interaction event types across interaction sequences."""
    CONTENT_VIEW = "CONTENT_VIEW"
    CLAIM_PRESENTED = "CLAIM_PRESENTED"
    ACTION_REQUESTED = "ACTION_REQUESTED"
    ACTION_STARTED = "ACTION_STARTED"
    ACTION_CANCELLED = "ACTION_CANCELLED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    USER_HESITATION = "USER_HESITATION"
    USER_DECLINED = "USER_DECLINED"
    USER_CONFIRMED = "USER_CONFIRMED"
    CHANNEL_CHANGED = "CHANNEL_CHANGED"
    EXTERNAL_APP_REQUESTED = "EXTERNAL_APP_REQUESTED"
    CREDENTIAL_REQUESTED = "CREDENTIAL_REQUESTED"
    PAYMENT_REQUESTED = "PAYMENT_REQUESTED"
    WARNING_SHOWN = "WARNING_SHOWN"
    USER_OVERRIDE = "USER_OVERRIDE"
    UNKNOWN = "UNKNOWN"


# Prohibited metadata keys to enforce privacy preservation
FORBIDDEN_METADATA_KEYS = frozenset({
    "password", "passwd", "pwd", "otp", "pin", "cvv", "card_number",
    "account_number", "secret", "token", "auth_token", "private_key",
    "keystrokes", "raw_message", "message_body", "sms_body", "contact_list",
})


class InteractionEvent(BaseModel):
    """Structured interaction event representing an observable interaction step.

    Stores only references, categories, and timestamps. Does NOT store raw text,
    credentials, passwords, OTPs, or continuous surveillance streams.
    """
    event_id: str = Field(description="Unique event identifier (e.g. EVT-001)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of when the event occurred",
    )
    event_type: InteractionEventType = Field(
        default=InteractionEventType.UNKNOWN,
        description="Categorical event type",
    )
    action_id: Optional[str] = Field(default=None, description="Referenced action ID from Engine 3 if applicable")
    claim_id: Optional[str] = Field(default=None, description="Referenced claim ID from Engine 2 if applicable")
    decision_id: Optional[str] = Field(default=None, description="Referenced decision ID from Engine 8 if applicable")
    channel: Optional[str] = Field(default=None, description="Channel identifier (e.g. web, telegram, whatsapp, app)")
    sequence_index: int = Field(default=0, ge=0, description="0-indexed sequence ordering within the session")
    user_initiated: bool = Field(default=False, description="True if action/step was initiated by the user")
    system_initiated: bool = Field(default=True, description="True if action/step was requested by the content/system")
    source_type: Optional[str] = Field(default=None, description="Originating source type (e.g. web_page, messaging_app)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe structural attributes without PII")

    def model_post_init(self, __context: Any) -> None:
        """Sanitize metadata to strip any sensitive keys."""
        if self.metadata:
            lowered = {k.lower(): k for k in self.metadata}
            for forbidden in FORBIDDEN_METADATA_KEYS:
                if forbidden in lowered:
                    self.metadata.pop(lowered[forbidden], None)


class InteractionHistory(BaseModel):
    """Session history aggregating structured interaction events.

    Maintains chronologically ordered events for behavioural progression analysis.
    Stores IDs and categorizations, preserving user privacy.
    """
    session_id: str = Field(description="Unique session identifier (e.g. SESS-1001)")
    events: list[InteractionEvent] = Field(default_factory=list, description="Ordered interaction events")
    started_at: Optional[str] = Field(default=None, description="Timestamp of first event")
    last_event_at: Optional[str] = Field(default=None, description="Timestamp of most recent event")
    event_count: int = Field(default=0, description="Total count of recorded events")
    source_type: Optional[str] = Field(default=None, description="Primary session source type")

    def model_post_init(self, __context: Any) -> None:
        """Sync timestamps and counts upon initialization."""
        self._recompute()

    def _recompute(self) -> None:
        """Update event count and boundary timestamps."""
        self.event_count = len(self.events)
        if self.events:
            self.started_at = self.events[0].timestamp
            self.last_event_at = self.events[-1].timestamp
        else:
            self.started_at = None
            self.last_event_at = None

    def add_event(self, event: InteractionEvent) -> None:
        """Append a new event and maintain sequence indexing."""
        if event.sequence_index == 0 and len(self.events) > 0:
            event.sequence_index = len(self.events)
        self.events.append(event)
        self._recompute()

    def get_sorted_events(self) -> list[InteractionEvent]:
        """Return events sorted by sequence_index and timestamp."""
        return sorted(self.events, key=lambda e: (e.sequence_index, e.timestamp))

    def filter_by_type(self, event_type: InteractionEventType) -> list[InteractionEvent]:
        """Return all events matching a specific event type."""
        return [e for e in self.events if e.event_type == event_type]

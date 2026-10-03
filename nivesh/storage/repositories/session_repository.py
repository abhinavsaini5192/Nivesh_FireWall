"""Persistent Session Repository for Engine 10.

Persists structured, privacy-preserving interaction events and session sequences.
Guarantees:
- Strictly excludes raw keystrokes, passwords, OTPs, PINs, cards, or bank credentials.
- Records structural metadata only (event types, channel transitions, timing intervals).
- Isolates sessions to prevent cross-user contamination.
"""

import threading
from typing import Optional, Any
from sqlalchemy.orm import Session, joinedload

from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionHistory,
    InteractionEventType,
    FORBIDDEN_METADATA_KEYS,
)
from nivesh.storage.models import (
    SessionModel,
    SessionEventModel,
)
from nivesh.storage.database import get_db_session
from nivesh.storage.errors import ForbiddenFieldError


def _sanitize_event_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Sanitize metadata to ensure no forbidden keys or credentials leak."""
    if not metadata:
        return {}
    clean: dict[str, Any] = {}
    for k, v in metadata.items():
        lower_k = str(k).lower()
        if lower_k in FORBIDDEN_METADATA_KEYS:
            raise ForbiddenFieldError(f"Forbidden credential key '{k}' in session event metadata.")
        if isinstance(v, dict):
            clean[k] = _sanitize_event_metadata(v)
        elif isinstance(v, (str, int, float, bool, list)):
            clean[k] = v
    return clean


def _event_model_to_pydantic(m: SessionEventModel) -> InteractionEvent:
    """Convert SQLAlchemy SessionEventModel to Pydantic InteractionEvent."""
    return InteractionEvent(
        event_id=m.event_id,
        timestamp=m.timestamp,
        event_type=InteractionEventType(m.event_type) if m.event_type in InteractionEventType._value2member_map_ else InteractionEventType.UNKNOWN,
        action_id=m.action_id,
        claim_id=m.claim_id,
        decision_id=m.decision_id,
        channel=m.channel,
        sequence_index=m.sequence_index,
        user_initiated=m.user_initiated,
        system_initiated=m.system_initiated,
        source_type=m.source_type,
        metadata=dict(m.metadata_json or {}),
    )


class SqlAlchemySessionRepository:
    """Persistent storage for interaction sessions and sequential event progressions."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory
        self._lock = threading.RLock()

    def record_event(self, session_id: str, event: InteractionEvent) -> InteractionHistory:
        """Persist an interaction event into the session sequence with privacy enforcement."""
        clean_meta = _sanitize_event_metadata(event.metadata)

        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                sess_model = (
                    session.query(SessionModel)
                    .filter(SessionModel.session_id == session_id)
                    .first()
                )

                if not sess_model:
                    sess_model = SessionModel(
                        session_id=session_id,
                        started_at=event.timestamp,
                        last_event_at=event.timestamp,
                        event_count=1,
                        source_type=event.source_type,
                        created_at=event.timestamp,
                        updated_at=event.timestamp,
                    )
                    session.add(sess_model)
                else:
                    sess_model.event_count += 1
                    sess_model.last_event_at = event.timestamp
                    sess_model.updated_at = event.timestamp
                    if not sess_model.source_type and event.source_type:
                        sess_model.source_type = event.source_type

                event_model = SessionEventModel(
                    event_id=event.event_id,
                    session_id=session_id,
                    timestamp=event.timestamp,
                    event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                    action_id=event.action_id,
                    claim_id=event.claim_id,
                    decision_id=event.decision_id,
                    channel=event.channel,
                    sequence_index=event.sequence_index,
                    user_initiated=event.user_initiated,
                    system_initiated=event.system_initiated,
                    source_type=event.source_type,
                    metadata_json=clean_meta,
                )
                session.add(event_model)
                session.flush()

            # Retrieve complete updated history
            history = self.get_session(session_id)
            return history or InteractionHistory(session_id=session_id, events=[event])

    def get_session(self, session_id: str) -> Optional[InteractionHistory]:
        """Retrieve complete session history with ordered events."""
        with get_db_session(session_factory=self._session_factory) as session:
            sess_model = (
                session.query(SessionModel)
                .options(joinedload(SessionModel.events))
                .filter(SessionModel.session_id == session_id)
                .first()
            )
            if not sess_model:
                return None

            events = [_event_model_to_pydantic(e) for e in sess_model.events]
            events.sort(key=lambda x: x.sequence_index)

            return InteractionHistory(
                session_id=sess_model.session_id,
                events=events,
                started_at=sess_model.started_at,
                last_event_at=sess_model.last_event_at,
                event_count=sess_model.event_count,
                source_type=sess_model.source_type,
            )

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated interaction events."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                sess_model = (
                    session.query(SessionModel)
                    .filter(SessionModel.session_id == session_id)
                    .first()
                )
                if not sess_model:
                    return False
                session.delete(sess_model)
                return True

    def reset(self) -> None:
        """Clear all sessions and events (used in tests)."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                session.query(SessionEventModel).delete()
                session.query(SessionModel).delete()

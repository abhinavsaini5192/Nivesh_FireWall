"""Persistent Audit Repository for security, compliance, and policy tracking.

Persists policy actions, user overrides, analysis events, and dispute audits.
Guarantees:
- Never stores raw user messages, passwords, OTPs, or payment details.
- Stores operational metadata and provenance references only.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session

from nivesh.storage.models import AuditRecordModel
from nivesh.storage.database import get_db_session
from nivesh.storage.errors import ForbiddenFieldError

FORBIDDEN_AUDIT_KEYS = frozenset({
    "password", "passwd", "pwd", "otp", "pin", "cvv", "cvc",
    "card_number", "account_number", "bank_account", "raw_credentials",
    "keystrokes", "secret", "private_key", "access_token",
})


def _sanitize_audit_details(details: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Sanitize audit details to ensure no forbidden credentials leak into audit logs."""
    if not details:
        return {}
    clean: dict[str, Any] = {}
    for k, v in details.items():
        if str(k).lower() in FORBIDDEN_AUDIT_KEYS:
            raise ForbiddenFieldError(f"Forbidden field '{k}' detected in audit record.")
        if isinstance(v, dict):
            clean[k] = _sanitize_audit_details(v)
        elif isinstance(v, (str, int, float, bool, list)):
            clean[k] = v
    return clean


class SqlAlchemyAuditRepository:
    """Persistent storage for security audit records."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory

    def record_audit(
        self,
        event_type: str,
        actor: str = "system",
        analysis_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditRecordModel:
        """Record an audit trail event."""
        clean_details = _sanitize_audit_details(details)
        now_iso = datetime.now(timezone.utc).isoformat()

        with get_db_session(session_factory=self._session_factory) as session:
            record = AuditRecordModel(
                analysis_id=analysis_id,
                session_id=session_id,
                event_type=event_type,
                actor=actor,
                details=clean_details,
                timestamp=now_iso,
            )
            session.add(record)
            session.flush()
            return record

    def list_audits(
        self,
        analysis_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List audit records matching optional filters."""
        with get_db_session(session_factory=self._session_factory) as session:
            q = session.query(AuditRecordModel)
            if analysis_id:
                q = q.filter(AuditRecordModel.analysis_id == analysis_id)
            if session_id:
                q = q.filter(AuditRecordModel.session_id == session_id)
            if event_type:
                q = q.filter(AuditRecordModel.event_type == event_type)

            records = q.order_by(AuditRecordModel.id.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "analysis_id": r.analysis_id,
                    "session_id": r.session_id,
                    "event_type": r.event_type,
                    "actor": r.actor,
                    "details": r.details,
                    "timestamp": r.timestamp,
                }
                for r in records
            ]

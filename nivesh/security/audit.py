"""Security audit logging module for Nivesh Firewall.

Phase 14.3: Security, Access Control & Secrets.
Persists tamper-evident security audit events into the database via SqlAlchemyAuditRepository
with strict sanitization of credentials and PII.
"""

from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any

from nivesh.storage.repositories.audit_repository import SqlAlchemyAuditRepository
from nivesh.storage.database import get_db_session
from nivesh.storage.models import AuditRecordModel
from nivesh.orchestrator.service import sanitize_sensitive_data

logger = logging.getLogger("nivesh.security.audit")


def log_security_event(
    action: str,
    actor: str,
    target_entity: Optional[str] = None,
    analysis_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    status: str = "SUCCESS",
    reason_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a security-relevant event into the persistent audit trail.

    Sanitizes details to ensure zero secret/credential leakage.
    """
    clean_details = sanitize_sensitive_data(details or {})
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with get_db_session() as session:
            record = AuditRecordModel(
                event_type=action,
                actor=actor,
                target_entity=target_entity,
                analysis_id=analysis_id,
                session_id=session_id,
                request_id=request_id,
                ip_address=ip_address,
                status=status,
                reason_code=reason_code,
                details=clean_details,
                timestamp=now_iso,
            )
            session.add(record)
    except Exception as e:
        # Non-crashing fallback: log locally so pipeline does not crash on audit failure
        logger.warning("Failed to persist security audit event %s: %s", action, e)

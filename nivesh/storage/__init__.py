"""Persistent Data & Storage Layer for Nivesh Firewall.

Provides:
- Centralized database configuration and session lifecycle
- Declarative relational schema models
- Repositories for analyses, fingerprints, sessions, and audits
- Safe health reporting and connection pooling
"""

from .errors import (
    StorageError,
    DatabaseUnavailableError,
    ConstraintViolationError,
    AnalysisNotFoundError,
    FingerprintNotFoundError,
    SessionNotFoundError,
    ForbiddenFieldError,
)
from .models import (
    Base,
    AnalysisModel,
    PolicyDecisionModel,
    AnalysisResultModel,
    EngineExecutionModel,
    FingerprintModel,
    FingerprintObservationModel,
    SessionModel,
    SessionEventModel,
    AuditRecordModel,
)
from .database import (
    get_engine,
    get_session_factory,
    get_db_session,
    check_database_health,
    create_tables,
    drop_tables,
    run_migrations,
    mask_database_url,
    reset_engine_for_testing,
)
from .repositories import (
    AnalysisRepository,
    SqlAlchemyAnalysisRepository,
    SqlAlchemyFingerprintRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyAuditRepository,
)

__all__ = [
    "StorageError",
    "DatabaseUnavailableError",
    "ConstraintViolationError",
    "AnalysisNotFoundError",
    "FingerprintNotFoundError",
    "SessionNotFoundError",
    "ForbiddenFieldError",
    "Base",
    "AnalysisModel",
    "PolicyDecisionModel",
    "AnalysisResultModel",
    "EngineExecutionModel",
    "FingerprintModel",
    "FingerprintObservationModel",
    "SessionModel",
    "SessionEventModel",
    "AuditRecordModel",
    "get_engine",
    "get_session_factory",
    "get_db_session",
    "check_database_health",
    "create_tables",
    "drop_tables",
    "run_migrations",
    "mask_database_url",
    "reset_engine_for_testing",
    "AnalysisRepository",
    "SqlAlchemyAnalysisRepository",
    "SqlAlchemyFingerprintRepository",
    "SqlAlchemySessionRepository",
    "SqlAlchemyAuditRepository",
]

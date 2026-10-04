"""Database connection and session lifecycle management for Nivesh Firewall.

Handles:
- Centralized configuration via NIVESH_DATABASE_URL
- Engine creation with dialect-specific connection pool safeguards
- Context-managed database sessions with automatic commit/rollback
- Safe database health checking without secret exposure
- Migration and schema lifecycle utilities
"""

import os
import re
from contextlib import contextmanager
from typing import Optional, Generator, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool

from nivesh.config import get_settings
from nivesh.storage.models import Base
from nivesh.storage.errors import DatabaseUnavailableError

_ENGINE: Optional[Engine] = None
_SESSION_FACTORY: Optional[sessionmaker] = None


def mask_database_url(url: str) -> str:
    """Mask credentials in a database URL for safe logging/health reporting."""
    if not url:
        return ""
    # Matches scheme://user:password@host...
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:[REDACTED]@", url)


def get_engine(database_url: Optional[str] = None) -> Engine:
    """Retrieve or create the singleton SQLAlchemy Engine."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None and database_url is None:
        return _ENGINE

    settings = get_settings()
    url = database_url or settings.database_url or "sqlite:///./nivesh_dev.db"

    engine_kwargs: dict[str, Any] = {}
    if url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            # Maintain persistent in-memory database across connections for test isolation
            engine_kwargs["poolclass"] = StaticPool
    else:
        # PostgreSQL / Production settings
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = settings.db_pool_recycle
        engine_kwargs["pool_size"] = settings.db_pool_size
        engine_kwargs["max_overflow"] = settings.db_max_overflow
        engine_kwargs["pool_timeout"] = settings.db_pool_timeout

        # Configure SSL mode if specified and not already in connection string
        if settings.db_ssl_mode and "sslmode=" not in url.lower():
            connect_args = engine_kwargs.setdefault("connect_args", {})
            connect_args["sslmode"] = settings.db_ssl_mode

    created_engine = create_engine(url, **engine_kwargs)

    # Cache if initializing default engine
    if database_url is None:
        _ENGINE = created_engine
        _SESSION_FACTORY = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_ENGINE,
        )

    return created_engine


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """Retrieve or create a sessionmaker bound to the given or default engine."""
    global _SESSION_FACTORY
    if engine is not None:
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if _SESSION_FACTORY is None:
        get_engine()
    return _SESSION_FACTORY


@contextmanager
def get_db_session(
    engine: Optional[Engine] = None,
    session_factory: Optional[sessionmaker] = None,
) -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit, rollback, and closure."""
    factory = session_factory or (
        get_session_factory(engine) if engine else get_session_factory()
    )
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        try:
            from nivesh.observability import metrics
            metrics.persistence_rollbacks_total.inc(operation="db_session")
        except Exception:
            pass
        raise
    finally:
        session.close()


def check_database_health(engine: Optional[Engine] = None) -> dict[str, Any]:
    """Perform a lightweight database ping without exposing credentials."""
    eng = engine or get_engine()
    dialect = eng.dialect.name
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "dialect": dialect,
            "connected": True,
        }
    except Exception as e:
        try:
            from nivesh.observability import metrics
            metrics.persistence_connection_failures_total.inc()
        except Exception:
            pass
        return {
            "status": "unavailable",
            "dialect": dialect,
            "connected": False,
            "error": "Database connectivity check failed",
        }


def create_tables(engine: Optional[Engine] = None) -> None:
    """Create all defined tables in the database schema."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)


def drop_tables(engine: Optional[Engine] = None) -> None:
    """Drop all tables in the database schema (used for testing)."""
    eng = engine or get_engine()
    Base.metadata.drop_all(bind=eng)


def run_migrations(
    alembic_ini_path: Optional[str] = None,
    database_url: Optional[str] = None,
) -> None:
    """Programmatically run Alembic migrations to head idempotently."""
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import inspect, text
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ini_path = alembic_ini_path or os.path.join(base_dir, "alembic.ini")
    alembic_cfg = Config(ini_path)

    eng = get_engine(database_url) if database_url else get_engine()
    if database_url:
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    inspector = inspect(eng)
    tables = inspector.get_table_names()

    has_analyses = "analyses" in tables
    has_version_row = False
    if "alembic_version" in tables:
        with eng.connect() as conn:
            val = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if val:
                has_version_row = True

    try:
        # If schema exists but alembic_version row was not stamped, stamp head
        if has_analyses and not has_version_row:
            command.stamp(alembic_cfg, "head")
        else:
            command.upgrade(alembic_cfg, "head")
    finally:
        if database_url:
            eng.dispose()


def reset_engine_for_testing() -> None:
    """Clear cached engine and session factory singletons."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None

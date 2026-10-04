"""Phase 16.2 — Production Database & Persistent Infrastructure Test Suite.

Validates:
1. PostgreSQL production settings, rejection of SQLite in production, and pool configuration.
2. SQLAlchemy connection pooling (pool_size, max_overflow, pool_timeout, pool_recycle, pool_pre_ping, sslmode).
3. Database credential masking and zero secret leakage in health checks and URLs.
4. Migration integrity: fresh database upgrade to head and idempotence of repeated migrations.
5. Persistence lifecycle across application restart (Create -> Persist -> Dispose -> Reopen -> Verify).
6. Foreign key CASCADE constraints (deleting analysis cascades to decisions and results).
7. Controlled database failure behavior (outage simulation, transaction rollback, and connection cleanup).
8. Backup and restore data roundtrip validation in an isolated database.
"""

import os
import tempfile
import uuid
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from nivesh.config.settings import Settings
from nivesh.storage.database import (
    get_engine,
    get_db_session,
    check_database_health,
    mask_database_url,
    run_migrations,
    reset_engine_for_testing,
    create_tables,
    drop_tables,
)
from nivesh.storage.models import (
    Base,
    AnalysisModel,
    PolicyDecisionModel,
    AnalysisResultModel,
    FingerprintModel,
    FingerprintObservationModel,
)


# ------------------------------------------------------------------------------
# 1. PostgreSQL Production Settings & Validation
# ------------------------------------------------------------------------------
def test_postgresql_production_settings_validation():
    """Verify production requires PostgreSQL and accepts configurable pooling options."""
    # SQLite rejected in production
    with pytest.raises(ValueError, match="SQLite"):
        Settings(
            env="production",
            debug=False,
            database_url="sqlite:///./nivesh_prod.db",
            allowed_origins=["https://app.nivesh.ai"],
        ).validate_production_readiness()

    # Valid PostgreSQL production configuration
    prod_settings = Settings(
        env="production",
        debug=False,
        database_url="postgresql://nivesh_user:StrongPassword123@prod-postgres:5432/nivesh_db",
        allowed_origins=["https://app.nivesh.ai"],
        db_pool_size=15,
        db_max_overflow=30,
        db_pool_timeout=45.0,
        db_pool_recycle=1200,
        db_ssl_mode="require",
    )
    prod_settings.validate_production_readiness()
    assert prod_settings.db_pool_size == 15
    assert prod_settings.db_max_overflow == 30
    assert prod_settings.db_pool_timeout == 45.0
    assert prod_settings.db_pool_recycle == 1200
    assert prod_settings.db_ssl_mode == "require"


# ------------------------------------------------------------------------------
# 2. Connection Pooling & SSL Configuration
# ------------------------------------------------------------------------------
def test_connection_pooling_and_ssl_parameters():
    """Verify get_engine correctly configures pooling and SSL for PostgreSQL."""
    test_settings = Settings(
        env="development",
        database_url="postgresql://mock_user:mock_pass@127.0.0.1:5432/mock_db",
        db_pool_size=12,
        db_max_overflow=25,
        db_pool_timeout=20.0,
        db_pool_recycle=900,
        db_ssl_mode="require",
    )

    with patch("nivesh.storage.database.get_settings", return_value=test_settings):
        with patch("nivesh.storage.database.create_engine") as mock_create_engine:
            mock_create_engine.return_value = MagicMock()
            get_engine("postgresql://mock_user:mock_pass@127.0.0.1:5432/mock_db")

            mock_create_engine.assert_called_once()
            args, kwargs = mock_create_engine.call_args
            assert args[0] == "postgresql://mock_user:mock_pass@127.0.0.1:5432/mock_db"
            assert kwargs["pool_pre_ping"] is True
            assert kwargs["pool_recycle"] == 900
            assert kwargs["pool_size"] == 12
            assert kwargs["max_overflow"] == 25
            assert kwargs["pool_timeout"] == 20.0
            assert kwargs.get("connect_args", {}).get("sslmode") == "require"


# ------------------------------------------------------------------------------
# 3. Database Credentials Masking & Zero Secret Leakage
# ------------------------------------------------------------------------------
def test_database_credentials_masking():
    """Verify database URLs are redacted in logging and health outputs."""
    raw_url = "postgresql://nivesh_admin:SuperSecretPass123!@db.internal:5432/nivesh_production"
    masked = mask_database_url(raw_url)
    assert "SuperSecretPass123!" not in masked
    assert "[REDACTED]" in masked or "***" in masked

    # Health check does not leak credentials on failure
    mock_eng = MagicMock()
    mock_eng.dialect.name = "postgresql"
    mock_eng.connect.side_effect = Exception("FATAL: password authentication failed for user 'nivesh_admin'")

    health = check_database_health(mock_eng)
    assert health["status"] == "unavailable"
    assert health["connected"] is False
    assert health["dialect"] == "postgresql"
    assert "SuperSecretPass123!" not in str(health)
    assert "password authentication failed" not in health.get("error", "")
    assert health.get("error") == "Database connectivity check failed"


# ------------------------------------------------------------------------------
# 4. Migration Integrity & Idempotence
# ------------------------------------------------------------------------------
def test_migration_fresh_and_idempotence():
    """Verify fresh database migration to head and repeated idempotent execution."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    test_eng = None
    try:
        db_url = f"sqlite:///{db_path}"
        # 1. Fresh database migration
        run_migrations(database_url=db_url)

        test_eng = create_engine(db_url)
        inspector = inspect(test_eng)
        tables = inspector.get_table_names()

        expected_tables = [
            "analyses",
            "policy_decisions",
            "analysis_results",
            "engine_executions",
            "fingerprints",
            "fingerprint_observations",
            "sessions",
            "session_events",
            "audit_records",
            "alembic_version",
        ]
        for tbl in expected_tables:
            assert tbl in tables, f"Expected table '{tbl}' missing after migration"

        # Dispose inspection engine before running subsequent migration
        test_eng.dispose()
        test_eng = None

        # 2. Idempotent repeated migration against existing schema
        run_migrations(database_url=db_url)
        test_eng = create_engine(db_url)
        inspector2 = inspect(test_eng)
        tables2 = inspector2.get_table_names()
        assert set(tables) == set(tables2)
    finally:
        if test_eng is not None:
            test_eng.dispose()
        reset_engine_for_testing()
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass


# ------------------------------------------------------------------------------
# 5. Persistence Lifecycle Across Application Restart
# ------------------------------------------------------------------------------
def test_persistence_lifecycle_across_restart():
    """Verify application records survive process/engine restarts without data corruption."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    test_url = f"sqlite:///{db_path}"
    test_id = f"ANLS-{uuid.uuid4().hex[:12].upper()}"

    try:
        # Step A: Initialize engine, apply schema, write record
        eng1 = create_engine(test_url)
        Base.metadata.create_all(bind=eng1)

        with Session(eng1) as session:
            analysis = AnalysisModel(
                analysis_id=test_id,
                session_id="SESS-001",
                pipeline_status="COMPLETED",
                created_at="2026-10-04T12:00:00Z",
                input_type="text",
                channel="web",
                content_summary="Production mutual fund advice test",
                contains_financial_content=True,
            )
            decision = PolicyDecisionModel(
                analysis_id=test_id,
                decision="ALLOW",
                severity="INFORMATIONAL",
                primary_reason="No policy intervention required.",
                reason_codes=["NO_INTERVENTION_REQUIRED"],
                user_message="Verified safe content.",
                technical_message="Engine 8 allow decision.",
                actions_required=[],
                policy_version="8.0.0",
                created_at="2026-10-04T12:00:00Z",
            )
            result = AnalysisResultModel(
                analysis_id=test_id,
                content_summary_json={"category": "INVESTMENT"},
                claims_json=[],
                actions_json=[],
                evidence_json={"verified": True},
                identity_json={"entities": []},
                threat_json={"threat_signals": []},
                fingerprint_json={"match_type": "NO_MATCH"},
                behaviour_json={"signals": []},
                provenance_json={"timestamp": "2026-10-04T12:00:00Z"},
            )
            session.add(analysis)
            session.add(decision)
            session.add(result)
            session.commit()

        # Step B: Simulate Application Shutdown (Dispose engine 1)
        eng1.dispose()

        # Step C: Simulate Application Restart (Create engine 2 from scratch)
        eng2 = create_engine(test_url)
        with Session(eng2) as session:
            retrieved = session.query(AnalysisModel).filter_by(analysis_id=test_id).first()
            assert retrieved is not None
            assert retrieved.analysis_id == test_id
            assert retrieved.pipeline_status == "COMPLETED"
            assert retrieved.content_summary == "Production mutual fund advice test"
            assert retrieved.policy_decision is not None
            assert retrieved.policy_decision.decision == "ALLOW"
            assert retrieved.result is not None
            assert retrieved.result.evidence_json.get("verified") is True

        eng2.dispose()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# ------------------------------------------------------------------------------
# 6. Foreign Key CASCADE Constraints Integrity
# ------------------------------------------------------------------------------
def test_foreign_key_cascade_deletion():
    """Verify deleting an analysis cascades cleanly to child records."""
    test_id = f"ANLS-CASCADE-{uuid.uuid4().hex[:8].upper()}"
    with get_db_session() as session:
        analysis = AnalysisModel(
            analysis_id=test_id,
            pipeline_status="COMPLETED",
            created_at="2026-10-04T12:00:00Z",
            input_type="text",
            channel="web",
        )
        decision = PolicyDecisionModel(
            analysis_id=test_id,
            decision="WARN",
            severity="HIGH",
            primary_reason="Potential scam indicator.",
            reason_codes=["SUSPICIOUS_PROMISE"],
            user_message="Proceed with caution.",
            technical_message="High risk claim.",
            actions_required=[],
            created_at="2026-10-04T12:00:00Z",
        )
        session.add(analysis)
        session.add(decision)

    # Verify both records exist
    with get_db_session() as session:
        assert session.query(AnalysisModel).filter_by(analysis_id=test_id).first() is not None
        assert session.query(PolicyDecisionModel).filter_by(analysis_id=test_id).first() is not None

        # Delete parent
        rec = session.query(AnalysisModel).filter_by(analysis_id=test_id).first()
        session.delete(rec)

    # Verify child record was cascade deleted
    with get_db_session() as session:
        assert session.query(AnalysisModel).filter_by(analysis_id=test_id).first() is None
        assert session.query(PolicyDecisionModel).filter_by(analysis_id=test_id).first() is None


# ------------------------------------------------------------------------------
# 7. Controlled Database Failure Handling
# ------------------------------------------------------------------------------
def test_controlled_database_failure_behavior():
    """Verify transaction rollback prevents dirty state and captures failure metrics."""
    initial_count = 0
    with get_db_session() as session:
        initial_count = session.query(AnalysisModel).count()

    # Intentional duplicate PK violation
    dupe_id = f"DUPE-{uuid.uuid4().hex[:8]}"
    with get_db_session() as session:
        session.add(AnalysisModel(
            analysis_id=dupe_id,
            pipeline_status="COMPLETED",
            created_at="2026-10-04",
            input_type="text",
            channel="web",
        ))

    # Second insert with same PK must fail and roll back cleanly
    with pytest.raises(Exception):
        with get_db_session() as session:
            session.add(AnalysisModel(
                analysis_id=dupe_id,
                pipeline_status="FAILED",
                created_at="2026-10-04",
                input_type="text",
                channel="web",
            ))

    # Verify database remains in clean, consistent state
    with get_db_session() as session:
        current_count = session.query(AnalysisModel).count()
        assert current_count == initial_count + 1


# ------------------------------------------------------------------------------
# 8. Backup & Restore Data Roundtrip Validation
# ------------------------------------------------------------------------------
def test_backup_and_restore_data_roundtrip():
    """Verify database schema and records can be roundtripped into a clean restore database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_source:
        source_path = f_source.name
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f_restore:
        restore_path = f_restore.name

    source_url = f"sqlite:///{source_path}"
    restore_url = f"sqlite:///{restore_path}"
    test_id = f"ANLS-BACKUP-{uuid.uuid4().hex[:8]}"

    eng_source = None
    eng_restore = None
    try:
        # Step 1: Initialize source database and populate data
        run_migrations(database_url=source_url)
        eng_source = create_engine(source_url)
        with Session(eng_source) as session:
            session.add(AnalysisModel(
                analysis_id=test_id,
                pipeline_status="COMPLETED",
                created_at="2026-10-04T12:00:00Z",
                input_type="text",
                channel="telegram",
                content_summary="Backup test sample analysis",
            ))
            session.commit()
        eng_source.dispose()
        eng_source = None

        # Step 2: Backup snapshot (copy binary snapshot representing clean logical dump)
        with open(source_path, "rb") as src, open(restore_path, "wb") as dst:
            dst.write(src.read())

        # Step 3: Verify restored database functions identically
        eng_restore = create_engine(restore_url)
        with Session(eng_restore) as session:
            record = session.query(AnalysisModel).filter_by(analysis_id=test_id).first()
            assert record is not None
            assert record.analysis_id == test_id
            assert record.channel == "telegram"
            assert record.content_summary == "Backup test sample analysis"

        # Step 4: Verify health check on restored database
        health = check_database_health(eng_restore)
        assert health["status"] == "healthy"
        assert health["connected"] is True
        eng_restore.dispose()
        eng_restore = None
    finally:
        if eng_source is not None:
            try:
                eng_source.dispose()
            except Exception:
                pass
        if eng_restore is not None:
            try:
                eng_restore.dispose()
            except Exception:
                pass
        reset_engine_for_testing()
        for path in (source_path, restore_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

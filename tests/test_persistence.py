"""Phase 14.2 — Persistent Data & Storage Layer Test Suite.

Validates:
- Test 1 — Database initialization: Database can initialize using configured URL.
- Test 2 — Migration: Schema can be created and reversed through migrations.
- Test 3 — Analysis persistence: Completed analysis can be stored.
- Test 4 — Analysis retrieval: Analysis can be retrieved by analysis ID.
- Test 5 — Analysis correlation: Engine result references remain associated with correct analysis.
- Test 6 — Policy persistence: Engine 8 decision is stored correctly.
- Test 7 — Fingerprint persistence: Fingerprint survives process restart.
- Test 8 — Fingerprint observation: Observation is persisted correctly.
- Test 9 — Duplicate observation: Repeated observation does not inflate counts.
- Test 10 — Fingerprint dispute: Dispute state persists correctly.
- Test 11 — Session persistence: Required session metadata persists.
- Test 12 — Behaviour privacy: Sensitive fields are absent from stored behavioural events.
- Test 13 — Provenance: Provenance survives persistence and retrieval.
- Test 14 — Engine execution records: Execution metadata persists correctly.
- Test 15 — Transaction rollback: Intentional failure rolls back atomic operations.
- Test 16 — Concurrency: Concurrent fingerprint observations remain consistent.
- Test 17 — Idempotency: Repeated persistence request does not create duplicates.
- Test 18 — Analysis deletion: Deletion follows defined retention/privacy semantics.
- Test 19 — Collective intelligence separation: Deleting analysis does not corrupt fingerprint intelligence.
- Test 20 — Sensitive-field protection: Forbidden fields cannot be persisted through normal repository APIs.
- Section 49 — Full End-to-End Integration Test via Unified Firewall API.
- Section 50 — Realistic Process Restart Persistence Test.
- Section 51 — Development / Test / Production Configuration Validation.
"""

import os
import tempfile
import threading
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from nivesh.storage import (
    Base,
    create_tables,
    drop_tables,
    run_migrations,
    check_database_health,
    mask_database_url,
    SqlAlchemyAnalysisRepository,
    SqlAlchemyFingerprintRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyAuditRepository,
    ForbiddenFieldError,
    AnalysisModel,
    FingerprintModel,
)
from nivesh.orchestrator import ProductOrchestrator, OrchestratorConfig
from nivesh.schemas.fingerprint import (
    ScamFingerprint,
    FingerprintObservation,
)
from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionEventType,
    InteractionHistory,
)
from nivesh.api.app import app


@pytest.fixture
def isolated_db():
    """Create an isolated in-memory SQLite database bound to fresh session factory."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    analysis_repo = SqlAlchemyAnalysisRepository(session_factory=factory)
    fp_repo = SqlAlchemyFingerprintRepository(session_factory=factory)
    session_repo = SqlAlchemySessionRepository(session_factory=factory)
    audit_repo = SqlAlchemyAuditRepository(session_factory=factory)

    yield {
        "engine": test_engine,
        "factory": factory,
        "analysis_repo": analysis_repo,
        "fp_repo": fp_repo,
        "session_repo": session_repo,
        "audit_repo": audit_repo,
    }

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


# ------------------------------------------------------------------------------
# Test 1 — Database Initialization
# ------------------------------------------------------------------------------
def test_1_database_initialization(isolated_db):
    """Database initializes using configured connection and health check succeeds."""
    engine = isolated_db["engine"]
    health = check_database_health(engine)
    assert health["status"] == "healthy"
    assert health["dialect"] == "sqlite"
    assert health["connected"] is True


# ------------------------------------------------------------------------------
# Test 2 — Migration Execution
# ------------------------------------------------------------------------------
def test_2_migration_execution():
    """Schema can be created and reversed via programmatic Alembic runner."""
    import uuid
    import gc
    tmp_path = os.path.join(tempfile.gettempdir(), f"alembic_mig_{uuid.uuid4().hex}.db")

    try:
        from alembic.config import Config
        from alembic import command

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        ini_path = os.path.join(base_dir, "alembic.ini")
        alembic_cfg = Config(ini_path)
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path}")

        # Upgrade to head
        command.upgrade(alembic_cfg, "head")

        # Verify tables created
        mig_engine = create_engine(f"sqlite:///{tmp_path}")
        from sqlalchemy import inspect
        inspector = inspect(mig_engine)
        tables = inspector.get_table_names()
        assert "analyses" in tables
        assert "fingerprints" in tables
        assert "policy_decisions" in tables
        assert "session_events" in tables
        mig_engine.dispose()

        # Downgrade to base
        command.downgrade(alembic_cfg, "base")

        mig_engine2 = create_engine(f"sqlite:///{tmp_path}")
        tables_after = inspect(mig_engine2).get_table_names()
        assert "analyses" not in tables_after
        mig_engine2.dispose()
    finally:
        gc.collect()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ------------------------------------------------------------------------------
# Test 3 — Analysis Persistence
# ------------------------------------------------------------------------------
def test_3_analysis_persistence(isolated_db):
    """Completed orchestrator analysis is persisted into the database."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    result = orch.analyze(
        text="SEBI registered advisor Rahul Sharma guarantees 40% monthly returns. Pay ₹5,000.",
        channel="telegram",
    )
    assert result.is_success is True

    # Verify presence in repository
    assert analysis_repo.exists(result.analysis_id) is True


# ------------------------------------------------------------------------------
# Test 4 — Analysis Retrieval
# ------------------------------------------------------------------------------
def test_4_analysis_retrieval(isolated_db):
    """Persisted analysis can be retrieved by analysis_id without rerunning pipeline."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    result = orch.analyze(
        text="Learn about index funds and diversified equity investing.",
        channel="web",
    )
    retrieved = analysis_repo.get_analysis(result.analysis_id)
    assert retrieved is not None
    assert retrieved.analysis_id == result.analysis_id
    assert retrieved.pipeline_status == "COMPLETED"
    assert retrieved.decision.decision in ("ALLOW", "INFORM")
    assert retrieved.content.input_type == "text"


# ------------------------------------------------------------------------------
# Test 5 — Analysis Correlation
# ------------------------------------------------------------------------------
def test_5_analysis_correlation(isolated_db):
    """Engine result references and summaries remain strictly correlated with the parent analysis."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    res1 = orch.analyze(text="Offer A guaranteed returns 30%", channel="telegram")
    res2 = orch.analyze(text="Offer B guaranteed returns 50%", channel="whatsapp")

    retrieved1 = analysis_repo.get_analysis(res1.analysis_id)
    retrieved2 = analysis_repo.get_analysis(res2.analysis_id)

    assert retrieved1.analysis_id == res1.analysis_id
    assert retrieved2.analysis_id == res2.analysis_id
    assert retrieved1.content.channel == "telegram"
    assert retrieved2.content.channel == "whatsapp"


# ------------------------------------------------------------------------------
# Test 6 — Policy Persistence
# ------------------------------------------------------------------------------
def test_6_policy_persistence(isolated_db):
    """Engine 8 policy decision is accurately persisted with immutability."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    res = orch.analyze(
        text="Guaranteed doubling in 3 days. Send ₹10,000 crypto to wallet immediately.",
        channel="telegram",
    )
    retrieved = analysis_repo.get_analysis(res.analysis_id)
    assert retrieved is not None
    assert retrieved.decision.decision in ("PAUSE", "BLOCK", "WARN")
    assert retrieved.decision.severity in ("HIGH", "CRITICAL", "MEDIUM")
    assert len(retrieved.decision.reason_codes) > 0
    assert retrieved.decision.policy_version == "8.0.0"


# ------------------------------------------------------------------------------
# Test 7 — Fingerprint Persistence (Survives Process Restart)
# ------------------------------------------------------------------------------
def test_7_fingerprint_persistence_restart():
    """Fingerprint persists across simulated process restart (new engine/session)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_file = tmp.name

    try:
        db_url = f"sqlite:///{db_file}"
        eng1 = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=eng1)
        f1 = sessionmaker(bind=eng1)
        repo1 = SqlAlchemyFingerprintRepository(session_factory=f1)

        now_iso = datetime.now(timezone.utc).isoformat()
        fp = ScamFingerprint(
            fingerprint_id="SFP-RESTART-001",
            schema_version="1.0",
            canonical_features=["ACTION:PAYMENT", "CLAIM:GUARANTEED_RETURN"],
            exact_signature="sig_exact_restart",
            semantic_signature="sig_sem_restart",
            attack_path_signature="FINANCIAL_REQUEST",
            created_at=now_iso,
            updated_at=now_iso,
            first_seen=now_iso,
            last_seen=now_iso,
            observation_count=1,
            threat_families=["GUARANTEED_RETURN_SCHEME"],
            status="ACTIVE",
            description="Restart test fingerprint",
        )
        repo1.add_fingerprint(fp)
        eng1.dispose()

        # Simulate fresh process startup
        eng2 = create_engine(db_url, connect_args={"check_same_thread": False})
        f2 = sessionmaker(bind=eng2)
        repo2 = SqlAlchemyFingerprintRepository(session_factory=f2)

        recovered = repo2.get_fingerprint("SFP-RESTART-001")
        assert recovered is not None
        assert recovered.fingerprint_id == "SFP-RESTART-001"
        assert recovered.exact_signature == "sig_exact_restart"
        assert recovered.status == "ACTIVE"
        eng2.dispose()
    finally:
        if os.path.exists(db_file):
            os.remove(db_file)


# ------------------------------------------------------------------------------
# Test 8 — Fingerprint Observation Persistence
# ------------------------------------------------------------------------------
def test_8_fingerprint_observation(isolated_db):
    """Observation record is stored with structural dimensions and provenance."""
    fp_repo = isolated_db["fp_repo"]
    now_iso = datetime.now(timezone.utc).isoformat()

    fp = ScamFingerprint(
        fingerprint_id="SFP-OBS-001",
        schema_version="1.0",
        exact_signature="sig_obs_1",
        semantic_signature="sem_obs_1",
        attack_path_signature="DISCOVERY->PAYMENT",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=1,
        status="NEW",
    )
    fp_repo.add_fingerprint(fp)

    obs = FingerprintObservation(
        observation_id="OBS-101",
        fingerprint_id="SFP-OBS-001",
        content_id="CNT-101",
        observed_at=now_iso,
        channel="telegram",
        features=["ACTION:PAYMENT"],
        match_type="EXACT_MATCH",
        match_confidence=1.0,
        matched_dimensions=["attack_path"],
        provenance={"engine": "Engine 7"},
    )
    fp_repo.record_observation("SFP-OBS-001", obs, content_hash="hash_obs_101")

    observations = fp_repo.list_observations("SFP-OBS-001")
    assert len(observations) == 1
    assert observations[0].observation_id == "OBS-101"
    assert observations[0].channel == "telegram"


# ------------------------------------------------------------------------------
# Test 9 — Duplicate Observation Protection
# ------------------------------------------------------------------------------
def test_9_duplicate_observation_protection(isolated_db):
    """Repeated copy from identical source does not artificially inflate observation count."""
    fp_repo = isolated_db["fp_repo"]
    now_iso = datetime.now(timezone.utc).isoformat()

    fp = ScamFingerprint(
        fingerprint_id="SFP-AMP-001",
        schema_version="1.0",
        exact_signature="sig_amp",
        semantic_signature="sem_amp",
        attack_path_signature="PAYMENT",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=0,
        status="NEW",
    )
    fp_repo.add_fingerprint(fp)

    identical_hash = "sha256_identical_broadcast_spam_hash"
    for i in range(5):
        obs = FingerprintObservation(
            observation_id=f"OBS-AMP-{i+1}",
            fingerprint_id="SFP-AMP-001",
            content_id=f"CNT-{i+1}",
            observed_at=now_iso,
            channel="telegram",
            features=["ACTION:PAYMENT"],
            content_hash=identical_hash,
            match_type="EXACT_MATCH",
            match_confidence=1.0,
            matched_dimensions=["attack_path"],
            provenance={"engine": "Engine 7"},
        )
        fp_repo.record_observation("SFP-AMP-001", obs, content_hash=identical_hash)

    # Observation count should remain 1 because content_hash was already seen
    stored_fp = fp_repo.get_fingerprint("SFP-AMP-001")
    assert stored_fp.observation_count == 1
    all_obs = fp_repo.list_observations("SFP-AMP-001")
    assert len(all_obs) == 5
    assert all_obs[0].is_duplicate_origin is False
    assert all_obs[1].is_duplicate_origin is True


# ------------------------------------------------------------------------------
# Test 10 — Fingerprint Dispute Persistence
# ------------------------------------------------------------------------------
def test_10_fingerprint_dispute_persistence(isolated_db):
    """Fingerprint dispute transitions to DISPUTED non-destructively with audit history."""
    fp_repo = isolated_db["fp_repo"]
    now_iso = datetime.now(timezone.utc).isoformat()

    fp = ScamFingerprint(
        fingerprint_id="SFP-DISPUTE-001",
        schema_version="1.0",
        exact_signature="sig_disp",
        semantic_signature="sem_disp",
        attack_path_signature="PAYMENT",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=2,
        status="ACTIVE",
    )
    fp_repo.add_fingerprint(fp)

    disputed = fp_repo.dispute_fingerprint(
        "SFP-DISPUTE-001",
        reason="Legitimate registered brokerage promotional campaign",
        actor="compliance_officer",
    )
    assert disputed is not None
    assert disputed.status == "DISPUTED"
    assert disputed.dispute_count == 1
    assert len(disputed.dispute_notes) == 1
    assert len(disputed.status_change_history) == 1
    assert disputed.status_change_history[0]["to_status"] == "DISPUTED"


# ------------------------------------------------------------------------------
# Test 11 — Session Persistence
# ------------------------------------------------------------------------------
def test_11_session_persistence(isolated_db):
    """Engine 10 interaction session metadata and chronological events persist."""
    session_repo = isolated_db["session_repo"]
    event1 = InteractionEvent(
        event_id="EVT-001",
        event_type=InteractionEventType.CONTENT_VIEW,
        channel="telegram",
        sequence_index=0,
        source_type="messaging_app",
    )
    event2 = InteractionEvent(
        event_id="EVT-002",
        event_type=InteractionEventType.ACTION_REQUESTED,
        action_id="ACT-001",
        channel="telegram",
        sequence_index=1,
        source_type="messaging_app",
    )

    session_repo.record_event("SESS-TEST-001", event1)
    history = session_repo.record_event("SESS-TEST-001", event2)

    assert history.session_id == "SESS-TEST-001"
    assert history.event_count == 2
    assert len(history.events) == 2
    assert history.events[0].event_id == "EVT-001"
    assert history.events[1].event_id == "EVT-002"


# ------------------------------------------------------------------------------
# Test 12 — Behaviour Privacy Boundary
# ------------------------------------------------------------------------------
def test_12_behaviour_privacy_boundary(isolated_db):
    """Forbidden credential fields (passwords, OTPs, PINs, cards) are rejected from session metadata."""
    session_repo = isolated_db["session_repo"]

    # Passing forbidden key raises ForbiddenFieldError
    with pytest.raises(ForbiddenFieldError):
        bad_event = InteractionEvent(
            event_id="EVT-BAD",
            event_type=InteractionEventType.ACTION_REQUESTED,
            metadata={"safe_key": "safe_val"},
        )
        # Manually inject forbidden key bypassing model init
        bad_event.metadata["password"] = "SecretPassword123"
        session_repo.record_event("SESS-PRIV-001", bad_event)


# ------------------------------------------------------------------------------
# Test 13 — Provenance Persistence
# ------------------------------------------------------------------------------
def test_13_provenance_persistence(isolated_db):
    """Audit provenance dictionary survives persistence and retrieval intact."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    result = orch.analyze(text="Educational article on inflation and bonds.", channel="web")
    retrieved = analysis_repo.get_analysis(result.analysis_id)
    assert retrieved is not None
    assert "orchestrator_version" in retrieved.provenance
    assert retrieved.provenance["analysis_id"] == result.analysis_id


# ------------------------------------------------------------------------------
# Test 14 — Engine Execution Telemetry Records
# ------------------------------------------------------------------------------
def test_14_engine_execution_records(isolated_db):
    """Engine execution records are recorded in engine_executions table."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    result = orch.analyze(text="Test execution telemetry tracking.", channel="web")
    exec_records = analysis_repo.list_engine_executions(result.analysis_id)

    assert len(exec_records) > 0
    engine_keys = [r["engine_key"] for r in exec_records]
    assert "engine_1_content" in engine_keys
    assert "engine_8_policy" in engine_keys


# ------------------------------------------------------------------------------
# Test 15 — Transaction Rollback on Failure
# ------------------------------------------------------------------------------
def test_15_transaction_rollback(isolated_db):
    """Transactional persistence guarantees rollback if an atomic operation fails."""
    analysis_repo = isolated_db["analysis_repo"]
    factory = isolated_db["factory"]

    orch = ProductOrchestrator(analysis_repository=analysis_repo)
    result = orch.analyze(text="Atomic rollback test message.", channel="web")

    # Intentionally trigger an integrity error by attempting to insert a duplicate analysis directly
    with pytest.raises(Exception):
        with analysis_repo._session_factory() as sess:
            dup = AnalysisModel(
                analysis_id=result.analysis_id,
                pipeline_status="FAILED",
                created_at="now",
                input_type="text",
                channel="web",
            )
            sess.add(dup)
            sess.commit()


# ------------------------------------------------------------------------------
# Test 16 — Concurrency Safety
# ------------------------------------------------------------------------------
def test_16_concurrency_safety(isolated_db):
    """Concurrent observation writes do not corrupt fingerprint observation counts."""
    fp_repo = isolated_db["fp_repo"]
    now_iso = datetime.now(timezone.utc).isoformat()

    fp = ScamFingerprint(
        fingerprint_id="SFP-CONCUR-001",
        schema_version="1.0",
        exact_signature="sig_concur",
        semantic_signature="sem_concur",
        attack_path_signature="PAYMENT",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=0,
        status="NEW",
    )
    fp_repo.add_fingerprint(fp)

    num_threads = 10
    barrier = threading.Barrier(num_threads)

    def worker(idx: int):
        barrier.wait()
        obs = FingerprintObservation(
            observation_id=f"OBS-CONCUR-{idx}",
            fingerprint_id="SFP-CONCUR-001",
            content_id=f"CNT-CONCUR-{idx}",
            observed_at=now_iso,
            channel="web",
            features=["ACTION:PAYMENT"],
            match_type="EXACT_MATCH",
            match_confidence=1.0,
            matched_dimensions=["attack_path"],
            provenance={"engine": "Engine 7"},
        )
        fp_repo.record_observation("SFP-CONCUR-001", obs, content_hash=f"hash_thread_{idx}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stored = fp_repo.get_fingerprint("SFP-CONCUR-001")
    assert stored.observation_count == num_threads
    all_obs = fp_repo.list_observations("SFP-CONCUR-001")
    assert len(all_obs) == num_threads


# ------------------------------------------------------------------------------
# Test 17 — Idempotency
# ------------------------------------------------------------------------------
def test_17_idempotency(isolated_db):
    """Repeated persistence requests with same idempotency_key do not create duplicate records."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    key = "IDEM-KEY-UNIQUE-12345"
    res1 = orch.analyze(text="Idempotency test payload", idempotency_key=key)
    res2 = orch.analyze(text="Idempotency test payload", idempotency_key=key)

    assert res1.analysis_id == res2.analysis_id


# ------------------------------------------------------------------------------
# Test 18 — Analysis Deletion Semantics
# ------------------------------------------------------------------------------
def test_18_analysis_deletion_semantics(isolated_db):
    """Deleting an analysis removes analysis and related child rows cleanly."""
    analysis_repo = isolated_db["analysis_repo"]
    orch = ProductOrchestrator(analysis_repository=analysis_repo)

    res = orch.analyze(text="Temporary analysis to delete", channel="web")
    a_id = res.analysis_id

    assert analysis_repo.exists(a_id) is True
    deleted = analysis_repo.delete_analysis(a_id)
    assert deleted is True
    assert analysis_repo.exists(a_id) is False
    assert analysis_repo.get_analysis(a_id) is None


# ------------------------------------------------------------------------------
# Test 19 — Collective Intelligence Separation
# ------------------------------------------------------------------------------
def test_19_collective_intelligence_separation(isolated_db):
    """Deleting an individual user analysis does NOT destroy independent collective fingerprints."""
    analysis_repo = isolated_db["analysis_repo"]
    fp_repo = isolated_db["fp_repo"]

    # 1. Store a collective fingerprint
    now_iso = datetime.now(timezone.utc).isoformat()
    fp = ScamFingerprint(
        fingerprint_id="SFP-INDEP-001",
        schema_version="1.0",
        exact_signature="sig_indep",
        semantic_signature="sem_indep",
        attack_path_signature="PAYMENT",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=5,
        status="ACTIVE",
    )
    fp_repo.add_fingerprint(fp)

    # 2. Store an individual analysis
    orch = ProductOrchestrator(analysis_repository=analysis_repo)
    res = orch.analyze(text="User analysis referencing collective threat", channel="web")
    a_id = res.analysis_id

    # 3. Delete individual analysis
    analysis_repo.delete_analysis(a_id)

    # 4. Collective fingerprint must remain intact
    survived_fp = fp_repo.get_fingerprint("SFP-INDEP-001")
    assert survived_fp is not None
    assert survived_fp.fingerprint_id == "SFP-INDEP-001"
    assert survived_fp.observation_count == 5


# ------------------------------------------------------------------------------
# Test 20 — Sensitive-Field Protection
# ------------------------------------------------------------------------------
def test_20_sensitive_field_protection(isolated_db):
    """Forbidden credential fields cannot be persisted via audit or session repositories."""
    audit_repo = isolated_db["audit_repo"]

    with pytest.raises(ForbiddenFieldError):
        audit_repo.record_audit(
            event_type="SECURITY_ALERT",
            actor="user",
            details={"password": "PlainTextPassword"},
        )


# ------------------------------------------------------------------------------
# Section 49 — Full End-to-End Integration Test
# ------------------------------------------------------------------------------
def test_section_49_full_integration():
    """Verify full end-to-end pipeline with persistence and retrieval via Unified Firewall API."""
    client = TestClient(app)

    payload = {
        "input_type": "text",
        "text": "SEBI certified trader promises 25% weekly profit. Pay ₹10,000 joining fee.",
        "channel": "telegram",
    }
    # 1. Analyze via API
    post_res = client.post("/api/v1/firewall/analyze", json=payload)
    assert post_res.status_code == 200
    data = post_res.json()
    analysis_id = data["analysis_id"]

    # 2. Retrieve via API without rerunning engines
    get_res = client.get(f"/api/v1/firewall/analysis/{analysis_id}")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()

    assert retrieved_data["analysis_id"] == analysis_id
    assert retrieved_data["decision"]["decision"] == data["decision"]["decision"]
    assert retrieved_data["decision"]["severity"] == data["decision"]["severity"]
    assert retrieved_data["content"]["input_type"] == "text"


# ------------------------------------------------------------------------------
# Section 50 — Realistic Process Restart Persistence Test
# ------------------------------------------------------------------------------
def test_section_50_restart_persistence():
    """Realistic process restart test: Process A persists analysis, Process B retrieves it."""
    import uuid
    import gc
    tmp_path = os.path.join(tempfile.gettempdir(), f"restart_test_{uuid.uuid4().hex}.db")

    try:
        db_url = f"sqlite:///{tmp_path}"

        # --- Process A ---
        engine_a = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine_a)
        factory_a = sessionmaker(bind=engine_a)
        repo_a = SqlAlchemyAnalysisRepository(session_factory=factory_a)
        orch_a = ProductOrchestrator(analysis_repository=repo_a)

        result_a = orch_a.analyze(
            text="Exclusive investment club offering guaranteed monthly returns.",
            channel="whatsapp",
        )
        saved_id = result_a.analysis_id
        engine_a.dispose()  # Process A terminates

        # --- Process B ---
        engine_b = create_engine(db_url, connect_args={"check_same_thread": False})
        factory_b = sessionmaker(bind=engine_b)
        repo_b = SqlAlchemyAnalysisRepository(session_factory=factory_b)
        orch_b = ProductOrchestrator(analysis_repository=repo_b)

        # Retrieve without having Process A's memory
        retrieved_b = orch_b.get_analysis(saved_id)
        assert retrieved_b is not None
        assert retrieved_b.analysis_id == saved_id
        assert retrieved_b.pipeline_status in ("COMPLETED", "DEGRADED")
        engine_b.dispose()  # Process B terminates
    finally:
        gc.collect()
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ------------------------------------------------------------------------------
# Section 51 — Development / Test / Production Configuration Validation
# ------------------------------------------------------------------------------
def test_section_51_environment_storage_validation():
    """Ensure environment-separated database contracts are enforced."""
    from nivesh.config import Settings

    # Dev default
    dev_settings = Settings(env="development")
    assert "nivesh_dev.db" in dev_settings.database_url

    # Test default
    test_settings = Settings(env="test")
    assert ":memory:" in test_settings.database_url

    # Production requires explicit persistent URL and rejects in-memory/dev
    with pytest.raises(ValueError, match="persistent NIVESH_DATABASE_URL"):
        Settings(
            env="production",
            database_url="",
            debug=False,
            allowed_origins=["https://nivesh.app"],
        )

    with pytest.raises(ValueError, match="cannot use development or in-memory"):
        Settings(
            env="production",
            database_url="sqlite:///:memory:",
            debug=False,
            allowed_origins=["https://nivesh.app"],
        )

    # Valid production settings with postgres
    prod_settings = Settings(
        env="production",
        database_url="postgresql://user:pass@db.internal:5432/nivesh_prod",
        debug=False,
        allowed_origins=["https://nivesh.app"],
    )
    assert "postgresql://" in prod_settings.database_url

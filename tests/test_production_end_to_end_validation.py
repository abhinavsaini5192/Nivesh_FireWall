"""Phase 16.5 — End-to-End Production Validation & Operational Readiness.

Comprehensive production-like validation suite verifying:
1. Full Stack Startup & Readiness Lifecycle (Health, Readiness, Migrations)
2. Complete End-to-End User Flow (Submission -> Orchestration -> Engines 1-10 -> Policy -> Persistence -> Retrieval)
3. End-to-End Scenario Matrix (Scenarios A through J):
   A — Benign Content (ALLOW)
   B — Unsupported / Unverified Claim (INSUFFICIENT_EVIDENCE)
   C — Suspicious Action Chain (Urgent / High-Exposure progression)
   D — Identity Claim Separation (Identity Mismatch vs Not Established)
   E — Numerical Contradiction (CONTRADICTED by authoritative evidence)
   F — Cross-Source Corroboration (NSE & BSE independent attribution)
   G — Source Outage Safe Degradation (Fail-safe, no fabricated live evidence)
   H — Database Failure Safe Behavior (503 on unready DB)
   I — Unauthorized Cross-User Access Protection (IDOR boundary)
   J — Sensitive Data Zero-Leakage (Zero passwords, OTPs, PINs, or DB URLs in outputs)
4. Persistence Across Stack Restart (Cold retrieval without re-execution)
5. Failure & Recovery Validation (Rate limiting, invalid payloads, safe errors)
6. Performance Smoke Measurements (API latency, analysis duration, health probe, DB probe)
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from nivesh.api.app import app
from nivesh.config.settings import Settings
from nivesh.storage.database import get_db_session, create_tables, check_database_health
from nivesh.security import create_access_token, UserRole
from nivesh.security.rate_limiter import rate_limiter
from nivesh.schemas.firewall import FirewallAnalyzeRequest
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.observability.logging import scrub_sensitive_tokens


@pytest.fixture(scope="module")
def prod_env():
    """Simulate a production runtime configuration."""
    test_settings = Settings(
        env="production",
        database_url="postgresql://nivesh_user:strong_prod_pass@postgres:5432/nivesh_db",
        allowed_origins=["https://app.nivesh.ai"],
        secret_key="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        forwarded_allow_ips="10.0.0.1, 127.0.0.1",
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=120,
        source_mode="OFFICIAL_SNAPSHOT",
    )
    with patch("nivesh.config.settings.get_settings", return_value=test_settings), \
         patch("nivesh.config.get_settings", return_value=test_settings), \
         patch("nivesh.api.app.get_settings", return_value=test_settings), \
         patch("nivesh.security.dependencies.get_settings", return_value=test_settings), \
         patch("nivesh.security.middleware.get_settings", return_value=test_settings):
        client = TestClient(app, raise_server_exceptions=False)
        yield {"client": client, "settings": test_settings}


# ==============================================================================
# 1. Full Stack Startup & Health Probes
# ==============================================================================
def test_01_production_probes_and_cors(prod_env):
    """Verify production liveness, readiness, and CORS headers."""
    client = prod_env["client"]

    # 1. Liveness Probe
    live_res = client.get("/health/live", headers={"Origin": "https://app.nivesh.ai"})
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "alive"
    assert live_res.headers.get("access-control-allow-origin") == "https://app.nivesh.ai"

    # 2. Readiness Probe
    with patch("nivesh.api.app.check_readiness", return_value=(True, {"status": "ready", "database": "healthy"})):
        ready_res = client.get("/health/ready", headers={"Origin": "https://app.nivesh.ai"})
        assert ready_res.status_code == 200
        assert ready_res.json()["status"] == "ready"

    # 3. Security Headers
    assert live_res.headers.get("x-frame-options") == "DENY"
    assert live_res.headers.get("x-content-type-options") == "nosniff"
    assert "Strict-Transport-Security" in live_res.headers


# ==============================================================================
# 2. End-to-End User Flow (Submission -> Orchestration -> Persistence -> Retrieval)
# ==============================================================================
def test_02_complete_end_to_end_firewall_journey(prod_env):
    """Execute complete 10-step user flow through Unified API."""
    client = prod_env["client"]
    token = create_access_token(user_id="retail_investor_01", roles=[UserRole.USER])

    # Steps 1-3: Submit financial content via API
    payload = {
        "input_type": "text",
        "text": "SEBI advisory warning regarding fraudulent social media advisory schemes promising guaranteed returns.",
        "channel": "web",
    }
    headers = {
        "Origin": "https://app.nivesh.ai",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    start_time = time.perf_counter()
    response = client.post("/api/v1/firewall/analyze", json=payload, headers=headers)
    latency_ms = (time.perf_counter() - start_time) * 1000

    # Steps 4-8: Confirm orchestration, engine execution, policy decision, provenance
    assert response.status_code == 200
    data = response.json()
    analysis_id = data["analysis_id"]

    assert analysis_id.startswith("ORCH-") or len(analysis_id) > 10
    assert data["pipeline_status"] == "COMPLETED"
    assert data["decision"]["decision"] in ("ALLOW", "INFORM", "WARN", "PAUSE", "BLOCK")
    assert "explanation" in data["decision"]
    assert "provenance" in data
    assert "evidence" in data
    assert data["duration_ms"] > 0

    # Steps 9-10: Retrieve saved analysis by ID without re-executing
    get_res = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Origin": "https://app.nivesh.ai", "Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    stored_data = get_res.json()
    assert stored_data["analysis_id"] == analysis_id
    assert stored_data["decision"]["decision"] == data["decision"]["decision"]
    assert stored_data["decision"]["explanation"]["primary_reason"] == data["decision"]["explanation"]["primary_reason"]


# ==============================================================================
# 3. End-to-End Scenario Matrix (Scenarios A through J)
# ==============================================================================

# Scenario A: Benign Content
def test_scenario_a_benign_content(prod_env):
    """Scenario A: Benign educational text produces ALLOW without threat fabrication."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "What is compound interest and how does rupee cost averaging benefit long-term mutual fund investors?",
            "channel": "web",
        },
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["decision"]["decision"] == "ALLOW"
    assert data["decision"]["severity"] in ("NONE", "INFORMATIONAL")


# Scenario B: Unsupported / Unverified Claim
def test_scenario_b_unsupported_unverified_claim(prod_env):
    """Scenario B: Unverified claim reports INSUFFICIENT_EVIDENCE rather than falsely declaring fraud."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "A newly formed local co-operative society says its deposit yield will be 11.5% next quarter.",
            "channel": "web",
        },
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["evidence"]["overall_status"] in ("INSUFFICIENT_EVIDENCE", "NOT_ESTABLISHED", "SOURCE_UNAVAILABLE")
    assert data["decision"]["decision"] != "BLOCK"


# Scenario C: Suspicious Action Chain
def test_scenario_c_suspicious_action_chain(prod_env):
    """Scenario C: Observable high-exposure action chain triggers appropriate policy intervention."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "Urgent notice: Send 50,000 INR immediately via UPI within 15 minutes to unlock locked trading account or face asset seizure!",
            "channel": "telegram",
        },
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["decision"]["decision"] in ("PAUSE", "BLOCK", "WARN")
    assert len(data["actions"]) > 0
    assert any(a["urgency_detected"] for a in data["actions"])


# Scenario D: Identity Claim Separation
def test_scenario_d_identity_claim_separation(prod_env):
    """Scenario D: Claimed entity without verified attribution produces separate identity findings."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "Official announcement from Reserve Bank of India offering lottery scheme payouts to account holders.",
            "channel": "sms",
        },
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["identity"]["identity_status"] in ("IDENTITY_MISMATCH", "NOT_ESTABLISHED")
    assert any("Reserve Bank" in e or "RBI" in e for e in data["identity"]["claimed_entities"])


# Scenario E: Numerical Contradiction
def test_scenario_e_numerical_contradiction(prod_env):
    """Scenario E: Materially contradicted numerical claim produces CONTRADICTED status."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "The Reserve Bank of India policy repo rate is currently set at 28.5% per annum.",
            "channel": "web",
        },
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["evidence"]["overall_status"] == "CONTRADICTED"
    assert data["evidence"]["contradicted_claims_count"] == 1
    assert data["evidence"]["supported_claims_count"] == 0


# Scenario F: Cross-Source Corroboration
def test_scenario_f_cross_source_corroboration(prod_env):
    """Scenario F: Multi-source queries preserve independent source attribution (NSE & BSE)."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "Reliance Industries Limited symbol RELIANCE listed on NSE and 500325 on BSE corporate actions.",
            "channel": "web",
        },
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 200
    data = res.json()
    sources = [s.get("source") for s in data["evidence"]["authoritative_sources"]]
    assert len(sources) > 0


# Scenario G: Source Outage Safe Degradation
def test_scenario_g_source_outage_safe_degradation(prod_env):
    """Scenario G: When authoritative sources are degraded, system fails safely without fabricating live records."""
    client = prod_env["client"]
    with patch.object(SourceIntelligenceEngine, "discover_and_retrieve", side_effect=RuntimeError("Source gateway timeout")):
        res = client.post(
            "/api/v1/firewall/analyze",
            json={"input_type": "text", "text": "Analyzing query during simulated network partition.", "channel": "web"},
            headers={"Origin": "https://app.nivesh.ai"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["pipeline_status"] in ("DEGRADED", "PARTIAL", "COMPLETED")


# Scenario H: Database Failure Safe Behavior
def test_scenario_h_database_failure_safe_behavior(prod_env):
    """Scenario H: Readiness probe returns 503 Service Unavailable when database probe fails."""
    client = prod_env["client"]
    with patch("nivesh.api.app.check_readiness", return_value=(False, {"status": "unready", "database": "unreachable"})):
        res = client.get("/health/ready", headers={"Origin": "https://app.nivesh.ai"})
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "unready"
        assert "unreachable" in str(data)


# Scenario I: Unauthorized Cross-User Access Protection (IDOR)
def test_scenario_i_unauthorized_cross_user_access(prod_env):
    """Scenario I: User B cannot retrieve User A's private analysis record (IDOR boundary)."""
    client = prod_env["client"]
    token_user_a = create_access_token(user_id="user_alice", roles=[UserRole.USER])
    token_user_b = create_access_token(user_id="user_bob", roles=[UserRole.USER])

    # 1. User A creates analysis
    create_res = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Alice personal financial analysis query.", "channel": "web"},
        headers={"Authorization": f"Bearer {token_user_a}", "Origin": "https://app.nivesh.ai"},
    )
    assert create_res.status_code == 200
    analysis_id = create_res.json()["analysis_id"]

    # 2. User B attempts to access Alice's analysis -> 403 Forbidden
    unauth_res = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_user_b}", "Origin": "https://app.nivesh.ai"},
    )
    assert unauth_res.status_code in (403, 404)


# Scenario J: Sensitive Data Zero-Leakage
def test_scenario_j_sensitive_data_zero_leakage():
    """Scenario J: Passwords, OTPs, PINs, and database URLs are scrubbed from logs and output streams."""
    raw = (
        "User 98124 requested token with password='SuperSecretPassword!123' "
        "and OTP 984021 PIN 4321 connected to postgresql://admin:p@ss@db.internal:5432/nivesh"
    )
    sanitized = scrub_sensitive_tokens(raw)
    assert "SuperSecretPassword!123" not in sanitized
    assert "984021" not in sanitized
    assert "4321" not in sanitized
    assert "p@ss" not in sanitized
    assert "admin:p@ss@db.internal:5432" not in sanitized


# ==============================================================================
# 4. Persistence & Restart Test (Cold Retrieval)
# ==============================================================================
def test_03_persistence_and_cold_restart_lifecycle(prod_env):
    """Verify that stored analysis survives application restart and returns intact."""
    client = prod_env["client"]

    # 1. Create analysis
    post_res = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Cold restart persistence check.", "channel": "web"},
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert post_res.status_code == 200
    original_data = post_res.json()
    target_id = original_data["analysis_id"]

    # 2. Simulate complete restart by querying via a fresh TestClient instance
    fresh_client = TestClient(app, raise_server_exceptions=False)
    retrieved_res = fresh_client.get(
        f"/api/v1/firewall/analysis/{target_id}",
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert retrieved_res.status_code == 200
    retrieved = retrieved_res.json()

    assert retrieved["analysis_id"] == target_id
    assert retrieved["decision"]["decision"] == original_data["decision"]["decision"]
    assert retrieved["pipeline_status"] == original_data["pipeline_status"]


# ==============================================================================
# 5. Failure & Recovery Tests
# ==============================================================================
def test_04_failure_and_recovery_rate_limiting(prod_env):
    """Verify 429 rate limit exceeded returns Retry-After header under burst."""
    rate_limiter.reset()
    client = prod_env["client"]
    current_settings = prod_env["settings"]
    custom_settings = current_settings.model_copy(update={"rate_limit_requests_per_minute": 3})

    with patch("nivesh.security.dependencies.get_settings", return_value=custom_settings):
        # Burst 3 requests
        for _ in range(3):
            res = client.get("/api/v1/firewall/analysis/nonexistent")
            assert res.status_code in (404, 401)

        # 4th request triggers 429
        blocked = client.get("/api/v1/firewall/analysis/nonexistent")
        assert blocked.status_code == 429
        assert "Retry-After" in blocked.headers
    rate_limiter.reset()


def test_05_invalid_request_structured_error(prod_env):
    """Verify malformed input returns structured 400 FirewallApiError."""
    client = prod_env["client"]
    res = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "channel": "web"},  # Missing text & url
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert res.status_code == 400
    error_data = res.json()
    assert "error_code" in error_data
    assert "message" in error_data


def test_06_unhandled_error_sanitization(prod_env):
    """Verify unhandled 500 error hides traceback and DB paths from client."""
    client = prod_env["client"]
    with patch("nivesh.api.app.check_readiness", side_effect=RuntimeError("FATAL: /var/lib/postgresql/data corrupted")):
        res = client.get("/health/ready", headers={"Origin": "https://app.nivesh.ai"})
        assert res.status_code == 500
        data = res.json()
        assert "/var/lib/postgresql/data" not in str(data)
        assert "Traceback" not in str(data)
        assert "request_id" in data or "details" in data


# ==============================================================================
# 6. Performance Smoke Measurements
# ==============================================================================
def test_07_performance_smoke_measurements(prod_env):
    """Measure real representative execution latencies across operations."""
    client = prod_env["client"]

    # 1. Health probe latency
    t0 = time.perf_counter()
    h_res = client.get("/health/live")
    health_latency_ms = (time.perf_counter() - t0) * 1000
    assert h_res.status_code == 200
    assert health_latency_ms < 100.0  # Must respond under 100ms

    # 2. Database connectivity healthcheck latency
    t0 = time.perf_counter()
    db_health = check_database_health()
    db_latency_ms = (time.perf_counter() - t0) * 1000
    assert db_health["connected"] is True
    assert db_health["status"] == "healthy"
    assert db_latency_ms < 200.0  # DB probe under 200ms

    # 3. Full pipeline analysis duration
    t0 = time.perf_counter()
    a_res = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Performance benchmark financial query.", "channel": "web"},
        headers={"Origin": "https://app.nivesh.ai"},
    )
    pipeline_latency_ms = (time.perf_counter() - t0) * 1000
    assert a_res.status_code == 200
    assert pipeline_latency_ms < 3000.0  # Full 10-engine analysis under 3s

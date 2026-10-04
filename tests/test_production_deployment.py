"""Phase 16.1 — Production Deployment Validation Test Suite.

Validates:
1. Production environment configuration & strict validation enforcement.
2. Root and internal liveness probes (/health, /health/live, /api/v1/health/liveness).
3. Readiness probe dependencies, degraded states (503), and zero credential leakage.
4. Reverse proxy header processing (X-Forwarded-For) and client IP extraction.
5. Security response headers (HSTS in production, CSP, X-Frame-Options, Cache-Control).
6. Safe logging, credential masking, and zero secret leakage.
7. Representative API smoke test under production settings.
"""

import pytest
from unittest.mock import patch
from starlette.requests import Request
from fastapi.testclient import TestClient

from nivesh.config.settings import Settings
from nivesh.api.app import app
from nivesh.security.dependencies import get_client_ip
from nivesh.observability.health import check_liveness, check_readiness


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ------------------------------------------------------------------------------
# 1. Production Settings Validation
# ------------------------------------------------------------------------------
def test_production_settings_validation_enforcement():
    """Verify strict production controls on debug, database, origins, and secrets."""
    # Debug forbidden in production
    with pytest.raises(ValueError, match="debug mode"):
        Settings(
            env="production",
            debug=True,
            database_url="postgresql://usr:pwd@dbhost:5432/nivesh_db",
            allowed_origins=["https://app.nivesh.ai"],
        ).validate_production_readiness()

    # SQLite dev database forbidden in production
    with pytest.raises(ValueError, match="SQLite"):
        Settings(
            env="production",
            debug=False,
            database_url="sqlite:///./nivesh_dev.db",
            allowed_origins=["https://app.nivesh.ai"],
        ).validate_production_readiness()

    # SQLite in-memory forbidden in production
    with pytest.raises(ValueError, match="SQLite"):
        Settings(
            env="production",
            debug=False,
            database_url="sqlite:///:memory:",
            allowed_origins=["https://app.nivesh.ai"],
        ).validate_production_readiness()

    # Wildcard origin forbidden in production
    with pytest.raises(ValueError, match="wildcard"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@dbhost:5432/nivesh_db",
            allowed_origins=["*"],
        ).validate_production_readiness()

    # Insecure secret key forbidden in production
    with pytest.raises(ValueError, match="placeholder or insecure"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@dbhost:5432/nivesh_db",
            allowed_origins=["https://app.nivesh.ai"],
            secret_key="change_this_to_something_secret",
        ).validate_production_readiness()

    # Valid production settings pass cleanly
    prod_settings = Settings(
        env="production",
        debug=False,
        database_url="postgresql://prod_user:StrongPassword123@prod-db.internal:5432/nivesh_production",
        allowed_origins=["https://app.nivesh.ai", "https://admin.nivesh.ai"],
        secret_key="a" * 64,
        forwarded_allow_ips="*",
        workers=4,
    )
    prod_settings.validate_production_readiness()
    assert prod_settings.is_production() is True
    assert prod_settings.forwarded_allow_ips == "*"
    assert prod_settings.workers == 4


# ------------------------------------------------------------------------------
# 2. Production Liveness Probes
# ------------------------------------------------------------------------------
def test_production_liveness_probes(client):
    """Verify /health (system health) and /health/live / /api/v1/health/liveness (process liveness)."""
    # Root /health endpoint
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] in ["healthy", "degraded"]
    assert data_health["service"] == "Nivesh Firewall Unified API"
    assert "database" in data_health
    assert "password" not in str(data_health).lower()

    # Dedicated liveness probes
    for path in ["/health/live", "/api/v1/health/liveness"]:
        response = client.get(path)
        assert response.status_code == 200, f"Path {path} returned {response.status_code}"
        data = response.json()
        assert data["status"] == "alive"
        assert "service" in data
        assert "version" in data
        assert "engine_version" in data
        assert "timestamp" in data
        # Ensure no internal connection details leak
        assert "password" not in str(data).lower()
        assert "secret" not in str(data).lower()


# ------------------------------------------------------------------------------
# 3. Production Readiness Probes (Healthy & Degraded)
# ------------------------------------------------------------------------------
def test_production_readiness_probe_healthy(client):
    """Verify /health/ready and /api/v1/health/readiness return 200 when dependencies pass."""
    for path in ["/health/ready", "/api/v1/health/readiness"]:
        response = client.get(path)
        assert response.status_code == 200, f"Path {path} returned {response.status_code}"
        data = response.json()
        assert data["status"] == "ready"
        assert "dependencies" in data
        assert data["dependencies"]["engines"]["count"] == 10
        assert data["dependencies"]["engines"]["status"] == "ready"
        assert data["dependencies"]["database"]["status"] == "connected"
        # Zero database credential leakage
        assert "postgresql://" not in str(data)
        assert "sqlite://" not in str(data)
        assert "password" not in str(data).lower()


def test_production_readiness_probe_db_failure(client):
    """Verify readiness reports 503 Service Unavailable when DB is disconnected in production."""
    with patch("nivesh.observability.health.check_database_health", return_value={"connected": False, "dialect": "postgresql", "error": "Connection refused"}):
        with patch.object(Settings, "is_production", return_value=True):
            is_ready, details = check_readiness()
            assert is_ready is False
            assert details["status"] == "not_ready"
            assert details["dependencies"]["database"]["status"] == "unavailable"
            assert any("database connectivity failed in production" in r.lower() for r in details.get("reasons", []))
            # Test actual endpoint behavior
            with patch("nivesh.api.app.check_readiness", return_value=(False, details)):
                response = client.get("/health/ready")
                assert response.status_code == 503
                assert response.json()["status"] == "not_ready"


# ------------------------------------------------------------------------------
# 4. Reverse Proxy Header Processing & Client IP Extraction
# ------------------------------------------------------------------------------
def test_reverse_proxy_header_client_ip():
    """Verify client IP extraction safely respects X-Forwarded-For from reverse proxies."""
    # Scenario A: Single proxy hop
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.195")],
        "client": ("127.0.0.1", 54321),
    }
    req = Request(scope)
    assert get_client_ip(req) == "203.0.113.195"

    # Scenario B: Multi-proxy chain (Client, Proxy1, Proxy2) -> client is leftmost IP
    scope_multi = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"198.51.100.42, 10.0.0.1, 127.0.0.1")],
        "client": ("10.0.0.1", 54321),
    }
    req_multi = Request(scope_multi)
    assert get_client_ip(req_multi) == "198.51.100.42"

    # Scenario C: Direct connection without reverse proxy
    scope_direct = {
        "type": "http",
        "headers": [],
        "client": ("192.168.1.100", 54321),
    }
    req_direct = Request(scope_direct)
    assert get_client_ip(req_direct) == "192.168.1.100"


# ------------------------------------------------------------------------------
# 5. Security Headers and HSTS in Production
# ------------------------------------------------------------------------------
def test_production_security_headers(client):
    """Verify security headers, HSTS, and cache controls are emitted."""
    # Test on public health route
    response = client.get("/health/live")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in response.headers.get("Referrer-Policy", "")

    # Test HSTS emission when HTTPS request arrives
    response_https = client.get("/health/live", headers={"X-Forwarded-Proto": "https"})
    # Under test client scheme might be http, but in production or with https scheme HSTS is added
    with patch.object(Settings, "is_production", return_value=True):
        resp = client.get("/health/live")
        assert "Strict-Transport-Security" in resp.headers
        assert "max-age=31536000" in resp.headers["Strict-Transport-Security"]

    # Sensitive intelligence route cache control
    resp_cache = client.get("/api/v1/firewall/analysis/nonexistent-id")
    assert "no-store" in resp_cache.headers.get("Cache-Control", "")
    assert "no-cache" in resp_cache.headers.get("Pragma", "")


# ------------------------------------------------------------------------------
# 6. Safe Logging, Credential Masking & Zero Secret Leakage
# ------------------------------------------------------------------------------
def test_safe_logging_and_credential_masking():
    """Verify settings.safe_dump() redacts all passwords, API keys, and private credentials."""
    s = Settings(
        env="production",
        debug=False,
        database_url="postgresql://super_admin:P@ssw0rd!123@prod-cluster.db:5432/nivesh_db",
        secret_key="super_secret_production_cryptographic_key_64_characters_minimum_entropy",
        admin_api_key="admin_secret_key_12345",
        service_api_key="service_secret_key_67890",
        nse_api_key="nse_key_abc",
        nse_api_secret="nse_secret_def",
        bse_api_key="bse_key_ghi",
        bse_api_secret="bse_secret_jkl",
        allowed_origins=["https://app.nivesh.ai"],
    )

    dumped = s.safe_dump()
    # Masked database password
    assert "P@ssw0rd!123" not in dumped["database_url"]
    assert "***:***@" in dumped["database_url"] or ":***@" in dumped["database_url"]

    # Redacted keys
    assert dumped["secret_key"] == "***REDACTED***"
    assert dumped["admin_api_key"] == "***REDACTED***"
    assert dumped["service_api_key"] == "***REDACTED***"
    assert dumped["nse_api_key"] == "***REDACTED***"
    assert dumped["nse_api_secret"] == "***REDACTED***"
    assert dumped["bse_api_key"] == "***REDACTED***"
    assert dumped["bse_api_secret"] == "***REDACTED***"

    # String representation does not leak plaintext secrets
    repr_str = repr(s)
    assert "P@ssw0rd!123" not in repr_str
    assert "super_secret_production_cryptographic_key" not in repr_str
    assert "admin_secret_key" not in repr_str


# ------------------------------------------------------------------------------
# 7. Representative API Smoke Test
# ------------------------------------------------------------------------------
def test_representative_api_smoke_test(client):
    """Confirm representative unified firewall analysis endpoint responds correctly."""
    payload = {
        "text": "SBI mutual fund investment guide for disciplined long-term compounding.",
        "channel": "generic_web",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"
    data = response.json()
    assert "analysis_id" in data
    assert "pipeline_status" in data
    assert data["pipeline_status"] in ["COMPLETED", "DEGRADED"]
    assert "decision" in data
    assert "decision" in data["decision"]
    assert data["decision"]["decision"] in ["ALLOW", "CAUTION", "WARN", "BLOCK"]
    assert "content" in data
    assert "identity" in data
    assert "threat" in data
    assert "fingerprint" in data
    # Check that correlation ID is returned
    assert "X-Request-ID" in response.headers
    # Zero secret leakage in API output
    assert "secret" not in str(data).lower()
    assert "password" not in str(data).lower()

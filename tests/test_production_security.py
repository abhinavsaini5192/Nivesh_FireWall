"""Phase 16.3 — Production Security & Secrets Test Suite.

Validates:
1. Runtime secrets & rejection of weak/placeholder keys.
2. CORS production configuration & origin boundary enforcement.
3. Transport security & HTTP security headers (HSTS, CSP, X-Frame-Options, Cache-Control).
4. Authentication & Authorization boundaries (401 on unauthenticated, 403 on insufficient role, token tampering/expiry).
5. Safe error handling (zero traceback, credential, or filepath leakage on 500 errors).
6. Reverse proxy forwarded-header trust boundary (spoofed X-Forwarded-For rejection).
7. Logging sanitization (scrubbing tokens, passwords, OTPs, DB URLs from log streams).
8. Rate limiting & abuse protection (429 Too Many Requests enforcement).
"""

import pytest
from unittest.mock import patch, MagicMock
from starlette.requests import Request
from fastapi.testclient import TestClient

from nivesh.config.settings import Settings
from nivesh.api.app import app
from nivesh.security import (
    UserRole,
    AuthenticatedUser,
    create_access_token,
    decode_access_token,
    InvalidTokenError,
    TokenExpiredError,
    rate_limiter,
)
from nivesh.security.dependencies import get_client_ip
from nivesh.observability.logging import scrub_sensitive_tokens


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_rate_limit_state():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


# ------------------------------------------------------------------------------
# 1. Runtime Secrets & Insecure Key Rejection
# ------------------------------------------------------------------------------
def test_production_secrets_guardrails():
    """Verify production rejects weak/placeholder secret keys and properly redacts values."""
    # Placeholder key rejected
    with pytest.raises(ValueError, match="placeholder or insecure"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@host:5432/db",
            allowed_origins=["https://app.nivesh.ai"],
            secret_key="change_this_placeholder_key_now",
        ).validate_production_readiness()

    # Short key (< 16 chars) rejected
    with pytest.raises(ValueError, match="placeholder or insecure"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@host:5432/db",
            allowed_origins=["https://app.nivesh.ai"],
            secret_key="shortkey",
        ).validate_production_readiness()

    # Valid secret key accepted and redacted in dumps
    valid_key = "prod_random_cryptographic_secret_key_entropy_1234567890"
    s = Settings(
        env="production",
        debug=False,
        database_url="postgresql://usr:SuperPassword!@host:5432/db",
        allowed_origins=["https://app.nivesh.ai"],
        secret_key=valid_key,
        admin_api_key="admin_secret_key_abc",
        service_api_key="service_secret_key_def",
        nse_api_key="nse_key_1",
        nse_api_secret="nse_sec_1",
        bse_api_key="bse_key_1",
        bse_api_secret="bse_sec_1",
    )
    s.validate_production_readiness()
    dumped = s.safe_dump()
    assert dumped["secret_key"] == "***REDACTED***"
    assert dumped["admin_api_key"] == "***REDACTED***"
    assert dumped["service_api_key"] == "***REDACTED***"
    assert dumped["nse_api_key"] == "***REDACTED***"
    assert dumped["nse_api_secret"] == "***REDACTED***"
    assert dumped["bse_api_key"] == "***REDACTED***"
    assert dumped["bse_api_secret"] == "***REDACTED***"
    assert "SuperPassword!" not in dumped["database_url"]


# ------------------------------------------------------------------------------
# 2. CORS Production Configuration & Origin Boundary
# ------------------------------------------------------------------------------
def test_production_cors_boundaries():
    """Verify production CORS rejects wildcard origin and invalid URL schemes."""
    # Wildcard rejected
    with pytest.raises(ValueError, match="wildcard"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@host:5432/db",
            allowed_origins=["*"],
        ).validate_production_readiness()

    # Empty origins rejected
    with pytest.raises(ValueError, match="explicit allowed origin"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@host:5432/db",
            allowed_origins=[],
        ).validate_production_readiness()

    # Invalid scheme rejected
    with pytest.raises(ValueError, match="Invalid origin"):
        Settings(
            env="production",
            debug=False,
            database_url="postgresql://usr:pwd@host:5432/db",
            allowed_origins=["ftp://malicious.com"],
        ).validate_production_readiness()

    # Valid origins in production do NOT automatically include localhost
    prod_s = Settings(
        env="production",
        debug=False,
        database_url="postgresql://usr:pwd@host:5432/db",
        allowed_origins=["https://app.nivesh.ai", "https://admin.nivesh.ai"],
        allowed_extension_ids=["abcdefghijklmnopqrstuvwxyz123456"],
    )
    cors_list = prod_s.get_cors_origins()
    assert "https://app.nivesh.ai" in cors_list
    assert "https://admin.nivesh.ai" in cors_list
    assert "chrome-extension://abcdefghijklmnopqrstuvwxyz123456" in cors_list
    assert "http://localhost:5173" not in cors_list
    assert "http://127.0.0.1:5173" not in cors_list


# ------------------------------------------------------------------------------
# 3. Transport Security & Security Response Headers
# ------------------------------------------------------------------------------
def test_security_response_headers(client):
    """Verify security headers, CSP, and HSTS across responses."""
    resp = client.get("/health/live")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "strict-origin" in resp.headers["Referrer-Policy"]
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]

    # HSTS when forwarded over HTTPS
    resp_https = client.get("/health/live", headers={"X-Forwarded-Proto": "https"})
    assert "Strict-Transport-Security" in resp_https.headers
    assert "max-age=31536000" in resp_https.headers["Strict-Transport-Security"]

    # Cache control on sensitive routes
    resp_sensitive = client.get("/api/v1/firewall/analysis/nonexistent")
    assert "no-store" in resp_sensitive.headers.get("Cache-Control", "")
    assert "no-cache" in resp_sensitive.headers.get("Pragma", "")


# ------------------------------------------------------------------------------
# 4. Authentication & Authorization Boundaries
# ------------------------------------------------------------------------------
def test_auth_and_rbac_boundaries(client):
    """Verify protected endpoints enforce 401 for anonymous and 403 for unauthorized roles."""
    # 1. Anonymous access to admin endpoint returns 401
    resp_unauth = client.get("/api/v1/traces/recent")
    assert resp_unauth.status_code == 401
    assert "Bearer" in resp_unauth.headers.get("WWW-Authenticate", "")

    # 2. Regular user access to admin endpoint returns 403 Forbidden
    user_token = create_access_token(user_id="normal_user", roles=[UserRole.USER])
    resp_forbidden = client.get(
        "/api/v1/traces/recent",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp_forbidden.status_code == 403
    assert "Forbidden" in resp_forbidden.text

    # 3. Admin token grants access
    admin_token = create_access_token(user_id="admin_user", roles=[UserRole.ADMIN])
    resp_admin = client.get(
        "/api/v1/traces/recent",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200

    # 4. Tampered token returns 401
    tampered = f"{user_token[:-6]}XXXXXX"
    resp_tampered = client.get(
        "/api/v1/traces/recent",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert resp_tampered.status_code == 401

    # 5. Expired token returns 401
    expired_token = create_access_token(user_id="user_exp", expires_in_seconds=-10)
    resp_expired = client.get(
        "/api/v1/traces/recent",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp_expired.status_code == 401


# ------------------------------------------------------------------------------
# 5. Safe Error Handling: Zero Traceback or Secret Leakage
# ------------------------------------------------------------------------------
def test_safe_error_handling_on_internal_exception(client):
    """Verify unhandled 500 errors return sanitized responses without stack traces or secrets."""
    # Force an unhandled exception inside a test endpoint route
    with patch("nivesh.api.app.check_readiness", side_effect=RuntimeError("SecretDatabasePassword: 12345 in /app/db.py")):
        resp = client.get("/health/ready")
        assert resp.status_code == 500
        data = resp.json()
        # Verify no traceback, filepaths, or secret leaks
        assert "SecretDatabasePassword" not in str(data)
        assert "/app/db.py" not in str(data)
        assert "Traceback" not in str(data)
        assert "detail" in data or "message" in data


# ------------------------------------------------------------------------------
# 6. Reverse Proxy Forwarded-Header Trust Boundary
# ------------------------------------------------------------------------------
def test_reverse_proxy_trust_boundary_spoofing():
    """Verify spoofed X-Forwarded-For headers are rejected when peer is not in trusted set."""
    # Scenario A: Specific trusted proxy IP (e.g. 10.0.0.1)
    test_settings = Settings(
        env="production",
        database_url="postgresql://usr:pwd@host/db",
        allowed_origins=["https://app.nivesh.ai"],
        forwarded_allow_ips="10.0.0.1, 127.0.0.1",
    )

    with patch("nivesh.security.dependencies.get_settings", return_value=test_settings):
        # 1. Untrusted connecting client (attacker directly connecting from 198.51.100.99)
        scope_untrusted = {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"8.8.8.8, 1.1.1.1")],
            "client": ("198.51.100.99", 54321),
        }
        req_untrusted = Request(scope_untrusted)
        # MUST ignore spoofed X-Forwarded-For and return connecting client IP
        assert get_client_ip(req_untrusted) == "198.51.100.99"

        # 2. Trusted connecting client (e.g. internal reverse proxy 10.0.0.1)
        scope_trusted = {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"203.0.113.195, 10.0.0.1")],
            "client": ("10.0.0.1", 54321),
        }
        req_trusted = Request(scope_trusted)
        # Trusted proxy: accepts X-Forwarded-For and extracts original client IP
        assert get_client_ip(req_trusted) == "203.0.113.195"


# ------------------------------------------------------------------------------
# 7. Logging & Observability Sanitization
# ------------------------------------------------------------------------------
def test_logging_sanitizer_removes_secrets():
    """Verify scrub_sensitive_tokens redacts passwords, tokens, API keys, OTPs, and DB URLs."""
    raw_message = (
        "User authenticated with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.signature "
        "and api_key='secret_key_abcdef123456' for database postgresql://user:p@ssword!@db:5432/nivesh "
        "with OTP 849201 and PIN 1234."
    )
    scrubbed = scrub_sensitive_tokens(raw_message)

    assert "eyJhbGciOiJIUzI1Ni" not in scrubbed
    assert "[REDACTED_TOKEN]" in scrubbed
    assert "secret_key_abcdef123456" not in scrubbed
    assert "p@ssword!" not in scrubbed
    assert "849201" not in scrubbed
    assert "1234" not in scrubbed


# ------------------------------------------------------------------------------
# 8. Rate Limiting & Abuse Protection
# ------------------------------------------------------------------------------
def test_rate_limiting_enforcement(client):
    """Verify rate limiter blocks burst traffic exceeding configured requests per minute."""
    from nivesh.config.settings import get_settings
    current_settings = get_settings()
    custom_settings = current_settings.model_copy(update={"rate_limit_requests_per_minute": 5})

    with patch("nivesh.security.dependencies.get_settings", return_value=custom_settings):
        # 5 requests succeed
        for _ in range(5):
            res = client.get("/api/v1/firewall/analysis/nonexistent")
            assert res.status_code == 404

        # 6th request triggers 429
        res_blocked = client.get("/api/v1/firewall/analysis/nonexistent")
        assert res_blocked.status_code == 429
        assert "Rate limit exceeded" in res_blocked.text
        assert "Retry-After" in res_blocked.headers


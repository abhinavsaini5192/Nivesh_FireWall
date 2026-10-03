"""Security and Access Control Test Suite — Phase 14.3.

Covers:
1. Authentication: Bearer JWT tokens, API keys, expiration, tampering, malformed inputs.
2. Authorization & IDOR: Server-side RBAC, cross-user isolation, cross-org isolation, admin enforcement.
3. API Security: Security response headers, request correlation IDs, HTTP methods, rate limiting.
4. Secret & Privacy Protection: Redaction, zero leaked secrets, audit trail tamper evidence.
"""

import time
import pytest
from fastapi.testclient import TestClient

from nivesh.api.app import app, analysis_repo, audit_repo
from nivesh.config import get_settings
from nivesh.security import (
    UserRole,
    AuthenticatedUser,
    create_access_token,
    decode_access_token,
    InvalidTokenError,
    TokenExpiredError,
    MalformedTokenError,
    rate_limiter,
)
from nivesh.storage.models import AnalysisModel
from nivesh.storage.database import get_db_session
from nivesh.storage.errors import ForbiddenFieldError


@pytest.fixture(autouse=True)
def reset_rate_limit():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


# ==============================================================================
# 1. Authentication Tests
# ==============================================================================

def test_01_token_generation_and_decoding():
    """Verify access token creation and decoding with claims."""
    token = create_access_token(
        user_id="user_123",
        organization_id="org_alpha",
        roles=[UserRole.USER, UserRole.ANALYST],
        session_id="sess_abc",
        expires_in_seconds=300,
    )
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    user = decode_access_token(token)
    assert user.user_id == "user_123"
    assert user.organization_id == "org_alpha"
    assert user.session_id == "sess_abc"
    assert user.has_role(UserRole.USER)
    assert user.has_role(UserRole.ANALYST)
    assert not user.is_admin()


def test_02_tampered_token_rejected():
    """Verify modified token signature is rejected with InvalidTokenError."""
    token = create_access_token(user_id="legit_user")
    parts = token.split(".")
    # Modify payload
    tampered = f"{parts[0]}.eyJuZXdfdXNlciI6ImhhY2tlciJ9.{parts[2]}"
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_03_expired_token_rejected():
    """Verify expired token raises TokenExpiredError."""
    token = create_access_token(user_id="user_exp", expires_in_seconds=-10)
    with pytest.raises(TokenExpiredError):
        decode_access_token(token)


def test_04_malformed_token_rejected():
    """Verify random string or malformed token raises MalformedTokenError."""
    with pytest.raises(MalformedTokenError):
        decode_access_token("not-a-valid-token")

    with pytest.raises(MalformedTokenError):
        decode_access_token("part1.part2")


def test_05_api_key_authentication(monkeypatch):
    """Verify static administrative and service API keys are accepted."""
    client = TestClient(app)
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_api_key", "secret-admin-key-999")
    monkeypatch.setattr(settings, "service_api_key", "secret-service-key-888")

    # Admin API key on admin endpoint
    resp = client.get("/api/v1/admin/audit-logs", headers={"X-API-Key": "secret-admin-key-999"})
    assert resp.status_code == 200

    # Authorization header with ApiKey scheme
    resp2 = client.get("/api/v1/admin/audit-logs", headers={"Authorization": "ApiKey secret-admin-key-999"})
    assert resp2.status_code == 200

    # Invalid API key rejected with 401
    resp3 = client.get("/api/v1/admin/audit-logs", headers={"X-API-Key": "wrong-key"})
    assert resp3.status_code == 401
    assert "ApiKey" in resp3.headers.get("WWW-Authenticate", "")


# ==============================================================================
# 2. Authorization & IDOR Protection Tests
# ==============================================================================

def test_06_analysis_ownership_and_idor_protection():
    """Verify User A can access own analysis, but User B gets 404 (IDOR prevented)."""
    client = TestClient(app)
    token_user_a = create_access_token(user_id="user_alice", organization_id="org_a")
    token_user_b = create_access_token(user_id="user_bob", organization_id="org_b")

    # 1. User Alice submits an analysis
    payload = {
        "input_type": "text",
        "text": "Transfer ₹10,000 to private trading advisory pool immediately.",
        "channel": "telegram",
    }
    submit_resp = client.post(
        "/api/v1/firewall/analyze",
        json=payload,
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert submit_resp.status_code == 200
    analysis_id = submit_resp.json()["analysis_id"]

    # Verify ownership was persisted in the database
    record = analysis_repo.get_analysis_record(analysis_id)
    assert record is not None
    assert record.user_id == "user_alice"
    assert record.organization_id == "org_a"

    # 2. Alice retrieves own analysis -> 200 OK
    alice_resp = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert alice_resp.status_code == 200
    assert alice_resp.json()["analysis_id"] == analysis_id

    # 3. Bob attempts to access Alice's analysis (IDOR attack) -> 404 (existence concealed)
    bob_resp = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert bob_resp.status_code == 404
    assert bob_resp.json()["error_code"] == "ANALYSIS_NOT_FOUND"

    # 4. Unauthenticated request to private analysis -> 401
    anon_resp = client.get(f"/api/v1/firewall/analysis/{analysis_id}")
    assert anon_resp.status_code == 401
    assert "Bearer" in anon_resp.headers.get("WWW-Authenticate", "")


def test_07_organization_scoped_access():
    """Verify members of the same organization can view org-scoped analyses."""
    client = TestClient(app)
    token_alice = create_access_token(user_id="alice", organization_id="acme_corp")
    token_colleague = create_access_token(user_id="carol", organization_id="acme_corp")
    token_outsider = create_access_token(user_id="dave", organization_id="other_corp")

    # Alice creates analysis under acme_corp
    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Company financial statement review."},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    analysis_id = resp.json()["analysis_id"]

    # Carol (same org) retrieves analysis -> 200 OK
    carol_resp = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_colleague}"},
    )
    assert carol_resp.status_code == 200

    # Dave (different org) attempts retrieval -> 404
    dave_resp = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_outsider}"},
    )
    assert dave_resp.status_code == 404


def test_08_admin_can_access_any_analysis():
    """Verify administrator has universal visibility across tenant analyses."""
    client = TestClient(app)
    token_user = create_access_token(user_id="user_private", organization_id="isolated_org")
    token_admin = create_access_token(user_id="super_admin", roles=[UserRole.ADMIN])

    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Private client transaction check."},
        headers={"Authorization": f"Bearer {token_user}"},
    )
    analysis_id = resp.json()["analysis_id"]

    # Admin retrieves -> 200 OK
    admin_resp = client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert admin_resp.status_code == 200
    assert admin_resp.json()["analysis_id"] == analysis_id


def test_09_admin_endpoint_requires_admin_privilege():
    """Verify admin endpoints strictly reject non-admins with 403 and unauthenticated with 401."""
    client = TestClient(app)
    token_user = create_access_token(user_id="regular_user", roles=[UserRole.USER])
    token_admin = create_access_token(user_id="admin_user", roles=[UserRole.ADMIN])

    # 1. Unauthenticated -> 401
    anon_resp = client.get("/api/v1/admin/audit-logs")
    assert anon_resp.status_code == 401

    # 2. Regular user -> 403 Forbidden
    user_resp = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert user_resp.status_code == 403

    # 3. Admin user -> 200 OK
    admin_resp = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert admin_resp.status_code == 200


def test_10_fingerprint_creation_restricted_to_admin():
    """Verify manual fingerprint registration requires administrator role."""
    client = TestClient(app)
    token_user = create_access_token(user_id="analyst_test", roles=[UserRole.ANALYST])
    token_admin = create_access_token(user_id="admin_test", roles=[UserRole.ADMIN])

    fp_payload = {
        "fingerprint_id": "SFP-TEST-001",
        "exact_signature": "TEST-SIG-001",
        "semantic_signature": "SEM-TEST-001",
        "created_at": "2026-10-03T00:00:00Z",
        "updated_at": "2026-10-03T00:00:00Z",
        "first_seen": "2026-10-03T00:00:00Z",
        "last_seen": "2026-10-03T00:00:00Z",
        "description": "Test fingerprint created by admin",
    }

    # Non-admin rejected with 403
    user_resp = client.post(
        "/api/v1/fingerprints/create",
        json=fp_payload,
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert user_resp.status_code == 403

    # Admin accepted with 200
    admin_resp = client.post(
        "/api/v1/fingerprints/create",
        json=fp_payload,
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert admin_resp.status_code == 200
    assert admin_resp.json()["fingerprint_id"] == "SFP-TEST-001"


def test_11_delete_analysis_admin_only():
    """Verify deleting an analysis record requires administrator privilege."""
    client = TestClient(app)
    token_user = create_access_token(user_id="user_owner")
    token_admin = create_access_token(user_id="admin_owner", roles=[UserRole.ADMIN])

    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Record to delete."},
        headers={"Authorization": f"Bearer {token_user}"},
    )
    analysis_id = resp.json()["analysis_id"]

    # User attempts deletion -> 403
    del_user = client.delete(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert del_user.status_code == 403

    # Admin deletes -> 200
    del_admin = client.delete(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert del_admin.status_code == 200
    assert del_admin.json()["status"] == "deleted"

    # Verify deleted
    assert analysis_repo.get_analysis_record(analysis_id) is None


# ==============================================================================
# 3. API Security & Response Headers Tests
# ==============================================================================

def test_12_security_headers_enforced():
    """Verify security headers are attached across responses."""
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert headers.get("Permissions-Policy") == "geolocation=(), camera=(), microphone=()"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")


def test_13_cache_control_on_sensitive_endpoints():
    """Verify cache control headers prevent caching on sensitive firewall endpoints."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Checking cache headers."},
    )
    assert resp.status_code == 200
    assert "no-store" in resp.headers.get("Cache-Control", "")
    assert "no-cache" in resp.headers.get("Cache-Control", "")


def test_14_request_id_correlation():
    """Verify X-Request-ID is generated or preserved across requests."""
    client = TestClient(app)

    # 1. Generated if not supplied
    resp1 = client.get("/health")
    req_id = resp1.headers.get("X-Request-ID")
    assert req_id is not None
    assert req_id.startswith("REQ-")

    # 2. Preserved if supplied
    resp2 = client.get("/health", headers={"X-Request-ID": "CUSTOM-REQ-12345"})
    assert resp2.headers.get("X-Request-ID") == "CUSTOM-REQ-12345"


def test_15_strict_http_methods():
    """Verify unsupported HTTP methods are rejected with 405 Method Not Allowed."""
    client = TestClient(app)
    resp = client.put("/api/v1/firewall/analyze", json={"text": "hello"})
    assert resp.status_code == 405


def test_16_rate_limiting_enforcement(monkeypatch):
    """Verify rapid request bursts trigger 429 Too Many Requests with Retry-After header."""
    client = TestClient(app)
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_requests_per_minute", 5)

    # First 5 requests succeed
    for _ in range(5):
        r = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": "Normal traffic"})
        assert r.status_code == 200

    # 6th request triggers rate limit
    r6 = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": "Excess traffic"})
    assert r6.status_code == 429
    assert "Retry-After" in r6.headers
    assert r6.headers.get("X-RateLimit-Remaining") == "0"


# ==============================================================================
# 4. Secret & Privacy Protection Tests
# ==============================================================================

def test_17_secrets_not_printed_in_safe_dump():
    """Verify API keys and application secrets are never returned in safe_dump or repr."""
    settings = get_settings()
    dump = settings.safe_dump()
    assert dump.get("secret_key") in (None, "***REDACTED***")
    assert dump.get("admin_api_key") in (None, "***REDACTED***")
    assert dump.get("service_api_key") in (None, "***REDACTED***")

    repr_str = repr(settings)
    assert "secret_key='***REDACTED***'" in repr_str or "secret_key=None" in repr_str


def test_18_forbidden_credentials_rejected_in_audit_records():
    """Verify attempt to pass raw passwords or credentials into audit logs raises ForbiddenFieldError."""
    with pytest.raises(ForbiddenFieldError):
        audit_repo.record_audit(
            event_type="TEST_EVENT",
            actor="test_actor",
            details={"password": "raw_secret_password"},
        )

    with pytest.raises(ForbiddenFieldError):
        audit_repo.record_audit(
            event_type="TEST_EVENT",
            actor="test_actor",
            details={"card_number": "4111222233334444"},
        )


def test_19_audit_trail_records_security_events():
    """Verify security events (auth failures, IDOR attempts) are logged in the audit trail."""
    client = TestClient(app)
    token_alice = create_access_token(user_id="alice_sec", organization_id="org_sec")
    token_bob = create_access_token(user_id="bob_sec", organization_id="org_other")
    token_admin = create_access_token(user_id="admin_sec", roles=[UserRole.ADMIN])

    # 1. Create analysis by Alice
    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Security test payload."},
        headers={"Authorization": f"Bearer {token_alice}"},
    )
    analysis_id = resp.json()["analysis_id"]

    # 2. Bob attempts IDOR access
    client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Authorization": f"Bearer {token_bob}"},
    )

    # 3. Admin queries audit logs and verifies IDOR event was recorded
    audit_resp = client.get(
        "/api/v1/admin/audit-logs?event_type=IDOR_ACCESS_ATTEMPT",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert audit_resp.status_code == 200
    records = audit_resp.json()
    assert len(records) >= 1
    assert any(r["actor"] == "bob_sec" and r["target_entity"] == analysis_id for r in records)


def test_20_token_issue_endpoint():
    """Verify POST /api/v1/auth/token endpoint issues valid signed tokens."""
    client = TestClient(app)
    issue_resp = client.post(
        "/api/v1/auth/token",
        json={"user_id": "test_jwt_user", "organization_id": "test_org", "roles": ["user", "analyst"]},
    )
    assert issue_resp.status_code == 200
    data = issue_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Decode issued token and verify claims
    decoded = decode_access_token(data["access_token"])
    assert decoded.user_id == "test_jwt_user"
    assert decoded.organization_id == "test_org"
    assert decoded.has_role(UserRole.ANALYST)

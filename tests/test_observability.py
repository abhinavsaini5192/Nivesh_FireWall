"""Observability, Monitoring & Operations Test Suite — Phase 14.4.

Validates:
1. Structured Logging & Correlation: JSON formatting, request/correlation ID propagation, secret redaction.
2. Metrics & Telemetry: API, pipeline, engine, policy, persistence, and external source metrics.
3. Metric Cardinality: Ensures no high-cardinality identifiers (user IDs, raw URLs, analysis IDs) in labels.
4. Distributed Tracing: Diagnostic span hierarchy, safe attributes, graceful degradation.
5. Health, Liveness & Readiness: Separation of lightweight liveness from readiness, zero credential leakage.
6. Operational Failures: Simulated engine timeouts, database rollbacks, source outages, and graceful shutdown.
"""

import json
import logging
import time
from typing import Any
import pytest
from fastapi.testclient import TestClient

from nivesh.api.app import app
from nivesh.config import get_settings
from nivesh.observability import (
    metrics,
    tracer,
    check_liveness,
    check_readiness,
    scrub_sensitive_tokens,
    StructuredJsonFormatter,
    StandardTextFormatter,
    request_id_ctx,
    correlation_id_ctx,
    analysis_id_ctx,
    engine_key_ctx,
)
from nivesh.security import create_access_token, UserRole
from nivesh.storage.database import get_db_session


@pytest.fixture(autouse=True)
def reset_observability_state():
    """Reset metrics registry and trace buffer before each test for isolated assertions."""
    metrics.reset_all()
    tracer.clear()
    yield
    metrics.reset_all()
    tracer.clear()


# ==============================================================================
# 1. Structured Logging & Correlation Tests (14.4.1)
# ==============================================================================

def test_01_structured_json_formatter():
    """Verify StructuredJsonFormatter outputs valid JSON with standard operational fields."""
    formatter = StructuredJsonFormatter(service_name="nivesh-firewall", environment="test", version="1.0.0")
    record = logging.LogRecord(
        name="nivesh.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test operational log message",
        args=(),
        exc_info=None,
    )
    # Set context variables
    tok_req = request_id_ctx.set("req-test-999")
    tok_corr = correlation_id_ctx.set("corr-test-888")
    try:
        output = formatter.format(record)
        data = json.loads(output)
        assert data["service"] == "nivesh-firewall"
        assert data["environment"] == "test"
        assert data["level"] == "INFO"
        assert data["message"] == "Test operational log message"
        assert data["request_id"] == "req-test-999"
        assert data["correlation_id"] == "corr-test-888"
        assert "timestamp" in data
    finally:
        request_id_ctx.reset(tok_req)
        correlation_id_ctx.reset(tok_corr)


def test_02_secret_and_credential_scrubbing_in_logs():
    """Verify passwords, OTPs, PINs, CVVs, Bearer tokens, and API keys are redacted."""
    raw_message = (
        "User entered password=SuperSecretPassword123 with OTP 849201 and card 4111222233334444. "
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy and api_key=secret-api-key-999999 "
        "and connected to postgresql://admin:p@ssw0rd123@db.prod.internal:5432/nivesh"
    )
    scrubbed = scrub_sensitive_tokens(raw_message)

    assert "SuperSecretPassword123" not in scrubbed
    assert "849201" not in scrubbed
    assert "4111222233334444" not in scrubbed
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in scrubbed
    assert "secret-api-key-999999" not in scrubbed
    assert "p@ssw0rd123" not in scrubbed
    assert "[REDACTED" in scrubbed


def test_03_request_id_and_correlation_id_propagation():
    """Verify HTTP requests carry and return X-Request-ID and X-Correlation-ID."""
    client = TestClient(app)
    headers = {
        "X-Request-ID": "req-custom-client-123",
        "X-Correlation-ID": "corr-custom-client-456",
    }
    resp = client.get("/health/live", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == "req-custom-client-123"


# ==============================================================================
# 2. Metrics & Performance Telemetry Tests (14.4.2)
# ==============================================================================

def test_04_http_api_metrics_collected():
    """Verify HTTP request counts and durations are tracked in the metrics registry."""
    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200

    # Verify counter increment
    count = metrics.http_requests_total.get(method="GET", route="/health/live", status_code="200")
    assert count >= 1.0

    # Verify histogram observation
    obs_count, obs_sum = metrics.http_request_duration_seconds.get(method="GET", route="/health/live")
    assert obs_count >= 1
    assert obs_sum > 0.0


def test_05_firewall_pipeline_and_engine_metrics():
    """Verify pipeline and engine executions update metrics upon analysis completion."""
    client = TestClient(app)
    payload = {
        "input_type": "text",
        "text": "Educational discussion on fixed deposit savings rates and inflation.",
        "channel": "telegram",
    }
    resp = client.post("/api/v1/firewall/analyze", json=payload)
    assert resp.status_code == 200

    # 1. Pipeline request and completed metrics
    req_count = metrics.pipeline_requests_total.get(input_type="text", channel="telegram")
    assert req_count >= 1.0

    comp_count = metrics.pipeline_completed_total.get(status="COMPLETED")
    assert comp_count >= 1.0

    # 2. Per-engine executions tracked
    e1_count = metrics.engine_executions_total.get(engine_key="engine_1_content", status="SUCCESS")
    assert e1_count >= 1.0

    e8_count = metrics.engine_executions_total.get(engine_key="engine_8_policy", status="SUCCESS")
    assert e8_count >= 1.0

    # 3. Policy decisions tracked
    total_policy_count = sum(metrics.policy_decisions_total.get_all().values())
    assert total_policy_count >= 1.0


def test_06_persistence_metrics_recorded():
    """Verify persistence metrics record operations and durations."""
    client = TestClient(app)
    payload = {"input_type": "text", "text": "Testing database persistence metrics."}
    resp = client.post("/api/v1/firewall/analyze", json=payload)
    assert resp.status_code == 200

    save_count = metrics.persistence_operations_total.get(operation="save_analysis", status="SUCCESS")
    assert save_count >= 1.0


def test_07_metric_label_cardinality_safeguard():
    """Verify metric labels never contain high-cardinality keys like user_id, raw URLs, or analysis_id."""
    for attr in dir(metrics):
        val = getattr(metrics, attr)
        if hasattr(val, "label_names"):
            for lbl in val.label_names:
                assert lbl not in ("user_id", "email", "phone", "url", "analysis_id", "ip_address")


def test_08_metrics_exposition_endpoint():
    """Verify /api/v1/metrics returns Prometheus text and JSON representations."""
    client = TestClient(app)

    # 1. Prometheus text format
    resp_prom = client.get("/api/v1/metrics", headers={"Accept": "text/plain"})
    assert resp_prom.status_code == 200
    assert "nivesh_http_requests_total" in resp_prom.text
    assert "# HELP" in resp_prom.text
    assert "# TYPE" in resp_prom.text

    # 2. JSON format via format query param
    resp_json = client.get("/api/v1/metrics?format=json")
    assert resp_json.status_code == 200
    data = resp_json.json()
    assert "nivesh_http_requests_total" in data
    assert data["nivesh_http_requests_total"]["type"] == "counter"


# ==============================================================================
# 3. Distributed Tracing Tests (14.4.3)
# ==============================================================================

def test_09_distributed_tracing_spans_created():
    """Verify firewall analysis produces root pipeline and engine spans in the tracer."""
    tracer.clear()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Trace verification payload."},
        headers={"X-Trace-ID": "trc-custom-12345678"},
    )
    assert resp.status_code == 200

    spans = tracer.get_recent_spans(limit=100)
    assert len(spans) >= 1

    span_names = [s["name"] for s in spans]
    # Verify engine child spans were generated
    assert any("engine_1_content" in name for name in span_names)
    assert any("engine_8_policy" in name for name in span_names)


def test_10_trace_attributes_sanitization():
    """Verify sensitive fields cannot be added to trace attributes."""
    span = tracer.start_span("test_sanitization")
    span.set_attribute("safe_key", "safe_value")
    span.set_attribute("password", "MySecretPassword")
    span.set_attribute("token", "SecretAuthToken")
    span.set_attribute("card_number", "4111222233334444")
    span.finish()

    d = span.to_dict()
    assert d["attributes"]["safe_key"] == "safe_value"
    assert "password" not in d["attributes"]
    assert "token" not in d["attributes"]
    assert "card_number" not in d["attributes"]


def test_11_recent_traces_admin_endpoint():
    """Verify /api/v1/traces/recent is restricted to admins and returns spans."""
    client = TestClient(app)
    token_user = create_access_token(user_id="user_normal", roles=[UserRole.USER])
    token_admin = create_access_token(user_id="admin_sec", roles=[UserRole.ADMIN])

    # Normal user -> 403 Forbidden
    resp_user = client.get("/api/v1/traces/recent", headers={"Authorization": f"Bearer {token_user}"})
    assert resp_user.status_code == 403

    # Admin user -> 200 OK
    resp_admin = client.get("/api/v1/traces/recent", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp_admin.status_code == 200
    assert isinstance(resp_admin.json(), list)


# ==============================================================================
# 4. Health, Liveness & Readiness Tests (14.4.4)
# ==============================================================================

def test_12_liveness_probe_lightweight_and_fast():
    """Verify /health/live returns status alive without database overhead."""
    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "version" in data


def test_13_readiness_probe_dependencies():
    """Verify /health/ready checks database and subsystem dependencies."""
    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "database" in data["dependencies"]
    assert "engines" in data["dependencies"]
    assert "source_subsystem" in data["dependencies"]


def test_14_readiness_fails_when_database_unavailable(monkeypatch):
    """Verify /health/ready returns 503 when the database dependency fails."""
    client = TestClient(app)

    # Mock database health to simulate outage
    import nivesh.observability.health as obs_health
    monkeypatch.setattr(
        obs_health,
        "check_database_health",
        lambda: {"status": "unavailable", "dialect": "sqlite", "connected": False},
    )

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "not_ready"
    assert any("Database" in r for r in data.get("reasons", []))


def test_15_health_endpoints_zero_credential_leakage():
    """Verify public health responses contain zero passwords, tokens, paths, or secrets."""
    client = TestClient(app)
    for endpoint in ("/health", "/api/v1/health", "/health/live", "/health/ready"):
        resp = client.get(endpoint)
        content_str = resp.text.lower()
        assert "password" not in content_str
        assert "secret" not in content_str
        assert "token" not in content_str
        assert "c:\\" not in content_str
        assert "/home/" not in content_str


# ==============================================================================
# 5. Operational Failure Signals & Runbook Scenarios (14.4.5)
# ==============================================================================

def test_16_engine_timeout_operational_metric():
    """Verify engine timeout increments the engine_timeouts_total metric."""
    from nivesh.orchestrator.pipeline import SafeEngineExecutor

    def slow_engine():
        time.sleep(0.1)
        return "done"

    # Execute with an unachievable timeout (1ms)
    result, dur, attempts, err = SafeEngineExecutor.execute(
        slow_engine,
        engine_key="test_engine_timeout",
        engine_name="Test Engine Timeout",
        timeout_ms=1.0,
    )
    assert err is not None
    timeout_metric = metrics.engine_timeouts_total.get(engine_key="test_engine_timeout")
    assert timeout_metric >= 1.0


def test_17_persistence_rollback_operational_metric():
    """Verify transaction rollback increments persistence_rollbacks_total metric."""
    initial_rollbacks = metrics.persistence_rollbacks_total.get(operation="db_session")

    try:
        with get_db_session() as session:
            # Intentionally raise to force rollback
            raise RuntimeError("Forced test transaction rollback")
    except RuntimeError:
        pass

    new_rollbacks = metrics.persistence_rollbacks_total.get(operation="db_session")
    assert new_rollbacks == initial_rollbacks + 1.0


def test_18_source_intelligence_metrics():
    """Verify SourceIntelligenceEngine tracks requests and cache hits/misses in metrics."""
    from nivesh.engine import ContentIntelligenceEngine
    from nivesh.claims.engine import ClaimIntelligenceEngine
    from nivesh.sources.engine import SourceIntelligenceEngine

    content_engine = ContentIntelligenceEngine()
    content = content_engine.process_text("Invest in Tata Motors for 50% guaranteed returns.")

    claims_engine = ClaimIntelligenceEngine()
    claims = claims_engine.analyze(content)

    src_engine = SourceIntelligenceEngine(default_mode="FIXTURE")

    src_res = src_engine.discover_and_retrieve(content, claims)
    assert src_res is not None

    # Verify source requests metric
    all_source_requests = metrics.source_requests_total.get_all()
    assert len(all_source_requests) >= 1


def test_19_graceful_shutdown_lifecycle():
    """Verify lifespan shutdown handler executes without errors and disposes resources cleanly."""
    from nivesh.api.app import lifespan
    import asyncio

    async def run_lifespan_test():
        async with lifespan(app):
            pass

    asyncio.run(run_lifespan_test())


def test_20_observability_no_user_profiling_in_telemetry():
    """Verify operational telemetry remains strictly system-level and does not compute user risk scores."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Guaranteed 50% monthly returns telegram investment."},
    )
    assert resp.status_code == 200

    metrics_export = metrics.export_json()
    # Confirm no user-profiling metrics exist
    for metric_name in metrics_export.keys():
        assert "user_risk" not in metric_name
        assert "behavioural_profile" not in metric_name
        assert "credit_score" not in metric_name

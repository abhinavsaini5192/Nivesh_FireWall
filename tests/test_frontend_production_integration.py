"""Phase 16.4 — Frontend + API Production Integration & Smoke Test.

Validates end-to-end production contract compatibility between frontend and backend:
1. Production CORS preflight (OPTIONS) and request execution from https://app.nivesh.ai
2. Full firewall analysis request contract execution and schema verification
3. Health check probe contract compatibility
4. Retrieval of analysis record by ID
5. Error responses conform to FirewallApiError structure
6. Security headers and credentials behavior
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from nivesh.api.app import app
from nivesh.config.settings import Settings


@pytest.fixture(scope="module")
def prod_client():
    test_settings = Settings(
        env="production",
        database_url="postgresql://user:pass@host:5432/nivesh_db",
        allowed_origins=["https://app.nivesh.ai"],
        secret_key="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    with patch("nivesh.api.app.get_settings", return_value=test_settings), \
         patch("nivesh.config.get_settings", return_value=test_settings), \
         patch("nivesh.config.settings.get_settings", return_value=test_settings), \
         patch("nivesh.security.middleware.get_settings", return_value=test_settings):
        yield TestClient(app, raise_server_exceptions=False)


def test_01_cors_preflight_for_production_frontend(prod_client):
    """Verify OPTIONS preflight request from production frontend origin succeeds."""
    headers = {
        "Origin": "https://app.nivesh.ai",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,accept",
    }
    response = prod_client.options("/api/v1/firewall/analyze", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://app.nivesh.ai"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_02_health_probe_from_production_frontend(prod_client):
    """Verify GET /health probe succeeds from production frontend origin."""
    response = prod_client.get("/health", headers={"Origin": "https://app.nivesh.ai"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://app.nivesh.ai"
    data = response.json()
    assert data["status"] in ("healthy", "ready", "degraded")


def test_03_representative_firewall_analysis_end_to_end(prod_client):
    """Verify POST /api/v1/firewall/analyze executes and returns valid frontend contract."""
    payload = {
        "input_type": "text",
        "text": "SEBI advisory warning regarding unauthorized algorithmic trading schemes offering guaranteed returns.",
        "channel": "web",
    }
    headers = {
        "Origin": "https://app.nivesh.ai",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = prod_client.post("/api/v1/firewall/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://app.nivesh.ai"

    data = response.json()
    assert "analysis_id" in data
    assert "decision" in data
    assert data["decision"]["decision"] in ("ALLOW", "WARN", "PAUSE", "BLOCK")
    assert "pipeline_status" in data
    assert "duration_ms" in data

    # Verify decision structure matches frontend expectations
    decision = data["decision"]
    assert "primary_reason" in decision
    assert "explanation" in decision
    assert "user_message" in decision["explanation"]
    assert "technical_message" in decision["explanation"]


def test_04_analysis_retrieval_by_id(prod_client):
    """Verify GET /api/v1/firewall/analysis/{id} contract compatibility."""
    # 1. Create analysis
    payload = {
        "input_type": "text",
        "text": "RBI guidance on sovereign gold bonds tranche schedule.",
        "channel": "web",
    }
    create_res = prod_client.post(
        "/api/v1/firewall/analyze",
        json=payload,
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert create_res.status_code == 200
    analysis_id = create_res.json()["analysis_id"]

    # 2. Retrieve analysis by ID
    get_res = prod_client.get(
        f"/api/v1/firewall/analysis/{analysis_id}",
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert get_res.status_code == 200
    assert get_res.headers.get("access-control-allow-origin") == "https://app.nivesh.ai"
    record = get_res.json()
    assert record["analysis_id"] == analysis_id


def test_05_error_response_matches_firewall_api_error_schema(prod_client):
    """Verify validation error produces machine-readable FirewallApiError schema."""
    # Invalid empty payload
    response = prod_client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "channel": "web"},
        headers={"Origin": "https://app.nivesh.ai"},
    )
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") == "https://app.nivesh.ai"
    data = response.json()
    assert "error_code" in data
    assert "message" in data
    assert "details" in data

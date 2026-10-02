"""Unit tests for Engine 9 FastAPI Endpoints."""

from fastapi.testclient import TestClient
from nivesh.api.app import app, identity_engine


client = TestClient(app)


def test_api_health_includes_engine_9():
    """Verify health endpoint lists Engine 9."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert any("Engine 9" in e for e in data["engines"])


def test_api_verify_with_text():
    """Verify POST /api/v1/identity/verify with text payload."""
    payload = {
        "text": "SEBI registered advisor Rahul Sharma offers guaranteed returns. Join Telegram: https://t.me/rahulinvest"
    }
    resp = client.post("/api/v1/identity/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis_id" in data
    assert data["identity_status"] in ("NOT_ESTABLISHED", "ESTABLISHED", "IDENTITY_MISMATCH")
    assert len(data["entities"]) >= 1

    # Verify retrieval via GET
    analysis_id = data["analysis_id"]
    get_resp = client.get(f"/api/v1/identity/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["analysis_id"] == analysis_id


def test_api_get_entity():
    """Verify GET /api/v1/identity/entities/{entity_id}."""
    # First run verify to populate in-memory store
    payload = {"text": "ABC Securities Pvt Ltd is an official broker."}
    resp = client.post("/api/v1/identity/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entities"]) >= 1
    entity_id = data["entities"][0]["entity_id"]

    # Retrieve the entity
    get_resp = client.get(f"/api/v1/identity/entities/{entity_id}")
    assert get_resp.status_code == 200
    ent_data = get_resp.json()
    assert ent_data["entity_id"] == entity_id


def test_api_404_for_unknown_ids():
    """Verify 404 responses for non-existent analysis and entity IDs."""
    resp1 = client.get("/api/v1/identity/IDA-999999")
    assert resp1.status_code == 404

    resp2 = client.get("/api/v1/identity/entities/ENT-999999")
    assert resp2.status_code == 404

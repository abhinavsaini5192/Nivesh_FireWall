"""API tests for Engine 7 FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app, fingerprint_engine
from nivesh.engine import ContentIntelligenceEngine


@pytest.fixture(autouse=True)
def reset_engine():
    fingerprint_engine.reset()
    yield
    fingerprint_engine.reset()


def test_health_check_includes_engine_7():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "Engine 7: Scam Fingerprint & Collective Threat Intelligence Engine" in data["engines"]


def test_api_match_and_create_endpoints():
    client = TestClient(app)
    content_engine = ContentIntelligenceEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    normalized = content_engine.process_text(raw_text)

    # 1. Match endpoint (with auto-cascading)
    resp = client.post("/api/v1/fingerprints/match", json={"content": normalized.model_dump()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_new_pattern"] is True
    assert data["fingerprint"]["fingerprint_id"] == "SFP-001"
    assert data["fingerprint"]["observation_count"] == 1

    # 2. Get endpoint
    get_resp = client.get("/api/v1/fingerprints/SFP-001")
    assert get_resp.status_code == 200
    fp_data = get_resp.json()
    assert fp_data["fingerprint_id"] == "SFP-001"

    # 3. Search endpoint
    search_resp = client.get("/api/v1/fingerprints/search?query=SFP-001")
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) == 1
    assert results[0]["fingerprint_id"] == "SFP-001"

    # 4. Dispute endpoint
    dispute_resp = client.post(
        "/api/v1/fingerprints/SFP-001/dispute",
        json={"reason": "Testing dispute mechanism", "actor": "analyst_1"},
    )
    assert dispute_resp.status_code == 200
    disputed = dispute_resp.json()
    assert disputed["status"] == "DISPUTED"
    assert disputed["dispute_count"] == 1


def test_api_get_nonexistent_fingerprint_404():
    client = TestClient(app)
    resp = client.get("/api/v1/fingerprints/SFP-999")
    assert resp.status_code == 404

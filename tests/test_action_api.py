"""Unit tests for Action Intelligence API endpoints (Engine 3)."""

import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine

client = TestClient(app)
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()


def test_actions_analyze_endpoint_with_claims():
    raw_text = "Join our Telegram channel https://t.me/rahulinvest and pay ₹5,000."
    norm = content_engine.process_text(raw_text)
    claims = claims_engine.analyze(norm)

    payload = {
        "content": norm.model_dump(),
        "claims": claims.model_dump(),
    }

    response = client.post("/api/v1/actions/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["content_id"] == norm.content_id
    assert len(data["actions"]) >= 2
    action_types = [a["action_type"] for a in data["actions"]]
    assert "JOIN_CHANNEL" in action_types
    assert "PAYMENT" in action_types


def test_actions_analyze_endpoint_direct_content():
    raw_text = "Download our app and complete KYC."
    norm = content_engine.process_text(raw_text)

    # Post direct NormalizedContent without pre-computing claims
    response = client.post("/api/v1/actions/analyze", json=norm.model_dump())
    assert response.status_code == 200

    data = response.json()
    assert data["content_id"] == norm.content_id
    assert len(data["actions"]) >= 2


def test_actions_analyze_invalid_payload():
    response = client.post("/api/v1/actions/analyze", json={"invalid": "payload"})
    assert response.status_code in {400, 422}


def test_health_check_shows_all_three_engines():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "engines" in data
    assert any("Engine 1" in e for e in data["engines"])
    assert any("Engine 2" in e for e in data["engines"])
    assert any("Engine 3" in e for e in data["engines"])

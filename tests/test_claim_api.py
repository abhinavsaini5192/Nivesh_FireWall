"""Unit tests for Claim Intelligence API endpoints."""

import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app
from nivesh.engine import ContentIntelligenceEngine

client = TestClient(app)
content_engine = ContentIntelligenceEngine()


def test_claims_analyze_endpoint_success():
    # 1. Obtain NormalizedContent via Engine 1
    norm = content_engine.process_text("SEBI registered advisor Rahul Sharma. Guaranteed 40% returns.")

    # 2. Post to /api/v1/claims/analyze
    response = client.post("/api/v1/claims/analyze", json=norm.model_dump())
    assert response.status_code == 200

    data = response.json()
    assert data["content_id"] == norm.content_id
    assert len(data["claims"]) >= 2
    predicates = [c["predicate"] for c in data["claims"]]
    assert "REGISTERED_WITH" in predicates
    assert "GUARANTEED_RETURN" in predicates


def test_claims_analyze_endpoint_invalid_payload():
    response = client.post("/api/v1/claims/analyze", json={"invalid": "payload"})
    assert response.status_code == 422  # Pydantic validation error


def test_health_check_shows_both_engines():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "engines" in data
    assert any("Engine 2" in e for e in data["engines"])

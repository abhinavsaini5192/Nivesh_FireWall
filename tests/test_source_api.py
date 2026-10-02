"""API endpoint tests for Engine 4 (Source Intelligence Engine)."""

import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_includes_engine_4(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "Engine 4: Source Intelligence Engine" in data["engines"]


def test_api_sources_analyze_direct_content_payload(client):
    content_resp = client.post(
        "/api/v1/content/analyze",
        json={"text": "Rahul Sharma is a SEBI registered advisor."}
    )
    assert content_resp.status_code == 200
    normalized_data = content_resp.json()

    sources_resp = client.post(
        "/api/v1/sources/analyze",
        json=normalized_data
    )
    assert sources_resp.status_code == 200
    source_data = sources_resp.json()

    assert source_data["content_id"] == normalized_data["content_id"]
    assert len(source_data["claim_sources"]) >= 1
    assert source_data["analysis_metadata"]["claims_processed"] >= 1


def test_api_sources_analyze_envelope_payload(client):
    content_resp = client.post(
        "/api/v1/content/analyze",
        json={"text": "ABC announced a 1:1 bonus."}
    )
    normalized_data = content_resp.json()

    claims_resp = client.post(
        "/api/v1/claims/analyze",
        json=normalized_data
    )
    claims_data = claims_resp.json()

    envelope = {
        "content": normalized_data,
        "claims": claims_data,
        "actions": None
    }

    sources_resp = client.post(
        "/api/v1/sources/analyze",
        json=envelope
    )
    assert sources_resp.status_code == 200
    source_data = sources_resp.json()
    assert source_data["content_id"] == normalized_data["content_id"]
    assert len(source_data["claim_sources"]) >= 1

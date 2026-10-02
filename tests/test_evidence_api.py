"""API endpoint tests for Engine 5 (Evidence Verification Engine)."""

import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_includes_engine_5(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "Engine 5: Evidence Verification Engine" in data["engines"]


def test_api_evidence_verify_direct_content_payload(client):
    content_resp = client.post(
        "/api/v1/content/analyze",
        json={"text": "ABC announced a 1:1 bonus."}
    )
    assert content_resp.status_code == 200
    normalized_data = content_resp.json()

    evidence_resp = client.post(
        "/api/v1/evidence/verify",
        json=normalized_data
    )
    assert evidence_resp.status_code == 200
    evidence_data = evidence_resp.json()

    assert evidence_data["content_id"] == normalized_data["content_id"]
    assert len(evidence_data["verifications"]) >= 1
    assert evidence_data["analysis_metadata"]["total_claims"] >= 1


def test_api_evidence_verify_envelope_payload(client):
    content_resp = client.post(
        "/api/v1/content/analyze",
        json={"text": "Guaranteed 40% returns."}
    )
    normalized_data = content_resp.json()

    claims_resp = client.post(
        "/api/v1/claims/analyze",
        json=normalized_data
    )
    claims_data = claims_resp.json()

    sources_resp = client.post(
        "/api/v1/sources/analyze",
        json={"content": normalized_data, "claims": claims_data}
    )
    sources_data = sources_resp.json()

    envelope = {
        "content": normalized_data,
        "claims": claims_data,
        "sources": sources_data
    }

    evidence_resp = client.post(
        "/api/v1/evidence/verify",
        json=envelope
    )
    assert evidence_resp.status_code == 200
    evidence_data = evidence_resp.json()

    assert evidence_data["content_id"] == normalized_data["content_id"]
    assert len(evidence_data["verifications"]) == 1
    v = evidence_data["verifications"][0]
    assert v["status"] == "INSUFFICIENT_EVIDENCE"
    assert len(v["regulatory_findings"]) >= 1
    assert v["regulatory_findings"][0]["type"] == "REGULATORY_CONFLICT"

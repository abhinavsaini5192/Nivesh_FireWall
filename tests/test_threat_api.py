"""API endpoint tests for Engine 6 (Threat & Attack-Path Intelligence Engine)."""

import pytest
from fastapi.testclient import TestClient
from nivesh.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_includes_engine_6(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "Engine 6: Threat & Attack-Path Intelligence Engine" in data["engines"]
    assert len(data["engines"]) >= 6


def test_api_threat_analyze_direct_content_payload(client):
    # Test auto-cascading from raw content through all 6 engines
    content_resp = client.post(
        "/api/v1/content/analyze",
        json={"text": "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join Telegram: https://t.me/rahulinvest. Download our app and pay ₹5,000."}
    )
    assert content_resp.status_code == 200
    normalized_data = content_resp.json()

    threat_resp = client.post(
        "/api/v1/threat/analyze",
        json=normalized_data
    )
    assert threat_resp.status_code == 200
    threat_data = threat_resp.json()

    assert threat_data["content_id"] == normalized_data["content_id"]
    assert len(threat_data["threat_signals"]) >= 3
    assert len(threat_data["attack_path"]["nodes"]) >= 3
    assert len(threat_data["transitions"]) >= 2
    assert len(threat_data["threat_families"]) >= 1
    assert "fingerprint_preparation" in threat_data
    assert "explanation" in threat_data
    assert threat_data["provenance"]["engine_name"] == "Threat & Attack-Path Intelligence Engine"


def test_api_threat_analyze_envelope_payload(client):
    text = "Guaranteed 40% returns. Pay ₹5,000 activation fee now."
    content_resp = client.post("/api/v1/content/analyze", json={"text": text})
    normalized_data = content_resp.json()

    claims_resp = client.post("/api/v1/claims/analyze", json=normalized_data)
    claims_data = claims_resp.json()

    actions_resp = client.post(
        "/api/v1/actions/analyze",
        json={"content": normalized_data, "claims": claims_data}
    )
    actions_data = actions_resp.json()

    sources_resp = client.post(
        "/api/v1/sources/analyze",
        json={"content": normalized_data, "claims": claims_data, "actions": actions_data}
    )
    sources_data = sources_resp.json()

    evidence_resp = client.post(
        "/api/v1/evidence/verify",
        json={"content": normalized_data, "claims": claims_data, "sources": sources_data}
    )
    evidence_data = evidence_resp.json()

    envelope = {
        "content": normalized_data,
        "claims": claims_data,
        "actions": actions_data,
        "sources": sources_data,
        "evidence": evidence_data,
    }

    threat_resp = client.post(
        "/api/v1/threat/analyze",
        json=envelope
    )
    assert threat_resp.status_code == 200
    threat_data = threat_resp.json()

    assert threat_data["content_id"] == normalized_data["content_id"]
    assert len(threat_data["threat_signals"]) >= 2
    assert len(threat_data["high_impact_actions"]) >= 1
    assert threat_data["high_impact_actions"][0]["impact_category"] == "FINANCIAL"


def test_api_threat_analyze_invalid_payload_error(client):
    threat_resp = client.post(
        "/api/v1/threat/analyze",
        json={"invalid_field": 12345}
    )
    assert threat_resp.status_code == 400
    assert "detail" in threat_resp.json()

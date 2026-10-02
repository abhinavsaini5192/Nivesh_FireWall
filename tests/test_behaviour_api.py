"""Tests for Engine 10 Behavioural Signal Intelligence FastAPI endpoints."""

from fastapi.testclient import TestClient
from nivesh.api.app import app, behaviour_engine
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine


def test_api_behaviour_analyze_with_text():
    """Verify POST /api/v1/behaviour/analyze accepting text."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/behaviour/analyze",
        json={"text": "Act now! Limited time offer to join our program and pay ₹5,000."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert data["analysis_id"].startswith("BHA-")
    assert "signals" in data
    assert "findings" in data
    assert "session_summary" in data
    assert "policy_hints" in data
    assert data["policy_hints"]["pressure_present"] is True


def test_api_behaviour_analyze_with_content():
    """Verify POST /api/v1/behaviour/analyze with pre-processed NormalizedContent."""
    client = TestClient(app)
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()

    content = ce.process_text("Learn about our program. Join our Telegram: https://t.me/edu and pay ₹5,000.")
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)

    payload = {
        "content": content.model_dump(),
        "claims": claims.model_dump(),
        "actions": actions.model_dump(),
    }
    response = client.post("/api/v1/behaviour/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"].startswith("BHA-")
    assert len(data["signals"]) >= 1


def test_api_behaviour_get_by_id():
    """Verify GET /api/v1/behaviour/{analysis_id} retrieves prior analysis."""
    client = TestClient(app)
    # 1. Analyze
    post_resp = client.post(
        "/api/v1/behaviour/analyze",
        json={"text": "Only 2 minutes left to claim this offer!"},
    )
    assert post_resp.status_code == 200
    analysis_id = post_resp.json()["analysis_id"]

    # 2. Retrieve
    get_resp = client.get(f"/api/v1/behaviour/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["analysis_id"] == analysis_id

    # 3. Not found
    not_found_resp = client.get("/api/v1/behaviour/BHA-NONEXISTENT")
    assert not_found_resp.status_code == 404


def test_api_behaviour_record_event():
    """Verify POST /api/v1/behaviour/events successfully appends event to session."""
    client = TestClient(app)
    event_payload = {
        "session_id": "SESS-API-001",
        "event": {
            "event_id": "EVT-01",
            "timestamp": "2026-10-02T10:00:00Z",
            "event_type": "CONTENT_VIEW",
            "channel": "web",
            "sequence_index": 0,
            "metadata": {"action": "view_page"},
        },
    }
    response = client.post("/api/v1/behaviour/events", json=event_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["session_id"] == "SESS-API-001"
    assert data["event_count"] >= 1

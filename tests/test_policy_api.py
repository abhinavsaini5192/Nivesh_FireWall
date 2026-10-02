"""API endpoint tests for Engine 8: Policy & Intervention Engine."""

import pytest
from fastapi.testclient import TestClient

from nivesh.engine import ContentIntelligenceEngine
from nivesh.api.app import app, policy_engine


@pytest.fixture(autouse=True)
def reset_policy():
    policy_engine.reset()
    yield
    policy_engine.reset()


def test_health_check_includes_engine_8():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "Engine 8: Policy & Intervention Engine" in data["engines"]


def test_api_list_policy_rules():
    client = TestClient(app)
    response = client.get("/api/v1/policy/rules")
    assert response.status_code == 200
    rules = response.json()
    assert isinstance(rules, list)
    assert len(rules) >= 10
    rule_ids = [r["rule_id"] for r in rules]
    assert "RULE-PAUSE-01" in rule_ids
    assert "RULE-ALLOW-01" in rule_ids


def test_api_policy_decide_endpoint():
    client = TestClient(app)
    ce = ContentIntelligenceEngine()
    c = ce.process_text("Learn what mutual funds are and how diversification protects your capital over the long term.")

    response = client.post("/api/v1/policy/decide", json={"content": c.model_dump()})
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in ("ALLOW", "INFORM")
    assert data["policy_version"] == "8.0.0"
    assert "decision_id" in data
    assert "user_message" in data

    # Retrieve decision via GET
    dec_id = data["decision_id"]
    get_resp = client.get(f"/api/v1/policy/{dec_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["decision_id"] == dec_id


def test_api_policy_explain_endpoint():
    client = TestClient(app)
    ce = ContentIntelligenceEngine()
    text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c = ce.process_text(text)

    # 1. Decide
    dec_resp = client.post("/api/v1/policy/decide", json={"content": c.model_dump()})
    assert dec_resp.status_code == 200
    dec_id = dec_resp.json()["decision_id"]

    # 2. Explain via decision_id
    exp_resp = client.post("/api/v1/policy/explain", json={"decision_id": dec_id})
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert exp_data["decision_id"] == dec_id
    assert exp_data["decision"] == "PAUSE"
    assert "user_message" in exp_data
    assert "technical_message" in exp_data

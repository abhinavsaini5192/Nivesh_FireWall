"""Unit tests for Action Intelligence Engine on the primary benchmark fixture (Section 26)."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis


PRIMARY_FIXTURE_TEXT = (
    "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
    "Join our Telegram VIP group: https://t.me/rahulinvest. "
    "Download our app and pay ₹5,000. Contact rahul@example.com."
)


@pytest.fixture
def content_engine():
    return ContentIntelligenceEngine()


@pytest.fixture
def claims_engine():
    return ClaimIntelligenceEngine()


@pytest.fixture
def actions_engine():
    return ActionIntelligenceEngine()


def test_primary_benchmark_actions_extraction(content_engine, claims_engine, actions_engine):
    """Verifies that the primary benchmark content extracts exactly the 4 intended atomic actions."""
    # 1. Process via Engine 1
    normalized: NormalizedContent = content_engine.process_text(PRIMARY_FIXTURE_TEXT)

    # 2. Process via Engine 2
    claim_analysis: ClaimAnalysis = claims_engine.analyze(normalized)

    # 3. Process via Engine 3
    action_analysis: ActionAnalysis = actions_engine.analyze(normalized, claim_analysis)

    # 4. Check Content ID linkage
    assert action_analysis.content_id == normalized.content_id
    assert len(action_analysis.actions) == 4

    # 5. Check Action 1: Join Telegram VIP group
    act1 = action_analysis.actions[0]
    assert act1.action_id == "ACTION-001"
    assert act1.action_type == "JOIN_CHANNEL"
    assert act1.category == "CHANNEL_MIGRATION"
    assert act1.target.type == "channel"
    assert "telegram" in (act1.target.value or "").lower() or "t.me" in (act1.target.value or "").lower()
    assert act1.sequence.index == 1

    # 6. Check Action 2: Download our app
    act2 = action_analysis.actions[1]
    assert act2.action_id == "ACTION-002"
    assert act2.action_type == "DOWNLOAD"
    assert act2.category == "SOFTWARE_INSTALLATION"
    assert act2.target.type == "application"
    assert act2.sequence.index == 2

    # 7. Check Action 3: Pay ₹5,000
    act3 = action_analysis.actions[2]
    assert act3.action_id == "ACTION-003"
    assert act3.action_type == "PAYMENT"
    assert act3.category == "FINANCIAL_TRANSACTION"
    assert act3.parameters.get("amount") == 5000.0
    assert act3.parameters.get("currency") == "INR"
    assert act3.sequence.index == 3

    # 8. Check Action 4: Contact rahul@example.com
    act4 = action_analysis.actions[3]
    assert act4.action_id == "ACTION-004"
    assert act4.action_type == "CONTACT"
    assert act4.category == "COMMUNICATION"
    assert act4.target.type == "person"
    assert act4.target.value == "rahul@example.com"
    assert act4.sequence.index == 4

    # 9. Verify sequential ordering
    assert [a.sequence.index for a in action_analysis.actions] == [1, 2, 3, 4]

    # 10. STRICT CONSTRAINT: NO scam / risk / block / threat decision!
    dumped = action_analysis.model_dump()
    dumped_str = str(dumped).lower()
    assert "is_scam" not in dumped_str
    assert "risk_score" not in dumped_str
    assert "threat_level" not in dumped_str
    assert "block_decision" not in dumped_str

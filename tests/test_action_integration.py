"""Full pipeline integration tests: Engine 1 -> Engine 2 -> Engine 3."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis


@pytest.fixture
def content_engine():
    return ContentIntelligenceEngine()


@pytest.fixture
def claims_engine():
    return ClaimIntelligenceEngine()


@pytest.fixture
def actions_engine():
    return ActionIntelligenceEngine()


def test_full_three_engine_pipeline(content_engine, claims_engine, actions_engine):
    """Verifies end-to-end data flow:
    Raw Content -> Engine 1 (NormalizedContent) -> Engine 2 (ClaimAnalysis) -> Engine 3 (ActionAnalysis).
    """
    raw_text = (
        "SEBI registered advisor Rahul Sharma guarantees 40% returns. "
        "Join our Telegram channel: https://t.me/rahulinvest to get daily stock calls. "
        "Download our mobile app and pay ₹10,000 subscription fee."
    )

    # 1. Engine 1
    normalized: NormalizedContent = content_engine.process_text(raw_text)
    assert normalized.status == "success"
    assert normalized.content_id != ""

    # 2. Engine 2
    claims: ClaimAnalysis = claims_engine.analyze(normalized)
    assert claims.content_id == normalized.content_id
    assert len(claims.claims) >= 2

    # 3. Engine 3
    actions: ActionAnalysis = actions_engine.analyze(normalized, claims)
    assert actions.content_id == normalized.content_id
    assert len(actions.actions) >= 3

    # Verification of Separation:
    # Claims are distinct from Actions
    claim_types = [c.claim_type for c in claims.claims]
    assert "REGULATORY" in claim_types or "FINANCIAL" in claim_types

    action_types = [a.action_type for a in actions.actions]
    assert "JOIN_CHANNEL" in action_types
    assert "DOWNLOAD" in action_types
    assert "PAYMENT" in action_types

    # Parameter extraction from Engine 1 data
    payment_act = [a for a in actions.actions if a.action_type == "PAYMENT"][0]
    assert payment_act.parameters.get("amount") == 10000.0
    assert payment_act.parameters.get("currency") == "INR"

    # Spans are within valid bounds
    full_len = len(normalized.normalized.text)
    for act in actions.actions:
        assert 0 <= act.source_span.start <= full_len
        assert 0 <= act.source_span.end <= full_len


def test_empty_content_graceful_handling(actions_engine):
    """Empty or whitespace-only content produces clean empty ActionAnalysis without errors."""
    from nivesh.schemas.normalized import SourceInfo, RawContent, NormalizedText, Provenance

    empty_norm = NormalizedContent(
        content_id="empty-1",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=""),
        normalized=NormalizedText(text="", language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-02T00:00:00Z", input_type="text")
    )

    res = actions_engine.analyze(empty_norm)
    assert res.content_id == "empty-1"
    assert len(res.actions) == 0
    assert res.analysis_metadata.total_actions == 0

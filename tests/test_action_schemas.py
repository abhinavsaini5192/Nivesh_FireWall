"""Unit tests for Action Intelligence Engine schemas (Engine 3)."""

import pytest
from nivesh.schemas.actions import (
    CanonicalAction,
    ActionAnalysis,
    ActionText,
    ActionActor,
    ActionTarget,
    ActionModality,
    ActionSequence,
    ActionProvenance,
    ActionRelation,
    ActionAnalysisMetadata,
)
from nivesh.schemas.claims import SourceSpan


def test_canonical_action_schema_validation():
    action = CanonicalAction(
        action_id="ACTION-001",
        source_content_id="cnt-123",
        text=ActionText(original="Join our Telegram group", normalized="Join Telegram."),
        action_type="JOIN_CHANNEL",
        category="CHANNEL_MIGRATION",
        actor=ActionActor(type="user"),
        target=ActionTarget(type="channel", value="Telegram"),
        sequence=ActionSequence(index=1),
        modality=ActionModality(type="instruction", strength="direct"),
        source_span=SourceSpan(start=0, end=23),
        source_spans=[SourceSpan(start=0, end=23)],
        confidence=0.95,
        canonical_fingerprint="ACTION:JOIN_CHANNEL|TARGET:TELEGRAM|CATEGORY:CHANNEL_MIGRATION"
    )

    dumped = action.model_dump()
    assert dumped["action_id"] == "ACTION-001"
    assert dumped["action_type"] == "JOIN_CHANNEL"
    assert dumped["category"] == "CHANNEL_MIGRATION"
    assert dumped["target"]["type"] == "channel"
    assert dumped["target"]["value"] == "Telegram"
    assert dumped["sequence"]["index"] == 1


def test_strict_boundary_no_threat_or_scam_in_schema():
    analysis = ActionAnalysis(
        content_id="cnt-1",
        actions=[
            CanonicalAction(
                action_id="ACTION-001",
                source_content_id="cnt-1",
                text=ActionText(original="Pay ₹5,000", normalized="Pay INR 5000."),
                action_type="PAYMENT",
                category="FINANCIAL_TRANSACTION",
                parameters={"amount": 5000.0, "currency": "INR"},
                source_span=SourceSpan(start=0, end=10)
            )
        ],
        analysis_metadata=ActionAnalysisMetadata(processing_time_ms=1.5, total_actions=1)
    )

    dumped_str = str(analysis.model_dump()).lower()
    # Engine 3 MUST NOT decide scam or risk
    assert "is_scam" not in dumped_str
    assert "risk_score" not in dumped_str
    assert "threat_level" not in dumped_str
    assert "block_decision" not in dumped_str

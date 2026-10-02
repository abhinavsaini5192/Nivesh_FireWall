"""Unit tests for Attack Path and Stage Transitions in Engine 6."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim, ClaimText
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction, ActionTarget, ActionText
from nivesh.schemas.evidence import EvidenceAnalysis, EvidenceAnalysisMetadata
from nivesh.threat.attack_path_builder import AttackPathBuilder


def test_build_multi_stage_attack_path():
    content_engine = ContentIntelligenceEngine()
    content = content_engine.process_text("SEBI registered advisor. Join Telegram. Download app. Pay ₹5,000.")

    claims = ClaimAnalysis(
        content_id=content.content_id,
        claims=[
            CanonicalClaim(
                claim_id="C-1",
                source_content_id=content.content_id,
                text=ClaimText(original="SEBI registered advisor.", normalized="SEBI registered advisor."),
                claim_type="REGULATORY",
                subject="advisor",
                predicate="REGISTERED_WITH",
                object="SEBI"
            )
        ]
    )
    actions = ActionAnalysis(
        content_id=content.content_id,
        actions=[
            CanonicalAction(
                action_id="A-1",
                source_content_id=content.content_id,
                text=ActionText(original="Join Telegram", normalized="Join Telegram"),
                action_type="JOIN_CHANNEL",
                category="CHANNEL_MIGRATION",
                target=ActionTarget(type="channel", value="Telegram")
            ),
            CanonicalAction(
                action_id="A-2",
                source_content_id=content.content_id,
                text=ActionText(original="Download app", normalized="Download app"),
                action_type="DOWNLOAD",
                category="SOFTWARE_INSTALLATION",
                target=ActionTarget(type="application", value="app")
            ),
            CanonicalAction(
                action_id="A-3",
                source_content_id=content.content_id,
                text=ActionText(original="Pay ₹5,000", normalized="Pay ₹5,000"),
                action_type="PAYMENT",
                category="FINANCIAL_TRANSACTION",
                target=ActionTarget(type="account", value="Bank")
            )
        ]
    )
    evidence = EvidenceAnalysis(
        content_id=content.content_id,
        verifications=[],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    path, transitions = AttackPathBuilder.build_path(content, claims, actions, evidence)

    stages = [n.stage for n in path.nodes if n.stage != "DISCOVERY"]
    assert "TRUST_BUILDING" in stages
    assert "CHANNEL_MIGRATION" in stages
    assert "SOFTWARE_INSTALLATION" in stages
    assert "FINANCIAL_REQUEST" in stages

    assert len(transitions) == 3
    t_pairs = [(t.from_stage, t.to_stage) for t in transitions]
    assert ("TRUST_BUILDING", "CHANNEL_MIGRATION") in t_pairs
    assert ("CHANNEL_MIGRATION", "SOFTWARE_INSTALLATION") in t_pairs
    assert ("SOFTWARE_INSTALLATION", "FINANCIAL_REQUEST") in t_pairs

    assert path.entry_stage == "TRUST_BUILDING"
    assert path.terminal_stage == "FINANCIAL_REQUEST"

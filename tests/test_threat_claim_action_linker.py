"""Unit tests for Claim-to-Action Linker in Engine 6."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim, ClaimText
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction, ActionTarget, ActionText
from nivesh.threat.claim_action_linker import ClaimActionLinker


def test_claim_action_direct_rationale_linking():
    content_engine = ContentIntelligenceEngine()
    content = content_engine.process_text("SEBI approved this platform, so join our Telegram group.")

    claims = ClaimAnalysis(
        content_id=content.content_id,
        claims=[
            CanonicalClaim(
                claim_id="CLAIM-001",
                source_content_id=content.content_id,
                text=ClaimText(original="SEBI approved this platform.", normalized="SEBI approved this platform."),
                claim_type="REGULATORY",
                subject="Platform",
                predicate="APPROVED_BY",
                object="SEBI"
            )
        ]
    )
    actions = ActionAnalysis(
        content_id=content.content_id,
        actions=[
            CanonicalAction(
                action_id="ACTION-001",
                source_content_id=content.content_id,
                text=ActionText(original="join our Telegram group", normalized="Join Telegram Group"),
                action_type="JOIN_CHANNEL",
                category="CHANNEL_MIGRATION",
                target=ActionTarget(type="channel", value="Telegram"),
                rationale_claim_ids=["CLAIM-001"]
            )
        ]
    )

    links = ClaimActionLinker.link_claims_and_actions(content, claims, actions)
    assert len(links) >= 1
    assert any(l.type == "RATIONALE_FOR" for l in links)
    r_link = next(l for l in links if l.type == "RATIONALE_FOR")
    assert r_link.claim_id == "CLAIM-001"
    assert r_link.action_id == "ACTION-001"


def test_adjacent_claims_and_actions_without_connective_produce_no_links():
    content_engine = ContentIntelligenceEngine()
    content = content_engine.process_text("SEBI registered advisor Rahul Sharma. Download our app.")

    claims = ClaimAnalysis(
        content_id=content.content_id,
        claims=[
            CanonicalClaim(
                claim_id="CLAIM-101",
                source_content_id=content.content_id,
                text=ClaimText(original="Rahul Sharma is registered with SEBI.", normalized="Rahul Sharma is registered with SEBI."),
                claim_type="REGULATORY",
                subject="Rahul Sharma",
                predicate="REGISTERED_WITH",
                object="SEBI"
            )
        ]
    )
    actions = ActionAnalysis(
        content_id=content.content_id,
        actions=[
            CanonicalAction(
                action_id="ACTION-101",
                source_content_id=content.content_id,
                text=ActionText(original="Download our app", normalized="Download app"),
                action_type="DOWNLOAD",
                category="SOFTWARE_INSTALLATION",
                target=ActionTarget(type="application", value="app")
            )
        ]
    )

    links = ClaimActionLinker.link_claims_and_actions(content, claims, actions)
    # Proximity alone must NOT generate claim->action justification links
    assert len(links) == 0


def test_return_claim_with_purpose_connective_links_to_payment():
    content_engine = ContentIntelligenceEngine()
    content = content_engine.process_text("Guaranteed 40% returns. Pay ₹5,000 to participate.")

    claims = ClaimAnalysis(
        content_id=content.content_id,
        claims=[
            CanonicalClaim(
                claim_id="CLAIM-201",
                source_content_id=content.content_id,
                text=ClaimText(original="Guaranteed 40% returns.", normalized="Guaranteed 40% returns."),
                claim_type="FINANCIAL",
                subject="unspecified_offer",
                predicate="GUARANTEED_RETURN",
                object="40% returns"
            )
        ]
    )
    actions = ActionAnalysis(
        content_id=content.content_id,
        actions=[
            CanonicalAction(
                action_id="ACTION-201",
                source_content_id=content.content_id,
                text=ActionText(original="Pay ₹5,000 to participate.", normalized="Pay ₹5,000"),
                action_type="PAYMENT",
                category="FINANCIAL_TRANSACTION",
                target=ActionTarget(type="unknown")
            )
        ]
    )

    links = ClaimActionLinker.link_claims_and_actions(content, claims, actions)
    assert len(links) == 1
    assert links[0].type == "RATIONALE_FOR"
    assert links[0].claim_id == "CLAIM-201"
    assert links[0].action_id == "ACTION-201"


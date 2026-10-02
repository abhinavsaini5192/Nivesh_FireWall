"""Unit tests covering the benchmark action cases from Section 27 (Engine 3)."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent, SourceInfo, RawContent, NormalizedText, Provenance


@pytest.fixture
def content_engine():
    return ContentIntelligenceEngine()


@pytest.fixture
def claims_engine():
    return ClaimIntelligenceEngine()


@pytest.fixture
def actions_engine():
    return ActionIntelligenceEngine()


def make_normalized(text: str, content_id: str = "test-item") -> NormalizedContent:
    """Helper to wrap raw text in NormalizedContent."""
    return NormalizedContent(
        content_id=content_id,
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=text),
        normalized=NormalizedText(text=text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-02T00:00:00Z", input_type="text")
    )


def test_case_multiple_actions_in_sequence(actions_engine):
    """'Join Telegram, download the app, complete KYC and pay ₹5,000.'
    Must generate 4 distinct actions with sequential sequence index and parameters.
    """
    text = "Join Telegram, download the app, complete KYC and pay ₹5,000."
    norm = make_normalized(text)
    res = actions_engine.analyze(norm)

    assert len(res.actions) == 4

    # Verify action types
    assert res.actions[0].action_type == "JOIN_CHANNEL"
    assert res.actions[1].action_type == "DOWNLOAD"
    assert res.actions[2].action_type == "UPLOAD_DOCUMENT"
    assert res.actions[3].action_type == "PAYMENT"

    # Verify sequencing
    assert [a.sequence.index for a in res.actions] == [1, 2, 3, 4]

    # Verify parameters
    payment_act = res.actions[3]
    assert payment_act.parameters.get("amount") == 5000.0
    assert payment_act.parameters.get("currency") == "INR"


def test_case_claim_action_separation(content_engine, claims_engine, actions_engine):
    """'SEBI approved this platform, so register now.'
    Claim remains Engine 2 claim; 'register now' becomes Engine 3 action.
    """
    text = "SEBI approved this platform, so register now."
    norm = content_engine.process_text(text)
    claim_res = claims_engine.analyze(norm)
    action_res = actions_engine.analyze(norm, claim_res)

    # Claim is extracted by Engine 2
    assert len(claim_res.claims) >= 1
    reg_claim = claim_res.claims[0]
    assert reg_claim.predicate == "OFFICIALLY_APPROVED"

    # Action is extracted by Engine 3
    assert len(action_res.actions) >= 1
    reg_action = action_res.actions[0]
    assert reg_action.action_type in {"CONNECT_ACCOUNT", "OTHER"}
    assert "register" in reg_action.text.original.lower()

    # The action must NOT absorb the claim
    assert "sebi approved" not in reg_action.text.normalized.lower()


def test_case_action_rationale_linking(content_engine, claims_engine, actions_engine):
    """'Join our Telegram because SEBI approved this group.'
    Claim is linked to action as rationale.
    """
    text = "Join our Telegram because SEBI approved this group."
    norm = content_engine.process_text(text)
    claim_res = claims_engine.analyze(norm)
    action_res = actions_engine.analyze(norm, claim_res)

    assert len(action_res.actions) >= 1
    join_act = action_res.actions[0]
    assert join_act.action_type == "JOIN_CHANNEL"

    # Verify claim rationale linkage
    assert len(join_act.rationale_claim_ids) >= 1
    linked_claim_id = join_act.rationale_claim_ids[0]
    claim_ids = [c.claim_id for c in claim_res.claims]
    assert linked_claim_id in claim_ids


def test_case_duplicate_action_deduplication(actions_engine):
    """'Join Telegram now. Join our Telegram channel.'
    Must merge into one canonical action with multiple source spans.
    """
    text = "Join Telegram now. Join our Telegram channel."
    norm = make_normalized(text)
    res = actions_engine.analyze(norm)

    assert len(res.actions) == 1
    act = res.actions[0]
    assert act.action_type == "JOIN_CHANNEL"
    assert act.target.type == "channel"

    # Multiple source spans recorded
    assert len(act.source_spans) >= 2
    assert res.analysis_metadata.duplicate_actions_merged >= 1


def test_case_ambiguous_non_action_no_invention(actions_engine):
    """'Something may be coming soon.'
    Does NOT contain an action; must NOT invent an action.
    """
    text = "Something may be coming soon."
    norm = make_normalized(text)
    res = actions_engine.analyze(norm)

    assert len(res.actions) == 0


def test_case_modalities(actions_engine):
    # Direct instruction
    res1 = actions_engine.analyze(make_normalized("Pay ₹5,000 now."))
    assert len(res1.actions) == 1
    assert res1.actions[0].modality.type == "instruction"
    assert res1.actions[0].modality.strength == "direct"

    # Suggestion
    res2 = actions_engine.analyze(make_normalized("You should consider joining our group."))
    assert len(res2.actions) == 1
    assert res2.actions[0].modality.type == "suggestion"
    assert res2.actions[0].modality.strength == "indirect"

    # Invitation
    res3 = actions_engine.analyze(make_normalized("Join us on Telegram."))
    assert len(res3.actions) == 1
    assert res3.actions[0].modality.type == "invitation"
    assert res3.actions[0].modality.strength == "direct"

    # Implicit action
    res4 = actions_engine.analyze(make_normalized("To activate your account, your KYC must be completed."))
    assert len(res4.actions) == 1
    assert res4.actions[0].modality.type == "implicit"
    assert res4.actions[0].modality.strength == "indirect"

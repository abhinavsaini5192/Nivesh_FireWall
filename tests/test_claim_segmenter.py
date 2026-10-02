"""Unit tests for ClaimSegmenter and Action-filtering."""

import pytest
from nivesh.claims.segmenter import ClaimSegmenter


@pytest.fixture
def segmenter():
    return ClaimSegmenter()


def test_pure_actions_are_filtered(segmenter):
    # Pure action sentences must not become claims
    text = (
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000. "
        "Contact rahul@example.com."
    )
    candidates, actions_filtered = segmenter.segment(text)
    assert len(candidates) == 0
    assert actions_filtered >= 3


def test_action_vs_claim_buy_now(segmenter):
    text = "Buy now and join our Telegram."
    candidates, actions_filtered = segmenter.segment(text)
    assert len(candidates) == 0
    assert actions_filtered >= 1


def test_embedded_claim_inside_action_rationale(segmenter):
    # Action + claim reason: claim should be extracted, action filtered
    text = "Join our Telegram because SEBI approved this group."
    candidates, actions_filtered = segmenter.segment(text)
    assert len(candidates) == 1
    assert "SEBI approved this group" in candidates[0].text
    assert actions_filtered >= 1


def test_compound_statement_split(segmenter):
    text = "Revenue increased 40% and therefore the company will double."
    candidates, actions_filtered = segmenter.segment(text)
    assert len(candidates) >= 2
    c_texts = [c.text for c in candidates]
    assert any("Revenue increased 40%" in t for t in c_texts)
    assert any("company will double" in t for t in c_texts)


def test_appositive_regulatory_and_returns_split(segmenter):
    text = "SEBI registered advisor Rahul Sharma guarantees 40% returns."
    candidates, _ = segmenter.segment(text)
    assert len(candidates) >= 2
    c_texts = [c.text for c in candidates]
    assert any("Rahul Sharma is a SEBI registered advisor" in t for t in c_texts)
    assert any("guarantees 40% returns" in t for t in c_texts)

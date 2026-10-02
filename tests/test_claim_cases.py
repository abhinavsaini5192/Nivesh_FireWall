"""Unit tests covering the specific required benchmark cases from Section 27."""

import pytest
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent, SourceInfo, RawContent, NormalizedText, Provenance


@pytest.fixture
def claims_engine():
    return ClaimIntelligenceEngine()


def make_normalized(text: str, content_id: str = "test-item") -> NormalizedContent:
    """Helper to wrap raw text in NormalizedContent."""
    return NormalizedContent(
        content_id=content_id,
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=text),
        normalized=NormalizedText(text=text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-02T00:00:00Z", input_type="text")
    )


def test_case_same_underlying_claim(claims_engine):
    """'XYZ is debt free.' vs 'XYZ has zero debt.' -> compatible canonical representation."""
    c1 = claims_engine.analyze(make_normalized("XYZ is debt free."))
    c2 = claims_engine.analyze(make_normalized("XYZ has zero debt."))

    assert len(c1.claims) == 1
    assert len(c2.claims) == 1

    claim1 = c1.claims[0]
    claim2 = c2.claims[0]

    assert claim1.subject == "XYZ" and claim2.subject == "XYZ"
    assert claim1.predicate == "HAS_DEBT" and claim2.predicate == "HAS_DEBT"
    assert claim1.object == "0" and claim2.object == "0"
    assert claim1.canonical_fingerprint == claim2.canonical_fingerprint


def test_case_opinion(claims_engine):
    """'I think XYZ is undervalued.' -> claim_type = OPINION, modality = OPINION."""
    res = claims_engine.analyze(make_normalized("I think XYZ is undervalued."))
    assert len(res.claims) == 1
    claim = res.claims[0]
    assert claim.claim_type == "OPINION"
    assert claim.modality.type == "opinion"
    assert "XYZ" in claim.subject


def test_case_prediction(claims_engine):
    """'XYZ will reach ₹500 next year.' -> claim_type = PREDICTION, temporal_context = FUTURE."""
    res = claims_engine.analyze(make_normalized("XYZ will reach ₹500 next year."))
    assert len(res.claims) == 1
    claim = res.claims[0]
    assert claim.claim_type == "PREDICTION"
    assert claim.temporal_context.type == "future"
    assert "500" in (claim.object or "")


def test_case_regulatory_claim(claims_engine):
    """'SEBI approved XYZ.' -> claim_type = REGULATORY."""
    res = claims_engine.analyze(make_normalized("SEBI approved XYZ."))
    assert len(res.claims) == 1
    claim = res.claims[0]
    assert claim.claim_type == "REGULATORY"
    assert claim.predicate == "OFFICIALLY_APPROVED"
    assert "XYZ" in claim.subject
    assert "SEBI" in (claim.object or "")


def test_case_historical_fact(claims_engine):
    """'XYZ reported ₹40 crore profit in FY2025.' -> claim_type = FINANCIAL, temporal_context = HISTORICAL."""
    res = claims_engine.analyze(make_normalized("XYZ reported ₹40 crore profit in FY2025."))
    assert len(res.claims) == 1
    claim = res.claims[0]
    assert claim.claim_type == "FINANCIAL"
    assert claim.temporal_context.type == "historical"
    assert claim.predicate == "REPORTED_PROFIT"
    assert "40 crore" in (claim.object or "")


def test_case_compound_statement(claims_engine):
    """'Revenue increased 40% and therefore the company will double.' -> at least two claims + relation."""
    res = claims_engine.analyze(make_normalized("Revenue increased 40% and therefore the company will double."))
    assert len(res.claims) >= 2
    claim_types = [c.claim_type for c in res.claims]
    assert "FINANCIAL" in claim_types
    assert "PREDICTION" in claim_types

    # Verify causal relationship detection
    assert len(res.claim_relations) >= 1
    rel_types = [r.relation_type for r in res.claim_relations]
    assert "CAUSES" in rel_types or "DEPENDS_ON" in rel_types


def test_case_action_vs_claim(claims_engine):
    """'Buy now and join our Telegram.' -> no accidental conversion of actions into claims."""
    res = claims_engine.analyze(make_normalized("Buy now and join our Telegram."))
    assert len(res.claims) == 0
    assert res.analysis_metadata.actions_filtered_count >= 1


def test_regression_no_implicit_attribution(claims_engine):
    """Test 1 — No implicit attribution:
    Input: 'Rahul Sharma is a SEBI registered advisor. Guaranteed 40% returns.'
    Assert:
    claim 1.subject == 'Rahul Sharma'
    claim 2.subject != 'Rahul Sharma'
    """
    from nivesh.engine import ContentIntelligenceEngine
    content_engine = ContentIntelligenceEngine()
    norm = content_engine.process_text("Rahul Sharma is a SEBI registered advisor. Guaranteed 40% returns.")
    res = claims_engine.analyze(norm)

    assert len(res.claims) >= 2
    claim1 = res.claims[0]
    claim2 = res.claims[1]

    assert claim1.subject == "Rahul Sharma"
    assert claim1.predicate == "REGISTERED_WITH"

    assert claim2.subject != "Rahul Sharma"
    assert claim2.subject in {"unspecified_offer", "unspecified", "investment_offer"}
    assert claim2.predicate == "GUARANTEED_RETURN"
    assert claim2.attribution is None


def test_regression_explicit_attribution(claims_engine):
    """Test 2 — Explicit attribution:
    Input: 'Rahul Sharma guarantees 40% returns.'
    Assert:
    claim.subject == 'Rahul Sharma'
    """
    from nivesh.engine import ContentIntelligenceEngine
    content_engine = ContentIntelligenceEngine()
    norm = content_engine.process_text("Rahul Sharma guarantees 40% returns.")
    res = claims_engine.analyze(norm)

    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.subject == "Rahul Sharma"
    assert claim.predicate == "GUARANTEED_RETURN"
    assert "40%" in (claim.object or "")


def test_regression_according_to_attribution(claims_engine):
    """Test 3 — According-to attribution:
    Input: 'According to Rahul Sharma, the investment guarantees 40% returns.'
    Assert:
    claim.subject != 'Rahul Sharma'
    claim.attribution.entity == 'Rahul Sharma'
    claim.attribution.explicit == true
    """
    from nivesh.engine import ContentIntelligenceEngine
    content_engine = ContentIntelligenceEngine()
    norm = content_engine.process_text("According to Rahul Sharma, the investment guarantees 40% returns.")
    res = claims_engine.analyze(norm)

    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.subject != "Rahul Sharma"
    assert claim.attribution is not None
    assert claim.attribution.entity == "Rahul Sharma"
    assert claim.attribution.explicit is True
    assert claim.predicate == "GUARANTEED_RETURN"


def test_regression_generic_offer(claims_engine):
    """Test 4 — Generic offer:
    Input: 'This investment guarantees 40% returns.'
    Assert:
    claim.subject == 'this investment'
    """
    from nivesh.engine import ContentIntelligenceEngine
    content_engine = ContentIntelligenceEngine()
    norm = content_engine.process_text("This investment guarantees 40% returns.")
    res = claims_engine.analyze(norm)

    assert len(res.claims) >= 1
    claim = res.claims[0]
    assert claim.subject.lower() == "this investment"
    assert claim.predicate == "GUARANTEED_RETURN"


def test_regression_multiple_nearby_entities(claims_engine):
    """Test 5 — Multiple nearby entities:
    Input: 'Rahul Sharma works at ABC Investments. ABC Investments offers guaranteed 40% returns.'
    Assert:
    claim.subject == 'ABC Investments'
    not Rahul Sharma.
    """
    from nivesh.engine import ContentIntelligenceEngine
    content_engine = ContentIntelligenceEngine()
    norm = content_engine.process_text("Rahul Sharma works at ABC Investments. ABC Investments offers guaranteed 40% returns.")
    res = claims_engine.analyze(norm)

    return_claims = [c for c in res.claims if c.predicate == "GUARANTEED_RETURN"]
    assert len(return_claims) >= 1
    claim = return_claims[0]
    assert claim.subject == "ABC Investments"
    assert claim.subject != "Rahul Sharma"

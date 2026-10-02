"""Unit tests for ClaimCanonicalizer and fingerprinting."""

import pytest
from nivesh.claims.canonicalizer import ClaimCanonicalizer
from nivesh.schemas.claims import SourceSpan


@pytest.fixture
def canonicalizer():
    return ClaimCanonicalizer()


def test_debt_free_canonicalization_equivalence(canonicalizer):
    span = SourceSpan(start=0, end=20)
    c1 = canonicalizer.canonicalize("XYZ is debt free", span, "c-1", 1)
    c2 = canonicalizer.canonicalize("XYZ has zero debt", span, "c-1", 2)
    c3 = canonicalizer.canonicalize("XYZ carries no debt", span, "c-1", 3)

    assert c1 is not None and c2 is not None and c3 is not None
    # All 3 variations must produce identical canonical representation
    assert c1.predicate == "HAS_DEBT"
    assert c2.predicate == "HAS_DEBT"
    assert c3.predicate == "HAS_DEBT"

    assert c1.object == "0"
    assert c2.object == "0"
    assert c3.object == "0"

    assert c1.canonical_fingerprint == c2.canonical_fingerprint == c3.canonical_fingerprint


def test_regulatory_registration_canonicalization(canonicalizer):
    span = SourceSpan(start=0, end=35)
    claim = canonicalizer.canonicalize("Rahul Sharma is a SEBI registered advisor", span, "c-1", 1)
    assert claim is not None
    assert claim.claim_type == "REGULATORY"
    assert claim.subject == "Rahul Sharma"
    assert claim.predicate == "REGISTERED_WITH"
    assert claim.object == "SEBI"
    assert "ENTITY:RAHUL_SHARMA" in claim.canonical_fingerprint
    assert "PREDICATE:REGISTERED_WITH" in claim.canonical_fingerprint


def test_guaranteed_return_canonicalization(canonicalizer):
    span = SourceSpan(start=0, end=25)
    claim = canonicalizer.canonicalize("Guaranteed 40% returns", span, "c-1", 1)
    assert claim is not None
    assert claim.claim_type == "FINANCIAL"
    assert claim.predicate == "GUARANTEED_RETURN"
    assert "40%" in (claim.object or "")
    assert claim.modality.type == "assertion"
    assert claim.modality.certainty_language == "Guaranteed"


def test_corporate_event_bonus(canonicalizer):
    span = SourceSpan(start=0, end=30)
    claim = canonicalizer.canonicalize("ABC announced a 1:1 bonus", span, "c-1", 1)
    assert claim is not None
    assert claim.claim_type == "CORPORATE_EVENT"
    assert claim.subject == "ABC"
    assert claim.predicate == "ANNOUNCED_BONUS"
    assert claim.object == "1:1"


def test_price_prediction_canonicalization(canonicalizer):
    span = SourceSpan(start=0, end=30)
    claim = canonicalizer.canonicalize("ABC will reach ₹500", span, "c-1", 1)
    assert claim is not None
    assert claim.claim_type == "PREDICTION"
    assert claim.subject == "ABC"
    assert claim.predicate == "REACH_PRICE"
    assert "500" in (claim.object or "")
    assert claim.temporal_context.type == "future"


def test_undervalued_opinion_canonicalization(canonicalizer):
    span = SourceSpan(start=0, end=30)
    claim = canonicalizer.canonicalize("I think XYZ is undervalued", span, "c-1", 1)
    assert claim is not None
    assert claim.claim_type == "OPINION"
    assert claim.subject == "XYZ"
    assert claim.predicate == "VALUATION_STATUS"
    assert claim.object == "undervalued"
    assert claim.modality.type == "opinion"


def test_heuristic_fallback_unknown_claim(canonicalizer):
    span = SourceSpan(start=0, end=35)
    claim = canonicalizer.canonicalize("Something big is coming soon", span, "c-1", 1)
    assert claim is not None
    assert claim.confidence <= 0.80
    assert claim.subject is not None
    assert claim.predicate == "ASSERTS"

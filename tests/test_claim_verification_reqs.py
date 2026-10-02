"""Unit tests for Verification Requirements and Claim Relations."""

import pytest
from nivesh.claims.verification_reqs import VerificationRequirementsGenerator
from nivesh.claims.relation_detector import RelationDetector
from nivesh.schemas.claims import CanonicalClaim, ClaimText, SourceSpan


@pytest.fixture
def req_gen():
    return VerificationRequirementsGenerator()


@pytest.fixture
def rel_detector():
    return RelationDetector()


def test_regulatory_verification_requirements(req_gen):
    reqs = req_gen.generate(
        claim_type="REGULATORY",
        predicate="REGISTERED_WITH",
        subject="Rahul Sharma",
        obj="SEBI"
    )
    assert "official_regulator_registry" in reqs
    assert "registration_number" in reqs
    assert "registration_status" in reqs


def test_future_prediction_verification_requirements(req_gen):
    reqs = req_gen.generate(
        claim_type="PREDICTION",
        predicate="REACH_PRICE",
        subject="ABC",
        obj="₹500",
        temporal_type="future",
        modality_type="prediction"
    )
    assert "unverifiable_future_outcome" in reqs


def test_bonus_corporate_event_verification_requirements(req_gen):
    reqs = req_gen.generate(
        claim_type="CORPORATE_EVENT",
        predicate="ANNOUNCED_BONUS",
        subject="ABC",
        obj="1:1"
    )
    assert "official_company_announcement" in reqs
    assert "exchange_filing_bse_nse" in reqs


def test_causes_and_depends_on_relations(rel_detector):
    c1 = CanonicalClaim(
        claim_id="CLAIM-001",
        source_content_id="cnt-1",
        text=ClaimText(original="Revenue increased 40%", normalized="Revenue increased 40%."),
        claim_type="FINANCIAL",
        subject="revenue",
        predicate="INCREASED",
        object="40%",
        source_span=SourceSpan(start=0, end=20)
    )
    c2 = CanonicalClaim(
        claim_id="CLAIM-002",
        source_content_id="cnt-1",
        text=ClaimText(original="the company will double", normalized="Company growth predicted to double."),
        claim_type="PREDICTION",
        subject="company",
        predicate="GROWTH_PREDICTION",
        object="double",
        source_span=SourceSpan(start=35, end=60)
    )

    relations = rel_detector.detect_relations(
        claims=[c1, c2],
        discourse_markers={"CLAIM-002": "therefore"}
    )

    types = [r.relation_type for r in relations]
    assert "CAUSES" in types
    assert "DEPENDS_ON" in types


def test_same_underlying_claim_relation(rel_detector):
    fp = "ENTITY:XYZ|PREDICATE:HAS_DEBT|OBJECT:0|TEMPORAL:CURRENT|MODALITY:ASSERTION"
    c1 = CanonicalClaim(
        claim_id="CLAIM-001",
        source_content_id="cnt-1",
        text=ClaimText(original="XYZ is debt free", normalized="XYZ is debt free."),
        claim_type="FINANCIAL",
        subject="XYZ",
        predicate="HAS_DEBT",
        object="0",
        canonical_fingerprint=fp,
    )
    c2 = CanonicalClaim(
        claim_id="CLAIM-002",
        source_content_id="cnt-1",
        text=ClaimText(original="XYZ has zero debt", normalized="XYZ is debt free."),
        claim_type="FINANCIAL",
        subject="XYZ",
        predicate="HAS_DEBT",
        object="0",
        canonical_fingerprint=fp,
    )

    relations = rel_detector.detect_relations([c1, c2])
    types = [r.relation_type for r in relations]
    assert "SAME_UNDERLYING_CLAIM" in types

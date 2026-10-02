"""Unit tests for Engine 9 Typed Schemas."""

import pytest
from pydantic import ValidationError
from nivesh.identity.schemas import (
    IdentityEntityType,
    IdentityStatus,
    IdentityMatchStatus,
    IdentityFindingType,
    IdentityRelationshipType,
    ClaimedEntity,
    ResolvedEntity,
    IdentityMatch,
    AuthorityAlignment,
    DomainAlignment,
    IdentityFinding,
    IdentityProvenance,
    IdentityAnalysis,
    ENGINE_VERSION,
)


def test_identity_enums():
    """Verify all required enums have expected values."""
    assert IdentityEntityType.PERSON.value == "PERSON"
    assert IdentityEntityType.ORGANIZATION.value == "ORGANIZATION"
    assert IdentityEntityType.REGULATOR.value == "REGULATOR"
    assert IdentityEntityType.ADVISER.value == "ADVISER"
    assert IdentityEntityType.BROKER.value == "BROKER"
    assert IdentityEntityType.DOMAIN.value == "DOMAIN"
    assert IdentityEntityType.CHANNEL.value == "CHANNEL"

    assert IdentityStatus.ESTABLISHED.value == "ESTABLISHED"
    assert IdentityStatus.PARTIALLY_ESTABLISHED.value == "PARTIALLY_ESTABLISHED"
    assert IdentityStatus.NOT_ESTABLISHED.value == "NOT_ESTABLISHED"
    assert IdentityStatus.IDENTITY_MISMATCH.value == "IDENTITY_MISMATCH"
    assert IdentityStatus.AMBIGUOUS.value == "AMBIGUOUS"
    assert IdentityStatus.SOURCE_UNAVAILABLE.value == "SOURCE_UNAVAILABLE"

    assert IdentityFindingType.REGISTRATION_ENTITY_MATCH.value == "REGISTRATION_ENTITY_MATCH"
    assert IdentityFindingType.REGISTRATION_ENTITY_MISMATCH.value == "REGISTRATION_ENTITY_MISMATCH"
    assert IdentityFindingType.DOMAIN_IDENTITY_MISMATCH.value == "DOMAIN_IDENTITY_MISMATCH"
    assert IdentityFindingType.AUTHORITY_CLAIM.value == "AUTHORITY_CLAIM"
    assert IdentityFindingType.SOCIAL_ACCOUNT_NOT_ESTABLISHED.value == "SOCIAL_ACCOUNT_NOT_ESTABLISHED"


def test_claimed_entity_instantiation():
    """Verify ClaimedEntity schema creation and validation."""
    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
        original_form="Rahul Sharma",
        associated_registration="INA000012345",
        associated_domain="rahulinvest.in",
        associated_channel="telegram:rahulinvest",
        source_claim_ids=["CLM-001"],
    )
    assert entity.entity_id == "ENT-001"
    assert entity.normalized_name == "rahul sharma"
    assert entity.entity_type == IdentityEntityType.ADVISER
    assert entity.associated_registration == "INA000012345"


def test_resolved_entity_instantiation():
    """Verify ResolvedEntity schema creation and validation."""
    resolved = ResolvedEntity(
        candidate_id="CAND-001",
        legal_name="Rahul Sharma Advisory Services",
        normalized_name="rahul sharma advisory services",
        entity_type=IdentityEntityType.ADVISER,
        registration_number="INA000012345",
        official_domain="rahulsharma.co.in",
        regulator="SEBI",
        jurisdiction="IN",
        source_document_ids=["DOC-001"],
    )
    assert resolved.candidate_id == "CAND-001"
    assert resolved.regulator == "SEBI"
    assert resolved.jurisdiction == "IN"


def test_identity_match_confidence_bounds():
    """Verify confidence must be between 0.0 and 1.0."""
    match = IdentityMatch(
        identity_match_id="IDM-001",
        claimed_entity_id="ENT-001",
        candidate_entity_id="CAND-001",
        entity_type=IdentityEntityType.PERSON,
        match_status=IdentityMatchStatus.ESTABLISHED,
        match_basis="All attributes match authoritative records.",
        matching_attributes=["legal_name", "registration_number"],
        confidence=0.98,
    )
    assert match.confidence == 0.98

    with pytest.raises(ValidationError):
        IdentityMatch(
            identity_match_id="IDM-002",
            claimed_entity_id="ENT-001",
            entity_type=IdentityEntityType.PERSON,
            match_status=IdentityMatchStatus.ESTABLISHED,
            match_basis="Invalid confidence.",
            confidence=1.5,
        )


def test_identity_analysis_schema():
    """Verify top-level IdentityAnalysis model."""
    provenance = IdentityProvenance(
        engine_version=ENGINE_VERSION,
        verified_at="2026-10-02T12:00:00Z",
        input_content_id="CNT-001",
        claim_count=2,
        source_document_count=1,
        evidence_count=2,
    )
    analysis = IdentityAnalysis(
        analysis_id="IDA-001",
        entities=[],
        identity_matches=[],
        identity_findings=[],
        identity_status=IdentityStatus.NOT_ESTABLISHED,
        authority_alignments=[],
        domain_alignments=[],
        confidence=0.85,
        provenance=provenance,
        upstream_references={"content_id": "CNT-001"},
    )
    assert analysis.analysis_id == "IDA-001"
    assert analysis.identity_status == IdentityStatus.NOT_ESTABLISHED
    assert analysis.provenance.claim_count == 2

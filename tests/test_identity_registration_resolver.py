"""Unit tests for RegistrationResolver in Engine 9."""

from nivesh.identity.schemas import (
    ClaimedEntity,
    IdentityEntityType,
    IdentityMatchStatus,
    IdentityFindingType,
)
from nivesh.identity.registration_resolver import RegistrationResolver
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourcePlan,
    SourceQuery,
    SourceDocument,
    RetrievalMetadata,
    SourceAnalysisMetadata,
)
from nivesh.schemas.evidence import (
    EvidenceAnalysis,
    VerificationResult,
    VerificationProvenance,
    EvidenceAnalysisMetadata,
)


def _make_source_doc(doc_id: str, reg_no: str, legal_name: str, status: str = "SUCCESS", content: str = ""):
    return SourceDocument(
        document_id=doc_id,
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title=f"Registry Entry: {legal_name}",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content=content or f"Entity Legal Name: {legal_name}\nRegistration Number: {reg_no}",
        content_hash="abc123hash",
        metadata={"registration_number": reg_no, "legal_name": legal_name},
        retrieval=RetrievalMetadata(status=status, method="fixture", mode="FIXTURE"),
    )


def _make_sources(docs: list[SourceDocument]) -> SourceAnalysis:
    csr = ClaimSourceResult(
        claim_id="CLM-001",
        source_plan=SourcePlan(query=SourceQuery(name="Test"), primary=["sebi_registry"]),
        documents=docs,
    )
    return SourceAnalysis(
        content_id="CNT-001",
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=len(docs)),
    )


def test_registration_exists_and_matches():
    """Verify that matching legal name and registration ID yields ESTABLISHED and REGISTRATION_ENTITY_MATCH."""
    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="ABC Securities Pvt Ltd",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_registration="INZ00012345",
    )
    doc = _make_source_doc("DOC-001", "INZ00012345", "ABC Securities Private Limited")
    sources = _make_sources([doc])

    candidates, records = RegistrationResolver.resolve_registrations(
        claimed_entities=[entity],
        sources=sources,
    )

    assert len(candidates) == 1
    assert candidates[0].legal_name == "ABC Securities Private Limited"
    assert len(records) == 1
    assert records[0]["status"] == IdentityMatchStatus.ESTABLISHED
    assert records[0]["finding_type"] == IdentityFindingType.REGISTRATION_ENTITY_MATCH
    assert "matches claimed entity" in records[0]["basis"]


def test_registration_exists_but_entity_mismatch():
    """Verify that a registration belonging to a different entity yields IDENTITY_MISMATCH."""
    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
        associated_registration="INH000009999",
    )
    # Registration belongs to Alpha Wealth Advisors, NOT Rahul Sharma
    doc = _make_source_doc(
        "DOC-002",
        "INH000009999",
        "Alpha Wealth Advisors Private Limited",
        content="SEBI registration INH000009999 belongs to Alpha Wealth Advisors Private Limited, not Rahul Sharma.",
    )
    sources = _make_sources([doc])

    candidates, records = RegistrationResolver.resolve_registrations(
        claimed_entities=[entity],
        sources=sources,
    )

    assert len(records) == 1
    assert records[0]["status"] == IdentityMatchStatus.IDENTITY_MISMATCH
    assert records[0]["finding_type"] == IdentityFindingType.REGISTRATION_ENTITY_MISMATCH
    assert "Alpha Wealth Advisors" in records[0]["basis"]
    assert "Rahul Sharma" in records[0]["basis"]


def test_registration_search_no_match():
    """Verify registry search NO_MATCH yields NOT_ESTABLISHED and NOT IDENTITY_MISMATCH."""
    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
        associated_registration="INA999999999",
    )
    # Source document indicates no records found
    doc = SourceDocument(
        document_id="DOC-003",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Search Result",
        url="https://sebi.gov.in/search",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Query: 'INA999999999'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND",
        content_hash="hash000",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    sources = _make_sources([doc])

    candidates, records = RegistrationResolver.resolve_registrations(
        claimed_entities=[entity],
        sources=sources,
    )

    assert len(candidates) == 0
    assert len(records) == 1
    assert records[0]["status"] == IdentityMatchStatus.NOT_ESTABLISHED
    assert records[0]["finding_type"] == IdentityFindingType.AUTHORITY_IDENTITY_NOT_ESTABLISHED
    # Must NOT be MISMATCH
    assert records[0]["status"] != IdentityMatchStatus.IDENTITY_MISMATCH


def test_registration_claimed_but_identifier_missing():
    """Verify entity claiming to be registered without providing identifier yields REGISTRATION_IDENTIFIER_UNRESOLVED."""
    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
        associated_registration=None,  # No registration number
    )
    # Search by name in registry returns nothing
    doc = SourceDocument(
        document_id="DOC-004",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Name Search",
        url="https://sebi.gov.in/search",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Query: 'Rahul Sharma'\nMatches Found: 0",
        content_hash="hash001",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    sources = _make_sources([doc])

    candidates, records = RegistrationResolver.resolve_registrations(
        claimed_entities=[entity],
        sources=sources,
    )

    assert len(records) == 1
    assert records[0]["status"] == IdentityMatchStatus.NOT_ESTABLISHED
    assert records[0]["finding_type"] == IdentityFindingType.REGISTRATION_IDENTIFIER_UNRESOLVED


def test_registration_source_unavailable():
    """Verify that failure to connect to official registry yields SOURCE_UNAVAILABLE."""
    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="ABC Capital",
        normalized_name="abc capital",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_registration="INZ00055555",
    )
    doc = SourceDocument(
        document_id="DOC-005",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="Registry Error",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Connection timeout",
        content_hash="hash002",
        metadata={},
        retrieval=RetrievalMetadata(status="SOURCE_UNAVAILABLE", method="fixture", mode="FIXTURE"),
    )
    sources = _make_sources([doc])

    candidates, records = RegistrationResolver.resolve_registrations(
        claimed_entities=[entity],
        sources=sources,
    )

    assert len(records) == 1
    assert records[0]["status"] == IdentityMatchStatus.SOURCE_UNAVAILABLE
    assert records[0]["finding_type"] == IdentityFindingType.SOURCE_UNAVAILABLE

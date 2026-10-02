"""Unit tests for Source Intelligence Engine schemas."""

import pytest
from pydantic import ValidationError
from nivesh.schemas.sources import (
    SourceQuery,
    SourcePlan,
    SourceSearchResult,
    RetrievalMetadata,
    SourceDocument,
    EvidenceCandidate,
    EvidenceRelevance,
    EvidenceProvenance,
    ClaimSourceResult,
    SourceAnalysisMetadata,
    SourceAnalysis,
    SourceCatalogEntry,
)


def test_source_query_creation():
    query = SourceQuery(
        name="Rahul Sharma",
        registration_number="INA000012345",
        keywords=["advisor", "sebi"],
        temporal_focus="current"
    )
    assert query.name == "Rahul Sharma"
    assert query.registration_number == "INA000012345"
    assert "advisor" in query.keywords
    assert query.temporal_focus == "current"


def test_source_document_provenance_and_hash():
    doc = SourceDocument(
        document_id="DOC-001",
        source_id="sebi_recognised_intermediaries",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Intermediaries Registry",
        url="https://www.sebi.gov.in/intermediaries.html",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content="Official registry record",
        content_hash="abc123hash",
        metadata={"category": "adviser"},
        retrieval=RetrievalMetadata(
            status="SUCCESS",
            http_status=200,
            method="SEBIAdapter",
            mode="FIXTURE",
            response_time_ms=12.5
        )
    )
    assert doc.document_id == "DOC-001"
    assert doc.organization == "SEBI"
    assert doc.retrieval.mode == "FIXTURE"
    assert doc.retrieval.status == "SUCCESS"


def test_evidence_candidate_strictly_unverified():
    candidate = EvidenceCandidate(
        evidence_id="EVID-001",
        claim_id="CLAIM-001",
        source_document_id="DOC-001",
        excerpt="No entity named Rahul Sharma registered.",
        relevance=EvidenceRelevance(
            matched_terms=["registered"],
            matched_entities=["Rahul Sharma"],
            matched_dates=[],
            relevance_score=0.8
        ),
        source_type="REGULATORY_REGISTRY",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(
            retrieved_at="2026-10-02T12:00:00Z",
            retrieval_method="SEBIAdapter",
            source_mode="FIXTURE",
            source_url="https://www.sebi.gov.in"
        ),
        verification_status="UNVERIFIED"
    )
    assert candidate.verification_status == "UNVERIFIED"
    assert candidate.authority_tier == "PRIMARY_OFFICIAL"


def test_source_analysis_structure():
    analysis = SourceAnalysis(
        content_id="test-content-uuid",
        claim_sources=[
            ClaimSourceResult(
                claim_id="CLAIM-001",
                source_plan=SourcePlan(
                    primary=["sebi_recognised_intermediaries"],
                    fallback=[],
                    query=SourceQuery(name="Test"),
                    required_source_types=["REGULATORY_REGISTRY"]
                ),
                searches=[],
                documents=[],
                evidence_candidates=[]
            )
        ],
        analysis_metadata=SourceAnalysisMetadata(
            claims_processed=1,
            sources_queried=1,
            documents_retrieved=0,
            evidence_candidates_count=0,
            retrieval_failures=0,
            cache_hits=0,
            processing_time_ms=5.2
        )
    )
    assert analysis.content_id == "test-content-uuid"
    assert len(analysis.claim_sources) == 1
    assert analysis.analysis_metadata.claims_processed == 1

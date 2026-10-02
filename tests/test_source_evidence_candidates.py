"""Unit tests for Source Normalizer and Evidence Candidate extraction."""

from nivesh.schemas.claims import CanonicalClaim, ClaimText, TemporalContext
from nivesh.schemas.sources import SourceDocument, RetrievalMetadata
from nivesh.sources.normalizer import SourceNormalizer


def test_extract_evidence_candidates_preserves_unverified_and_provenance():
    claim = CanonicalClaim(
        claim_id="CLAIM-001",
        source_content_id="content-1",
        text=ClaimText(original="Rahul Sharma is a SEBI registered advisor", normalized="Rahul Sharma is registered with SEBI."),
        claim_type="REGULATORY",
        subject="Rahul Sharma",
        predicate="REGISTERED_WITH",
        object="SEBI",
        temporal_context=TemporalContext(type="current")
    )

    doc = SourceDocument(
        document_id="DOC-SEBI-001",
        source_id="sebi_recognised_intermediaries",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Intermediary Registry Search: Rahul Sharma",
        url="https://www.sebi.gov.in/intermediaries.html",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content="SEBI RECOGNISED INTERMEDIARY DATABASE SEARCH RESULT\nQuery: 'Rahul Sharma'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND",
        content_hash="hash123",
        metadata={"matched": False},
        retrieval=RetrievalMetadata(
            status="NO_MATCH",
            http_status=200,
            method="SEBIAdapter",
            mode="FIXTURE",
            response_time_ms=15.0
        )
    )

    candidates = SourceNormalizer.extract_evidence_candidates(
        claim=claim,
        document=doc,
        authority_tier="PRIMARY_OFFICIAL"
    )

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.claim_id == "CLAIM-001"
    assert cand.source_document_id == "DOC-SEBI-001"
    assert cand.verification_status == "UNVERIFIED"
    assert cand.authority_tier == "PRIMARY_OFFICIAL"
    assert cand.provenance.retrieval_method == "SEBIAdapter"
    assert cand.provenance.source_mode == "FIXTURE"
    assert "Rahul Sharma" in cand.relevance.matched_entities

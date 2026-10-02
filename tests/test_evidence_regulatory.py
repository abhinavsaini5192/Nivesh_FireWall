"""Unit tests for Regulatory and Identity Verification in Engine 5."""

from nivesh.schemas.claims import CanonicalClaim, ClaimText, TemporalContext
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument, EvidenceRelevance, EvidenceProvenance, RetrievalMetadata
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator
from nivesh.schemas.sources import ClaimSourceResult, SourcePlan, SourceQuery


def test_regulatory_registered_entity_supported():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-001",
        source_content_id="c-1",
        text=ClaimText(original="Amit Patel is a SEBI registered advisor", normalized="Amit Patel is registered with SEBI."),
        claim_type="REGULATORY",
        subject="Amit Patel",
        predicate="REGISTERED_WITH",
        object="SEBI"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-001",
        claim_id="CLAIM-001",
        source_document_id="DOC-001",
        excerpt="Legal Name: Amit Patel Wealth Advisors LLP\nRegistration Number: INA000012345\nRegistration Status: CURRENT",
        relevance=EvidenceRelevance(matched_terms=["registered"], matched_entities=["Amit Patel"]),
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

    doc = SourceDocument(
        document_id="DOC-001",
        source_id="sebi_recognised_intermediaries",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Recognized Intermediary Registry",
        url="https://www.sebi.gov.in",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content=candidate.excerpt,
        content_hash="h1",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="SEBIAdapter", mode="FIXTURE")
    )

    source_res = ClaimSourceResult(
        claim_id="CLAIM-001",
        source_plan=SourcePlan(query=SourceQuery(name="Amit Patel")),
        documents=[doc],
        evidence_candidates=[candidate]
    )

    res = evaluator.evaluate(claim, source_res)
    assert res.status == "SUPPORTED"
    assert res.evidence_strength == "HIGH"
    assert len(res.supporting_evidence) == 1
    assert any("CURRENT" in step for step in res.reasoning_trace)


def test_regulatory_unregistered_entity_insufficient_evidence():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-002",
        source_content_id="c-1",
        text=ClaimText(original="Rahul Sharma is a SEBI registered advisor", normalized="Rahul Sharma is registered with SEBI."),
        claim_type="REGULATORY",
        subject="Rahul Sharma",
        predicate="REGISTERED_WITH",
        object="SEBI"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-002",
        claim_id="CLAIM-002",
        source_document_id="DOC-002",
        excerpt="SEBI RECOGNISED INTERMEDIARY DATABASE SEARCH RESULT\nQuery: 'Rahul Sharma'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND",
        relevance=EvidenceRelevance(matched_terms=["registered"], matched_entities=["Rahul Sharma"]),
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

    doc = SourceDocument(
        document_id="DOC-002",
        source_id="sebi_recognised_intermediaries",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Recognized Intermediary Registry",
        url="https://www.sebi.gov.in",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content=candidate.excerpt,
        content_hash="h2",
        metadata={"matched": False},
        retrieval=RetrievalMetadata(status="NO_MATCH", method="SEBIAdapter", mode="FIXTURE")
    )

    source_res = ClaimSourceResult(
        claim_id="CLAIM-002",
        source_plan=SourcePlan(query=SourceQuery(name="Rahul Sharma")),
        documents=[doc],
        evidence_candidates=[candidate]
    )

    res = evaluator.evaluate(claim, source_res)
    # Registry returned 0 records -> claim not established; records absence without fraud accusation
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert res.evidence_strength == "HIGH"
    assert len(res.contradicting_evidence) == 1
    assert any("returned 0 matches" in step for step in res.reasoning_trace)
    assert not any("fraudulent" in step.lower() for step in res.reasoning_trace)


def test_regulatory_guaranteed_return_statutory_prohibition_contradicted():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-003",
        source_content_id="c-1",
        text=ClaimText(original="Guaranteed 40% returns.", normalized="40% returns are guaranteed."),
        claim_type="FINANCIAL",
        subject="unspecified_offer",
        predicate="GUARANTEED_RETURN",
        object="40% returns"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-003",
        claim_id="CLAIM-003",
        source_document_id="DOC-003",
        excerpt="Securities and Exchange Board of India [Code of Conduct]: Prohibition on Assured / Guaranteed Returns: No registered intermediary shall assure, promise, or guarantee any fixed percentage of returns.",
        relevance=EvidenceRelevance(matched_terms=["guaranteed"]),
        source_type="REGULATOR",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(
            retrieved_at="2026-10-02T12:00:00Z",
            retrieval_method="SEBIAdapter",
            source_mode="FIXTURE",
            source_url="https://www.sebi.gov.in"
        ),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-003",
        source_id="sebi_public_regulatory_pages",
        organization="SEBI",
        source_type="REGULATOR",
        title="SEBI Code of Conduct Prohibition",
        url="https://www.sebi.gov.in",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2020-09-23T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h3",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="SEBIAdapter", mode="FIXTURE")
    )

    source_res = ClaimSourceResult(
        claim_id="CLAIM-003",
        source_plan=SourcePlan(query=SourceQuery(keywords=["guaranteed"])),
        documents=[doc],
        evidence_candidates=[candidate]
    )

    res = evaluator.evaluate(claim, source_res)
    assert res.status == "CONTRADICTED"
    assert res.evidence_strength == "HIGH"
    assert len(res.contradicting_evidence) == 1
    assert any("prohibit" in step.lower() for step in res.reasoning_trace)

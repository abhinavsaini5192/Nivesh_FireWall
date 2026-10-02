"""Unit tests for Source Conflicts and Missing Evidence in Engine 5."""

from nivesh.schemas.claims import CanonicalClaim, ClaimText
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument, EvidenceRelevance, EvidenceProvenance, RetrievalMetadata, ClaimSourceResult, SourcePlan, SourceQuery
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator


def test_source_conflict_detected():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-301",
        source_content_id="c-1",
        text=ClaimText(original="ABC reported ₹100 Cr profit.", normalized="ABC reported ₹100 Cr profit."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REPORTED_PROFIT",
        object="₹100 Cr"
    )

    doc_a = SourceDocument(
        document_id="DOC-301-A",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="Filing A",
        url="https://nseindia.com/filingA",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content="ABC Net Profit reported as ₹100 Cr for FY2025.",
        content_hash="ha",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    doc_b = SourceDocument(
        document_id="DOC-301-B",
        source_id="bse_corporate_filings",
        organization="BSE",
        source_type="STOCK_EXCHANGE",
        title="Filing B",
        url="https://bseindia.com/filingB",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content="ABC Net Profit reported as ₹120 Cr with conflicting adjustments.",
        content_hash="hb",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="BSEAdapter", mode="FIXTURE")
    )

    cand_a = EvidenceCandidate(
        evidence_id="EVID-301-A",
        claim_id="CLAIM-301",
        source_document_id="DOC-301-A",
        excerpt=doc_a.content,
        relevance=EvidenceRelevance(),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url=doc_a.url),
        verification_status="UNVERIFIED"
    )

    cand_b = EvidenceCandidate(
        evidence_id="EVID-301-B",
        claim_id="CLAIM-301",
        source_document_id="DOC-301-B",
        excerpt=doc_b.content,
        relevance=EvidenceRelevance(),
        source_type="STOCK_EXCHANGE",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="BSEAdapter", source_mode="FIXTURE", source_url=doc_b.url),
        verification_status="UNVERIFIED"
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-301", source_plan=SourcePlan(query=SourceQuery()), documents=[doc_a, doc_b], evidence_candidates=[cand_a, cand_b]))
    assert res.status == "SOURCE_CONFLICT"
    assert any("conflict" in step.lower() or "discrepancy" in step.lower() for step in res.reasoning_trace)


def test_no_evidence_is_insufficient_not_false():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-302",
        source_content_id="c-1",
        text=ClaimText(original="ABC opened a new branch in Tokyo.", normalized="ABC opened a new branch in Tokyo."),
        claim_type="FACTUAL",
        subject="ABC",
        predicate="OPENED_BRANCH",
        object="Tokyo"
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-302", source_plan=SourcePlan(query=SourceQuery()), documents=[], evidence_candidates=[]))
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert res.evidence_strength == "NONE"
    assert not any("false" in step.lower() and "claim is" in step.lower() for step in res.reasoning_trace)


def test_source_unavailable_status():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-303",
        source_content_id="c-1",
        text=ClaimText(original="ABC reported results.", normalized="ABC reported results."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REPORTED_RESULTS",
        object="results"
    )

    doc_unavail = SourceDocument(
        document_id="DOC-303",
        source_id="bse_corporate_filings",
        organization="BSE",
        source_type="STOCK_EXCHANGE",
        title="BSE Filings",
        url="https://bseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at=None,
        content="Interface unconfigured.",
        content_hash="h303",
        metadata={},
        retrieval=RetrievalMetadata(status="SOURCE_UNAVAILABLE", method="BSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-303", source_plan=SourcePlan(query=SourceQuery()), documents=[doc_unavail], evidence_candidates=[]))
    assert res.status == "SOURCE_UNAVAILABLE"

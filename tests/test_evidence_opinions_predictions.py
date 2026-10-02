"""Unit tests for Predictions and Subjective Opinions in Engine 5."""

from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimModality
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument, EvidenceRelevance, EvidenceProvenance, RetrievalMetadata, ClaimSourceResult, SourcePlan, SourceQuery
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator


def test_future_prediction_insufficient_evidence():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-201",
        source_content_id="c-1",
        text=ClaimText(original="ABC will reach ₹500 next year.", normalized="ABC will reach ₹500 next year."),
        claim_type="PREDICTION",
        subject="ABC",
        predicate="REACH_PRICE",
        object="₹500",
        modality=ClaimModality(type="prediction")
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-201",
        claim_id="CLAIM-201",
        source_document_id="DOC-201",
        excerpt="Historical Annual Report: ABC closed at ₹350 at the end of FY2025.",
        relevance=EvidenceRelevance(matched_terms=["ABC"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-201",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Annual Report",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2025-05-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h201",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-201", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert any("future" in step.lower() or "prediction" in step.lower() for step in res.reasoning_trace)
    assert not any("target" in step.lower() and "set to" in step.lower() for step in res.reasoning_trace)


def test_subjective_opinion_not_verifiable():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-202",
        source_content_id="c-1",
        text=ClaimText(original="ABC is the safest investment.", normalized="ABC is the safest investment."),
        claim_type="OPINION",
        subject="ABC",
        predicate="VALUATION_STATUS",
        object="safest investment",
        modality=ClaimModality(type="opinion")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-202", source_plan=SourcePlan(query=SourceQuery(name="ABC")), documents=[], evidence_candidates=[]))
    assert res.status == "NOT_VERIFIABLE"
    assert any("subjective" in step.lower() or "evaluative" in step.lower() for step in res.reasoning_trace)

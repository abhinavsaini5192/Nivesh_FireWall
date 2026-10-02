"""Unit tests for Numerical, Arithmetic, and Context Gap Verification in Engine 5."""

from nivesh.schemas.claims import CanonicalClaim, ClaimText, TemporalContext
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument, EvidenceRelevance, EvidenceProvenance, RetrievalMetadata, ClaimSourceResult, SourcePlan, SourceQuery
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator


def test_numerical_percentage_change_supported():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-101",
        source_content_id="c-1",
        text=ClaimText(original="ABC revenue increased 40%.", normalized="ABC revenue increased 40%."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REVENUE_GROWTH",
        object="40%"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-101",
        claim_id="CLAIM-101",
        source_document_id="DOC-101",
        excerpt="Annual Revenue Comparison: FY2025 = ₹100 Cr, FY2026 = ₹140 Cr. Audited.",
        relevance=EvidenceRelevance(matched_terms=["revenue", "40%"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-101",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Audited Results",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2026-05-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h101",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-101", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    assert res.status == "SUPPORTED"
    assert res.evidence_strength == "HIGH"
    assert len(res.supporting_evidence) == 1
    assert any("40.0%" in step for step in res.reasoning_trace)


def test_numerical_percentage_change_contradicted():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-102",
        source_content_id="c-1",
        text=ClaimText(original="ABC revenue increased 40%.", normalized="ABC revenue increased 40%."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REVENUE_GROWTH",
        object="40%"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-102",
        claim_id="CLAIM-102",
        source_document_id="DOC-102",
        excerpt="Annual Revenue Comparison: FY2025 = ₹100 Cr, FY2026 = ₹120 Cr. Audited.",
        relevance=EvidenceRelevance(matched_terms=["revenue"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-102",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Audited Results",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2026-05-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h102",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-102", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    assert res.status == "CONTRADICTED"
    assert res.evidence_strength == "HIGH"
    assert len(res.contradicting_evidence) == 1
    assert any("20.0%" in step for step in res.reasoning_trace)


def test_numerical_tolerance_rounding():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-103",
        source_content_id="c-1",
        text=ClaimText(original="Revenue grew 40%.", normalized="Revenue grew 40%."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REVENUE_GROWTH",
        object="40%"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-103",
        claim_id="CLAIM-103",
        source_document_id="DOC-103",
        excerpt="The company achieved a 39.8% year-on-year revenue increase.",
        relevance=EvidenceRelevance(matched_terms=["revenue", "increase"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-103",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Results",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2026-05-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h103",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-103", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    # 39.8% is within 0.5% tolerance of claimed 40%
    assert res.status == "SUPPORTED"
    assert any("tolerance" in step for step in res.reasoning_trace)


def test_debt_free_contradiction():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-104",
        source_content_id="c-1",
        text=ClaimText(original="ABC is debt free.", normalized="ABC carries 0 debt."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="HAS_DEBT",
        object="0"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-104",
        claim_id="CLAIM-104",
        source_document_id="DOC-104",
        excerpt="Audited Balance Sheet: Outstanding borrowings as of 31 March: ₹240 crore.",
        relevance=EvidenceRelevance(matched_terms=["borrowings"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-104",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Balance Sheet",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2026-05-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h104",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-104", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    assert res.status == "CONTRADICTED"
    assert len(res.contradicting_evidence) == 1
    assert any("₹240 crore" in step or "borrowings" in step for step in res.reasoning_trace)


def test_partial_support_with_unverified_date():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-105",
        source_content_id="c-1",
        text=ClaimText(original="ABC announced a 1:1 bonus on 1 June.", normalized="ABC announced a 1:1 bonus on 1 June."),
        claim_type="CORPORATE_EVENT",
        subject="ABC",
        predicate="ANNOUNCED_BONUS",
        object="1:1"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-105",
        claim_id="CLAIM-105",
        source_document_id="DOC-105",
        excerpt="NSE CORPORATE ACTION: Company Symbol ABC announced bonus issue ratio 1:1.",
        relevance=EvidenceRelevance(matched_terms=["1:1", "bonus"]),
        source_type="CORPORATE_ACTION",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-105",
        source_id="nse_corporate_actions",
        organization="NSE",
        source_type="CORPORATE_ACTION",
        title="ABC Bonus Filing",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2025-06-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h105",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-105", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    assert res.status == "PARTIALLY_SUPPORTED"
    assert len(res.supporting_evidence) == 1
    assert any("1 June" in elem for elem in res.missing_elements)


def test_context_gaps_on_omitted_reporting_period():
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-106",
        source_content_id="c-1",
        text=ClaimText(original="Profit increased 200%.", normalized="Profit increased 200%."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REPORTED_PROFIT",
        object="200%"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-106",
        claim_id="CLAIM-106",
        source_document_id="DOC-106",
        excerpt="Audited Financial Results: FY2025 Net Profit = ₹10 Cr, FY2026 Net Profit = ₹30 Cr.",
        relevance=EvidenceRelevance(matched_terms=["profit"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-02T12:00:00Z", retrieval_method="NSEAdapter", source_mode="FIXTURE", source_url="https://nseindia.com"),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-106",
        source_id="nse_company_filings",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Profit Filing",
        url="https://nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2026-05-15T00:00:00Z",
        content=candidate.excerpt,
        content_hash="h106",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(claim, ClaimSourceResult(claim_id="CLAIM-106", source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")), documents=[doc], evidence_candidates=[candidate]))
    assert res.status == "SUPPORTED"
    assert len(res.context_gaps) >= 1
    assert any("period" in gap.lower() for gap in res.context_gaps)

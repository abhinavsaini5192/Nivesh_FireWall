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


def test_regulatory_guaranteed_return_statutory_prohibition_conflict():
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
    assert res.status != "CONTRADICTED"
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert res.evidence_strength == "HIGH"
    assert len(res.supporting_evidence) == 0
    assert len(res.contradicting_evidence) == 0
    assert len(res.regulatory_findings) == 1
    rf = res.regulatory_findings[0]
    assert rf.type == "REGULATORY_CONFLICT"
    assert rf.source_document_id == "DOC-003"
    assert rf.source_url == "https://www.sebi.gov.in"
    assert rf.organization == "REGULATOR"
    assert rf.retrieved_at == "2026-10-02T12:00:00Z"
    assert any("prohibit" in step.lower() for step in res.reasoning_trace)


def test_regression_regulatory_prohibition_is_not_factual_contradiction():
    """Test 1: Regulatory prohibition is not factual contradiction."""
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-REG-01",
        source_content_id="c-1",
        text=ClaimText(original="40% returns are guaranteed.", normalized="40% returns are guaranteed."),
        claim_type="FINANCIAL",
        subject="unspecified_offer",
        predicate="GUARANTEED_RETURN",
        object="40% returns"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-REG-01",
        claim_id="CLAIM-REG-01",
        source_document_id="DOC-REG-01",
        excerpt="Covered intermediaries are prohibited from guaranteeing returns in securities market.",
        relevance=EvidenceRelevance(matched_terms=["prohibited", "guaranteeing"]),
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
        document_id="DOC-REG-01",
        source_id="sebi_rules",
        organization="SEBI",
        source_type="REGULATOR",
        title="SEBI Prohibition",
        url="https://www.sebi.gov.in",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2020-09-23T00:00:00Z",
        content=candidate.excerpt,
        content_hash="hreg01",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="SEBIAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(
        claim,
        ClaimSourceResult(
            claim_id="CLAIM-REG-01",
            source_plan=SourcePlan(query=SourceQuery(keywords=["prohibited"])),
            documents=[doc],
            evidence_candidates=[candidate]
        )
    )

    assert res.status != "CONTRADICTED"
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert any(rf.type == "REGULATORY_CONFLICT" for rf in res.regulatory_findings)


def test_regression_direct_factual_contradiction_still_works():
    """Test 2: Direct factual contradiction still works."""
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-FACT-01",
        source_content_id="c-1",
        text=ClaimText(original="ABC is debt free.", normalized="ABC is debt free."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="HAS_DEBT",
        object="debt free"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-FACT-01",
        claim_id="CLAIM-FACT-01",
        source_document_id="DOC-FACT-01",
        excerpt="Balance Sheet: Outstanding borrowings as of 31 March: ₹240 crore.",
        relevance=EvidenceRelevance(matched_terms=["borrowings"]),
        source_type="FINANCIAL_FILING",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(
            retrieved_at="2026-10-02T12:00:00Z",
            retrieval_method="NSEAdapter",
            source_mode="FIXTURE",
            source_url="https://www.nseindia.com"
        ),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-FACT-01",
        source_id="nse_filing",
        organization="NSE",
        source_type="FINANCIAL_FILING",
        title="ABC Annual Report",
        url="https://www.nseindia.com",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2026-03-31T00:00:00Z",
        content=candidate.excerpt,
        content_hash="hfact01",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(
        claim,
        ClaimSourceResult(
            claim_id="CLAIM-FACT-01",
            source_plan=SourcePlan(query=SourceQuery(company_symbol="ABC")),
            documents=[doc],
            evidence_candidates=[candidate]
        )
    )

    assert res.status == "CONTRADICTED"
    assert len(res.contradicting_evidence) >= 1
    assert "borrowings" in res.contradicting_evidence[0].excerpt.lower()


def test_regression_regulatory_finding_preserves_provenance():
    """Test 3: Regulatory finding preserves provenance."""
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLAIM-PROV-01",
        source_content_id="c-1",
        text=ClaimText(original="Guaranteed 40% returns.", normalized="40% returns are guaranteed."),
        claim_type="FINANCIAL",
        subject="unspecified_offer",
        predicate="GUARANTEED_RETURN",
        object="40% returns"
    )

    candidate = EvidenceCandidate(
        evidence_id="EVID-PROV-01",
        claim_id="CLAIM-PROV-01",
        source_document_id="DOC-PROV-01",
        excerpt="SEBI Prohibition: No intermediary shall guarantee returns.",
        relevance=EvidenceRelevance(matched_terms=["guarantee"]),
        source_type="REGULATOR",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(
            retrieved_at="2026-10-02T12:00:00Z",
            retrieval_method="SEBIAdapter",
            source_mode="FIXTURE",
            source_url="https://www.sebi.gov.in/rules"
        ),
        verification_status="UNVERIFIED"
    )

    doc = SourceDocument(
        document_id="DOC-PROV-01",
        source_id="sebi_circular",
        organization="SEBI",
        source_type="REGULATOR",
        title="SEBI Circular",
        url="https://www.sebi.gov.in/rules",
        retrieved_at="2026-10-02T12:00:00Z",
        published_at="2020-09-23T00:00:00Z",
        content=candidate.excerpt,
        content_hash="hprov01",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="SEBIAdapter", mode="FIXTURE")
    )

    res = evaluator.evaluate(
        claim,
        ClaimSourceResult(
            claim_id="CLAIM-PROV-01",
            source_plan=SourcePlan(query=SourceQuery(keywords=["guarantee"])),
            documents=[doc],
            evidence_candidates=[candidate]
        )
    )

    assert len(res.regulatory_findings) == 1
    rf = res.regulatory_findings[0]
    assert rf.source_document_id == "DOC-PROV-01"
    assert rf.source_url == "https://www.sebi.gov.in/rules"
    assert rf.organization == "REGULATOR"
    assert rf.excerpt == "SEBI Prohibition: No intermediary shall guarantee returns."
    assert rf.retrieved_at == "2026-10-02T12:00:00Z"

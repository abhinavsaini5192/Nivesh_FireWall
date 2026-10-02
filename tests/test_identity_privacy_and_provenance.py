"""Privacy, Provenance, and Determinism Tests for Engine 9."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import IdentityFindingType
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourcePlan,
    SourceQuery,
    SourceDocument,
    RetrievalMetadata,
    SourceAnalysisMetadata,
)


def test_privacy_boundaries_no_credentials():
    """Verify that credentials, OTP, and sensitive financial credentials are not stored in outputs."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    sensitive_text = (
        "Advisor Rahul Sharma says: Enter OTP 482910 and password secretPass123 to verify account. "
        "Bank account 123456789012 at HDFC Bank."
    )
    content = ce.process_text(sensitive_text)
    claims = cl.analyze(content)

    analysis = ie.verify(content=content, claims=claims)
    dumped = analysis.model_dump_json()

    assert "482910" not in dumped
    assert "secretPass123" not in dumped
    assert "123456789012" not in dumped


def test_provenance_integrity_across_findings():
    """Verify that every identity finding connects to source/evidence references."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    raw_text = "SEBI registered advisor Rahul Sharma (Registration INH000009999)."
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)

    doc = SourceDocument(
        document_id="DOC-PROV-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Registry Document",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content="SEBI registration INH000009999 belongs to Alpha Wealth Advisors Private Limited, not Rahul Sharma.",
        content_hash="hash_p1",
        metadata={"legal_name": "Alpha Wealth Advisors Private Limited", "registration_number": "INH000009999"},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id=claims.claims[0].claim_id,
        source_plan=SourcePlan(query=SourceQuery(registration_number="INH000009999")),
        documents=[doc],
    )
    sources = SourceAnalysis(
        content_id=content.content_id,
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=1),
    )

    analysis = ie.verify(content=content, claims=claims, sources=sources)

    # All mismatch findings have valid source document IDs
    mismatch_findings = [f for f in analysis.identity_findings if f.finding_type == IdentityFindingType.REGISTRATION_ENTITY_MISMATCH]
    assert len(mismatch_findings) >= 1
    for f in mismatch_findings:
        assert "DOC-PROV-01" in f.source_ids

    # Provenance object integrity
    assert analysis.provenance.input_content_id == content.content_id
    assert analysis.provenance.source_document_count == 1
    assert "DOC-PROV-01" in analysis.upstream_references["source_ids"]


def test_determinism():
    """Verify that identical inputs produce identical identity results."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie1 = IdentityVerificationEngine()
    ie2 = IdentityVerificationEngine()

    raw_text = "SEBI registered broker ABC Securities Private Limited. Visit https://abcsecurities.com"
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)

    doc = SourceDocument(
        document_id="DOC-DET-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Registry Document",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Legal Name: ABC Securities Private Limited\nRegistration Number: INZ00012345\nOfficial Website: https://abcsecurities.com",
        content_hash="hash_det",
        metadata={"legal_name": "ABC Securities Private Limited", "registration_number": "INZ00012345", "official_domain": "abcsecurities.com"},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id=claims.claims[0].claim_id,
        source_plan=SourcePlan(query=SourceQuery(name="ABC Securities")),
        documents=[doc],
    )
    sources = SourceAnalysis(
        content_id=content.content_id,
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=1),
    )

    res1 = ie1.verify(content=content, claims=claims, sources=sources)
    res2 = ie2.verify(content=content, claims=claims, sources=sources)

    assert res1.identity_status == res2.identity_status
    assert res1.confidence == res2.confidence
    assert len(res1.identity_matches) == len(res2.identity_matches)
    assert len(res1.identity_findings) == len(res2.identity_findings)

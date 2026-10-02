"""Negative Cases and Safety Boundaries for Engine 9.

Explicitly verifies:
1. registry NO_MATCH != IDENTITY_MISMATCH
2. unknown domain != malicious domain
3. name similarity != same person
4. same brand keyword != official ownership
5. authority claim != authority impersonation
"""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import (
    IdentityStatus,
    IdentityMatchStatus,
    IdentityFindingType,
)
from nivesh.identity.normalizer import IdentityNormalizer
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourcePlan,
    SourceQuery,
    SourceDocument,
    RetrievalMetadata,
    SourceAnalysisMetadata,
)


def test_registry_no_match_is_not_mismatch():
    """Verify: registry NO_MATCH != IDENTITY_MISMATCH (Must be NOT_ESTABLISHED)."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    content = ce.process_text("SEBI registered advisor Rahul Sharma offers market tips.")
    claims = cl.analyze(content)

    doc = SourceDocument(
        document_id="DOC-NEG-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="Registry Search",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Query: 'Rahul Sharma'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND",
        content_hash="h1",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id=claims.claims[0].claim_id,
        source_plan=SourcePlan(query=SourceQuery(name="Rahul Sharma")),
        documents=[doc],
    )
    sources = SourceAnalysis(
        content_id=content.content_id,
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=1),
    )

    analysis = ie.verify(content=content, claims=claims, sources=sources)

    # Must be NOT_ESTABLISHED, strictly NEVER IDENTITY_MISMATCH
    assert analysis.identity_status == IdentityStatus.NOT_ESTABLISHED
    assert analysis.identity_status != IdentityStatus.IDENTITY_MISMATCH
    for match in analysis.identity_matches:
        assert match.match_status != IdentityMatchStatus.IDENTITY_MISMATCH


def test_unknown_domain_is_not_malicious():
    """Verify: unknown domain != malicious domain (Must be NOT_ESTABLISHED)."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    content = ce.process_text("Check financial reports at https://market-data-today.in/overview")
    claims = cl.analyze(content)

    analysis = ie.verify(content=content, claims=claims)

    assert analysis.domain_alignments[0].alignment_status == "NOT_ESTABLISHED"
    # Verify description is non-accusatory
    domain_findings = [f for f in analysis.identity_findings if f.finding_type == IdentityFindingType.DOMAIN_ALIGNMENT_NOT_ESTABLISHED]
    assert len(domain_findings) >= 1
    assert "not automatically malicious" in domain_findings[0].description


def test_name_similarity_is_not_same_person():
    """Verify: name similarity != same person (Rahul Sharma != Rahul K Sharma)."""
    norm1 = IdentityNormalizer.normalize_person_name("Rahul Sharma")
    norm2 = IdentityNormalizer.normalize_person_name("Rahul K Sharma")
    norm3 = IdentityNormalizer.normalize_person_name("Rahul Kumar Sharma")

    assert norm1 != norm2
    assert norm2 != norm3
    assert norm1 != norm3


def test_brand_keyword_is_not_official_ownership():
    """Verify: same brand keyword in domain != official ownership."""
    ce = ContentIntelligenceEngine()
    ie = IdentityVerificationEngine()

    content = ce.process_text("Official ABC Securities portal at https://abc-securities-portal.com")
    analysis = ie.verify(content=content)

    # Without authoritative evidence, domain is NOT established
    domain_align = analysis.domain_alignments[0]
    assert domain_align.alignment_status == "NOT_ESTABLISHED"


def test_authority_claim_is_not_authority_impersonation():
    """Verify: authority claim != authority impersonation."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    # Claiming to be registered with SEBI is an AUTHORITY_CLAIM, not impersonation of SEBI
    content = ce.process_text("SEBI registered advisor Rahul Sharma.")
    claims = cl.analyze(content)
    analysis = ie.verify(content=content, claims=claims)

    finding_types = [f.finding_type for f in analysis.identity_findings]
    assert IdentityFindingType.AUTHORITY_CLAIM in finding_types
    assert IdentityFindingType.AUTHORITY_IDENTITY_MISMATCH not in finding_types

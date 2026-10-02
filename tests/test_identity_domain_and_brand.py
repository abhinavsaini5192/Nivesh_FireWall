"""Unit tests for Domain and Brand Alignment in Engine 9."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.identity.schemas import (
    ClaimedEntity,
    ResolvedEntity,
    IdentityEntityType,
    IdentityMatchStatus,
    IdentityFindingType,
)
from nivesh.identity.domain_resolver import DomainResolver
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourcePlan,
    SourceQuery,
    SourceDocument,
    RetrievalMetadata,
    SourceAnalysisMetadata,
)


def _make_sources_with_domain(legal_name: str, official_domain: str) -> SourceAnalysis:
    doc = SourceDocument(
        document_id="DOC-DOM-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title=f"Record: {legal_name}",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content=f"Legal Name: {legal_name}\nOfficial Website: https://{official_domain}",
        content_hash="hash_dom_01",
        metadata={"legal_name": legal_name, "official_domain": official_domain},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id="CLM-001",
        source_plan=SourcePlan(query=SourceQuery(company_name=legal_name)),
        documents=[doc],
    )
    return SourceAnalysis(
        content_id="CNT-001",
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=1),
    )


def test_official_domain_alignment_established():
    """Verify that observed domain matching official registry record yields ALIGNED."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("Visit our official portal: https://www.abcsecurities.com/invest?ref=10")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="ABC Securities",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_domain="abcsecurities.com",
    )
    candidate = ResolvedEntity(
        candidate_id="CAND-001",
        legal_name="ABC Securities Limited",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        official_domain="abcsecurities.com",
    )
    sources = _make_sources_with_domain("ABC Securities Limited", "abcsecurities.com")

    alignments, findings = DomainResolver.resolve_domains(
        content=content,
        claimed_entities=[entity],
        candidate_entities=[candidate],
        sources=sources,
    )

    assert len(alignments) == 1
    assert alignments[0].alignment_status == "ALIGNED"
    assert alignments[0].authoritative_domain == "abcsecurities.com"
    assert len(findings) == 1
    assert findings[0]["finding_type"] == IdentityFindingType.DOMAIN_ALIGNMENT_ESTABLISHED
    assert findings[0]["status"] == IdentityMatchStatus.ESTABLISHED


def test_domain_identity_mismatch():
    """Verify that lookalike or different domain when official domain is on record yields MISMATCH."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("Official ABC Securities portal: https://abc-securities-portal.com/login")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="ABC Securities",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_domain="abc-securities-portal.com",
    )
    candidate = ResolvedEntity(
        candidate_id="CAND-001",
        legal_name="ABC Securities Limited",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        official_domain="abcsecurities.com",
    )
    sources = _make_sources_with_domain("ABC Securities Limited", "abcsecurities.com")

    alignments, findings = DomainResolver.resolve_domains(
        content=content,
        claimed_entities=[entity],
        candidate_entities=[candidate],
        sources=sources,
    )

    assert len(alignments) == 1
    assert alignments[0].alignment_status == "MISMATCH"
    assert alignments[0].authoritative_domain == "abcsecurities.com"
    assert len(findings) == 1
    assert findings[0]["finding_type"] == IdentityFindingType.DOMAIN_IDENTITY_MISMATCH
    assert findings[0]["status"] == IdentityMatchStatus.IDENTITY_MISMATCH


def test_unknown_domain_not_established_and_not_malicious():
    """Verify that an unrecognized domain yields NOT_ESTABLISHED and does NOT declare malice."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("Read our report at https://fintech-blog-analysis.org/market")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="Fintech Blog",
        normalized_name="fintech blog",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_domain="fintech-blog-analysis.org",
    )

    alignments, findings = DomainResolver.resolve_domains(
        content=content,
        claimed_entities=[entity],
        candidate_entities=[],
        sources=None,
    )

    assert len(alignments) == 1
    assert alignments[0].alignment_status == "NOT_ESTABLISHED"
    assert alignments[0].authoritative_domain is None
    assert len(findings) == 1
    assert findings[0]["finding_type"] == IdentityFindingType.DOMAIN_ALIGNMENT_NOT_ESTABLISHED
    assert "not automatically malicious" in findings[0]["description"]

"""Unit tests for Authority and Social Channel Resolution in Engine 9."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.identity.schemas import (
    ClaimedEntity,
    IdentityEntityType,
    IdentityMatchStatus,
    IdentityFindingType,
)
from nivesh.identity.authority_resolver import AuthorityResolver
from nivesh.identity.social_resolver import SocialResolver
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourcePlan,
    SourceQuery,
    SourceDocument,
    RetrievalMetadata,
    SourceAnalysisMetadata,
)


def test_regulatory_authority_claim_vs_not_established():
    """Verify that referencing SEBI produces AUTHORITY_CLAIM and AUTHORITY_IDENTITY_NOT_ESTABLISHED when unverified."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("SEBI registered advisor Rahul Sharma offers investment ideas.")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
    )
    reg_records = [{
        "entity": entity,
        "status": IdentityMatchStatus.NOT_ESTABLISHED,
        "finding_type": IdentityFindingType.REGISTRATION_IDENTIFIER_UNRESOLVED,
    }]

    alignments, findings = AuthorityResolver.resolve_authorities(
        content=content,
        claims=None,
        claimed_entities=[entity],
        candidate_entities=[],
        registration_records=reg_records,
    )

    assert len(alignments) >= 1
    sebi_alignment = next(a for a in alignments if a.authority_name == "SEBI")
    assert sebi_alignment.alignment_status == "NOT_ESTABLISHED"

    finding_types = [f["finding_type"] for f in findings]
    assert IdentityFindingType.AUTHORITY_CLAIM in finding_types
    assert IdentityFindingType.AUTHORITY_IDENTITY_NOT_ESTABLISHED in finding_types


def test_regulator_direct_impersonation_mismatch():
    """Verify that an entity purporting to be SEBI itself yields AUTHORITY_IDENTITY_MISMATCH."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("SEBI Official Support Helpdesk. Pay fine of ₹10,000.")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="SEBI",
        normalized_name="sebi",
        entity_type=IdentityEntityType.ORGANIZATION,  # Claimed as an organization, not verified regulator
    )

    alignments, findings = AuthorityResolver.resolve_authorities(
        content=content,
        claims=None,
        claimed_entities=[entity],
        candidate_entities=[],
        registration_records=[],
    )

    sebi_align = next(a for a in alignments if a.authority_name == "SEBI")
    assert sebi_align.alignment_status == "MISMATCH"

    finding_types = [f["finding_type"] for f in findings]
    assert IdentityFindingType.AUTHORITY_IDENTITY_MISMATCH in finding_types


def test_social_channel_not_established():
    """Verify that matching social handle (@abcsecurities_official) does NOT assume ownership."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("Join our Telegram: https://t.me/abcsecurities_official for daily stock tips.")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="ABC Securities",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_channel="telegram:abcsecurities_official",
    )

    findings = SocialResolver.resolve_social_channels(
        content=content,
        claimed_entities=[entity],
        candidate_entities=[],
        sources=None,
    )

    assert len(findings) == 1
    assert findings[0]["status"] == IdentityMatchStatus.NOT_ESTABLISHED
    assert findings[0]["finding_type"] == IdentityFindingType.SOCIAL_ACCOUNT_NOT_ESTABLISHED
    assert "matching username does not establish official ownership" in findings[0]["description"]


def test_social_channel_officially_attested():
    """Verify that social handle confirmed in registry source records yields ESTABLISHED."""
    ce = ContentIntelligenceEngine()
    content = ce.process_text("Contact our desk on Telegram: https://t.me/abcsecurities_desk")

    entity = ClaimedEntity(
        entity_id="ENT-001",
        name="ABC Securities",
        normalized_name="abc securities",
        entity_type=IdentityEntityType.ORGANIZATION,
        associated_channel="telegram:abcsecurities_desk",
    )

    doc = SourceDocument(
        document_id="DOC-SOC-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="ABC Securities Registry Detail",
        url="https://sebi.gov.in/registry",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Official Telegram: @abcsecurities_desk",
        content_hash="soc_hash",
        metadata={
            "legal_name": "ABC Securities Limited",
            "social_handles": ["telegram:@abcsecurities_desk"],
        },
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id="CLM-001",
        source_plan=SourcePlan(query=SourceQuery(name="ABC Securities")),
        documents=[doc],
    )
    sources = SourceAnalysis(
        content_id="CNT-001",
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=1),
    )

    findings = SocialResolver.resolve_social_channels(
        content=content,
        claimed_entities=[entity],
        candidate_entities=[],
        sources=sources,
    )

    assert len(findings) == 1
    assert findings[0]["status"] == IdentityMatchStatus.ESTABLISHED
    assert findings[0]["finding_type"] == IdentityFindingType.IDENTITY_ESTABLISHED

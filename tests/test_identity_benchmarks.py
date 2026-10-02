"""Core Benchmarks for Engine 9: Identity Verification & Entity Resolution.

Tests:
1. Primary Benchmark (Rahul Sharma SEBI registered advisor -> IDENTITY_NOT_ESTABLISHED)
2. Positive Benchmark (Verified legal entity + registration + domain -> ESTABLISHED)
3. Mismatch Benchmark (Registration belongs to different entity -> IDENTITY_MISMATCH)
4. Ambiguous Benchmark (Multiple plausible candidates -> AMBIGUOUS)
"""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import (
    IdentityStatus,
    IdentityMatchStatus,
    IdentityFindingType,
)
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourcePlan,
    SourceQuery,
    SourceDocument,
    RetrievalMetadata,
    SourceAnalysisMetadata,
)
from nivesh.schemas.evidence import (
    EvidenceAnalysis,
    VerificationResult,
    VerificationProvenance,
    EvidenceAnalysisMetadata,
)


def test_primary_benchmark_identity_not_established():
    """Primary benchmark: Unregistered advisor asserting SEBI registration.
    
    Content:
    'SEBI registered advisor Rahul Sharma. Guaranteed 40% returns.
     Join our Telegram VIP group. Download our app and pay ₹5,000.'
    
    Expected:
    IDENTITY_NOT_ESTABLISHED (NOT IDENTITY_MISMATCH, because registry returned 0 matches).
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    raw_text = (
        "SEBI registered advisor Rahul Sharma. Guaranteed 40% returns. "
        "Join our Telegram VIP group. Download our app and pay ₹5,000."
    )
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)

    # Official SEBI registry search returns 0 matches for Rahul Sharma
    doc = SourceDocument(
        document_id="DOC-PRI-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Intermediary Registry Search: Rahul Sharma",
        url="https://sebi.gov.in/intermediaries",
        retrieved_at="2026-10-02T12:00:00Z",
        content="SEBI RECOGNISED INTERMEDIARY DATABASE SEARCH RESULT\nQuery: 'Rahul Sharma'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND",
        content_hash="pri_hash_01",
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

    # Verification of Primary Benchmark requirements
    assert analysis.identity_status == IdentityStatus.NOT_ESTABLISHED
    assert analysis.identity_status != IdentityStatus.IDENTITY_MISMATCH

    rahul_entity = next((e for e in analysis.entities if "rahul" in e.normalized_name), None)
    assert rahul_entity is not None
    assert rahul_entity.entity_type.value == "ADVISER"

    # Authority alignment evaluated
    sebi_align = next((a for a in analysis.authority_alignments if a.authority_name == "SEBI"), None)
    assert sebi_align is not None
    assert sebi_align.alignment_status == "NOT_ESTABLISHED"


def test_positive_benchmark_established():
    """Positive benchmark: Fully verified legal entity with matching registration and domain.
    
    Expected:
    ESTABLISHED with high confidence (>= 0.95).
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    raw_text = (
        "ABC Securities Private Limited is a SEBI registered broker (Registration: INZ00012345). "
        "Visit our official portal at https://www.abcsecurities.com for services."
    )
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)

    doc = SourceDocument(
        document_id="DOC-POS-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Registry Record: ABC Securities Private Limited",
        url="https://sebi.gov.in/registry/inz00012345",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Legal Name: ABC Securities Private Limited\nRegistration Number: INZ00012345\nOfficial Website: https://abcsecurities.com",
        content_hash="pos_hash_01",
        metadata={
            "legal_name": "ABC Securities Private Limited",
            "registration_number": "INZ00012345",
            "official_domain": "abcsecurities.com",
        },
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id=claims.claims[0].claim_id,
        source_plan=SourcePlan(query=SourceQuery(name="ABC Securities", registration_number="INZ00012345")),
        documents=[doc],
    )
    sources = SourceAnalysis(
        content_id=content.content_id,
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=1),
    )

    analysis = ie.verify(content=content, claims=claims, sources=sources)

    # Verification of Positive Benchmark requirements
    assert analysis.identity_status == IdentityStatus.ESTABLISHED
    assert analysis.confidence >= 0.95
    assert len(analysis.identity_matches) >= 1
    primary_match = analysis.identity_matches[0]
    assert primary_match.match_status == IdentityMatchStatus.ESTABLISHED
    assert "legal_name" in primary_match.matching_attributes
    assert "registration_number" in primary_match.matching_attributes


def test_mismatch_benchmark_identity_mismatch():
    """Mismatch benchmark: Claim asserts registration number belonging to another entity.
    
    Content claims: Rahul Sharma, registration INH000009999.
    Registry shows: INH000009999 belongs to Alpha Wealth Advisors Private Limited, not Rahul Sharma.
    
    Expected:
    IDENTITY_MISMATCH with REGISTRATION_ENTITY_MISMATCH.
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    raw_text = "SEBI registered advisor Rahul Sharma (Registration INH000009999)."
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)

    doc = SourceDocument(
        document_id="DOC-MIS-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Registry Record: INH000009999",
        url="https://sebi.gov.in/registry/inh000009999",
        retrieved_at="2026-10-02T12:00:00Z",
        content="SEBI registration INH000009999 belongs to Alpha Wealth Advisors Private Limited, not Rahul Sharma.",
        content_hash="mis_hash_01",
        metadata={
            "legal_name": "Alpha Wealth Advisors Private Limited",
            "registration_number": "INH000009999",
        },
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

    # Verification of Mismatch Benchmark requirements
    assert analysis.identity_status == IdentityStatus.IDENTITY_MISMATCH
    mismatch_findings = [f for f in analysis.identity_findings if f.finding_type == IdentityFindingType.REGISTRATION_ENTITY_MISMATCH]
    assert len(mismatch_findings) >= 1
    assert "Alpha Wealth Advisors" in mismatch_findings[0].basis


def test_ambiguous_benchmark():
    """Ambiguous benchmark: Multiple plausible authoritative entities exist without distinguishing data.
    
    Expected:
    AMBIGUOUS (System must not arbitrarily pick one).
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ie = IdentityVerificationEngine()

    raw_text = "SEBI registered advisor Amit Patel offers equity strategies."
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)

    # Two distinct registry documents matching Amit Patel
    doc1 = SourceDocument(
        document_id="DOC-AMB-01",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Record 1",
        url="https://sebi.gov.in/registry/1",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Entity Legal Name: Amit Patel\nRegistration Number: INA000011111\nState: Gujarat",
        content_hash="amb_hash_01",
        metadata={"legal_name": "Amit Patel", "registration_number": "INA000011111"},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    doc2 = SourceDocument(
        document_id="DOC-AMB-02",
        source_id="sebi_registry",
        organization="SEBI",
        source_type="REGULATORY_REGISTRY",
        title="SEBI Record 2",
        url="https://sebi.gov.in/registry/2",
        retrieved_at="2026-10-02T12:00:00Z",
        content="Entity Legal Name: Amit Patel\nRegistration Number: INA000022222\nState: Maharashtra",
        content_hash="amb_hash_02",
        metadata={"legal_name": "Amit Patel", "registration_number": "INA000022222"},
        retrieval=RetrievalMetadata(status="SUCCESS", method="fixture", mode="FIXTURE"),
    )
    csr = ClaimSourceResult(
        claim_id=claims.claims[0].claim_id,
        source_plan=SourcePlan(query=SourceQuery(name="Amit Patel")),
        documents=[doc1, doc2],
    )
    sources = SourceAnalysis(
        content_id=content.content_id,
        claim_sources=[csr],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, documents_retrieved=2),
    )

    analysis = ie.verify(content=content, claims=claims, sources=sources)

    # Verification of Ambiguous Benchmark requirements
    assert analysis.identity_status == IdentityStatus.AMBIGUOUS
    amb_findings = [f for f in analysis.identity_findings if f.finding_type == IdentityFindingType.IDENTITY_AMBIGUOUS]
    assert len(amb_findings) >= 1
    assert "Multiple authoritative records found" in amb_findings[0].basis

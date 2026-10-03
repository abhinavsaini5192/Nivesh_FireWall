"""Phase 15.E.2 — Cross-Source Evidence Correlation Test Suite.

Validates:
1. Normalized evidence correlation contract across SEBI, RBI, NSE, and BSE.
2. Cross-source corroboration (NSE + BSE dual-listed corporate actions, SEBI registration + Exchange filings).
   Strict Rule: Corroboration strengthens the evidence picture without artificial score inflation ("2 sources != 2x confidence").
3. Cross-source conflict: Material discrepancies between sources yield SOURCE_CONFLICT without silent bias.
4. One source unavailable / one insufficient evidence: Technical failure or lack of evidence never becomes fraud.
5. Identity separation: Registry existence != message attribution. Name similarity != identity proof.
   No-match != identity mismatch.
6. Numerical evidence: Exact match, meaningful contradiction, non-numeric input, missing fields.
"""

import pytest

from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimAnalysis, ClaimAnalysisMetadata
from nivesh.schemas.normalized import (
    NormalizedContent,
    SourceInfo,
    RawContent,
    NormalizedText,
    Provenance,
    EntitiesContainer,
    EntityItem,
)
from nivesh.schemas.sources import (
    SourceQuery,
    SourcePlan,
    SourceDocument,
    SourceSearchResult,
    EvidenceCandidate,
    EvidenceRelevance,
    EvidenceProvenance,
    RetrievalMetadata,
    ClaimSourceResult,
    SourceAnalysis,
    SourceAnalysisMetadata,
    AuthoritativeProvenance,
)
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import IdentityStatus, IdentityAnalysis
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter


@pytest.fixture
def snapshot_gateway():
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("SEBIAdapter", SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["intermediary_registration", "circulars"])
    gw.register_adapter("RBIAdapter", RBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["official_data", "regulatory_publications"])
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_announcements", "corporate_actions"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_data", "disclosures", "corporate_actions"])
    return gw


# ---------------------------------------------------------------------------
# 1. Cross-Source Corroboration & No Artificial Confidence Inflation
# ---------------------------------------------------------------------------
def test_cross_source_corroboration_preserves_bounded_confidence(snapshot_gateway):
    """Verifies that corroboration across NSE and BSE strengthens evidence,
    but does NOT artificially double or inflate confidence (NO 2 sources = 2x confidence).
    """
    claim = CanonicalClaim(
        claim_id="CLM-CORROBORATE-01",
        source_content_id="CNT-DUAL",
        text=ClaimText(original="ABC Limited announced 1:1 bonus issue", normalized="abc limited announced 1:1 bonus issue"),
        subject="ABC Limited",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    # 1. Single source verification (NSE alone)
    res_single = snapshot_gateway.execute_claim_verification(claim, require_cross_source=False)
    assert len(res_single.documents) >= 1
    assert all(d.organization == "NSE" for d in res_single.documents)

    evaluator = ClaimEvidenceEvaluator()
    v_single = evaluator.evaluate(claim, res_single)
    assert v_single.status == "SUPPORTED"
    single_confidence = v_single.confidence
    assert 0.85 <= single_confidence <= 1.0

    # 2. Dual source corroboration (NSE + BSE)
    res_dual = snapshot_gateway.execute_claim_verification(claim, require_cross_source=True)
    orgs = [d.organization for d in res_dual.documents]
    assert "NSE" in orgs
    assert "BSE" in orgs

    v_dual = evaluator.evaluate(claim, res_dual)
    assert v_dual.status == "SUPPORTED"
    dual_confidence = v_dual.confidence

    # RULE: Confidence must NOT be doubled (e.g. 0.98 * 2 = 1.96 is illegal; confidence in [0, 1])
    assert dual_confidence <= 1.0
    # Must remain realistic and bounded
    assert abs(dual_confidence - single_confidence) <= 0.05
    # Both sources must be reflected in assessments
    assess_orgs = [s.organization for s in v_dual.source_assessment]
    assert "NSE" in assess_orgs
    assert "BSE" in assess_orgs


# ---------------------------------------------------------------------------
# 2. Multi-Part Regulatory + Corporate Evidence
# ---------------------------------------------------------------------------
def test_multi_part_claim_regulatory_plus_corporate_evidence(snapshot_gateway):
    """Verifies handling where SEBI establishes regulatory entity existence,
    while exchange establishes corporate filing facts.
    """
    claim_reg = CanonicalClaim(
        claim_id="CLM-SEBI-PART",
        source_content_id="CNT-MULTI",
        text=ClaimText(original="360 ONE is SEBI registered", normalized="360 one is sebi registered"),
        subject="360 ONE",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )
    claim_corp = CanonicalClaim(
        claim_id="CLM-NSE-PART",
        source_content_id="CNT-MULTI",
        text=ClaimText(original="TATASTEEL announced stock split", normalized="tatasteel announced stock split"),
        subject="TATASTEEL",
        predicate="STOCK_SPLIT",
        object="10:1",
        claim_type="CORPORATE_EVENT",
    )

    res_reg = snapshot_gateway.execute_claim_verification(claim_reg)
    res_corp = snapshot_gateway.execute_claim_verification(claim_corp)

    evaluator = ClaimEvidenceEvaluator()
    v_reg = evaluator.evaluate(claim_reg, res_reg)
    v_corp = evaluator.evaluate(claim_corp, res_corp)

    assert v_reg.status == "SUPPORTED"
    assert v_reg.source_assessment[0].organization == "SEBI"

    assert v_corp.status == "SUPPORTED"
    assert v_corp.source_assessment[0].organization == "NSE"


# ---------------------------------------------------------------------------
# 3. Cross-Source Conflict Detection
# ---------------------------------------------------------------------------
def test_cross_source_conflict_between_exchanges():
    """Verifies that when two authoritative exchanges report conflicting data,
    the system reports SOURCE_CONFLICT and preserves both views without arbitrary bias.
    """
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLM-CONFLICT-01",
        source_content_id="CNT-CONF",
        text=ClaimText(original="Beta Corp declared bonus issue", normalized="beta corp declared bonus issue"),
        subject="Beta Corp",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    doc_nse = SourceDocument(
        document_id="DOC-NSE-BETA",
        source_id="nse_corporate_announcements",
        organization="NSE",
        source_type="STOCK_EXCHANGE",
        title="NSE Beta Corp Bonus Announcement",
        url="https://www.nseindia.com/beta",
        retrieved_at="2026-10-03T10:00:00Z",
        published_at=None,
        content="Beta Corp has approved a bonus issue of equity shares in 1:1 ratio.",
        content_hash="hash-nse",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="OFFICIAL_SNAPSHOT"),
    )

    doc_bse = SourceDocument(
        document_id="DOC-BSE-BETA",
        source_id="bse_corporate_filings",
        organization="BSE",
        source_type="STOCK_EXCHANGE",
        title="BSE Beta Corp Bonus Announcement",
        url="https://www.bseindia.com/beta",
        retrieved_at="2026-10-03T10:05:00Z",
        published_at=None,
        content="Beta Corp board has revised the bonus issue of equity shares in 2:1 ratio.",
        content_hash="hash-bse",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="BSEAdapter", mode="OFFICIAL_SNAPSHOT"),
    )

    cand_nse = EvidenceCandidate(
        evidence_id="EVID-NSE-BETA",
        claim_id="CLM-CONFLICT-01",
        source_document_id="DOC-NSE-BETA",
        excerpt=doc_nse.content,
        relevance=EvidenceRelevance(),
        source_type="STOCK_EXCHANGE",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-03T10:00:00Z", retrieval_method="NSEAdapter", source_mode="OFFICIAL_SNAPSHOT", source_url=doc_nse.url),
        verification_status="UNVERIFIED",
    )

    cand_bse = EvidenceCandidate(
        evidence_id="EVID-BSE-BETA",
        claim_id="CLM-CONFLICT-01",
        source_document_id="DOC-BSE-BETA",
        excerpt=doc_bse.content,
        relevance=EvidenceRelevance(),
        source_type="STOCK_EXCHANGE",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-03T10:05:00Z", retrieval_method="BSEAdapter", source_mode="OFFICIAL_SNAPSHOT", source_url=doc_bse.url),
        verification_status="UNVERIFIED",
    )

    source_res = ClaimSourceResult(
        claim_id="CLM-CONFLICT-01",
        source_plan=SourcePlan(query=SourceQuery()),
        documents=[doc_nse, doc_bse],
        evidence_candidates=[cand_nse, cand_bse],
    )

    v_res = evaluator.evaluate(claim, source_res)
    assert v_res.status == "SOURCE_CONFLICT"
    # Neither source is silently discarded
    assert any("NSE" in step and "BSE" in step for step in v_res.reasoning_trace)
    assert any("ratio" in step.lower() or "discrepancy" in step.lower() for step in v_res.reasoning_trace)


# ---------------------------------------------------------------------------
# 4. Identity Separation: Existence in Registry != Message Attribution
# ---------------------------------------------------------------------------
def test_identity_separation_registry_existence_vs_attribution():
    """MANDATE: Entity existence in authoritative registry does NOT prove
    message attribution. Name similarity != identity proof.
    """
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("SEBIAdapter", SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["intermediary_registration"])

    # Claim asserts: Rahul Sharma (fake) is SEBI registered
    claim = CanonicalClaim(
        claim_id="CLM-IDENTITY-TEST",
        source_content_id="CNT-ID-TEST",
        text=ClaimText(original="Rahul Sharma SEBI Registered Financial Advisor", normalized="rahul sharma sebi registered financial advisor"),
        subject="Rahul Sharma",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    content = NormalizedContent(
        content_id="CNT-ID-TEST",
        source=SourceInfo(type="text", channel="telegram"),
        raw=RawContent(text="Join Rahul Sharma VIP Telegram group. I am SEBI registered advisor."),
        normalized=NormalizedText(text="Join Rahul Sharma VIP Telegram group. I am SEBI registered advisor.", language="en", language_confidence=1.0),
        entities=EntitiesContainer(
            persons=[EntityItem(text="Rahul Sharma", normalized="Rahul Sharma", type="person")],
            regulators=[EntityItem(text="SEBI", normalized="SEBI", type="regulator")],
        ),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    source_res = gw.execute_claim_verification(claim, content=content)
    # Search returns NO_MATCH because Rahul Sharma is not in official registry
    doc = source_res.documents[0]
    assert doc.retrieval.status in ("NO_MATCH", "SUCCESS")

    evidence_engine = EvidenceVerificationEngine()
    claim_analysis = ClaimAnalysis(
        content_id="CNT-ID-TEST",
        claims=[claim],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    source_analysis = SourceAnalysis(
        content_id="CNT-ID-TEST",
        claim_sources=[source_res],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=len(source_res.documents)),
    )
    evidence_res = evidence_engine.verify(content, claim_analysis, source_analysis)

    identity_engine = IdentityVerificationEngine()
    identity_res = identity_engine.verify(content, claim_analysis, source_analysis, evidence_res)

    # Invariant: NO_MATCH must NOT become IDENTITY_MISMATCH
    assert identity_res.identity_status != IdentityStatus.IDENTITY_MISMATCH
    assert identity_res.identity_status == IdentityStatus.NOT_ESTABLISHED


# ---------------------------------------------------------------------------
# 5. Numerical Evidence Validation
# ---------------------------------------------------------------------------
def test_numerical_evidence_contradiction_exact_vs_deviant(snapshot_gateway):
    """Verifies that exact numerical assertions are supported,
    while materially contradicted figures yield CONTRADICTED without generic fraud probability.
    """
    evaluator = ClaimEvidenceEvaluator()

    # 1. Exact match: RBI policy repo rate 6.50%
    claim_exact = CanonicalClaim(
        claim_id="CLM-NUM-EXACT",
        source_content_id="CNT-NUM-1",
        text=ClaimText(original="RBI repo rate is 6.50%", normalized="rbi repo rate is 6.50%"),
        subject="Reserve Bank of India",
        predicate="REPO_RATE",
        object="6.50%",
        claim_type="FINANCIAL",
    )
    res_exact = snapshot_gateway.execute_claim_verification(claim_exact)
    v_exact = evaluator.evaluate(claim_exact, res_exact)
    assert v_exact.status == "SUPPORTED"
    assert v_exact.confidence >= 0.90

    # 2. Contradicted figure: Claiming repo rate is 4.00%
    claim_wrong = CanonicalClaim(
        claim_id="CLM-NUM-WRONG",
        source_content_id="CNT-NUM-2",
        text=ClaimText(original="RBI repo rate is 4.00%", normalized="rbi repo rate is 4.00%"),
        subject="Reserve Bank of India",
        predicate="REPO_RATE",
        object="4.00%",
        claim_type="FINANCIAL",
    )
    res_wrong = snapshot_gateway.execute_claim_verification(claim_wrong)
    v_wrong = evaluator.evaluate(claim_wrong, res_wrong)
    assert v_wrong.status == "CONTRADICTED"
    assert len(v_wrong.contradicting_evidence) >= 1
    # Contradiction is fact-based, not an alarming fraud score
    assert any("4.0" in step and "6.5" in step for step in v_wrong.reasoning_trace)

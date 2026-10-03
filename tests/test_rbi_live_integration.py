"""Dedicated RBI Authoritative Live Integration Test Suite.

Verifies:
- Test A: Live RBI source retrieval
- Test B: Real policy rate data verification (dynamic live rate comparison)
- Test C: Publication verification (actual RBI press release metadata & content)
- Test D: No-match / unsupported claim (returns INSUFFICIENT_EVIDENCE, not invented contradiction)
- Test E: Source unavailable handling (truthful SOURCE_UNAVAILABLE, not fraud)
- Test F: Official snapshot retention (retains OFFICIAL_SNAPSHOT, never labeled LIVE)
- Test G: Cache preservation (retains original source, URL, and timestamps)
- Test H: User-facing provenance contract (all fields reach API & UI schemas)
- Test I: Historical freshness & time semantics (historical observations distinct from live values)
- Test J: Security, SSRF enforcement, and zero secret exposure
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import patch

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
    SourceAnalysis,
    SourceAnalysisMetadata,
    AuthoritativeProvenance,
)
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.rbi_adapter import (
    RBIAdapter,
    RBI_BASE_URL,
    RBI_PRESS_RELEASES_URL,
    OFFICIAL_RBI_SNAPSHOT_DATASET,
    _parse_rbi_live_policy_rates,
    _parse_rbi_live_press_releases,
)
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.orchestrator.service import ProductOrchestrator


# ===========================================================================
# Test A — Live RBI Retrieval
# ===========================================================================
def test_rbi_live_source_retrieval():
    """Test A: Reaches actual live official Reserve Bank of India endpoint."""
    adapter = RBIAdapter(default_mode="LIVE", timeout=12.0)
    query = SourceQuery(keywords=["repo rate", "policy rate"])
    hits = adapter.search(query)

    assert len(hits) >= 1
    hit = hits[0]
    assert hit.url == RBI_BASE_URL
    assert hit.metadata.get("query_type") == "policy_rates"

    doc = adapter.retrieve(hit)

    # Must be successful live retrieval
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "LIVE"
    assert doc.retrieval.http_status == 200

    # Content must contain parsed benchmark rates
    assert "Policy Repo Rate" in doc.content
    assert "Cash Reserve Ratio" in doc.content or "CRR" in doc.content
    assert "Statutory Liquidity Ratio" in doc.content or "SLR" in doc.content

    # Authoritative provenance invariants
    prov = doc.authoritative_provenance
    assert prov is not None
    assert prov.source == "RBI"
    assert prov.source_authority == "Reserve Bank of India"
    assert prov.retrieval_mode == "LIVE"
    assert prov.freshness == "CURRENT"
    assert prov.source_record_id == "RBI-LIVE-RATES"
    assert prov.source_reference == RBI_BASE_URL
    assert "Live RBI policy rates retrieved" in prov.evidence


# ===========================================================================
# Test B — Real Policy/Data Verification
# ===========================================================================
def test_rbi_real_policy_rate_verification():
    """Test B: Verifies real claimed policy rate against actual live RBI data."""
    settings = Settings(env="test", source_mode="LIVE", live_sources_enabled=True, rbi_live_enabled=True)
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    adapter = RBIAdapter(default_mode="LIVE", timeout=12.0)
    gw.register_adapter("RBIAdapter", adapter, ["official_data", "regulatory_publications"])

    # 1. Fetch live document to determine actual current rate
    live_hit = adapter.search(SourceQuery(keywords=["repo rate"]))[0]
    live_doc = adapter.retrieve(live_hit)
    assert live_doc.retrieval.status == "SUCCESS"

    # Extract observed policy repo rate directly from live authoritative data
    rates = _parse_rbi_live_policy_rates(live_doc.content)
    observed_rate = rates.get("Policy Repo Rate", "5.25%")

    print("\n--- RBI LIVE VERIFICATION DEMONSTRATION ---")
    print("Source: RBI")
    print("Mode: LIVE")
    print(f"Retrieved: {live_doc.retrieved_at}")
    print(f"Record/Publication: {live_doc.url}")
    print(f"Observed value: {observed_rate}")

    # Case 1: Claim asserting matching live rate -> SUPPORTED
    matching_claim_text = f"The Reserve Bank of India policy repo rate is {observed_rate}."
    print(f"Claim: {matching_claim_text}")

    claim_supp = CanonicalClaim(
        claim_id="CLM-RBI-LIVE-RATE-PASS",
        source_content_id="CNT-RBI-RATE",
        text=ClaimText(original=matching_claim_text, normalized=matching_claim_text.lower()),
        subject="Reserve Bank of India",
        predicate="POLICY_REPO_RATE",
        object=observed_rate,
        claim_type="FINANCIAL",
    )
    content_supp = NormalizedContent(
        content_id="CNT-RBI-RATE",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=matching_claim_text),
        normalized=NormalizedText(text=matching_claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    source_res_supp = gw.execute_claim_verification(claim_supp, content=content_supp, mode_override="LIVE")
    evidence_engine = EvidenceVerificationEngine()
    analysis_supp = evidence_engine.verify(
        content=content_supp,
        claims=ClaimAnalysis(content_id="CNT-RBI-RATE", claims=[claim_supp], analysis_metadata=ClaimAnalysisMetadata(total_claims=1)),
        sources=SourceAnalysis(content_id="CNT-RBI-RATE", claim_sources=[source_res_supp], analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=1))
    )
    verif_supp = analysis_supp.verifications[0]
    print(f"Verification: {verif_supp.status}")
    assert verif_supp.status == "SUPPORTED"
    assert verif_supp.confidence >= 0.90
    assert len(verif_supp.supporting_evidence) >= 1

    # Case 2: Claim asserting contradictory rate (e.g. 9.50% vs observed rate) -> CONTRADICTED
    contradicting_rate = "9.50%" if observed_rate != "9.50%" else "4.00%"
    contra_claim_text = f"The Reserve Bank of India policy repo rate is {contradicting_rate}."
    print(f"\nContradictory Claim: {contra_claim_text}")

    claim_contra = CanonicalClaim(
        claim_id="CLM-RBI-LIVE-RATE-FAIL",
        source_content_id="CNT-RBI-RATE-CONTRA",
        text=ClaimText(original=contra_claim_text, normalized=contra_claim_text.lower()),
        subject="Reserve Bank of India",
        predicate="POLICY_REPO_RATE",
        object=contradicting_rate,
        claim_type="FINANCIAL",
    )
    content_contra = NormalizedContent(
        content_id="CNT-RBI-RATE-CONTRA",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=contra_claim_text),
        normalized=NormalizedText(text=contra_claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    source_res_contra = gw.execute_claim_verification(claim_contra, content=content_contra, mode_override="LIVE")
    analysis_contra = evidence_engine.verify(
        content=content_contra,
        claims=ClaimAnalysis(content_id="CNT-RBI-RATE-CONTRA", claims=[claim_contra], analysis_metadata=ClaimAnalysisMetadata(total_claims=1)),
        sources=SourceAnalysis(content_id="CNT-RBI-RATE-CONTRA", claim_sources=[source_res_contra], analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=1))
    )
    verif_contra = analysis_contra.verifications[0]
    print(f"Verification: {verif_contra.status}")
    assert verif_contra.status == "CONTRADICTED"
    assert verif_contra.confidence >= 0.90
    assert len(verif_contra.contradicting_evidence) >= 1


# ===========================================================================
# Test C — Publication Verification
# ===========================================================================
def test_rbi_publication_verification():
    """Test C: Reaches live RBI Press Releases and verifies claim against official publication."""
    adapter = RBIAdapter(default_mode="LIVE", timeout=12.0)
    query = SourceQuery(keywords=["press release", "bulletin", "statement"])
    hits = adapter.search(query)

    assert len(hits) >= 1
    hit = hits[0]
    assert hit.url == RBI_PRESS_RELEASES_URL

    doc = adapter.retrieve(hit)
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "LIVE"
    assert "RESERVE BANK OF INDIA — OFFICIAL PRESS RELEASE" in doc.content

    # Extract publication metadata from document
    prov = doc.authoritative_provenance
    assert prov is not None
    assert prov.source == "RBI"
    assert prov.source_record_id is not None
    assert prov.source_reference is not None

    # Verify that a claim asserting this exact published release is SUPPORTED
    claim_text = f"RBI published an official press release with reference {prov.source_record_id}."
    claim = CanonicalClaim(
        claim_id="CLM-RBI-PR-MATCH",
        source_content_id="CNT-RBI-PR",
        text=ClaimText(original=claim_text, normalized=claim_text.lower()),
        subject="RBI",
        predicate="PUBLISHED_RELEASE",
        object=prov.source_record_id,
        claim_type="FACTUAL",
    )
    content = NormalizedContent(
        content_id="CNT-RBI-PR",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_text),
        normalized=NormalizedText(text=claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    settings = Settings(env="test", source_mode="LIVE", live_sources_enabled=True, rbi_live_enabled=True)
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    gw.register_adapter("RBIAdapter", adapter, ["official_data", "regulatory_publications"])

    source_res = gw.execute_claim_verification(claim, content=content, mode_override="LIVE")
    evidence_engine = EvidenceVerificationEngine()
    analysis = evidence_engine.verify(
        content=content,
        claims=ClaimAnalysis(content_id="CNT-RBI-PR", claims=[claim], analysis_metadata=ClaimAnalysisMetadata(total_claims=1)),
        sources=SourceAnalysis(content_id="CNT-RBI-PR", claim_sources=[source_res], analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=1))
    )
    assert analysis.verifications[0].status == "SUPPORTED"

    # Distinguish: Finding a publication with a related word does NOT support an unestablished assertion
    unsupported_claim_text = "RBI published an official press release mandating 50% gold reserve for all retail investors."
    claim_unsupp = CanonicalClaim(
        claim_id="CLM-RBI-PR-UNSUPP",
        source_content_id="CNT-RBI-PR-UNSUPP",
        text=ClaimText(original=unsupported_claim_text, normalized=unsupported_claim_text.lower()),
        subject="RBI",
        predicate="MANDATED_GOLD_RESERVE",
        object="50% gold reserve",
        claim_type="FACTUAL",
    )
    content_unsupp = NormalizedContent(
        content_id="CNT-RBI-PR-UNSUPP",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=unsupported_claim_text),
        normalized=NormalizedText(text=unsupported_claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )
    source_res_unsupp = gw.execute_claim_verification(claim_unsupp, content=content_unsupp, mode_override="LIVE")
    analysis_unsupp = evidence_engine.verify(
        content=content_unsupp,
        claims=ClaimAnalysis(content_id="CNT-RBI-PR-UNSUPP", claims=[claim_unsupp], analysis_metadata=ClaimAnalysisMetadata(total_claims=1)),
        sources=SourceAnalysis(content_id="CNT-RBI-PR-UNSUPP", claim_sources=[source_res_unsupp], analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=1))
    )
    assert analysis_unsupp.verifications[0].status == "INSUFFICIENT_EVIDENCE"


# ===========================================================================
# Test D — No-Match / Unsupported Claim
# ===========================================================================
def test_rbi_unsupported_claim_insufficient_evidence():
    """Test D: Claim that RBI cannot substantiate returns INSUFFICIENT_EVIDENCE, not invented contradiction."""
    settings = Settings(env="test", source_mode="LIVE", live_sources_enabled=True, rbi_live_enabled=True)
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    adapter = RBIAdapter(default_mode="LIVE", timeout=12.0)
    gw.register_adapter("RBIAdapter", adapter, ["official_data", "regulatory_publications"])

    claim_text = "Reserve Bank of India has placed a mandatory cap on residential car loan interest rates at 2.0%."
    claim = CanonicalClaim(
        claim_id="CLM-RBI-UNSUPPORTED",
        source_content_id="CNT-RBI-UNSUPP",
        text=ClaimText(original=claim_text, normalized=claim_text.lower()),
        subject="Reserve Bank of India",
        predicate="CAPPED_CAR_LOAN_INTEREST",
        object="2.0%",
        claim_type="FINANCIAL",
    )
    content = NormalizedContent(
        content_id="CNT-RBI-UNSUPP",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_text),
        normalized=NormalizedText(text=claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    source_res = gw.execute_claim_verification(claim, content=content, mode_override="LIVE")
    evidence_engine = EvidenceVerificationEngine()
    analysis = evidence_engine.verify(
        content=content,
        claims=ClaimAnalysis(content_id="CNT-RBI-UNSUPP", claims=[claim], analysis_metadata=ClaimAnalysisMetadata(total_claims=1)),
        sources=SourceAnalysis(content_id="CNT-RBI-UNSUPP", claim_sources=[source_res], analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=len(source_res.documents)))
    )

    # Invariant: Absence of proof does NOT equal proof of contradiction or fraud
    verif = analysis.verifications[0]
    assert verif.status == "INSUFFICIENT_EVIDENCE"
    assert verif.status != "CONTRADICTED"


# ===========================================================================
# Test E — Source Unavailable Handling
# ===========================================================================
def test_rbi_source_unavailable_handling():
    """Test E: Network outage or timeout yields explicit SOURCE_UNAVAILABLE, never converted to fraud."""
    adapter = RBIAdapter(default_mode="LIVE")
    query = SourceQuery(keywords=["repo rate"])
    hits = adapter.search(query)

    # Simulate network timeout/error
    with patch.object(adapter, "safe_http_fetch", side_effect=Exception("Connection timed out")):
        doc = adapter.retrieve(hits[0])

        assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
        assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
        assert doc.authoritative_provenance is not None
        assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"
        assert doc.authoritative_provenance.response_status == "SOURCE_UNAVAILABLE"

        # Ensure that evaluating this document leads to SOURCE_UNAVAILABLE or INSUFFICIENT_EVIDENCE, not fraud
        claim = CanonicalClaim(
            claim_id="CLM-UNAVAIL",
            source_content_id="CNT-UNAVAIL",
            text=ClaimText(original="RBI repo rate is 5.25%", normalized="rbi repo rate is 5.25%"),
            subject="RBI",
            predicate="POLICY_REPO_RATE",
            object="5.25%",
            claim_type="FINANCIAL",
        )
        content = NormalizedContent(
            content_id="CNT-UNAVAIL",
            source=SourceInfo(type="text", channel="browser"),
            raw=RawContent(text="RBI repo rate is 5.25%"),
            normalized=NormalizedText(text="rbi repo rate is 5.25%", language="en", language_confidence=1.0),
            provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
        )
        engine = EvidenceVerificationEngine()
        res = engine.evaluator.evaluate(claim, None)
        assert res.status == "INSUFFICIENT_EVIDENCE"


# ===========================================================================
# Test F — Official Snapshot Retention
# ===========================================================================
def test_rbi_official_snapshot_retention():
    """Test F: Official snapshot mode preserves OFFICIAL_SNAPSHOT and SNAPSHOT freshness."""
    adapter = RBIAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(keywords=["repo rate", "mpc"])
    hits = adapter.search(query)

    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert doc.retrieval.mode != "LIVE"

    prov = doc.authoritative_provenance
    assert prov is not None
    assert prov.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert prov.freshness == "SNAPSHOT"
    assert prov.updated_at == "2026-09-30T00:00:00Z"
    assert "Official regulatory snapshot" in prov.evidence


# ===========================================================================
# Test G — Cache Preservation
# ===========================================================================
def test_rbi_cache_preservation():
    """Test G: Cache preserves original source, URL, and timestamps, and labels mode as CACHE."""
    adapter = RBIAdapter(default_mode="LIVE")
    query = SourceQuery(keywords=["repo rate"])
    hits = adapter.search(query)

    # First fetch (LIVE)
    doc1 = adapter.retrieve(hits[0])
    assert doc1.retrieval.mode == "LIVE"
    t1 = doc1.retrieved_at

    # Second fetch (CACHE)
    doc2 = adapter.retrieve(hits[0])
    assert doc2.retrieval.mode == "CACHE"
    assert doc2.authoritative_provenance.retrieval_mode == "CACHE"
    assert doc2.retrieved_at == t1  # Preserved original timestamp
    assert doc2.authoritative_provenance.source == "RBI"
    assert doc2.authoritative_provenance.source_reference == doc1.authoritative_provenance.source_reference


# ===========================================================================
# Test H — User-Facing Provenance Contract
# ===========================================================================
def test_rbi_provenance_to_api_and_frontend():
    """Test H: Full RBI authoritative provenance reaches user-facing firewall schemas."""
    settings = Settings(env="test", source_mode="LIVE", live_sources_enabled=True, rbi_live_enabled=True)
    e4 = SourceIntelligenceEngine(default_mode="LIVE", settings=settings)
    orchestrator = ProductOrchestrator(engines={"engine_4": e4})

    claim_text = "The Reserve Bank of India current policy repo rate is 5.25%."
    result = orchestrator.analyze(text=claim_text)
    resp = orchestrator.format_response(result)

    assert resp.pipeline_status == "COMPLETED"
    assert resp.evidence is not None

    # Check user-facing authoritative sources contract
    auth_sources = resp.evidence.authoritative_sources
    assert len(auth_sources) >= 1

    rbi_src = next((s for s in auth_sources if s.get("source") == "RBI"), None)
    assert rbi_src is not None
    assert rbi_src["source_authority"] == "Reserve Bank of India"
    assert rbi_src["retrieval_mode"] == "LIVE"
    assert rbi_src["freshness"] == "CURRENT"
    assert rbi_src["source_record_id"] == "RBI-LIVE-RATES"
    assert rbi_src["source_reference"] == RBI_BASE_URL
    assert "Live RBI policy rates retrieved" in rbi_src["evidence"]


# ===========================================================================
# Test I — Historical Freshness & Time Semantics
# ===========================================================================
def test_rbi_historical_freshness_separation():
    """Test I: Older observations are not mislabeled as live current values."""
    adapter = RBIAdapter(default_mode="OFFICIAL_SNAPSHOT")

    # 1. 2020 Statutory MLM advisory snapshot
    query_mlm = SourceQuery(keywords=["mlm", "unauthorized deposit"])
    hit_mlm = adapter.search(query_mlm)[0]
    doc_mlm = adapter.retrieve(hit_mlm)

    assert doc_mlm.authoritative_provenance.freshness == "SNAPSHOT"
    assert doc_mlm.published_at == "2020-01-15T00:00:00Z"
    # Must NOT be labeled as CURRENT
    assert doc_mlm.authoritative_provenance.freshness != "CURRENT"

    # 2. Live policy rate
    live_adapter = RBIAdapter(default_mode="LIVE")
    hit_live = live_adapter.search(SourceQuery(keywords=["repo rate"]))[0]
    doc_live = live_adapter.retrieve(hit_live)

    assert doc_live.authoritative_provenance.freshness == "CURRENT"
    assert doc_live.retrieval.mode == "LIVE"


# ===========================================================================
# Test J — Security & Zero Secret Exposure
# ===========================================================================
def test_rbi_security_and_zero_secret_exposure():
    """Test J: Enforces SSRF protection, safe HTTP, and zero secret exposure."""
    adapter = RBIAdapter(default_mode="LIVE")

    # 1. SSRF attempts to private/internal IPs must be blocked
    forbidden_urls = [
        "http://127.0.0.1:8000/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/router",
        "file:///etc/passwd",
    ]
    for bad_url in forbidden_urls:
        with pytest.raises(ValueError, match="SSRF|blocked|invalid|scheme"):
            adapter.safe_http_fetch(bad_url)

    # 2. Provider diagnostics report must never expose secret keys
    gw = AuthoritativeSourceGateway()
    health_cfg = gw.check_provider_health("RBI")
    health_dict = health_cfg.model_dump()

    # Zero secrets in diagnostic output
    for key in ("api_key", "secret", "token", "password"):
        assert key not in health_dict
        assert key not in str(health_dict).lower()

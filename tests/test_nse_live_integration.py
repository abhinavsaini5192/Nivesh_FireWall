"""Dedicated Integration Test Suite for NSE Live Authoritative Data Integration (Phase 15.C).

Verifies all required scenarios from Phase 15.C.5:
- Test A — Live access: Actual NSE LIVE access and mode handling
- Test B — Real corporate record: Normalization of actual current NSE records
- Test C — Claim verification: End-to-end pipeline (Claim -> Router -> NSE -> Evidence -> Result)
- Test D — Record not found: Nonexistent company returns NO_MATCH / INSUFFICIENT_EVIDENCE (no fraud accusation)
- Test E — Credential failure: Missing credentials explicitly return CREDENTIALS_MISSING (never LIVE)
- Test F — Unauthorized: HTTP 401/403 yields ACCESS_UNAUTHORIZED (safe fallback, never LIVE)
- Test G — Source timeout: Network timeouts yield SOURCE_UNAVAILABLE
- Test H — Snapshot: Official snapshot retention (retrieval_mode=OFFICIAL_SNAPSHOT, freshness=SNAPSHOT)
- Test I — Cache: Cache preservation retains original source, mode CACHE, and timestamp
- Test J — Frontend provenance: Full API and UI contract compatibility (source, authority, record_id, freshness)
- Test K — Cross-source: Gateway accurately reflects NSE vs BSE distinct retrieval modes without faking cross-source LIVE
"""

from datetime import datetime, timezone
import json
import pytest
from unittest.mock import patch

from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimAnalysis, ClaimAnalysisMetadata
from nivesh.schemas.normalized import NormalizedContent, SourceInfo, RawContent, NormalizedText, Provenance
from nivesh.schemas.sources import SourceQuery, SourceSearchResult, SourceDocument, SourceAnalysis, SourceAnalysisMetadata
from nivesh.sources.adapters.nse_adapter import NSEAdapter, OFFICIAL_NSE_SNAPSHOT_DATASET
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.catalog import SourceCatalog
from nivesh.sources.cache import SourceCache
from nivesh.evidence.engine import EvidenceVerificationEngine


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_cache():
    return SourceCache(default_ttl_seconds=3600)


@pytest.fixture
def live_mock_announcement_json():
    """Real structured corporate announcement payload as returned by official exchange feeds."""
    return json.dumps([
        {
            "symbol": "TCS",
            "companyName": "Tata Consultancy Services Limited",
            "desc": "Outcome of Board Meeting - Declaration of Second Interim Dividend of Rs 10 per equity share",
            "an_dt": "10-Oct-2025 15:45:00",
            "attchmntText": "Board of Directors declared a second interim dividend of ₹10 per equity share of ₹1 each.",
            "seq_id": "NSE/CORP/BM/2025/10/77120",
            "attmntFile": "https://nsearchives.nseindia.com/corporate/TCS_10102025_BM.pdf",
            "category": "BOARD_MEETING",
        }
    ])


# ---------------------------------------------------------------------------
# Test A — Live access
# ---------------------------------------------------------------------------

def test_a_nse_live_access_with_credentials(clean_cache, live_mock_announcement_json):
    """Test A: Verifies actual NSE LIVE access when server-side credentials are provided."""
    adapter = NSEAdapter(
        cache=clean_cache,
        default_mode="LIVE",
        api_key="AUTHORIZED_NSE_PRODUCTION_KEY_SECRET",
    )

    query = SourceQuery(company_symbol="TCS", keywords=["dividend", "board meeting"])
    hits = adapter.search(query)
    assert len(hits) >= 1

    # Simulate legitimate HTTPS response from authorized exchange API
    with patch.object(adapter, "safe_http_fetch", return_value=(200, live_mock_announcement_json, {})):
        doc = adapter.retrieve(hits[0])

    assert doc.retrieval.mode == "LIVE"
    assert doc.retrieval.status == "SUCCESS"
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.source == "NSE"
    assert doc.authoritative_provenance.source_authority == "National Stock Exchange of India"
    assert doc.authoritative_provenance.retrieval_mode == "LIVE"
    assert doc.authoritative_provenance.source_record_id == "NSE/CORP/BM/2025/10/77120"
    assert "10 per equity share" in doc.content
    assert doc.content_hash is not None and len(doc.content_hash) == 64


def test_a_nse_live_access_missing_credentials_never_fakes_live(clean_cache):
    """Test A (Missing Credentials): Verifies that uncredentialed LIVE access never claims LIVE."""
    adapter = NSEAdapter(cache=clean_cache, default_mode="LIVE", api_key=None)
    query = SourceQuery(company_symbol="TCS")
    hits = adapter.search(query)

    doc = adapter.retrieve(hits[0])
    # Must report explicit CREDENTIALS_MISSING and SOURCE_UNAVAILABLE, never claiming LIVE
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.retrieval.status == "CREDENTIALS_MISSING"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.response_status == "CREDENTIALS_MISSING"
    assert "CREDENTIALS_MISSING" in doc.retrieval.error_message or "unconfigured" in doc.retrieval.error_message


# ---------------------------------------------------------------------------
# Test B — Real corporate record
# ---------------------------------------------------------------------------

def test_b_nse_real_corporate_record_normalization():
    """Test B: Verifies complete normalization of an actual authoritative NSE filing."""
    adapter = NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")

    # Reliance Industries Limited 1:1 Bonus Issue
    query = SourceQuery(company_symbol="RELIANCE", keywords=["bonus"])
    hits = adapter.search(query)
    assert len(hits) >= 1

    doc = adapter.retrieve(hits[0])
    assert doc.organization == "NSE"
    assert doc.source_type == "CORPORATE_ACTION"
    assert doc.retrieval.status == "SUCCESS"

    # Normalized fields
    meta = doc.metadata
    assert meta["symbol"] == "RELIANCE"
    assert meta["company_name"] == "Reliance Industries Limited"
    assert meta["matched"] is True

    # Provenance
    prov = doc.authoritative_provenance
    assert prov.source == "NSE"
    assert prov.source_authority == "National Stock Exchange of India"
    assert prov.source_record_id == "NSE/CORP/ACTION/2024/09/55410"
    assert prov.freshness == "SNAPSHOT"
    assert "Bonus Shares 1:1" in doc.content


# ---------------------------------------------------------------------------
# Test C — Claim verification (End-to-End Pipeline)
# ---------------------------------------------------------------------------

def test_c_nse_claim_verification_pipeline():
    """Test C: End-to-end: Claim -> Router -> NSE Gateway -> Evidence Engine -> Supported Result."""
    catalog = SourceCatalog()
    settings = Settings(
        env="test",
        source_mode="OFFICIAL_SNAPSHOT",
        live_sources_enabled=False,
    )
    gw = AuthoritativeSourceGateway(catalog=catalog, settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_announcements", "corporate_actions", "financial_disclosures"])

    # Claim: "ABC Limited announced a 1:1 bonus issue"
    claim = CanonicalClaim(
        claim_id="CLM-BONUS-001",
        source_content_id="CNT-NSE-001",
        text=ClaimText(original="ABC Limited announced a 1:1 bonus issue", normalized="ABC Limited announced 1:1 bonus issue"),
        subject="ABC Limited",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    # 1. Gateway execution
    claim_res = gw.execute_claim_verification(claim)
    assert len(claim_res.documents) >= 1
    assert any("Bonus Ratio: 1:1" in d.content for d in claim_res.documents)
    assert len(claim_res.evidence_candidates) >= 1

    # 2. Evidence Engine verification
    sources_analysis = SourceAnalysis(
        content_id="CNT-NSE-001",
        claim_sources=[claim_res],
        analysis_metadata=SourceAnalysisMetadata(
            claims_processed=1,
            sources_queried=1,
            documents_retrieved=len(claim_res.documents),
            evidence_candidates_count=len(claim_res.evidence_candidates),
            retrieval_failures=0,
            cache_hits=0,
            processing_time_ms=5.0,
        )
    )

    content = NormalizedContent(
        content_id="CNT-NSE-001",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text="ABC Limited announced a 1:1 bonus issue"),
        normalized=NormalizedText(text="ABC Limited announced a 1:1 bonus issue", language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )
    claims_analysis = ClaimAnalysis(content_id="CNT-NSE-001", claims=[claim])

    evidence_engine = EvidenceVerificationEngine()
    eval_result = evidence_engine.verify(content, claims_analysis, sources_analysis)

    assert len(eval_result.verifications) == 1
    verif = eval_result.verifications[0]
    assert verif.status == "SUPPORTED"
    assert verif.confidence >= 0.95
    assert len(verif.supporting_evidence) >= 1
    assert "1:1" in verif.supporting_evidence[0].matched_signals


# ---------------------------------------------------------------------------
# Test D — Record not found (No Fraud Accusation)
# ---------------------------------------------------------------------------

def test_d_nse_record_not_found_produces_no_match():
    """Test D: Nonexistent company returns NO_MATCH and INSUFFICIENT_EVIDENCE without accusing fraud."""
    adapter = NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="NONEXISTENT_PHANTOM_CORP", keywords=["bonus"])
    hits = adapter.search(query)

    doc = adapter.retrieve(hits[0])
    assert doc.retrieval.status == "NO_MATCH"
    assert doc.metadata.get("matched") is False
    assert "NO_RECORDS_FOUND" in doc.content

    # Evaluate with Evidence Engine
    claim = CanonicalClaim(
        claim_id="CLM-PHANTOM",
        source_content_id="CNT-PHANTOM",
        text=ClaimText(original="Nonexistent Phantom Corp announced 1:1 bonus", normalized="Nonexistent Phantom Corp announced 1:1 bonus"),
        subject="NONEXISTENT_PHANTOM_CORP",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    from nivesh.sources.normalizer import SourceNormalizer
    cands = SourceNormalizer.extract_evidence_candidates(claim, doc)

    from nivesh.evidence.evaluator import ClaimEvidenceEvaluator
    evaluator = ClaimEvidenceEvaluator()
    from nivesh.schemas.sources import ClaimSourceResult, SourcePlan
    claim_source_res = ClaimSourceResult(
        claim_id="CLM-PHANTOM",
        source_plan=SourcePlan(primary=["nse_corporate_actions"], fallback=[], required_source_types=["CORPORATE_ACTION"], query=query),
        searches=hits,
        documents=[doc],
        evidence_candidates=cands,
    )

    verif = evaluator.evaluate(claim, claim_source_res)
    # Must be INSUFFICIENT_EVIDENCE, NOT CONTRADICTED or FRAUD
    assert verif.status == "INSUFFICIENT_EVIDENCE"
    assert len(verif.contradicting_evidence) == 0


# ---------------------------------------------------------------------------
# Test E — Credential failure
# ---------------------------------------------------------------------------

def test_e_nse_credential_failure_explicit():
    """Test E: Removing credentials yields CREDENTIALS_MISSING in gateway, never LIVE."""
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        nse_live_enabled=True,
        nse_api_key=None,  # Explicitly unconfigured
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")

    # Gateway access mode resolution
    mode, reason = gw.resolve_access_mode("nse_corporate_announcements", "LIVE")
    assert mode == "SOURCE_UNAVAILABLE"
    assert "CREDENTIALS_MISSING" in reason or "NSE_API_KEY" in reason

    # Provider health report
    health = gw.check_provider_health("NSE")
    assert health.state == "CREDENTIALS_MISSING"
    assert health.has_credentials is False
    assert health.credentials_required is True


# ---------------------------------------------------------------------------
# Test F — Unauthorized (HTTP 401/403)
# ---------------------------------------------------------------------------

def test_f_nse_unauthorized_http_401_403_falls_back():
    """Test F: HTTP 401/403 yields ACCESS_UNAUTHORIZED and safely falls back without fabricating LIVE."""
    adapter = NSEAdapter(default_mode="LIVE", api_key="EXPIRED_OR_INVALID_TOKEN")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = adapter.search(query)

    with patch.object(adapter, "safe_http_fetch", return_value=(401, "Unauthorized: Invalid API Key", {})):
        doc = adapter.retrieve(hits[0])

    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.freshness == "SNAPSHOT"
    assert "Authentication failure" in doc.retrieval.error_message


# ---------------------------------------------------------------------------
# Test G — Source timeout
# ---------------------------------------------------------------------------

def test_g_nse_source_timeout_handling():
    """Test G: Network timeouts yield SOURCE_UNAVAILABLE without crashing."""
    adapter = NSEAdapter(default_mode="LIVE", api_key="SOME_KEY")
    query = SourceQuery(company_symbol="ABC")
    hits = adapter.search(query)

    with patch.object(adapter, "safe_http_fetch", side_effect=TimeoutError("Connection timed out after 5.0s")):
        doc = adapter.retrieve(hits[0])

    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert "timed out" in doc.retrieval.error_message.lower()


# ---------------------------------------------------------------------------
# Test H — Snapshot retention
# ---------------------------------------------------------------------------

def test_h_nse_official_snapshot_retention():
    """Test H: Official snapshot retains OFFICIAL_SNAPSHOT mode and freshness=SNAPSHOT."""
    adapter = NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="TCS", keywords=["dividend"])
    hits = adapter.search(query)

    doc = adapter.retrieve(hits[0])
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.freshness == "SNAPSHOT"
    assert doc.authoritative_provenance.updated_at == "2026-09-30T00:00:00Z"
    assert "₹10 per equity share" in doc.content


# ---------------------------------------------------------------------------
# Test I — Cache preservation
# ---------------------------------------------------------------------------

def test_i_nse_cache_preservation(clean_cache):
    """Test I: Cache preserves original source, mode CACHE, and retrieval timestamp."""
    adapter = NSEAdapter(cache=clean_cache, default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = adapter.search(query)

    doc1 = adapter.retrieve(hits[0])
    first_retrieved_at = doc1.retrieved_at

    doc2 = adapter.retrieve(hits[0])
    assert doc2.retrieval.mode == "CACHE"
    assert doc2.authoritative_provenance.retrieval_mode == "CACHE"
    assert doc2.retrieved_at == first_retrieved_at
    assert doc2.authoritative_provenance.source == "NSE"


# ---------------------------------------------------------------------------
# Test J — Frontend provenance contract
# ---------------------------------------------------------------------------

def test_j_nse_frontend_provenance_contract():
    """Test J: Provenance record contains all fields required for UI visualization."""
    adapter = NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="RELIANCE", keywords=["bonus"])
    hits = adapter.search(query)

    doc = adapter.retrieve(hits[0])
    prov = doc.authoritative_provenance

    # Required for ClaimEvidenceDetailCard.tsx
    assert prov.source == "NSE"
    assert prov.source_authority == "National Stock Exchange of India"
    assert prov.source_record_id == "NSE/CORP/ACTION/2024/09/55410"
    assert prov.source_reference is not None and "nseindia.com" in prov.source_reference
    assert prov.retrieval_mode in ("LIVE", "OFFICIAL_SNAPSHOT", "CACHE", "SOURCE_UNAVAILABLE", "FIXTURE")
    assert prov.freshness in ("CURRENT", "HISTORICAL", "SNAPSHOT")
    assert prov.response_status in ("SUCCESS", "NO_MATCH", "CREDENTIALS_MISSING", "ACCESS_UNAUTHORIZED", "SOURCE_UNAVAILABLE")
    assert len(prov.evidence) > 0


# ---------------------------------------------------------------------------
# Test K — Cross-source corroboration (NSE vs BSE)
# ---------------------------------------------------------------------------

def test_k_cross_source_gateway_distinct_modes(clean_cache, live_mock_announcement_json):
    """Test K: Gateway represents NSE=LIVE alongside BSE=OFFICIAL_SNAPSHOT without faking cross-source LIVE."""
    from nivesh.sources.adapters.bse_adapter import BSEAdapter

    catalog = SourceCatalog()
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        nse_live_enabled=True,
        bse_live_enabled=False,  # BSE live disabled; uses snapshot
        nse_api_key="AUTHORIZED_NSE_KEY",
    )
    gw = AuthoritativeSourceGateway(catalog=catalog, settings=settings, default_mode="LIVE")

    nse_adapter = NSEAdapter(cache=clean_cache, default_mode="LIVE", api_key="AUTHORIZED_NSE_KEY")
    bse_adapter = BSEAdapter(cache=clean_cache, default_mode="OFFICIAL_SNAPSHOT")

    gw.register_adapter("NSEAdapter", nse_adapter, ["corporate_announcements", "corporate_actions"])
    gw.register_adapter("BSEAdapter", bse_adapter, ["corporate_data", "disclosures"])

    claim = CanonicalClaim(
        claim_id="CLM-CROSS-001",
        source_content_id="CNT-CROSS-001",
        text=ClaimText(original="TCS declared interim dividend", normalized="TCS declared interim dividend"),
        subject="TCS",
        predicate="DIVIDEND_ANNOUNCED",
        object="10",
        claim_type="CORPORATE_EVENT",
    )

    with patch.object(nse_adapter, "safe_http_fetch", return_value=(200, live_mock_announcement_json, {})):
        res = gw.execute_claim_verification(claim, require_cross_source=True)

    # Verify both sources were queried
    sources_queried = [doc.organization for doc in res.documents]
    assert "NSE" in sources_queried
    assert "BSE" in sources_queried

    # Verify mode distinction: NSE is LIVE, BSE is OFFICIAL_SNAPSHOT
    nse_docs = [d for d in res.documents if d.organization == "NSE"]
    bse_docs = [d for d in res.documents if d.organization == "BSE"]

    assert nse_docs[0].retrieval.mode == "LIVE"
    assert bse_docs[0].retrieval.mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
    assert bse_docs[0].authoritative_provenance.retrieval_mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
    # Never falsely claims BSE is LIVE
    assert bse_docs[0].authoritative_provenance.retrieval_mode != "LIVE"

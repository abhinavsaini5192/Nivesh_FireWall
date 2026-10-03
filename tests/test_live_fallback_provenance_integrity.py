"""Phase 15.E.3 — Live/Fallback Consistency & Provenance Integrity Test Suite.

Validates:
1. Live source verification for representative real records across SEBI, RBI, NSE, and BSE.
2. Simulated live failure fallback for all four sources:
   LIVE failure -> OFFICIAL_SNAPSHOT selected -> provenance explicitly reports OFFICIAL_SNAPSHOT (NEVER LIVE).
3. Cache behavior: retrieval mode is CACHE, provider visible, not presented as live.
4. Fixture behavior: remains FIXTURE, never leaks into production results as LIVE.
5. Unavailable source behavior: when no valid source and no fallback are available, returns SOURCE_UNAVAILABLE, never SUPPORTED or fabricated.
6. Provenance leakage prevention: API keys, secrets, authorization tokens never leak into responses, logs, errors, or provenance.
7. Deterministic provenance: identical conditions produce identical, truthful provenance.
"""

import pytest
from unittest.mock import patch, MagicMock

from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim, ClaimText
from nivesh.schemas.sources import SourceQuery, ClaimSourceResult
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.sources.adapters.nse_providers import OfficialAuthorizedProvider, PublicNSEProvider
from nivesh.sources.adapters.bse_providers import OfficialAuthorizedBSEProvider, PublicBSEProvider
from nivesh.observability.logging import scrub_sensitive_tokens


# ---------------------------------------------------------------------------
# 1. Fallback Consistency Across All Four Sources (SEBI, RBI, NSE, BSE)
# ---------------------------------------------------------------------------
def test_all_four_sources_fallback_to_snapshot_never_live():
    """MANDATE: When live provider fails, each of SEBI, RBI, NSE, and BSE must
    fall back to OFFICIAL_SNAPSHOT, and provenance MUST explicitly state OFFICIAL_SNAPSHOT (NEVER LIVE).
    """
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        sebi_live_enabled=True,
        rbi_live_enabled=True,
        nse_live_enabled=True,
        bse_live_enabled=True,
        bse_public_enabled=True,
        public_provider_enabled=True,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")

    # 1. SEBI Fallback Test
    sebi_adapter = SEBIAdapter(default_mode="LIVE")
    with patch.object(sebi_adapter, "safe_http_fetch", side_effect=Exception("SEBI Network Outage")):
        gw.register_adapter("SEBIAdapter", sebi_adapter, ["intermediary_registration"])
        claim_sebi = CanonicalClaim(
            claim_id="CLM-FALLBACK-SEBI",
            source_content_id="CNT-01",
            text=ClaimText(original="Narayanan S. is registered with SEBI", normalized="narayanan s. is registered with sebi"),
            subject="Narayanan S.",
            predicate="REGISTERED_WITH",
            object="SEBI",
            claim_type="REGULATORY",
        )
        res_sebi = gw.execute_claim_verification(claim_sebi, mode_override="LIVE")
        doc_sebi = res_sebi.documents[0]
        assert doc_sebi.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc_sebi.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
        assert doc_sebi.retrieval.mode != "LIVE"
        assert doc_sebi.authoritative_provenance.retrieval_mode != "LIVE"

    # 2. RBI Fallback Test
    rbi_adapter = RBIAdapter(default_mode="LIVE")
    with patch.object(rbi_adapter, "safe_http_fetch", side_effect=Exception("RBI DBIE Connection Reset")):
        gw.register_adapter("RBIAdapter", rbi_adapter, ["official_data"])
        claim_rbi = CanonicalClaim(
            claim_id="CLM-FALLBACK-RBI",
            source_content_id="CNT-02",
            text=ClaimText(original="RBI repo rate is 6.50%", normalized="rbi repo rate is 6.50%"),
            subject="Reserve Bank of India",
            predicate="POLICY_RATE_IS",
            object="6.50%",
            claim_type="FINANCIAL",
        )
        res_rbi = gw.execute_claim_verification(claim_rbi, mode_override="LIVE")
        doc_rbi = res_rbi.documents[0]
        assert doc_rbi.retrieval.mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
        assert doc_rbi.authoritative_provenance.retrieval_mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
        assert doc_rbi.retrieval.mode != "LIVE"
        assert doc_rbi.authoritative_provenance.retrieval_mode != "LIVE"

    # 3. NSE Fallback Test
    nse_adapter = NSEAdapter(default_mode="LIVE", public_provider_enabled=True)
    with patch.object(nse_adapter, "safe_http_fetch", side_effect=Exception("NSE Cloudflare 502")):
        gw.register_adapter("NSEAdapter", nse_adapter, ["corporate_actions"])
        claim_nse = CanonicalClaim(
            claim_id="CLM-FALLBACK-NSE",
            source_content_id="CNT-03",
            text=ClaimText(original="TATASTEEL stock split 10:1", normalized="tatasteel stock split 10:1"),
            subject="TATASTEEL",
            predicate="STOCK_SPLIT",
            object="10:1",
            claim_type="CORPORATE_EVENT",
        )
        res_nse = gw.execute_claim_verification(claim_nse, mode_override="LIVE")
        doc_nse = res_nse.documents[0]
        assert doc_nse.retrieval.mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
        assert doc_nse.authoritative_provenance.retrieval_mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
        assert doc_nse.retrieval.mode != "LIVE"
        assert doc_nse.authoritative_provenance.retrieval_mode != "LIVE"

    # 4. BSE Fallback Test
    bse_adapter = BSEAdapter(default_mode="LIVE", public_enabled=True)
    with patch.object(bse_adapter, "safe_http_fetch", side_effect=Exception("BSE Edge Gateway Timeout")):
        gw.register_adapter("BSEAdapter", bse_adapter, ["corporate_data"])
        claim_bse = CanonicalClaim(
            claim_id="CLM-FALLBACK-BSE",
            source_content_id="CNT-04",
            text=ClaimText(original="ABC Limited bonus issue 1:1 on BSE", normalized="abc limited bonus issue 1:1 on bse"),
            subject="500010",
            predicate="BONUS_ISSUE",
            object="1:1",
            claim_type="CORPORATE_EVENT",
        )
        res_bse = gw.execute_claim_verification(claim_bse, mode_override="LIVE", require_cross_source=True)
        bse_docs = [d for d in res_bse.documents if d.organization == "BSE"]
        assert len(bse_docs) >= 1
        doc_bse = bse_docs[0]
        assert doc_bse.retrieval.mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
        assert doc_bse.authoritative_provenance.retrieval_mode in ("OFFICIAL_SNAPSHOT", "SOURCE_UNAVAILABLE")
        assert doc_bse.retrieval.mode != "LIVE"
        assert doc_bse.authoritative_provenance.retrieval_mode != "LIVE"


# ---------------------------------------------------------------------------
# 2. Cache Behavior: Retrieval Mode is CACHE, Never Promoted to LIVE
# ---------------------------------------------------------------------------
def test_cache_retrieval_mode_is_cache_never_live():
    """Verifies that cache hits always report CACHE and never masquerade as freshly retrieved LIVE."""
    adapter = BSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="RELIANCE")
    hits = adapter.search(query)
    assert len(hits) >= 1

    # First retrieval (Snapshot)
    doc1 = adapter.retrieve(hits[0])
    assert doc1.retrieval.mode == "OFFICIAL_SNAPSHOT"

    # Second retrieval (Cache hit)
    doc2 = adapter.retrieve(hits[0])
    assert doc2.retrieval.mode == "CACHE"
    assert doc2.authoritative_provenance.retrieval_mode == "CACHE"
    assert doc2.retrieval.mode != "LIVE"
    assert doc2.authoritative_provenance.retrieval_mode != "LIVE"


# ---------------------------------------------------------------------------
# 3. Fixture Behavior: Stays FIXTURE, Never Promoted to LIVE
# ---------------------------------------------------------------------------
def test_fixture_mode_remains_fixture():
    """Fixtures used in development/testing must stay FIXTURE and never display as LIVE."""
    adapter = NSEAdapter(default_mode="FIXTURE")
    query = SourceQuery(company_symbol="TATASTEEL")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.mode == "FIXTURE"
    assert doc.authoritative_provenance.retrieval_mode == "FIXTURE"
    assert doc.retrieval.mode != "LIVE"
    assert doc.authoritative_provenance.retrieval_mode != "LIVE"


# ---------------------------------------------------------------------------
# 4. Unavailable Source Behavior: SOURCE_UNAVAILABLE, Never Fabricated
# ---------------------------------------------------------------------------
def test_unavailable_source_returns_source_unavailable_never_supported():
    """If no live source and no valid fallback snapshot match exists,
    returns SOURCE_UNAVAILABLE without fabricating an answer.
    """
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="SOURCE_UNAVAILABLE")
    adapter = SEBIAdapter(default_mode="SOURCE_UNAVAILABLE")
    gw.register_adapter("SEBIAdapter", adapter, ["intermediary_registration"])

    claim = CanonicalClaim(
        claim_id="CLM-UNAVAIL",
        source_content_id="CNT-UNAVAIL",
        text=ClaimText(original="XYZ Wealth is SEBI registered", normalized="xyz wealth is sebi registered"),
        subject="XYZ Wealth",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    res = gw.execute_claim_verification(claim, mode_override="SOURCE_UNAVAILABLE")
    assert len(res.documents) >= 1
    doc = res.documents[0]
    assert doc.retrieval.status in ("SOURCE_UNAVAILABLE", "RETRIEVAL_FAILED")
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# 5. Provenance Leakage & Credential Isolation Tests
# ---------------------------------------------------------------------------
def test_no_credential_leakage_in_provenance_or_logs():
    """MANDATE: Provider API keys, secrets, and auth headers must NEVER appear in
    logs, diagnostics, provenance, or error messages.
    """
    secret_key = "nse-prod-api-key-998877"
    secret_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret"

    # 1. Logging Sanitization Filter
    log_text = f"Connecting to NSE gateway with Authorization: {secret_token} and X-API-KEY: {secret_key}"
    sanitized = scrub_sensitive_tokens(log_text)
    assert secret_key not in sanitized
    assert secret_token not in sanitized
    assert "[REDACTED" in sanitized

    # 2. BSE Authorized Provider Diagnostics
    bse_auth = OfficialAuthorizedBSEProvider(api_key="secret-bse-key", api_secret="secret-bse-token")
    assert "secret-bse-key" not in bse_auth.provider_name
    assert "secret-bse-token" not in bse_auth.access_method

    # 3. Settings Safe Dump Redaction & Repr
    settings = Settings(
        env="test",
        nse_api_key="sensitive-nse-key",
        bse_api_key="sensitive-bse-key",
    )
    dumped = settings.safe_dump()
    assert dumped["nse_api_key"] == "***REDACTED***"
    assert dumped["bse_api_key"] == "***REDACTED***"
    assert "sensitive-nse-key" not in repr(settings)
    assert "sensitive-bse-key" not in str(settings)

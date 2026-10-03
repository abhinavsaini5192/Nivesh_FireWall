"""Tests for Live-vs-Fallback Safety & Mode Separation (Phase 15.A).

Verifies the foundational safety invariant:
- LIVE success -> LIVE
- LIVE failure + official snapshot -> OFFICIAL_SNAPSHOT
- LIVE failure + valid cache -> CACHE
- TEST MODE -> FIXTURE
- No trustworthy evidence -> SOURCE_UNAVAILABLE
- A fallback MUST NEVER silently become SUPPORTED + LIVE.
"""

import pytest
from unittest.mock import patch
import pytest
from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim, ClaimText
from nivesh.schemas.sources import SourceQuery
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.gateway import AuthoritativeSourceGateway


def test_safety_live_success_produces_live():
    """Live network query success produces explicit LIVE retrieval mode."""
    adapter = SEBIAdapter(default_mode="LIVE")
    mock_html = "<table><tr><td>INA000000001</td><td>Narayanan S.</td><td>Investment Adviser</td></tr></table>"
    query = SourceQuery(registration_number="INA000000001")

    with patch.object(adapter, "safe_http_fetch", return_value=(200, mock_html, {})):
        hits = adapter.search(query)
        doc = adapter.retrieve(hits[0])
        assert doc.retrieval.mode == "LIVE"
        assert doc.authoritative_provenance.retrieval_mode == "LIVE"
        assert doc.authoritative_provenance.freshness == "CURRENT"


def test_safety_live_failure_falls_to_official_snapshot_never_live():
    """Live failure with pre-downloaded regulatory dataset produces OFFICIAL_SNAPSHOT, NEVER LIVE."""
    adapter = SEBIAdapter(default_mode="LIVE")
    query = SourceQuery(registration_number="INA000000001")

    with patch.object(adapter, "safe_http_fetch", side_effect=Exception("Timeout")):
        hits = adapter.search(query)
        doc = adapter.retrieve(hits[0])
        assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.freshness == "SNAPSHOT"
        # Invariant: Never claim live when using pre-downloaded snapshot
        assert doc.retrieval.mode != "LIVE"
        assert doc.authoritative_provenance.retrieval_mode != "LIVE"


def test_safety_cache_hit_produces_cache_never_live():
    """Subsequent retrieval from cache produces CACHE mode, never LIVE."""
    adapter = SEBIAdapter(default_mode="LIVE")
    mock_html = "<table><tr><td>INA000000001</td><td>Narayanan S.</td><td>Investment Adviser</td></tr></table>"
    query = SourceQuery(registration_number="INA000000001")

    with patch.object(adapter, "safe_http_fetch", return_value=(200, mock_html, {})):
        hits = adapter.search(query)
        doc1 = adapter.retrieve(hits[0])
        assert doc1.retrieval.mode == "LIVE"

    # Second call should be a cache hit
    doc2 = adapter.retrieve(hits[0])
    assert doc2.retrieval.mode == "CACHE"
    assert doc2.authoritative_provenance.retrieval_mode == "CACHE"
    assert doc2.retrieval.mode != "LIVE"
    assert doc2.authoritative_provenance.retrieval_mode != "LIVE"


def test_safety_test_mode_produces_fixture():
    """Test environment produces FIXTURE mode."""
    adapter = SEBIAdapter(default_mode="FIXTURE")
    query = SourceQuery(registration_number="INA000000001")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.mode == "FIXTURE"
    assert doc.authoritative_provenance.retrieval_mode == "FIXTURE"
    assert doc.retrieval.mode != "LIVE"


def test_safety_no_trustworthy_evidence_produces_unavailable():
    """When source is unreachable and no snapshot/cache exists, status is SOURCE_UNAVAILABLE."""
    adapter = SEBIAdapter(default_mode="SOURCE_UNAVAILABLE")
    query = SourceQuery(registration_number="INA000000001")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.freshness == "UNKNOWN"


def test_gateway_fallback_never_silently_becomes_live():
    """Gateway verification under network failure falls back to snapshot, never marking as LIVE."""
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        sebi_live_enabled=True,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    adapter = SEBIAdapter(default_mode="LIVE")
    gw.register_adapter("SEBIAdapter", adapter, ["intermediary_registration"])

    claim = CanonicalClaim(
        claim_id="CLM-SAFE-01",
        source_content_id="CNT-01",
        text=ClaimText(original="Narayanan S. is registered with SEBI", normalized="Narayanan S. registered with SEBI"),
        subject="Narayanan S.",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    with patch.object(adapter, "safe_http_fetch", side_effect=Exception("Upstream network error")):
        res = gw.execute_claim_verification(claim)
        assert len(res.documents) >= 1
        for doc in res.documents:
            assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
            assert doc.retrieval.mode != "LIVE"
            assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
            assert doc.authoritative_provenance.retrieval_mode != "LIVE"
        for prov in res.authoritative_provenances:
            assert prov.retrieval_mode != "LIVE"


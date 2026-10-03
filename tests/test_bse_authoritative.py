"""Tests for BSE Authoritative Integration (Phase 15.A.3).

Verifies:
- BSE Corporate Data API integration
- Server-side credentials loading & zero credential leakage
- Authenticated success vs unauthorized access
- Timeout, malformed response, and source unavailable handling
- Provenance and acknowledgement tracking
"""

import pytest
from unittest.mock import patch
from nivesh.schemas.sources import SourceQuery
from nivesh.sources.adapters.bse_adapter import BSEAdapter


@pytest.fixture
def bse_snapshot_adapter():
    return BSEAdapter(default_mode="OFFICIAL_SNAPSHOT")


def test_bse_corporate_action_lookup(bse_snapshot_adapter):
    """Verifies retrieval of official 1:1 bonus issue disclosure for ABC Limited."""
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = bse_snapshot_adapter.search(query)
    assert len(hits) >= 1

    doc = bse_snapshot_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert "Bonus Issue in 1:1 Ratio" in doc.content
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.source == "BSE"
    assert doc.authoritative_provenance.source_record_id == "BSE/CORP/DISC/2025/06/99312"


def test_bse_live_unauthorized_without_credentials():
    """Verifies that attempting live BSE API query without credentials returns UNAUTHORIZED / SOURCE_UNAVAILABLE."""
    adapter = BSEAdapter(default_mode="LIVE", api_key=None)
    query = SourceQuery(company_symbol="ABC")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status in ("UNAUTHORIZED", "SOURCE_UNAVAILABLE", "CREDENTIALS_MISSING")
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert "BSE_API_KEY" in doc.content or "credentials" in doc.content


def test_bse_live_authenticated_success():
    """Verifies successful live BSE API call with valid server-side API key."""
    adapter = BSEAdapter(default_mode="LIVE", api_key="secret-test-key-12345")
    query = SourceQuery(company_symbol="ABC")
    hits = adapter.search(query)

    mock_json = '{"scrip": "500010", "announcements": [{"id": "1", "title": "Bonus Issue 1:1"}]}'
    with patch.object(adapter, "safe_http_fetch", return_value=(200, mock_json, {})):
        doc = adapter.retrieve(hits[0])
        assert doc.retrieval.status == "SUCCESS"
        assert doc.retrieval.mode == "LIVE"
        assert doc.authoritative_provenance.retrieval_mode == "LIVE"
        assert doc.authoritative_provenance.freshness == "CURRENT"
        # Verify ZERO credentials leaked into document or provenance
        assert "secret-test-key-12345" not in doc.content
        assert "secret-test-key-12345" not in str(doc.metadata)
        assert "secret-test-key-12345" not in str(doc.authoritative_provenance)


def test_bse_malformed_upstream_response_fallback():
    """Verifies that malformed JSON from BSE API falls back to snapshot safely without crashing."""
    adapter = BSEAdapter(default_mode="LIVE", api_key="valid-key")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = adapter.search(query)

    with patch.object(adapter, "safe_http_fetch", return_value=(200, "INVALID NON-JSON HTML", {})):
        doc = adapter.retrieve(hits[0])
        assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc.retrieval.status == "SUCCESS"
        assert "Bonus Issue in 1:1 Ratio" in doc.content

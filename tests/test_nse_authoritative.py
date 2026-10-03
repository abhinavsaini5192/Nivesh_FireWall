"""Tests for NSE Authoritative Integration (Phase 15.A.3).

Verifies:
- Official corporate filings, announcements, and corporate actions
- Record found vs record not found
- Server-side credentials and authentication error handling
- Unavailability handling
- Full provenance and accession number tracking
"""

import pytest
from unittest.mock import patch
from nivesh.schemas.sources import SourceQuery
from nivesh.sources.adapters.nse_adapter import NSEAdapter


@pytest.fixture
def nse_snapshot_adapter():
    return NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")


def test_nse_bonus_action_filing(nse_snapshot_adapter):
    """Verifies retrieval of official 1:1 bonus issue filing for ABC Limited."""
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = nse_snapshot_adapter.search(query)
    assert len(hits) >= 1
    assert "ABC" in hits[0].title

    doc = nse_snapshot_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert "Bonus Ratio: 1:1" in doc.content
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.source == "NSE"
    assert doc.authoritative_provenance.source_record_id == "NSE/CORP/ACTION/2025/06/11245"


def test_nse_financial_results_filing(nse_snapshot_adapter):
    """Verifies retrieval of audited financial results filing."""
    query = SourceQuery(company_symbol="ABC", keywords=["profit", "financial results"])
    hits = nse_snapshot_adapter.search(query)
    assert len(hits) >= 1

    doc = nse_snapshot_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert "₹40.25 Crore" in doc.content
    assert "Zero Long-Term Debt" in doc.content


def test_nse_nonexistent_company_no_match(nse_snapshot_adapter):
    """Verifies that an unknown symbol returns NO_MATCH without crashing or fabricating."""
    query = SourceQuery(company_symbol="NONEXISTENT_XYZ", keywords=["bonus"])
    hits = nse_snapshot_adapter.search(query)
    doc = nse_snapshot_adapter.retrieve(hits[0])

    assert doc.retrieval.status == "NO_MATCH"
    assert doc.metadata.get("matched") is False
    assert "NO_RECORDS_FOUND" in doc.content


def test_nse_source_unavailable():
    """Verifies graceful handling when NSE portal is unreachable."""
    adapter = NSEAdapter(default_mode="SOURCE_UNAVAILABLE")
    query = SourceQuery(company_symbol="ABC")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"


def test_nse_live_auth_failure_falls_to_snapshot():
    """Verifies that authentication errors in live mode fall back to snapshot, never claiming LIVE."""
    adapter = NSEAdapter(default_mode="LIVE", api_key="INVALID_KEY")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = adapter.search(query)

    with patch.object(adapter, "safe_http_fetch", return_value=(401, "Unauthorized", {})):
        doc = adapter.retrieve(hits[0])
        assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.freshness == "SNAPSHOT"

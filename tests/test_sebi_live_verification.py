"""Tests for SEBI Authoritative Verification (Phase 15.A.2).

Verifies:
- Legitimate public intermediary lookup across categories (IA, RA, Stock Broker, PMS)
- Valid registration -> MATCH / ESTABLISHED
- Nonexistent registration -> NO_MATCH / NOT_ESTABLISHED (never a fraud accusation)
- Name difference -> Identity resolution preserved
- Source unreachable -> SOURCE_UNAVAILABLE
- Provenance, timestamp, freshness, and snapshot isolation
"""

import pytest
from unittest.mock import patch
from nivesh.schemas.sources import SourceQuery
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter


@pytest.fixture
def sebi_fixture_adapter():
    return SEBIAdapter(default_mode="FIXTURE")


@pytest.fixture
def sebi_snapshot_adapter():
    return SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT")


@pytest.fixture
def sebi_live_adapter():
    return SEBIAdapter(default_mode="LIVE")


def test_sebi_valid_investment_adviser_lookup(sebi_snapshot_adapter):
    """Tests looking up a valid registered Investment Adviser (Individual)."""
    query = SourceQuery(registration_number="INA000000001")
    search_hits = sebi_snapshot_adapter.search(query)
    assert len(search_hits) >= 1

    doc = sebi_snapshot_adapter.retrieve(search_hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert "Narayanan S." in doc.content
    assert "INA000000001" in doc.content
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.freshness == "SNAPSHOT"
    assert doc.authoritative_provenance.source == "SEBI"


def test_sebi_valid_research_analyst_lookup(sebi_snapshot_adapter):
    """Tests looking up a valid Research Analyst (INH category)."""
    query = SourceQuery(registration_number="INH000001234")
    search_hits = sebi_snapshot_adapter.search(query)
    assert len(search_hits) >= 1

    doc = sebi_snapshot_adapter.retrieve(search_hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert "Kavita Sharma" in doc.content
    assert "Research Analyst" in doc.content


def test_sebi_valid_stock_broker_lookup(sebi_snapshot_adapter):
    """Tests looking up a valid registered Stock Broker (INZ category)."""
    query = SourceQuery(registration_number="INZ000200000")
    search_hits = sebi_snapshot_adapter.search(query)
    doc = sebi_snapshot_adapter.retrieve(search_hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert "Alpha Capital Securities" in doc.content
    assert "Stock Broker" in doc.content


def test_sebi_valid_portfolio_manager_lookup(sebi_snapshot_adapter):
    """Tests looking up a valid Portfolio Manager (INP category)."""
    query = SourceQuery(registration_number="INP000006789")
    search_hits = sebi_snapshot_adapter.search(query)
    doc = sebi_snapshot_adapter.retrieve(search_hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert "Horizon Portfolio Managers" in doc.content
    assert "Portfolio Manager" in doc.content


def test_sebi_nonexistent_registration_no_match(sebi_snapshot_adapter):
    """Tests that a nonexistent registration number yields explicit NO_MATCH without fraud accusations."""
    query = SourceQuery(registration_number="INA999999999")
    search_hits = sebi_snapshot_adapter.search(query)
    assert len(search_hits) >= 1

    doc = sebi_snapshot_adapter.retrieve(search_hits[0])
    assert doc.retrieval.status == "NO_MATCH"
    assert doc.metadata.get("matched") is False
    assert "0" in doc.content or "NO_RECORDS_FOUND" in doc.content
    # Never accuse of fraud
    assert "fraud" not in doc.content.lower()
    assert "scam" not in doc.content.lower()


def test_sebi_claimed_name_differs_from_registered_entity(sebi_snapshot_adapter):
    """Tests lookup when claimed entity name does not match the registered entity."""
    query = SourceQuery(name="Bogus Fake Advisors", registration_number="INA000000001")
    search_hits = sebi_snapshot_adapter.search(query)
    doc = sebi_snapshot_adapter.retrieve(search_hits[0])
    # The registration number matches Narayanan S., not Bogus Fake Advisors
    assert doc.retrieval.status == "SUCCESS"
    assert doc.metadata.get("name") == "Narayanan S."
    assert "Bogus Fake Advisors" not in doc.metadata.get("name")


def test_sebi_source_unreachable_handling():
    """Tests handling when SEBI public portal is unreachable or down."""
    adapter = SEBIAdapter(default_mode="SOURCE_UNAVAILABLE")
    query = SourceQuery(registration_number="INA000000001")
    search_hits = adapter.search(query)
    doc = adapter.retrieve(search_hits[0])

    assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.freshness == "UNKNOWN"


def test_sebi_live_network_success():
    """Tests legitimate live HTTP query parsing when SEBI returns official HTML results table."""
    adapter = SEBIAdapter(default_mode="LIVE")
    query = SourceQuery(registration_number="INA000000001")
    search_hits = adapter.search(query)

    mock_html = """
    <html>
      <body>
        <table>
          <tr><th>Reg No</th><th>Name</th><th>Category</th></tr>
          <tr><td>INA000000001</td><td>Narayanan S.</td><td>Investment Adviser (Individual)</td></tr>
        </table>
      </body>
    </html>
    """

    with patch.object(adapter, "safe_http_fetch", return_value=(200, mock_html, {})):
        doc = adapter.retrieve(search_hits[0])
        assert doc.retrieval.status == "SUCCESS"
        assert doc.retrieval.mode == "LIVE"
        assert doc.authoritative_provenance.retrieval_mode == "LIVE"
        assert doc.authoritative_provenance.freshness == "CURRENT"
        assert "Narayanan S." in doc.content


def test_sebi_live_network_failure_falls_back_to_official_snapshot():
    """Tests that network timeout during live query falls back to OFFICIAL_SNAPSHOT, never claiming LIVE."""
    adapter = SEBIAdapter(default_mode="LIVE")
    query = SourceQuery(registration_number="INA000000001")
    search_hits = adapter.search(query)

    with patch.object(adapter, "safe_http_fetch", side_effect=Exception("Connection timed out after 5.0s")):
        doc = adapter.retrieve(search_hits[0])
        # Crucial safety mandate: MUST be OFFICIAL_SNAPSHOT, never LIVE
        assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.freshness == "SNAPSHOT"
        assert doc.retrieval.status == "SUCCESS"
        assert "Narayanan S." in doc.content

"""Tests for RBI Authoritative Integration (Phase 15.A.3).

Verifies:
- Official Database on Indian Economy (DBIE) and regulatory circular access
- Monetary Policy Committee benchmark repo rate dataset
- Master directions on prohibition of prize chits / MLM schemes
- Registered entity / NBFC verification
- Mode handling and truthful provenance
"""

import pytest
from unittest.mock import patch
from nivesh.schemas.sources import SourceQuery
from nivesh.sources.adapters.rbi_adapter import RBIAdapter


@pytest.fixture
def rbi_adapter():
    return RBIAdapter(default_mode="OFFICIAL_SNAPSHOT")


def test_rbi_mpc_policy_rate_dataset(rbi_adapter):
    """Verifies retrieval of official MPC policy repo rate benchmark dataset."""
    query = SourceQuery(keywords=["repo rate", "policy rate", "mpc"])
    hits = rbi_adapter.search(query)
    assert len(hits) >= 1
    assert "Policy Repo Rate" in hits[0].title

    doc = rbi_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert "6.50%" in doc.content
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.source == "RBI"
    assert doc.authoritative_provenance.freshness == "SNAPSHOT"


def test_rbi_statutory_advisory_mlm_prohibition(rbi_adapter):
    """Verifies retrieval of RBI statutory directions against illegal MLM / deposit schemes."""
    query = SourceQuery(keywords=["mlm", "unauthorized deposit", "guarantee"])
    hits = rbi_adapter.search(query)
    assert len(hits) >= 1
    assert "Multi-Level Marketing" in hits[0].title or "Illegal" in hits[0].title

    doc = rbi_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert "Prize Chits and Money Circulation Schemes" in doc.content


def test_rbi_registered_nbfc_lookup(rbi_adapter):
    """Verifies retrieval of registered NBFC authorization records."""
    query = SourceQuery(name="Bajaj Finance", registration_number="B-13.00407")
    hits = rbi_adapter.search(query)
    assert len(hits) >= 1

    doc = rbi_adapter.retrieve(hits[0])
    # When found in snapshot dataset
    assert doc.retrieval.status in ("SUCCESS", "NO_MATCH")
    assert doc.authoritative_provenance.source == "RBI"


def test_rbi_source_unavailable():
    """Verifies graceful handling when RBI portal is unreachable."""
    adapter = RBIAdapter(default_mode="SOURCE_UNAVAILABLE")
    query = SourceQuery(keywords=["repo rate"])
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"


def test_rbi_live_network_fetch_success():
    """Verifies live query handling with truthful LIVE provenance."""
    adapter = RBIAdapter(default_mode="LIVE")
    query = SourceQuery(keywords=["repo rate"])
    hits = adapter.search(query)

    mock_resp = "RESERVE BANK OF INDIA - LIVE MPC RESOLUTION 2026: Repo Rate 6.50%"
    with patch.object(adapter, "safe_http_fetch", return_value=(200, mock_resp, {})):
        doc = adapter.retrieve(hits[0])
        assert doc.retrieval.status == "SUCCESS"
        assert doc.retrieval.mode == "LIVE"
        assert doc.authoritative_provenance.retrieval_mode == "LIVE"
        assert doc.authoritative_provenance.freshness == "CURRENT"

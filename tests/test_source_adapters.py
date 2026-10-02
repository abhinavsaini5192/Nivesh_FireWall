"""Unit tests for Source Adapters in Engine 4."""

from nivesh.schemas.sources import SourceQuery
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.boundary_adapters import BSEAdapter, RBIAdapter, CompanySourceAdapter
from nivesh.sources.cache import SourceCache


def test_sebi_adapter_registered_entity_lookup():
    cache = SourceCache()
    adapter = SEBIAdapter(cache=cache, default_mode="FIXTURE")

    # Query for registered adviser Amit Patel
    query = SourceQuery(name="Amit Patel", keywords=["advisor", "sebi"])
    search_hits = adapter.search(query)
    assert len(search_hits) > 0

    doc = adapter.retrieve(search_hits[0])
    assert doc.organization == "SEBI"
    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "FIXTURE"
    assert "Amit Patel" in doc.content
    assert "INA000012345" in doc.content


def test_sebi_adapter_unregistered_entity_no_match():
    cache = SourceCache()
    adapter = SEBIAdapter(cache=cache, default_mode="FIXTURE")

    # Query for unregistered advisor Rahul Sharma
    query = SourceQuery(name="Rahul Sharma", keywords=["advisor"])
    search_hits = adapter.search(query)
    assert len(search_hits) > 0

    doc = adapter.retrieve(search_hits[0])
    assert doc.organization == "SEBI"
    assert doc.retrieval.status == "NO_MATCH"
    assert "NO_RECORDS_FOUND" in doc.content
    assert "https://www.sebi.gov.in" in doc.url


def test_sebi_adapter_statutory_prohibition_query():
    adapter = SEBIAdapter(default_mode="FIXTURE")
    query = SourceQuery(keywords=["guaranteed returns prohibition", "investment advisers"])
    search_hits = adapter.search(query)
    assert len(search_hits) > 0

    doc = adapter.retrieve(search_hits[0])
    assert doc.organization == "SEBI"
    assert doc.source_type == "REGULATOR"
    assert doc.retrieval.status == "SUCCESS"
    assert "Prohibition on Assured / Guaranteed Returns" in doc.content


def test_sebi_adapter_cache_hit():
    cache = SourceCache()
    adapter = SEBIAdapter(cache=cache, default_mode="FIXTURE")

    query = SourceQuery(registration_number="INA000000001")
    search_hits = adapter.search(query)
    doc1 = adapter.retrieve(search_hits[0])
    assert doc1.retrieval.mode == "FIXTURE"

    # Second call must hit cache and return mode="CACHE"
    doc2 = adapter.retrieve(search_hits[0])
    assert doc2.retrieval.mode == "CACHE"
    assert doc2.document_id == doc1.document_id


def test_nse_adapter_bonus_corporate_action():
    adapter = NSEAdapter(default_mode="FIXTURE")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus", "1:1"])
    search_hits = adapter.search(query)
    assert len(search_hits) > 0

    doc = adapter.retrieve(search_hits[0])
    assert doc.organization == "NSE"
    assert doc.source_type == "CORPORATE_ACTION"
    assert doc.retrieval.status == "SUCCESS"
    assert "1:1" in doc.content
    assert doc.published_at == "2025-06-15T11:30:00Z"


def test_nse_adapter_unmatched_announcement():
    adapter = NSEAdapter(default_mode="FIXTURE")
    query = SourceQuery(company_symbol="NONEXISTENT_CO", keywords=["bonus"])
    search_hits = adapter.search(query)
    assert len(search_hits) > 0

    doc = adapter.retrieve(search_hits[0])
    assert doc.retrieval.status == "NO_MATCH"
    assert "NO_RECORDS_FOUND" in doc.content


def test_boundary_adapters_return_source_unavailable():
    bse = BSEAdapter()
    hits = bse.search(SourceQuery(company_symbol="XYZ"))
    doc = bse.retrieve(hits[0])
    assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
    assert "unconfigured" in doc.content.lower()

    rbi = RBIAdapter()
    rbi_hits = rbi.search(SourceQuery(keywords=["nbfc"]))
    rbi_doc = rbi.retrieve(rbi_hits[0])
    assert rbi_doc.retrieval.status == "SOURCE_UNAVAILABLE"

    comp = CompanySourceAdapter()
    comp_hits = comp.search(SourceQuery(company_name="Acme"))
    comp_doc = comp.retrieve(comp_hits[0])
    assert comp_doc.retrieval.status == "SOURCE_UNAVAILABLE"

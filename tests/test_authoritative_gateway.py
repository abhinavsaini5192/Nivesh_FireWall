"""Tests for the Authoritative Source Gateway (Phase 15.A).

Verifies:
- Gateway initialization and capability declarations
- Dynamic access mode resolution
- Claim routing and source selection without hardcoding
- Truthful provenance preservation (never faking LIVE)
"""

import pytest
from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import SourceQuery, SourcePlan
from nivesh.sources.catalog import SourceCatalog
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter


@pytest.fixture
def gateway():
    catalog = SourceCatalog()
    settings = Settings(
        env="test",
        source_mode="FIXTURE",
        live_sources_enabled=False,
        sebi_live_enabled=False,
        rbi_live_enabled=False,
        nse_live_enabled=False,
        bse_live_enabled=False,
    )
    gw = AuthoritativeSourceGateway(catalog=catalog, settings=settings, default_mode="FIXTURE")

    # Register all primary adapters
    gw.register_adapter("SEBIAdapter", SEBIAdapter(default_mode="FIXTURE"), ["intermediary_registration", "regulatory_documents", "circulars", "notices"])
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="FIXTURE"), ["corporate_announcements", "filings", "corporate_actions", "company_disclosures"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="FIXTURE"), ["corporate_data", "disclosures", "announcements", "corporate_actions"])
    gw.register_adapter("RBIAdapter", RBIAdapter(default_mode="FIXTURE"), ["official_data", "regulatory_publications", "supported_entity_information"])

    return gw


def test_gateway_capabilities_registration(gateway):
    """Verifies that adapters declare genuine, verifiable capabilities."""
    sebi_caps = gateway.get_capabilities("SEBIAdapter")
    assert "intermediary_registration" in sebi_caps
    assert "circulars" in sebi_caps

    nse_caps = gateway.get_capabilities("NSEAdapter")
    assert "corporate_announcements" in nse_caps
    assert "corporate_actions" in nse_caps

    bse_caps = gateway.get_capabilities("BSEAdapter")
    assert "corporate_data" in bse_caps
    assert "disclosures" in bse_caps

    rbi_caps = gateway.get_capabilities("RBIAdapter")
    assert "official_data" in rbi_caps
    assert "regulatory_publications" in rbi_caps


def test_gateway_mode_resolution_fixture(gateway):
    """Verifies that FIXTURE mode remains FIXTURE without live calls."""
    mode, reason = gateway.resolve_access_mode("sebi_recognised_intermediaries", "FIXTURE")
    assert mode == "FIXTURE"
    assert reason is None


def test_gateway_mode_resolution_live_disabled_falls_to_snapshot(gateway):
    """Verifies that requesting LIVE when live queries are disabled falls back to OFFICIAL_SNAPSHOT."""
    mode, reason = gateway.resolve_access_mode("sebi_recognised_intermediaries", "LIVE")
    assert mode == "OFFICIAL_SNAPSHOT"
    assert "disabled" in reason.lower() or "snapshot" in reason.lower()


def test_gateway_mode_resolution_bse_missing_credentials():
    """Verifies that BSE live access without credentials yields SOURCE_UNAVAILABLE."""
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        bse_live_enabled=True,
        bse_api_key=None,  # No credentials
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    mode, reason = gw.resolve_access_mode("bse_corporate_filings", "LIVE")
    assert mode == "SOURCE_UNAVAILABLE"
    assert "BSE_API_KEY" in reason


def test_gateway_execute_sebi_claim(gateway):
    """Verifies gateway end-to-end claim verification with SEBI intermediary lookup."""
    from nivesh.schemas.claims import ClaimText
    claim = CanonicalClaim(
        claim_id="CLM-001",
        source_content_id="CNT-001",
        text=ClaimText(original="Narayanan S. is registered with SEBI", normalized="Narayanan S. registered with SEBI"),
        subject="Narayanan S.",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    result = gateway.execute_claim_verification(claim)
    assert result.claim_id == "CLM-001"
    assert len(result.documents) >= 1
    doc = result.documents[0]
    assert doc.organization == "SEBI"
    assert doc.retrieval.status == "SUCCESS"
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.retrieval_mode == "FIXTURE"
    assert doc.authoritative_provenance.source == "SEBI"


def test_gateway_provenance_truthfulness(gateway):
    """Verifies that provenance NEVER represents FIXTURE as LIVE."""
    from nivesh.schemas.claims import ClaimText
    claim = CanonicalClaim(
        claim_id="CLM-002",
        source_content_id="CNT-002",
        text=ClaimText(original="ABC Limited announced 1:1 bonus", normalized="ABC Limited announced 1:1 bonus"),
        subject="ABC Limited",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    result = gateway.execute_claim_verification(claim)
    assert len(result.authoritative_provenances) >= 1
    for prov in result.authoritative_provenances:
        # Crucial mandate: FIXTURE must never be labeled LIVE
        assert prov.retrieval_mode != "LIVE"
        assert prov.retrieval_mode in ("FIXTURE", "OFFICIAL_SNAPSHOT", "CACHE")
        assert prov.freshness in ("HISTORICAL", "SNAPSHOT", "CURRENT")

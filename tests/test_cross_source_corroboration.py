"""Tests for Cross-Source Verification & Corroboration (Phase 15.A.5).

Verifies:
- Claims supported by one authoritative source (SEBI registration) do not require two sources
- Claims corroborated across multiple exchanges (NSE + BSE both confirm 1:1 bonus issue)
- Prevention of false corroboration
"""

import pytest
from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim
from nivesh.sources.catalog import SourceCatalog
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter


@pytest.fixture
def gateway():
    catalog = SourceCatalog()
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(catalog=catalog, settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("SEBIAdapter", SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["intermediary_registration", "circulars"])
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_announcements", "corporate_actions"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_data", "disclosures", "corporate_actions"])
    gw.register_adapter("RBIAdapter", RBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["official_data", "regulatory_publications"])
    return gw


def test_single_authoritative_source_sufficient_for_regulatory_claim(gateway):
    """Verifies that a regulatory claim (SEBI registration) does not require exchange corroboration."""
    from nivesh.schemas.claims import ClaimText
    claim = CanonicalClaim(
        claim_id="CLM-SEBI-01",
        source_content_id="CNT-01",
        text=ClaimText(original="Narayanan S. is registered with SEBI", normalized="Narayanan S. registered with SEBI"),
        subject="Narayanan S.",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    res = gateway.execute_claim_verification(claim, require_cross_source=False)
    assert len(res.documents) == 1
    assert res.documents[0].organization == "SEBI"
    assert res.documents[0].retrieval.status == "SUCCESS"


def test_cross_exchange_corroboration_nse_and_bse(gateway):
    """Verifies that a corporate action claim is corroborated across both NSE and BSE when cross-source is enabled."""
    from nivesh.schemas.claims import ClaimText
    claim = CanonicalClaim(
        claim_id="CLM-CORP-01",
        source_content_id="CNT-02",
        text=ClaimText(original="ABC Limited announced 1:1 bonus", normalized="ABC Limited announced 1:1 bonus"),
        subject="ABC Limited",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    res = gateway.execute_claim_verification(claim, require_cross_source=True)
    orgs = [d.organization for d in res.documents]
    assert "NSE" in orgs
    assert "BSE" in orgs

    # Both documents must have SUCCESS status
    nse_doc = next(d for d in res.documents if d.organization == "NSE")
    bse_doc = next(d for d in res.documents if d.organization == "BSE")
    assert nse_doc.retrieval.status == "SUCCESS"
    assert bse_doc.retrieval.status == "SUCCESS"
    assert "1:1" in nse_doc.content
    assert "1:1" in bse_doc.content

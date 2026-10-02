"""Unit tests for Source Router in Engine 4."""

from nivesh.schemas.claims import CanonicalClaim, ClaimText, TemporalContext
from nivesh.schemas.sources import SourcePlan
from nivesh.sources.router import SourceRouter
from nivesh.sources.catalog import SourceCatalog


def test_route_regulatory_claim():
    router = SourceRouter()
    claim = CanonicalClaim(
        claim_id="CLAIM-001",
        source_content_id="content-1",
        text=ClaimText(original="Rahul Sharma is a SEBI registered advisor", normalized="Rahul Sharma is registered with SEBI."),
        claim_type="REGULATORY",
        subject="Rahul Sharma",
        predicate="REGISTERED_WITH",
        object="SEBI",
        temporal_context=TemporalContext(type="current")
    )

    plan = router.route_claim(claim)
    assert "sebi_recognised_intermediaries" in plan.primary
    assert "REGULATORY_REGISTRY" in plan.required_source_types
    assert plan.query.name == "Rahul Sharma"
    assert plan.query.temporal_focus == "current"


def test_route_guaranteed_return_statutory_claim():
    router = SourceRouter()
    claim = CanonicalClaim(
        claim_id="CLAIM-002",
        source_content_id="content-1",
        text=ClaimText(original="Guaranteed 40% returns.", normalized="40% returns are guaranteed."),
        claim_type="FINANCIAL",
        subject="unspecified_offer",
        predicate="GUARANTEED_RETURN",
        object="40% returns",
        temporal_context=TemporalContext(type="unknown")
    )

    plan = router.route_claim(claim)
    assert "sebi_public_regulatory_pages" in plan.primary
    assert any("guaranteed" in kw for kw in plan.query.keywords)


def test_route_corporate_event_bonus_claim():
    router = SourceRouter()
    claim = CanonicalClaim(
        claim_id="CLAIM-003",
        source_content_id="content-1",
        text=ClaimText(original="ABC announced a 1:1 bonus.", normalized="ABC announced a 1:1 bonus."),
        claim_type="CORPORATE_EVENT",
        subject="ABC",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        temporal_context=TemporalContext(type="historical", date="2025-06-15")
    )

    plan = router.route_claim(claim)
    assert "nse_corporate_actions" in plan.primary
    assert "CORPORATE_ACTION" in plan.required_source_types
    assert plan.query.company_symbol == "ABC"
    assert "bonus" in plan.query.keywords
    assert plan.query.date_range == ("2025-06-15", "2025-06-15")
    assert plan.query.temporal_focus == "historical"


def test_route_financial_profit_claim():
    router = SourceRouter()
    claim = CanonicalClaim(
        claim_id="CLAIM-004",
        source_content_id="content-1",
        text=ClaimText(original="ABC reported ₹40 crore profit.", normalized="ABC reported ₹40 crore profit."),
        claim_type="FINANCIAL",
        subject="ABC",
        predicate="REPORTED_PROFIT",
        object="₹40 crore",
        temporal_context=TemporalContext(type="historical")
    )

    plan = router.route_claim(claim)
    assert "nse_company_filings" in plan.primary
    assert "FINANCIAL_FILING" in plan.required_source_types
    assert plan.query.company_symbol == "ABC"

"""Primary benchmark fixture test for Engine 4 (Source Intelligence Engine)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine


def test_primary_benchmark_source_intelligence():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000. Contact rahul@example.com."
    )

    # Step 1: Engine 1
    normalized = content_engine.process_text(raw_text)

    # Step 2: Engine 2
    claims = claims_engine.analyze(normalized)
    assert len(claims.claims) == 2
    c1, c2 = claims.claims[0], claims.claims[1]

    # Step 3: Engine 3
    actions = actions_engine.analyze(normalized, claims)
    assert len(actions.actions) == 4

    # Step 4: Engine 4
    source_analysis = sources_engine.discover_and_retrieve(normalized, claims, actions)

    # Verification: IDs preserved
    assert source_analysis.content_id == normalized.content_id
    assert source_analysis.analysis_metadata.claims_processed == 2

    # Verify CLAIM-001 Source Routing and Retrieval
    claim_1_res = next(r for r in source_analysis.claim_sources if r.claim_id == c1.claim_id)
    assert "sebi_recognised_intermediaries" in claim_1_res.source_plan.primary
    assert claim_1_res.source_plan.query.name == "Rahul Sharma"
    assert len(claim_1_res.documents) > 0
    doc_1 = claim_1_res.documents[0]
    assert doc_1.organization == "SEBI"
    assert doc_1.retrieval.status == "NO_MATCH"
    assert "https://www.sebi.gov.in" in doc_1.url
    assert len(claim_1_res.evidence_candidates) > 0
    assert claim_1_res.evidence_candidates[0].verification_status == "UNVERIFIED"

    # Verify CLAIM-002 Source Routing and Retrieval (Guaranteed Returns)
    claim_2_res = next(r for r in source_analysis.claim_sources if r.claim_id == c2.claim_id)
    assert "sebi_public_regulatory_pages" in claim_2_res.source_plan.primary
    assert len(claim_2_res.documents) > 0
    doc_2 = claim_2_res.documents[0]
    assert doc_2.organization == "SEBI"
    assert doc_2.retrieval.status == "SUCCESS"
    assert "prohibition" in doc_2.content.lower() or "guaranteed" in doc_2.content.lower()
    assert len(claim_2_res.evidence_candidates) > 0
    assert claim_2_res.evidence_candidates[0].verification_status == "UNVERIFIED"

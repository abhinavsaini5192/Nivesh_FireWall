"""Integration test for full 4-engine pipeline (Engine 1 -> 2 -> 3 -> 4)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine


def test_full_pipeline_multi_claim_source_retrieval():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")

    input_text = "SEBI registered advisor Rahul Sharma guarantees 40% returns. ABC announced a 1:1 bonus."

    # Engine 1
    normalized = content_engine.process_text(input_text)
    assert normalized.content_id is not None

    # Engine 2
    claims = claims_engine.analyze(normalized)
    assert len(claims.claims) >= 3

    # Engine 3
    actions = actions_engine.analyze(normalized, claims)

    # Engine 4
    source_analysis = sources_engine.discover_and_retrieve(normalized, claims, actions)

    assert source_analysis.content_id == normalized.content_id
    assert len(source_analysis.claim_sources) >= 3

    # Check each claim's corresponding sources
    # 1. Regulatory claim (Rahul Sharma SEBI)
    reg_claim = next(c for c in claims.claims if c.predicate == "REGISTERED_WITH")
    reg_sources = next(s for s in source_analysis.claim_sources if s.claim_id == reg_claim.claim_id)
    assert "sebi_recognised_intermediaries" in reg_sources.source_plan.primary
    assert any(doc.organization == "SEBI" for doc in reg_sources.documents)

    # 2. Guaranteed return claim
    guar_claim = next(c for c in claims.claims if "GUARANTEE" in c.predicate)
    guar_sources = next(s for s in source_analysis.claim_sources if s.claim_id == guar_claim.claim_id)
    assert any(doc.organization == "SEBI" for doc in guar_sources.documents)

    # 3. Bonus announcement claim (ABC 1:1 bonus)
    bonus_claim = next(c for c in claims.claims if c.predicate == "ANNOUNCED_BONUS")
    bonus_sources = next(s for s in source_analysis.claim_sources if s.claim_id == bonus_claim.claim_id)
    assert "nse_corporate_actions" in bonus_sources.source_plan.primary
    assert any(doc.organization == "NSE" for doc in bonus_sources.documents)
    bonus_doc = next(d for d in bonus_sources.documents if d.organization == "NSE")
    assert "1:1" in bonus_doc.content
    assert bonus_doc.retrieval.status == "SUCCESS"

    # Verify no truth decision made
    for src_res in source_analysis.claim_sources:
        for cand in src_res.evidence_candidates:
            assert cand.verification_status == "UNVERIFIED"

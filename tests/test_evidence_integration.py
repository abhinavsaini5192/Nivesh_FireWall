"""Integration test for full 5-engine pipeline (Engine 1 -> 2 -> 3 -> 4 -> 5)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine


def test_full_5_engine_pipeline_end_to_end():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()

    raw_text = (
        "SEBI registered advisor Rahul Sharma guarantees 40% returns. "
        "ABC announced a 1:1 bonus."
    )

    # 1. Engine 1
    normalized = content_engine.process_text(raw_text)
    assert normalized.content_id is not None

    # 2. Engine 2
    claims = claims_engine.analyze(normalized)
    assert len(claims.claims) >= 3

    # 3. Engine 3
    actions = actions_engine.analyze(normalized, claims)

    # 4. Engine 4
    sources = sources_engine.discover_and_retrieve(normalized, claims, actions)
    assert sources.content_id == normalized.content_id

    # 5. Engine 5
    evidence_analysis = evidence_engine.verify(normalized, claims, sources)

    # Verify ID preservation
    assert evidence_analysis.content_id == normalized.content_id
    assert len(evidence_analysis.verifications) == len(claims.claims)

    for v in evidence_analysis.verifications:
        assert v.claim_id is not None
        assert v.status in (
            "SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED",
            "INSUFFICIENT_EVIDENCE", "NOT_VERIFIABLE", "SOURCE_CONFLICT"
        )
        assert v.confidence > 0.0
        assert len(v.reasoning_trace) > 0

    # Specifically check the 1:1 bonus claim verification
    bonus_claim = next(c for c in claims.claims if c.predicate == "ANNOUNCED_BONUS")
    bonus_v = next(v for v in evidence_analysis.verifications if v.claim_id == bonus_claim.claim_id)
    assert bonus_v.status == "SUPPORTED"
    assert len(bonus_v.supporting_evidence) >= 1
    assert bonus_v.supporting_evidence[0].source_document_id is not None
    assert bonus_v.supporting_evidence[0].evidence_id is not None

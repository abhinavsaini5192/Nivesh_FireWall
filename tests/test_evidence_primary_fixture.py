"""Primary benchmark fixture test for Engine 5 (Evidence Verification Engine)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine


def test_primary_benchmark_evidence_verification():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()

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

    # Step 4: Engine 4
    sources = sources_engine.discover_and_retrieve(normalized, claims, actions)

    # Step 5: Engine 5
    evidence_analysis = evidence_engine.verify(normalized, claims, sources)

    assert evidence_analysis.content_id == normalized.content_id
    assert len(evidence_analysis.verifications) == 2

    # Verification 1: Rahul Sharma SEBI registration
    v1 = next(v for v in evidence_analysis.verifications if v.claim_id == c1.claim_id)
    assert v1.status == "INSUFFICIENT_EVIDENCE"
    assert v1.evidence_strength == "HIGH"
    assert len(v1.contradicting_evidence) >= 1
    assert any("returned 0 matches" in step for step in v1.reasoning_trace)
    assert not any("fraudulent" in step.lower() for step in v1.reasoning_trace)
    assert v1.provenance.engine_version == "1.0.0"

    # Verification 2: Guaranteed 40% returns
    v2 = next(v for v in evidence_analysis.verifications if v.claim_id == c2.claim_id)
    assert v2.status != "CONTRADICTED"
    assert v2.status == "INSUFFICIENT_EVIDENCE"
    assert v2.evidence_strength == "HIGH"
    assert len(v2.supporting_evidence) == 0
    assert len(v2.contradicting_evidence) == 0
    assert len(v2.regulatory_findings) >= 1
    assert v2.regulatory_findings[0].type == "REGULATORY_CONFLICT"
    assert any("prohibit" in step.lower() for step in v2.reasoning_trace)
    assert any("40%" in rf.excerpt or "guaranteed" in rf.excerpt.lower() for rf in v2.regulatory_findings)

    # Check aggregate metadata
    assert evidence_analysis.analysis_metadata.total_claims == 2
    assert evidence_analysis.analysis_metadata.claims_contradicted == 0
    assert evidence_analysis.analysis_metadata.claims_insufficient == 2

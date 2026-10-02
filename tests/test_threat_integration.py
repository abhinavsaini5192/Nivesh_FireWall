"""End-to-end integration test for full 6-engine pipeline (Engine 1 -> 2 -> 3 -> 4 -> 5 -> 6)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.schemas.threat import AttackStage, ThreatFamily


def test_full_6_engine_pipeline_end_to_end_preservation():
    # Instantiate all 6 engines
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()

    raw_text = (
        "SEBI registered advisor Rahul Sharma guarantees 40% returns. "
        "Join our Telegram channel: https://t.me/rahulinvest. Download our trading app. "
        "Pay ₹5,000 activation fee."
    )

    # 1. Engine 1
    content = content_engine.process_text(raw_text)
    assert content.content_id is not None

    # 2. Engine 2
    claims = claims_engine.analyze(content)
    assert claims.content_id == content.content_id
    assert len(claims.claims) >= 2
    claim_ids = {c.claim_id for c in claims.claims}

    # 3. Engine 3
    actions = actions_engine.analyze(content, claims)
    assert actions.content_id == content.content_id
    assert len(actions.actions) >= 3
    action_ids = {a.action_id for a in actions.actions}

    # 4. Engine 4
    sources = sources_engine.discover_and_retrieve(content, claims, actions)
    assert sources.content_id == content.content_id
    source_doc_ids = {doc.source_id for cs in sources.claim_sources for doc in cs.documents}

    # 5. Engine 5
    evidence = evidence_engine.verify(content, claims, sources)
    assert evidence.content_id == content.content_id
    assert len(evidence.verifications) == len(claims.claims)
    for v in evidence.verifications:
        assert v.claim_id in claim_ids

    # 6. Engine 6
    threat = threat_engine.analyze(content, claims, actions, sources, evidence)

    # Verify Strict Content ID Preservation
    assert threat.content_id == content.content_id

    # Verify Claim ID Preservation in Threat
    for link in threat.claim_action_links:
        assert link.claim_id in claim_ids
        assert link.action_id in action_ids

    for weakness in threat.evidence_weaknesses:
        if weakness.claim_id:
            assert weakness.claim_id in claim_ids

    # Verify Action ID Preservation in Threat
    for node in threat.attack_path.nodes:
        for aid in node.linked_action_ids:
            assert aid in action_ids

    for hia in threat.high_impact_actions:
        assert hia.action_id in action_ids

    # Verify Provenance Upstream Engine Versions
    assert "content_intelligence" in threat.provenance.upstream_engine_versions
    assert "claim_intelligence" in threat.provenance.upstream_engine_versions
    assert "action_intelligence" in threat.provenance.upstream_engine_versions
    assert "source_intelligence" in threat.provenance.upstream_engine_versions
    assert "evidence_verification" in threat.provenance.upstream_engine_versions


def test_full_6_engine_pipeline_informational_content():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()

    raw_text = "Learn about mutual funds and SIP investments on SEBI investor portal."

    content = content_engine.process_text(raw_text)
    claims = claims_engine.analyze(content)
    actions = actions_engine.analyze(content, claims)
    sources = sources_engine.discover_and_retrieve(content, claims, actions)
    evidence = evidence_engine.verify(content, claims, sources)
    threat = threat_engine.analyze(content, claims, actions, sources, evidence)

    # Should have no threat path and no threat families
    assert threat.content_id == content.content_id
    assert len(threat.threat_families) == 0
    assert len(threat.high_impact_actions) == 0
    assert len(threat.transitions) == 0
    assert threat.confidence == 0.0 or len(threat.threat_signals) == 0

"""Primary benchmark fixture test for Engine 6 (Threat & Attack-Path Intelligence Engine)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.schemas.threat import AttackStage, ThreatFamily, ActionImpactCategory


def test_primary_benchmark_threat_intelligence():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000. Contact rahul@example.com."
    )

    # 1. Engine 1: Content Intelligence
    normalized = content_engine.process_text(raw_text)

    # 2. Engine 2: Claim Intelligence
    claims = claims_engine.analyze(normalized)
    assert len(claims.claims) == 2

    # 3. Engine 3: Action Intelligence
    actions = actions_engine.analyze(normalized, claims)
    assert len(actions.actions) >= 3

    # 4. Engine 4: Source Intelligence
    sources = sources_engine.discover_and_retrieve(normalized, claims, actions)

    # 5. Engine 5: Evidence Verification
    evidence = evidence_engine.verify(normalized, claims, sources)

    # 6. Engine 6: Threat & Attack-Path Intelligence
    threat_analysis = threat_engine.analyze(normalized, claims, actions, sources, evidence)

    # Verify ID preservation
    assert threat_analysis.content_id == normalized.content_id
    assert threat_analysis.provenance.engine_version == "1.0.0"
    assert threat_analysis.provenance.upstream_engine_versions["evidence_verification"] == "1.0.0"

    # Verify Threat Signals
    signal_types = {s.type for s in threat_analysis.threat_signals}
    assert "GUARANTEED_RETURN_LANGUAGE" in signal_types
    assert "PRIVATE_CHANNEL_MIGRATION" in signal_types
    assert "EXTERNAL_APP" in signal_types
    assert "PAYMENT_REQUEST" in signal_types
    assert "REGULATORY_AUTHORITY_CLAIM" in signal_types
    assert "IDENTITY_NOT_ESTABLISHED" in signal_types
    # Must NOT prematurely classify as impersonation without concrete identity mismatch evidence
    assert "AUTHORITY_IMPERSONATION" not in signal_types

    # Verify Signal Provenance
    for signal in threat_analysis.threat_signals:
        assert signal.signal_id is not None
        assert signal.source in [
            "content", "claim", "action", "source_verification", "evidence_verification", "fingerprint_database", "combination"
        ]
        assert 0.0 <= signal.confidence <= 1.0
        assert len(signal.description) > 0

    # Verify Attack Path & Stages
    assert len(threat_analysis.attack_path.nodes) >= 3
    node_stages = [n.stage for n in threat_analysis.attack_path.nodes]
    assert "CHANNEL_MIGRATION" in node_stages
    assert "SOFTWARE_INSTALLATION" in node_stages
    assert "FINANCIAL_REQUEST" in node_stages or "FINANCIAL_TRANSFER" in node_stages

    # Verify Transitions
    assert len(threat_analysis.transitions) >= 2
    transition_pairs = [(t.from_stage, t.to_stage) for t in threat_analysis.transitions]
    assert ("CHANNEL_MIGRATION", "SOFTWARE_INSTALLATION") in transition_pairs or \
           ("TRUST_BUILDING", "CHANNEL_MIGRATION") in transition_pairs

    # Verify High-Impact Actions
    assert len(threat_analysis.high_impact_actions) >= 2
    impact_cats = {hia.impact_category for hia in threat_analysis.high_impact_actions}
    assert "DEVICE" in impact_cats
    assert "FINANCIAL" in impact_cats

    # Verify Claim-Action Links
    # SEBI registration claim must NOT have unjustified blanket action links
    assert not any(l.claim_id == "CLAIM-001" for l in threat_analysis.claim_action_links)
    for link in threat_analysis.claim_action_links:
        assert link.link_id is not None
        assert link.claim_id is not None
        assert link.action_id is not None
        assert link.type in ["RATIONALE_FOR", "JUSTIFIES", "ENABLES", "PRECEDES", "LEADS_TO", "REQUESTS"]

    # Verify Evidence Weaknesses
    assert len(threat_analysis.evidence_weaknesses) >= 1
    weakness_types = {ew.weakness_type for ew in threat_analysis.evidence_weaknesses}
    assert "IDENTITY_NOT_ESTABLISHED" in weakness_types or "REGULATORY_CONFLICT" in weakness_types

    # Verify Multi-Signal Combinations
    assert len(threat_analysis.combinations) >= 1
    comb_mechanisms = {c.mechanism for c in threat_analysis.combinations}
    assert any("transition" in m or "solicitation" in m or "migration" in m for m in comb_mechanisms)

    # Verify Threat Families
    assert len(threat_analysis.threat_families) >= 2
    assert "INVESTMENT_PROMOTION_SCAM" in threat_analysis.threat_families
    assert "PAYMENT_FRAUD" in threat_analysis.threat_families
    assert "MALICIOUS_SOFTWARE" in threat_analysis.threat_families

    # Verify Explanation
    assert len(threat_analysis.explanation.summary) > 0
    assert len(threat_analysis.explanation.key_factors) > 0
    assert len(threat_analysis.uncertainty) > 0
    # Must not contain definitive criminal accusations
    assert "guilty of fraud" not in threat_analysis.explanation.summary.lower()
    assert "is a criminal" not in threat_analysis.explanation.summary.lower()

    # Verify Fingerprint Preparation
    fp = threat_analysis.fingerprint_preparation
    assert len(fp.normalized_claim_patterns) >= 1
    assert len(fp.normalized_action_patterns) >= 1
    assert len(fp.normalized_threat_families) >= 1
    assert len(fp.normalized_attack_stages) >= 3
    assert len(fp.normalized_transitions) >= 1

    # Verify Pattern Confidence (strictly bounded pattern detection confidence, not scam probability)
    assert 0.70 <= threat_analysis.confidence <= 1.0

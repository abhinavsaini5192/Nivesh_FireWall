"""Full end-to-end integration test across Engines 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine


def test_full_pipeline_engines_1_to_7_integration():
    # Instantiate all 7 engines
    engine1 = ContentIntelligenceEngine()
    engine2 = ClaimIntelligenceEngine()
    engine3 = ActionIntelligenceEngine()
    engine4 = SourceIntelligenceEngine(default_mode="FIXTURE")
    engine5 = EvidenceVerificationEngine()
    engine6 = ThreatIntelligenceEngine()
    engine7 = ScamFingerprintEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    # 1. Engine 1
    content = engine1.process_text(raw_text)
    assert bool(content.content_id) and isinstance(content.content_id, str)

    # 2. Engine 2
    claims = engine2.analyze(content)
    assert len(claims.claims) >= 1
    claim_id = claims.claims[0].claim_id

    # 3. Engine 3
    actions = engine3.analyze(content, claims)
    assert len(actions.actions) >= 1
    action_id = actions.actions[0].action_id

    # 4. Engine 4
    sources = engine4.discover_and_retrieve(content, claims, actions)
    assert len(sources.claim_sources) >= 1
    assert len(sources.claim_sources[0].documents) >= 1
    source_doc_id = sources.claim_sources[0].documents[0].document_id

    # 5. Engine 5
    evidence = engine5.verify(content, claims, sources)
    assert len(evidence.verifications) >= 1
    verified_claim_id = evidence.verifications[0].claim_id

    # 6. Engine 6
    threat = engine6.analyze(content, claims, actions, sources, evidence)
    assert threat.content_id == content.content_id
    assert len(threat.threat_signals) >= 1
    assert threat.threat_signals[0].signal_id.startswith("SIG-")

    # 7. Engine 7
    fingerprint_analysis = engine7.create_or_match(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )

    # Preserve and verify IDs across pipeline (Section 47)
    assert fingerprint_analysis.content_id == content.content_id
    assert fingerprint_analysis.fingerprint is not None
    assert fingerprint_analysis.fingerprint.fingerprint_id.startswith("SFP-")
    assert fingerprint_analysis.observation is not None
    assert fingerprint_analysis.observation.content_id == content.content_id

    # Provenance chaining check
    prov = fingerprint_analysis.provenance
    assert prov.engine_version == "1.0.0"
    assert prov.upstream_engine_versions["content_intelligence"] == "1.0.0"
    assert prov.upstream_engine_versions["threat_intelligence"] == "1.0.0"

    # Upstream ID integrity check
    assert claim_id.startswith("CLAIM-") or claim_id.startswith("CLM-")
    assert action_id.startswith("ACTION-") or action_id.startswith("ACT-")
    assert source_doc_id.startswith("DOC-")
    assert verified_claim_id.startswith("CLAIM-") or verified_claim_id.startswith("CLM-")

"""Unit tests for NormalizedFeatureExtractor in Engine 7."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.feature_extractor import NormalizedFeatureExtractor


def test_feature_extraction_canonical_ordering_and_deterministic_signatures():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()
    extractor = NormalizedFeatureExtractor()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    content = content_engine.process_text(raw_text)
    claims = claims_engine.analyze(content)
    actions = actions_engine.analyze(content, claims)
    sources = sources_engine.discover_and_retrieve(content, claims, actions)
    evidence = evidence_engine.verify(content, claims, sources)
    threat = threat_engine.analyze(content, claims, actions, sources, evidence)

    # Extract features twice to verify determinism
    features1 = extractor.extract_features(content, claims, actions, sources, evidence, threat)
    features2 = extractor.extract_features(content, claims, actions, sources, evidence, threat)

    assert features1["exact_signature"] == features2["exact_signature"]
    assert features1["semantic_signature"] == features2["semantic_signature"]
    assert features1["attack_path_signature"] == features2["attack_path_signature"]
    assert features1["content_hash"] == features2["content_hash"]

    # Verify canonical feature ordering (features must be strictly sorted)
    canonical = features1["canonical_features"]
    assert canonical == sorted(canonical)

    # Verify structural components
    assert "CLAIM:GUARANTEED_RETURN" in features1["claim_patterns"]
    assert any("CHANNEL_MIGRATION" in a for a in features1["action_patterns"])
    assert any("PAYMENT" in a for a in features1["action_patterns"])
    assert "IDENTITY:REGULATORY_AUTHORITY_CLAIM" in features1["identity_patterns"]
    assert "CHANNEL_MIGRATION" in features1["attack_stages"]
    assert "FINANCIAL_REQUEST" in features1["attack_stages"]
    assert "CHANNEL_MIGRATION>SOFTWARE_INSTALLATION>FINANCIAL_REQUEST" in features1["attack_path_signature"]


def test_content_hash_does_not_contain_raw_message():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()
    extractor = NormalizedFeatureExtractor()

    raw_text = "SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join Telegram."
    content = content_engine.process_text(raw_text)
    claims = claims_engine.analyze(content)
    actions = actions_engine.analyze(content, claims)
    sources = sources_engine.discover_and_retrieve(content, claims, actions)
    evidence = evidence_engine.verify(content, claims, sources)
    threat = threat_engine.analyze(content, claims, actions, sources, evidence)

    features = extractor.extract_features(content, claims, actions, sources, evidence, threat)
    # The exact signature is a 64-character SHA-256 hex digest, NOT raw string
    assert len(features["exact_signature"]) == 64
    assert len(features["semantic_signature"]) == 64
    assert len(features["content_hash"]) == 64
    assert "Rahul Sharma" not in features["exact_signature"]

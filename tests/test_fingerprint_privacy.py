"""Unit tests for privacy preservation and boundary restrictions in Engine 7."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine


def test_privacy_preservation_no_pii_in_fingerprint():
    """Ensure personal details like names, email, phone numbers are not in fingerprint canonical features."""
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()
    fp_engine = ScamFingerprintEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Call +91-9876543210 or email rahul.sharma99@gmail.com. "
        "Aadhaar verified. Guaranteed 40% returns. Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Pay ₹5,000 to bank account 123456789012."
    )

    content = content_engine.process_text(raw_text)
    claims = claims_engine.analyze(content)
    actions = actions_engine.analyze(content, claims)
    sources = sources_engine.discover_and_retrieve(content, claims, actions)
    evidence = evidence_engine.verify(content, claims, sources)
    threat = threat_engine.analyze(content, claims, actions, sources, evidence)

    analysis = fp_engine.create_or_match(content, claims, actions, sources, evidence, threat)
    fp = analysis.fingerprint

    # Check that PII is NOT present in canonical features or signatures
    for feature in fp.canonical_features:
        assert "Rahul Sharma" not in feature
        assert "9876543210" not in feature
        assert "rahul.sharma99@gmail.com" not in feature
        assert "123456789012" not in feature

    # Collective context for other users must NOT disclose private details
    ctx_str = str(analysis.collective_context)
    assert "Rahul Sharma" not in ctx_str
    assert "9876543210" not in ctx_str
    assert "rahul.sharma99@gmail.com" not in ctx_str
    assert "123456789012" not in ctx_str

    # Must NOT contain scam probability or criminal declaration
    assert "scam_probability" not in ctx_str
    assert "criminal" not in ctx_str.lower()
    assert "is_scammer" not in ctx_str.lower()

"""Unit tests for FingerprintMatcher."""

from nivesh.fingerprints.matcher import FingerprintMatcher
from nivesh.schemas.fingerprint import ScamFingerprint


def make_sample_fingerprint():
    return ScamFingerprint(
        fingerprint_id="SFP-001",
        schema_version="1.0",
        identity_patterns=["IDENTITY:REGULATORY_AUTHORITY_CLAIM"],
        claim_patterns=["CLAIM:GUARANTEED_RETURN"],
        action_patterns=["ACTION:CHANNEL_MIGRATION", "ACTION:SOFTWARE_INSTALLATION", "ACTION:PAYMENT"],
        channel_patterns=["CHANNEL:TELEGRAM"],
        technical_patterns=["TECH:EXTERNAL_APP"],
        threat_patterns=["THREAT:IDENTITY_NOT_ESTABLISHED", "THREAT:REGULATORY_CONFLICT"],
        attack_stages=["CHANNEL_MIGRATION", "SOFTWARE_INSTALLATION", "FINANCIAL_REQUEST"],
        attack_transitions=["CHANNEL_MIGRATION->SOFTWARE_INSTALLATION", "SOFTWARE_INSTALLATION->FINANCIAL_REQUEST"],
        evidence_patterns=["EVIDENCE:UNVERIFIED_REGISTRATION"],
        threat_families=["REGULATORY_IMPERSONATION", "GUARANTEED_RETURN_SCHEME"],
        canonical_features=[
            "ACTION:CHANNEL_MIGRATION",
            "ACTION:PAYMENT",
            "ACTION:SOFTWARE_INSTALLATION",
            "CLAIM:GUARANTEED_RETURN",
            "IDENTITY:REGULATORY_AUTHORITY_CLAIM",
            "STAGE:CHANNEL_MIGRATION",
            "STAGE:FINANCIAL_REQUEST",
            "STAGE:SOFTWARE_INSTALLATION",
        ],
        exact_signature="exact_sig_123",
        semantic_signature="semantic_sig_456",
        attack_path_signature="CHANNEL_MIGRATION>SOFTWARE_INSTALLATION>FINANCIAL_REQUEST",
        created_at="2026-09-18T10:00:00Z",
        updated_at="2026-09-18T10:00:00Z",
        first_seen="2026-09-18T10:00:00Z",
        last_seen="2026-09-18T10:00:00Z",
        observation_count=1,
        status="NEW",
    )


def test_matcher_exact_match():
    matcher = FingerprintMatcher()
    fp = make_sample_fingerprint()

    features = {
        "exact_signature": "exact_sig_123",
        "semantic_signature": "semantic_sig_456",
        "attack_path_signature": fp.attack_path_signature,
        "attack_stages": fp.attack_stages,
        "action_patterns": fp.action_patterns,
        "claim_patterns": fp.claim_patterns,
        "identity_patterns": fp.identity_patterns,
        "threat_patterns": fp.threat_patterns,
        "evidence_patterns": fp.evidence_patterns,
        "channel_patterns": fp.channel_patterns,
        "technical_patterns": fp.technical_patterns,
        "threat_families": fp.threat_families,
        "canonical_features": fp.canonical_features,
    }

    match = matcher.compare(features, fp)
    assert match.match_type == "EXACT_MATCH"
    assert match.match_confidence == 1.0
    assert "attack_path" in match.matched_dimensions


def test_matcher_semantic_variant_with_different_channel_and_domain():
    matcher = FingerprintMatcher()
    fp = make_sample_fingerprint()

    # Observation has identical semantic signature (same actions, claims, attack stages)
    # but different exact signature because channel is WhatsApp and exact wording/domain differed
    features = {
        "exact_signature": "different_exact_sig_789",
        "semantic_signature": "semantic_sig_456",  # Identical semantic signature
        "attack_path_signature": fp.attack_path_signature,
        "attack_stages": fp.attack_stages,
        "action_patterns": fp.action_patterns,
        "claim_patterns": fp.claim_patterns,
        "identity_patterns": fp.identity_patterns,
        "threat_patterns": fp.threat_patterns,
        "evidence_patterns": fp.evidence_patterns,
        "channel_patterns": ["CHANNEL:WHATSAPP"],  # Channel differs
        "technical_patterns": ["TECH:LOOKALIKE_DOMAIN"],  # Domain differs
        "threat_families": fp.threat_families,
        "canonical_features": fp.canonical_features,
    }

    match = matcher.compare(features, fp)
    assert match.match_type in ("SEMANTIC_VARIANT", "STRUCTURAL_MATCH")
    assert match.match_confidence >= 0.85
    assert "attack_path" in match.matched_dimensions
    assert "action_patterns" in match.matched_dimensions


def test_matcher_no_match_for_completely_unrelated():
    matcher = FingerprintMatcher()
    fp = make_sample_fingerprint()

    # Informational content
    features = {
        "exact_signature": "unrelated_sig",
        "semantic_signature": "unrelated_sem_sig",
        "attack_path_signature": "DISCOVERY",
        "attack_stages": [],
        "action_patterns": ["ACTION:RESEARCH"],
        "claim_patterns": [],
        "identity_patterns": [],
        "threat_patterns": [],
        "evidence_patterns": [],
        "channel_patterns": ["CHANNEL:WEB"],
        "technical_patterns": [],
        "threat_families": [],
        "canonical_features": ["ACTION:RESEARCH"],
    }

    match = matcher.compare(features, fp)
    assert match.match_type == "NO_MATCH"
    assert match.match_confidence < 0.40

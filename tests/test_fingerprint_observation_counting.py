"""Unit tests for observation counting and copy-amplification defense."""

from datetime import datetime, timezone
from nivesh.fingerprints.repository import FingerprintRepository
from nivesh.schemas.fingerprint import ScamFingerprint, FingerprintObservation


def test_repeated_copy_amplification_does_not_inflate_observation_count():
    """Ensure identical forwarded copies from same source do not count as independent corroboration."""
    repo = FingerprintRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    fp = ScamFingerprint(
        fingerprint_id="SFP-001",
        schema_version="1.0",
        identity_patterns=["IDENTITY:REGULATORY_AUTHORITY_CLAIM"],
        claim_patterns=["CLAIM:GUARANTEED_RETURN"],
        action_patterns=["ACTION:PAYMENT"],
        channel_patterns=["CHANNEL:TELEGRAM"],
        technical_patterns=[],
        threat_patterns=[],
        attack_stages=["FINANCIAL_REQUEST"],
        attack_transitions=[],
        evidence_patterns=[],
        threat_families=["GUARANTEED_RETURN_SCHEME"],
        canonical_features=["ACTION:PAYMENT", "CLAIM:GUARANTEED_RETURN"],
        exact_signature="sig_1",
        semantic_signature="sem_1",
        attack_path_signature="FINANCIAL_REQUEST",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=0,
        status="NEW",
    )
    repo.add_fingerprint(fp)

    # Ingest same message hash 10 times (e.g. forward spam copied across 10 groups)
    identical_hash = "sha256_identical_spam_content_abc123"
    for i in range(10):
        obs = FingerprintObservation(
            observation_id=f"OBS-{i+1}",
            fingerprint_id="SFP-001",
            content_id=f"CNT-{i+1}",
            observed_at=now_iso,
            channel="telegram",
            features=["ACTION:PAYMENT", "CLAIM:GUARANTEED_RETURN"],
            content_hash=identical_hash,
            match_type="EXACT_MATCH",
            match_confidence=1.0,
            matched_dimensions=["attack_path"],
            provenance={"engine_version": "1.0.0"},
        )
        repo.record_observation("SFP-001", obs, content_hash=identical_hash)

    # Crucial assertion: observation_count must be 1, NOT 10!
    assert fp.observation_count == 1
    stored_obs = repo.list_observations("SFP-001")
    assert len(stored_obs) == 10
    # First observation was genuine new report, subsequent 9 were duplicate origin
    assert stored_obs[0].is_duplicate_origin is False
    for dup in stored_obs[1:]:
        assert dup.is_duplicate_origin is True


def test_independent_observations_across_different_channels():
    repo = FingerprintRepository()
    now_iso = datetime.now(timezone.utc).isoformat()
    fp = ScamFingerprint(
        fingerprint_id="SFP-002",
        schema_version="1.0",
        identity_patterns=[],
        claim_patterns=[],
        action_patterns=[],
        channel_patterns=[],
        technical_patterns=[],
        threat_patterns=[],
        attack_stages=[],
        attack_transitions=[],
        evidence_patterns=[],
        threat_families=[],
        canonical_features=[],
        exact_signature="sig_2",
        semantic_signature="sem_2",
        attack_path_signature="FINANCIAL_REQUEST",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=0,
        status="NEW",
    )
    repo.add_fingerprint(fp)

    # Distinct observation 1: Telegram
    obs1 = FingerprintObservation(
        observation_id="OBS-1",
        fingerprint_id="SFP-002",
        content_id="CNT-1",
        observed_at=now_iso,
        channel="telegram",
        features=[],
        content_hash="hash_alpha",
        match_type="EXACT_MATCH",
        match_confidence=1.0,
        matched_dimensions=[],
        provenance={"engine_version": "1.0.0"},
    )
    repo.record_observation("SFP-002", obs1, content_hash="hash_alpha")

    # Distinct observation 2: WhatsApp
    obs2 = FingerprintObservation(
        observation_id="OBS-2",
        fingerprint_id="SFP-002",
        content_id="CNT-2",
        observed_at=now_iso,
        channel="whatsapp",
        features=[],
        content_hash="hash_beta",
        match_type="SEMANTIC_VARIANT",
        match_confidence=0.91,
        matched_dimensions=[],
        provenance={"engine_version": "1.0.0"},
    )
    repo.record_observation("SFP-002", obs2, content_hash="hash_beta")

    assert fp.observation_count == 2
    assert "telegram" in fp.distinct_channels
    assert "whatsapp" in fp.distinct_channels
    assert fp.distinct_variants == 2

"""Unit tests for Fingerprint lifecycle, status transitions, and dispute management."""

from datetime import datetime, timezone, timedelta
from nivesh.fingerprints.repository import FingerprintRepository
from nivesh.schemas.fingerprint import ScamFingerprint, FingerprintObservation


def make_test_fp(fp_id: str = "SFP-001") -> ScamFingerprint:
    now_iso = datetime.now(timezone.utc).isoformat()
    return ScamFingerprint(
        fingerprint_id=fp_id,
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
        exact_signature=f"sig_{fp_id}",
        semantic_signature=f"sem_{fp_id}",
        attack_path_signature="FINANCIAL_REQUEST",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=0,
        status="NEW",
    )


def test_promotion_from_new_to_active():
    repo = FingerprintRepository()
    fp = make_test_fp("SFP-001")
    repo.add_fingerprint(fp)
    assert fp.status == "NEW"

    # Observation 1: count becomes 1, status remains NEW
    obs1 = FingerprintObservation(
        observation_id="OBS-1",
        fingerprint_id="SFP-001",
        content_id="CNT-1",
        observed_at=datetime.now(timezone.utc).isoformat(),
        match_type="EXACT_MATCH",
        match_confidence=1.0,
        matched_dimensions=["attack_path"],
        provenance={"engine_version": "1.0.0"},
    )
    repo.record_observation("SFP-001", obs1, content_hash="hash_1")
    assert fp.observation_count == 1
    assert fp.status == "NEW"

    # Observation 2: count becomes 2, promoted to ACTIVE
    obs2 = FingerprintObservation(
        observation_id="OBS-2",
        fingerprint_id="SFP-001",
        content_id="CNT-2",
        observed_at=datetime.now(timezone.utc).isoformat(),
        match_type="EXACT_MATCH",
        match_confidence=1.0,
        matched_dimensions=["attack_path"],
        provenance={"engine_version": "1.0.0"},
    )
    repo.record_observation("SFP-001", obs2, content_hash="hash_2")
    assert fp.observation_count == 2
    assert fp.status == "ACTIVE"
    assert len(fp.status_change_history) >= 1
    assert fp.status_change_history[-1]["to_status"] == "ACTIVE"


def test_dispute_preserves_history_and_does_not_delete():
    repo = FingerprintRepository()
    fp = make_test_fp("SFP-002")
    repo.add_fingerprint(fp)

    obs = FingerprintObservation(
        observation_id="OBS-100",
        fingerprint_id="SFP-002",
        content_id="CNT-100",
        observed_at=datetime.now(timezone.utc).isoformat(),
        match_type="EXACT_MATCH",
        match_confidence=1.0,
        matched_dimensions=["attack_path"],
        provenance={"engine_version": "1.0.0"},
    )
    repo.record_observation("SFP-002", obs, content_hash="hash_100")

    # Register dispute
    disputed_fp = repo.dispute_fingerprint("SFP-002", reason="Claimed entity is legitimately licensed under different sub-code.", actor="compliance_officer")
    assert disputed_fp is not None
    assert disputed_fp.status == "DISPUTED"
    assert disputed_fp.dispute_count == 1
    assert len(disputed_fp.dispute_notes) == 1
    assert "legitimately licensed" in disputed_fp.dispute_notes[0]

    # Crucial rule: do not silently delete historical observations
    stored_obs = repo.list_observations("SFP-002")
    assert len(stored_obs) == 1
    assert stored_obs[0].observation_id == "OBS-100"


def test_staleness_transition():
    repo = FingerprintRepository()
    fp = make_test_fp("SFP-003")
    # Simulate last seen 120 days ago
    old_date = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    fp.last_seen = old_date
    repo.add_fingerprint(fp)

    is_stale = repo.mark_stale_if_inactive("SFP-003", threshold_days=90)
    assert is_stale is True
    assert fp.status == "STALE"


def test_archive_fingerprint():
    repo = FingerprintRepository()
    fp = make_test_fp("SFP-004")
    repo.add_fingerprint(fp)

    archived = repo.archive_fingerprint("SFP-004", reason="Campaign expired")
    assert archived is not None
    assert archived.status == "ARCHIVED"


def test_related_fingerprints_linking():
    repo = FingerprintRepository()
    fp1 = make_test_fp("SFP-010")
    fp2 = make_test_fp("SFP-011")
    repo.add_fingerprint(fp1)
    repo.add_fingerprint(fp2)

    repo.link_related_fingerprints("SFP-010", "SFP-011")
    assert "SFP-011" in fp1.related_fingerprint_ids
    assert "SFP-010" in fp2.related_fingerprint_ids

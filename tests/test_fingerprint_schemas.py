"""Unit tests for Engine 7 schemas (ScamFingerprint, FingerprintObservation, etc.)."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from nivesh.schemas.fingerprint import (
    ScamFingerprint,
    FingerprintObservation,
    FingerprintMatch,
    FingerprintProvenance,
    FingerprintAnalysisMetadata,
    FingerprintAnalysis,
    FingerprintMatchType,
    FingerprintStatus,
)


def test_scam_fingerprint_schema_valid():
    now_iso = datetime.now(timezone.utc).isoformat()
    fp = ScamFingerprint(
        fingerprint_id="SFP-001",
        schema_version="1.0",
        identity_patterns=["IDENTITY:REGULATORY_AUTHORITY_CLAIM"],
        claim_patterns=["CLAIM:GUARANTEED_RETURN"],
        action_patterns=["ACTION:JOIN_CHANNEL", "ACTION:PAYMENT"],
        channel_patterns=["CHANNEL:TELEGRAM"],
        technical_patterns=["TECH:EXTERNAL_APP"],
        threat_patterns=["THREAT:IDENTITY_NOT_ESTABLISHED"],
        attack_stages=["CHANNEL_MIGRATION", "FINANCIAL_REQUEST"],
        attack_transitions=["CHANNEL_MIGRATION->FINANCIAL_REQUEST"],
        evidence_patterns=["EVIDENCE:UNVERIFIED_REGISTRATION"],
        threat_families=["REGULATORY_IMPERSONATION"],
        canonical_features=[
            "IDENTITY:REGULATORY_AUTHORITY_CLAIM",
            "CLAIM:GUARANTEED_RETURN",
            "ACTION:JOIN_CHANNEL",
            "ACTION:PAYMENT",
        ],
        exact_signature="abcdef0123456789abcdef0123456789",
        semantic_signature="9876543210fedcba9876543210fedcba",
        attack_path_signature="CHANNEL_MIGRATION>FINANCIAL_REQUEST",
        created_at=now_iso,
        updated_at=now_iso,
        first_seen=now_iso,
        last_seen=now_iso,
        observation_count=1,
        distinct_channels=["telegram"],
        distinct_variants=1,
        status="NEW",
        description="Test fingerprint",
    )
    assert fp.fingerprint_id == "SFP-001"
    assert fp.observation_count == 1
    assert fp.status == "NEW"
    assert "REGULATORY_IMPERSONATION" in fp.threat_families


def test_fingerprint_observation_schema():
    now_iso = datetime.now(timezone.utc).isoformat()
    obs = FingerprintObservation(
        observation_id="OBS-12345678",
        fingerprint_id="SFP-001",
        content_id="CNT-001",
        observed_at=now_iso,
        channel="telegram",
        features=["CLAIM:GUARANTEED_RETURN", "ACTION:PAYMENT"],
        content_hash="hash123",
        is_duplicate_origin=False,
        match_type="STRUCTURAL_MATCH",
        match_confidence=0.91,
        matched_dimensions=["attack_path", "action_patterns", "claim_patterns"],
        provenance={"engine_version": "1.0.0"},
    )
    assert obs.observation_id == "OBS-12345678"
    assert obs.match_type == "STRUCTURAL_MATCH"
    assert obs.match_confidence == 0.91
    assert not obs.is_duplicate_origin


def test_fingerprint_match_schema():
    match = FingerprintMatch(
        fingerprint_id="SFP-001",
        match_type="STRUCTURAL_MATCH",
        match_confidence=0.92,
        matched_dimensions=["attack_path", "action_patterns", "claim_patterns"],
        matched_features=["CLAIM:GUARANTEED_RETURN", "ACTION:PAYMENT"],
        dimension_scores={
            "attack_path": 1.0,
            "action_patterns": 0.9,
            "claim_patterns": 0.95,
        },
        explanation="Structural match across attack path, action sequence, and claim patterns.",
    )
    assert match.fingerprint_id == "SFP-001"
    assert match.match_confidence == 0.92
    assert "attack_path" in match.matched_dimensions


def test_fingerprint_status_enum_values():
    assert "NEW" in FingerprintStatus.__args__
    assert "ACTIVE" in FingerprintStatus.__args__
    assert "STALE" in FingerprintStatus.__args__
    assert "ARCHIVED" in FingerprintStatus.__args__
    assert "DISPUTED" in FingerprintStatus.__args__


def test_fingerprint_match_type_values():
    assert "EXACT_MATCH" in FingerprintMatchType.__args__
    assert "STRUCTURAL_MATCH" in FingerprintMatchType.__args__
    assert "SEMANTIC_VARIANT" in FingerprintMatchType.__args__
    assert "RELATED_PATTERN" in FingerprintMatchType.__args__
    assert "NO_MATCH" in FingerprintMatchType.__args__

"""Scam Fingerprint and Collective Threat Intelligence schemas for Engine 7.

Represents privacy-preserving structural scam fingerprints, multi-dimensional matches,
collective observations, and lifecycle states without storing raw personal identifiers
or calculating arbitrary scam probabilities.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

FingerprintMatchType = Literal[
    "EXACT_MATCH",
    "STRUCTURAL_MATCH",
    "SEMANTIC_VARIANT",
    "RELATED_PATTERN",
    "NO_MATCH",
]

FingerprintStatus = Literal[
    "NEW",
    "ACTIVE",
    "STALE",
    "ARCHIVED",
    "DISPUTED",
]


class ScamFingerprint(BaseModel):
    """Normalized, privacy-preserving structural scam fingerprint."""
    fingerprint_id: str = Field(description="Unique fingerprint identifier e.g. SFP-001")
    schema_version: str = Field(default="1.0", description="Fingerprint schema version")

    # Normalized Structural Dimensions
    identity_patterns: list[str] = Field(default_factory=list, description="Canonical identity assertion types")
    claim_patterns: list[str] = Field(default_factory=list, description="Canonical claim types and predicates")
    action_patterns: list[str] = Field(default_factory=list, description="Canonical action types and categories")
    channel_patterns: list[str] = Field(default_factory=list, description="Canonical communication channels")
    technical_patterns: list[str] = Field(default_factory=list, description="Technical infrastructure patterns")
    threat_patterns: list[str] = Field(default_factory=list, description="Threat signals and behavioral cues")
    attack_stages: list[str] = Field(default_factory=list, description="Attack path stages in chronological order")
    attack_transitions: list[str] = Field(default_factory=list, description="Observed stage-to-stage transitions")
    evidence_patterns: list[str] = Field(default_factory=list, description="Normalized evidence verification states")
    threat_families: list[str] = Field(default_factory=list, description="Associated high-level threat families")

    # Canonical Features & Cryptographic Signatures
    canonical_features: list[str] = Field(default_factory=list, description="Sorted, standardized feature representations")
    exact_signature: str = Field(description="Deterministic SHA-256 digest of sorted canonical features")
    semantic_signature: str = Field(description="Deterministic SHA-256 digest of invariant core structural features")
    attack_path_signature: str = Field(default="", description="Deterministic string of stage progression")

    # Timestamps & Collective Observation Metrics
    created_at: str = Field(description="ISO 8601 creation timestamp")
    updated_at: str = Field(description="ISO 8601 last updated timestamp")
    first_seen: str = Field(description="ISO 8601 timestamp of first observation")
    last_seen: str = Field(description="ISO 8601 timestamp of most recent observation")
    observation_count: int = Field(default=1, description="Total independent observations matching this fingerprint")
    distinct_channels: list[str] = Field(default_factory=list, description="Unique communication channels observed")
    distinct_variants: int = Field(default=1, description="Number of distinct structural or channel variants observed")

    # Lifecycle, Disputes & Relationships
    status: FingerprintStatus = Field(default="NEW", description="Lifecycle state")
    dispute_count: int = Field(default=0, description="Number of recorded user or analyst disputes")
    dispute_notes: list[str] = Field(default_factory=list, description="Reasons recorded for disputes")
    status_change_history: list[dict[str, Any]] = Field(default_factory=list, description="Audit log of status changes")
    related_fingerprint_ids: list[str] = Field(default_factory=list, description="IDs of structurally related fingerprints")
    content_hashes: list[str] = Field(default_factory=list, description="Hashes of distinct observed contents (no raw text)")
    description: str = Field(default="", description="Human-readable summary of the structural threat pattern")


class FingerprintObservation(BaseModel):
    """An individual interaction observation associated with a fingerprint."""
    observation_id: str = Field(description="Unique observation ID e.g. OBS-001")
    fingerprint_id: str = Field(description="Associated ScamFingerprint ID")
    content_id: str = Field(description="Origin content ID from Engine 1")
    observed_at: str = Field(description="ISO 8601 observation timestamp")
    channel: Optional[str] = Field(default=None, description="Observed platform or channel e.g. telegram")
    features: list[str] = Field(default_factory=list, description="Normalized structural features extracted from this observation")
    content_hash: Optional[str] = Field(default=None, description="Privacy-safe hash of normalized text for amplification detection")
    is_duplicate_origin: bool = Field(default=False, description="True if content hash was previously observed (same origin copy)")
    match_type: FingerprintMatchType = Field(description="Relationship to the assigned fingerprint")
    match_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in structural pattern similarity")
    matched_dimensions: list[str] = Field(default_factory=list, description="Specific structural dimensions that matched")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Execution and upstream engine audit metadata")


class FingerprintMatch(BaseModel):
    """Result of comparing an observation against an existing fingerprint."""
    fingerprint_id: str = Field(description="Matched fingerprint ID")
    match_type: FingerprintMatchType = Field(description="Exact, structural, variant, related, or none")
    match_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in pattern similarity (NOT scam probability)")
    matched_features: list[str] = Field(default_factory=list, description="Common structural features")
    divergent_features: list[str] = Field(default_factory=list, description="Features that differ between observation and fingerprint")
    matched_dimensions: list[str] = Field(default_factory=list, description="Dimensions in agreement e.g. attack_stages")
    explanation: str = Field(description="Explainable breakdown of match rationale")
    threat_families: list[str] = Field(default_factory=list, description="Threat families represented by matched fingerprint")
    attack_stages: list[str] = Field(default_factory=list, description="Attack stages of matched fingerprint")
    observation_count: int = Field(default=0, description="Historical observation count of the fingerprint")
    first_seen: str = Field(default="", description="When this pattern was first observed")
    last_seen: str = Field(default="", description="When this pattern was most recently observed")


class FingerprintProvenance(BaseModel):
    """Audit metadata for Engine 7 fingerprint analysis."""
    engine_version: str = Field(default="1.0.0", description="Engine 7 version")
    engine_name: str = Field(default="Scam Fingerprint & Collective Threat Intelligence Engine")
    matching_method: Literal["deterministic", "weighted_structural", "hybrid"] = "hybrid"
    analyzed_at: str = Field(description="ISO 8601 timestamp")
    upstream_engine_versions: dict[str, str] = Field(default_factory=dict)


class FingerprintAnalysisMetadata(BaseModel):
    """Execution telemetry for fingerprint matching."""
    processing_time_ms: float = 0.0
    total_fingerprints_checked: int = 0
    exact_matches_found: int = 0
    structural_matches_found: int = 0
    semantic_variants_found: int = 0
    related_patterns_found: int = 0


class FingerprintAnalysis(BaseModel):
    """Complete output of Engine 7 (Scam Fingerprint & Collective Threat Intelligence Engine)."""
    content_id: str = Field(description="Source content identifier")
    fingerprint: ScamFingerprint = Field(description="Assigned or created ScamFingerprint")
    observation: FingerprintObservation = Field(description="Recorded observation record")
    matches: list[FingerprintMatch] = Field(default_factory=list, description="All evaluated candidate matches")
    primary_match: Optional[FingerprintMatch] = Field(default=None, description="Best candidate match if one exists")
    is_new_pattern: bool = Field(default=True, description="True if a new fingerprint was created rather than matched")
    match_type: FingerprintMatchType = Field(default="NO_MATCH", description="Relationship type of primary match")
    match_confidence: float = Field(default=0.0, description="Similarity confidence for primary match")
    collective_context: Optional[dict[str, Any]] = Field(default=None, description="Privacy-safe collective threat context")
    provenance: FingerprintProvenance
    analysis_metadata: FingerprintAnalysisMetadata = Field(default_factory=FingerprintAnalysisMetadata)

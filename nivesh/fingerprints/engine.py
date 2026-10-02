"""Scam Fingerprint & Collective Threat Intelligence Engine (Engine 7 of Nivesh Firewall).

Answers:
"Have we previously observed this underlying financial threat pattern?"

Builds and manages privacy-preserving structural scam fingerprints across multiple
observations. Identifies exact matches, structural variants, semantic mutations, and
shared threat families.
Does NOT store personal identifiers, calculate scam probabilities, or make final blocking decisions.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import (
    ScamFingerprint,
    FingerprintObservation,
    FingerprintMatch,
    FingerprintProvenance,
    FingerprintAnalysisMetadata,
    FingerprintAnalysis,
    FingerprintMatchType,
)
from nivesh.fingerprints.feature_extractor import NormalizedFeatureExtractor
from nivesh.fingerprints.matcher import FingerprintMatcher
from nivesh.fingerprints.repository import FingerprintRepository

ENGINE_VERSION = "1.0.0"


class ScamFingerprintEngine:
    """Core service for Engine 7: Scam Fingerprint & Collective Threat Intelligence Engine."""

    def __init__(self, repository: Optional[FingerprintRepository] = None):
        self.repository = repository or FingerprintRepository()
        self.feature_extractor = NormalizedFeatureExtractor()
        self.matcher = FingerprintMatcher()
        self._counter = 1

    def create_or_match(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
        threat: ThreatAnalysis,
    ) -> FingerprintAnalysis:
        """Main service interface for Engine 7.
        
        Consumes:
        - NormalizedContent (Engine 1)
        - ClaimAnalysis (Engine 2)
        - ActionAnalysis (Engine 3)
        - SourceAnalysis (Engine 4)
        - EvidenceAnalysis (Engine 5)
        - ThreatAnalysis (Engine 6)
        
        Returns:
        - FingerprintAnalysis
        """
        start_time = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Check if content has ANY active threat pattern
        active_stages = [n.stage for n in threat.attack_path.nodes if n.stage != "DISCOVERY"]
        has_threat_structure = bool(threat.threat_signals or active_stages or threat.threat_families)

        # Case 1: Informational / benign content without threat mechanics
        if not has_threat_structure:
            empty_fp = ScamFingerprint(
                fingerprint_id="SFP-NONE",
                schema_version="1.0",
                exact_signature="",
                semantic_signature="",
                created_at=now_iso,
                updated_at=now_iso,
                first_seen=now_iso,
                last_seen=now_iso,
                observation_count=0,
                status="ARCHIVED",
                description="No financial threat pattern observed in informational content."
            )
            empty_obs = FingerprintObservation(
                observation_id=f"OBS-{uuid.uuid4().hex[:8].upper()}",
                fingerprint_id="SFP-NONE",
                content_id=content.content_id,
                observed_at=now_iso,
                match_type="NO_MATCH",
                match_confidence=0.0,
                matched_dimensions=[],
                provenance={"engine_version": ENGINE_VERSION}
            )
            proc_time = round((time.time() - start_time) * 1000, 2)
            return FingerprintAnalysis(
                content_id=content.content_id,
                fingerprint=empty_fp,
                observation=empty_obs,
                matches=[],
                primary_match=None,
                is_new_pattern=False,
                match_type="NO_MATCH",
                match_confidence=0.0,
                collective_context={
                    "pattern_summary": "Content represents informational or educational material with no matching threat fingerprint.",
                    "observation_count": 0
                },
                provenance=FingerprintProvenance(
                    engine_version=ENGINE_VERSION,
                    analyzed_at=now_iso,
                    upstream_engine_versions={
                        "content_intelligence": getattr(content.provenance, "processing_version", getattr(content.provenance, "engine_version", "1.0.0")) if content.provenance else "1.0.0",
                        "claim_intelligence": claims.claims[0].provenance.processing_version if claims.claims and claims.claims[0].provenance else "1.0.0",
                        "threat_intelligence": threat.provenance.engine_version if threat.provenance else "1.0.0"
                    }
                ),
                analysis_metadata=FingerprintAnalysisMetadata(
                    processing_time_ms=proc_time,
                    total_fingerprints_checked=0
                )
            )

        # Case 2: Extract normalized features
        features = self.feature_extractor.extract_features(
            content=content,
            claims=claims,
            actions=actions,
            sources=sources,
            evidence=evidence,
            threat=threat
        )

        # Query candidates from repository
        candidates = self.repository.get_candidates(features)
        matches: list[FingerprintMatch] = []

        exact_matches = 0
        structural_matches = 0
        semantic_variants = 0
        related_patterns = 0

        for cand in candidates:
            match = self.matcher.compare(features, cand)
            if match.match_type != "NO_MATCH":
                matches.append(match)
                if match.match_type == "EXACT_MATCH":
                    exact_matches += 1
                elif match.match_type == "STRUCTURAL_MATCH":
                    structural_matches += 1
                elif match.match_type == "SEMANTIC_VARIANT":
                    semantic_variants += 1
                elif match.match_type == "RELATED_PATTERN":
                    related_patterns += 1

        # Sort matches by match confidence descending
        matches.sort(key=lambda m: m.match_confidence, reverse=True)

        primary_match: Optional[FingerprintMatch] = None
        # Select best actionable match (EXACT_MATCH, STRUCTURAL_MATCH, or SEMANTIC_VARIANT)
        actionable_matches = [m for m in matches if m.match_type in ("EXACT_MATCH", "STRUCTURAL_MATCH", "SEMANTIC_VARIANT")]
        if actionable_matches:
            primary_match = actionable_matches[0]
        elif matches:
            primary_match = matches[0]

        is_new_pattern = primary_match is None or primary_match.match_type == "RELATED_PATTERN"

        # -------------------------------------------------------------
        # Decision: Match Existing Fingerprint vs Create New
        # -------------------------------------------------------------
        if not is_new_pattern and primary_match:
            # Match existing fingerprint
            target_fp = self.repository.get_fingerprint(primary_match.fingerprint_id)
            if not target_fp:
                # Fallback if candidate was not found
                target_fp = self._create_new_fingerprint(features, now_iso)
                self.repository.add_fingerprint(target_fp)
                is_new_pattern = True

            obs_id = f"OBS-{uuid.uuid4().hex[:8].upper()}"
            observation = FingerprintObservation(
                observation_id=obs_id,
                fingerprint_id=target_fp.fingerprint_id,
                content_id=content.content_id,
                observed_at=now_iso,
                channel=features.get("observed_channel"),
                features=features.get("canonical_features", []),
                content_hash=features.get("content_hash"),
                is_duplicate_origin=False,
                match_type=primary_match.match_type,
                match_confidence=primary_match.match_confidence,
                matched_dimensions=primary_match.matched_dimensions,
                provenance={
                    "engine_version": ENGINE_VERSION,
                    "matched_fingerprint_id": target_fp.fingerprint_id
                }
            )

            # Record observation in repository
            self.repository.record_observation(
                fingerprint_id=target_fp.fingerprint_id,
                observation=observation,
                content_hash=features.get("content_hash")
            )

            # Build privacy-safe collective context
            collective_context = self._generate_collective_context(target_fp, primary_match)

            proc_time = round((time.time() - start_time) * 1000, 2)
            return FingerprintAnalysis(
                content_id=content.content_id,
                fingerprint=target_fp,
                observation=observation,
                matches=matches,
                primary_match=primary_match,
                is_new_pattern=False,
                match_type=primary_match.match_type,
                match_confidence=primary_match.match_confidence,
                collective_context=collective_context,
                provenance=FingerprintProvenance(
                    engine_version=ENGINE_VERSION,
                    analyzed_at=now_iso,
                    upstream_engine_versions={
                        "content_intelligence": getattr(content.provenance, "processing_version", getattr(content.provenance, "engine_version", "1.0.0")) if content.provenance else "1.0.0",
                        "threat_intelligence": threat.provenance.engine_version if threat.provenance else "1.0.0"
                    }
                ),
                analysis_metadata=FingerprintAnalysisMetadata(
                    processing_time_ms=proc_time,
                    total_fingerprints_checked=len(candidates),
                    exact_matches_found=exact_matches,
                    structural_matches_found=structural_matches,
                    semantic_variants_found=semantic_variants,
                    related_patterns_found=related_patterns
                )
            )

        else:
            # Create new fingerprint
            new_fp = self._create_new_fingerprint(features, now_iso)
            if primary_match and primary_match.match_type == "RELATED_PATTERN":
                new_fp.related_fingerprint_ids.append(primary_match.fingerprint_id)
                self.repository.link_related_fingerprints(new_fp.fingerprint_id, primary_match.fingerprint_id)

            self.repository.add_fingerprint(new_fp)

            obs_id = f"OBS-{uuid.uuid4().hex[:8].upper()}"
            observation = FingerprintObservation(
                observation_id=obs_id,
                fingerprint_id=new_fp.fingerprint_id,
                content_id=content.content_id,
                observed_at=now_iso,
                channel=features.get("observed_channel"),
                features=features.get("canonical_features", []),
                content_hash=features.get("content_hash"),
                is_duplicate_origin=False,
                match_type="NO_MATCH",
                match_confidence=1.0,
                matched_dimensions=["attack_path", "action_patterns", "claim_patterns", "identity_patterns"],
                provenance={"engine_version": ENGINE_VERSION}
            )

            self.repository.record_observation(
                fingerprint_id=new_fp.fingerprint_id,
                observation=observation,
                content_hash=features.get("content_hash")
            )

            collective_context = {
                "fingerprint_id": new_fp.fingerprint_id,
                "pattern_summary": "First observation of this structural threat pattern.",
                "first_seen": new_fp.first_seen,
                "observation_count": new_fp.observation_count,
                "status": new_fp.status,
                "recurring_characteristics": self._summarize_characteristics(new_fp)
            }

            proc_time = round((time.time() - start_time) * 1000, 2)
            return FingerprintAnalysis(
                content_id=content.content_id,
                fingerprint=new_fp,
                observation=observation,
                matches=matches,
                primary_match=primary_match,
                is_new_pattern=True,
                match_type=primary_match.match_type if primary_match else "NO_MATCH",
                match_confidence=primary_match.match_confidence if primary_match else 0.0,
                collective_context=collective_context,
                provenance=FingerprintProvenance(
                    engine_version=ENGINE_VERSION,
                    analyzed_at=now_iso,
                    upstream_engine_versions={
                        "content_intelligence": getattr(content.provenance, "processing_version", getattr(content.provenance, "engine_version", "1.0.0")) if content.provenance else "1.0.0",
                        "threat_intelligence": threat.provenance.engine_version if threat.provenance else "1.0.0"
                    }
                ),
                analysis_metadata=FingerprintAnalysisMetadata(
                    processing_time_ms=proc_time,
                    total_fingerprints_checked=len(candidates),
                    exact_matches_found=exact_matches,
                    structural_matches_found=structural_matches,
                    semantic_variants_found=semantic_variants,
                    related_patterns_found=related_patterns
                )
            )

    def find_matching_fingerprints(self, threat: ThreatAnalysis) -> list[FingerprintMatch]:
        """Queries collective memory for stored fingerprints matching the supplied threat structure."""
        # Synthesize minimal content & claim structures if only ThreatAnalysis provided
        active_stages = [n.stage for n in threat.attack_path.nodes if n.stage != "DISCOVERY"]
        attack_path_sig = ">".join(active_stages) if active_stages else "DIRECT"

        query_features = {
            "attack_stages": active_stages,
            "attack_path_signature": attack_path_sig,
            "threat_patterns": [f"THREAT:{s.type}" for s in threat.threat_signals],
            "threat_families": threat.threat_families,
            "action_patterns": [],
            "claim_patterns": [],
            "identity_patterns": [],
            "channel_patterns": [],
            "technical_patterns": [],
            "evidence_patterns": [f"EVIDENCE:{w.weakness_type}" for w in threat.evidence_weaknesses],
            "canonical_features": [f"FAMILY:{f}" for f in threat.threat_families] + [f"STAGE:{s}" for s in active_stages],
            "exact_signature": "",
            "semantic_signature": ""
        }

        candidates = self.repository.get_candidates(query_features)
        matches: list[FingerprintMatch] = []
        for cand in candidates:
            match = self.matcher.compare(query_features, cand)
            if match.match_type != "NO_MATCH":
                matches.append(match)

        matches.sort(key=lambda m: m.match_confidence, reverse=True)
        return matches

    def _create_new_fingerprint(self, features: dict[str, Any], now_iso: str) -> ScamFingerprint:
        """Instantiates a new ScamFingerprint with unique identifier and initial metrics."""
        fp_id = f"SFP-{self._counter:03d}"
        self._counter += 1

        channels = [features.get("observed_channel")] if features.get("observed_channel") else []
        content_hashes = [features.get("content_hash")] if features.get("content_hash") else []

        # Generate descriptive label
        fams = features.get("threat_families", [])
        fam_str = ", ".join(fams) if fams else "Financial Solicitation"
        path_str = features.get("attack_path_signature", "Direct")
        desc = f"Threat pattern: {fam_str} via {path_str}"

        return ScamFingerprint(
            fingerprint_id=fp_id,
            schema_version="1.0",
            identity_patterns=features.get("identity_patterns", []),
            claim_patterns=features.get("claim_patterns", []),
            action_patterns=features.get("action_patterns", []),
            channel_patterns=features.get("channel_patterns", []),
            technical_patterns=features.get("technical_patterns", []),
            threat_patterns=features.get("threat_patterns", []),
            attack_stages=features.get("attack_stages", []),
            attack_transitions=features.get("attack_transitions", []),
            evidence_patterns=features.get("evidence_patterns", []),
            threat_families=features.get("threat_families", []),
            canonical_features=features.get("canonical_features", []),
            exact_signature=features.get("exact_signature", ""),
            semantic_signature=features.get("semantic_signature", ""),
            attack_path_signature=features.get("attack_path_signature", ""),
            created_at=now_iso,
            updated_at=now_iso,
            first_seen=now_iso,
            last_seen=now_iso,
            observation_count=0,
            distinct_channels=[],
            distinct_variants=1,
            status="NEW",
            dispute_count=0,
            dispute_notes=[],
            status_change_history=[],
            related_fingerprint_ids=[],
            content_hashes=[],
            description=desc
        )

    def _generate_collective_context(
        self,
        fingerprint: ScamFingerprint,
        match: FingerprintMatch
    ) -> dict[str, Any]:
        """Generates privacy-preserving collective threat intelligence context."""
        first_date = fingerprint.first_seen[:10] if len(fingerprint.first_seen) >= 10 else fingerprint.first_seen
        return {
            "fingerprint_id": fingerprint.fingerprint_id,
            "pattern_summary": "This interaction matches a previously observed structural threat pattern.",
            "first_observed": first_date,
            "recent_observation_count": fingerprint.observation_count,
            "distinct_channels": fingerprint.distinct_channels,
            "status": fingerprint.status,
            "matching_characteristics": self._summarize_characteristics(fingerprint),
            "match_type": match.match_type,
            "match_confidence": match.match_confidence,
            "matched_dimensions": match.matched_dimensions,
            "explanation": match.explanation
        }

    def _summarize_characteristics(self, fingerprint: ScamFingerprint) -> list[str]:
        """Returns safe, human-readable structural descriptors."""
        summary = []
        if any("REGULATORY" in p for p in fingerprint.identity_patterns or fingerprint.claim_patterns):
            summary.append("Regulatory authority assertion")
        if any("GUARANTEED" in p for p in fingerprint.claim_patterns):
            summary.append("Guaranteed or assured return promise")
        if any("CHANNEL_MIGRATION" in p for p in fingerprint.action_patterns or fingerprint.attack_stages):
            summary.append("Private-channel migration solicitation")
        if any("SOFTWARE_INSTALLATION" in p or "EXTERNAL_APP" in p for p in fingerprint.action_patterns or fingerprint.technical_patterns):
            summary.append("External application software download")
        if any("PAYMENT" in p for p in fingerprint.action_patterns or fingerprint.attack_stages):
            summary.append("Direct payment or fee solicitation")
        if any("CREDENTIAL" in p for p in fingerprint.action_patterns):
            summary.append("Account credential or OTP request")
        return summary

    def get_fingerprint(self, fingerprint_id: str) -> Optional[ScamFingerprint]:
        """Retrieves a stored fingerprint by ID."""
        return self.repository.get_fingerprint(fingerprint_id)

    def search_fingerprints(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        threat_family: Optional[str] = None,
        channel: Optional[str] = None
    ) -> list[ScamFingerprint]:
        """Searches fingerprints in collective memory."""
        return self.repository.search(
            query=query,
            status=status,
            threat_family=threat_family,
            channel=channel
        )

    def dispute_fingerprint(
        self,
        fingerprint_id: str,
        reason: str,
        actor: Optional[str] = None
    ) -> Optional[ScamFingerprint]:
        """Registers a user or analyst dispute for a fingerprint."""
        return self.repository.dispute_fingerprint(fingerprint_id, reason=reason, actor=actor)

    def reset(self) -> None:
        """Resets the repository (for testing)."""
        self.repository.reset()
        self._counter = 1

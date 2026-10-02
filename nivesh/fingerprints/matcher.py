"""Multi-Dimensional Weighted Structural Matcher for Engine 7.

Evaluates structural similarity across independent dimensions (attack path, action sequences,
claim structures, identity assertions, threat cues, and technical channels).
Match confidence measures pattern similarity, NOT scam probability.
"""

from typing import Optional, Any
from nivesh.schemas.fingerprint import ScamFingerprint, FingerprintMatch, FingerprintMatchType


class FingerprintMatcher:
    """Compares query observation features against stored scam fingerprints."""

    # Dimension Weights (Total = 1.00)
    # High-value structural features contribute substantially more than superficial channels
    WEIGHTS = {
        "attack_path": 0.25,
        "action_patterns": 0.25,
        "claim_patterns": 0.20,
        "identity_patterns": 0.15,
        "threat_evidence": 0.10,
        "channel_technical": 0.05,
    }

    @classmethod
    def _jaccard_similarity(cls, set_a: set, set_b: set) -> float:
        """Calculates standard Jaccard set similarity."""
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    @classmethod
    def compare(
        cls,
        query_features: dict[str, Any],
        fingerprint: ScamFingerprint,
    ) -> FingerprintMatch:
        """Performs a multi-dimensional weighted comparison of query against a fingerprint."""

        # 1. Exact Signature Check
        if query_features.get("exact_signature") == fingerprint.exact_signature:
            return FingerprintMatch(
                fingerprint_id=fingerprint.fingerprint_id,
                match_type="EXACT_MATCH",
                structural_equivalence=True,
                match_confidence=1.0,
                matched_features=fingerprint.canonical_features,
                divergent_features=[],
                matched_dimensions=[
                    "attack_path", "action_patterns", "claim_patterns",
                    "identity_patterns", "threat_evidence", "channel_technical"
                ],
                explanation="Identical normalized structural signature matching all canonical threat features.",
                threat_families=fingerprint.threat_families,
                attack_stages=fingerprint.attack_stages,
                observation_count=fingerprint.observation_count,
                first_seen=fingerprint.first_seen,
                last_seen=fingerprint.last_seen,
            )

        # 2. Semantic Signature Check (Invariant core structural features match exactly)
        if query_features.get("semantic_signature") == fingerprint.semantic_signature:
            q_can = set(query_features.get("canonical_features", []))
            fp_can = set(fingerprint.canonical_features)
            matched = sorted(list(q_can.intersection(fp_can)))
            divergent = sorted(list(q_can.symmetric_difference(fp_can)))

            # If differing by surface details (channel, domain, specific amounts/wording),
            # classify deterministically as SEMANTIC_VARIANT with structural_equivalence=True
            return FingerprintMatch(
                fingerprint_id=fingerprint.fingerprint_id,
                match_type="SEMANTIC_VARIANT",
                structural_equivalence=True,
                match_confidence=0.91,
                matched_features=matched,
                divergent_features=divergent,
                matched_dimensions=[
                    "attack_path", "action_patterns", "claim_patterns", "identity_patterns"
                ],
                explanation=(
                    "Identical core attack path and threat mechanics observed with structural equivalence; differences are confined "
                    f"to superficial communication channel or domain variations ({', '.join(divergent[:3]) if divergent else 'surface wording/amounts'})."
                ),
                threat_families=fingerprint.threat_families,
                attack_stages=fingerprint.attack_stages,
                observation_count=fingerprint.observation_count,
                first_seen=fingerprint.first_seen,
                last_seen=fingerprint.last_seen,
            )

        # 3. Dimensional Similarity Evaluation
        q_stages = set(query_features.get("attack_stages", []))
        fp_stages = set(fingerprint.attack_stages)
        q_path_sig = query_features.get("attack_path_signature", "")
        fp_path_sig = fingerprint.attack_path_signature

        # Attack path similarity: combination of stage overlap and exact sequence match
        stage_sim = cls._jaccard_similarity(q_stages, fp_stages)
        path_sim = 1.0 if q_path_sig == fp_path_sig and q_path_sig else stage_sim
        score_path = (stage_sim * 0.4) + (path_sim * 0.6)

        # Action patterns similarity
        q_actions = set(query_features.get("action_patterns", []))
        fp_actions = set(fingerprint.action_patterns)
        score_actions = cls._jaccard_similarity(q_actions, fp_actions)

        # Claim patterns similarity
        q_claims = set(query_features.get("claim_patterns", []))
        fp_claims = set(fingerprint.claim_patterns)
        score_claims = cls._jaccard_similarity(q_claims, fp_claims)

        # Identity patterns similarity
        q_identity = set(query_features.get("identity_patterns", []))
        fp_identity = set(fingerprint.identity_patterns)
        score_identity = cls._jaccard_similarity(q_identity, fp_identity)

        # Threat signals & Evidence patterns
        q_threat = set(query_features.get("threat_patterns", [])) | set(query_features.get("evidence_patterns", []))
        fp_threat = set(fingerprint.threat_patterns) | set(fingerprint.evidence_patterns)
        score_threat = cls._jaccard_similarity(q_threat, fp_threat)

        # Channel & Technical patterns
        q_ch = set(query_features.get("channel_patterns", [])) | set(query_features.get("technical_patterns", []))
        fp_ch = set(fingerprint.channel_patterns) | set(fingerprint.technical_patterns)
        score_channel = cls._jaccard_similarity(q_ch, fp_ch)

        # Weighted Total
        total_score = (
            score_path * cls.WEIGHTS["attack_path"]
            + score_actions * cls.WEIGHTS["action_patterns"]
            + score_claims * cls.WEIGHTS["claim_patterns"]
            + score_identity * cls.WEIGHTS["identity_patterns"]
            + score_threat * cls.WEIGHTS["threat_evidence"]
            + score_channel * cls.WEIGHTS["channel_technical"]
        )

        matched_dims: list[str] = []
        if score_path >= 0.70:
            matched_dims.append("attack_path")
        if score_actions >= 0.60:
            matched_dims.append("action_patterns")
        if score_claims >= 0.60:
            matched_dims.append("claim_patterns")
        if score_identity >= 0.60:
            matched_dims.append("identity_patterns")
        if score_threat >= 0.50:
            matched_dims.append("threat_evidence")
        if score_channel >= 0.50:
            matched_dims.append("channel_technical")

        q_can = set(query_features.get("canonical_features", []))
        fp_can = set(fingerprint.canonical_features)
        matched = sorted(list(q_can.intersection(fp_can)))
        divergent = sorted(list(q_can.symmetric_difference(fp_can)))

        # Shared threat family check
        q_fams = set(query_features.get("threat_families", []))
        fp_fams = set(fingerprint.threat_families)
        shared_families = q_fams.intersection(fp_fams)

        # Determine Match Classification
        match_type: FingerprintMatchType = "NO_MATCH"
        explanation = ""
        is_struct_equiv = False

        if total_score >= 0.85 and "attack_path" in matched_dims and "action_patterns" in matched_dims:
            has_surface_divergence = bool(
                divergent
                or set(query_features.get("channel_patterns", [])) != set(fingerprint.channel_patterns)
                or set(query_features.get("technical_patterns", [])) != set(fingerprint.technical_patterns)
            )
            match_type = "SEMANTIC_VARIANT" if has_surface_divergence else "STRUCTURAL_MATCH"
            is_struct_equiv = True
            explanation = (
                f"Strong structural correspondence across {len(matched_dims)} dimensions with structural equivalence "
                f"({', '.join(matched_dims)})."
            )
        elif total_score >= 0.65 and ("attack_path" in matched_dims or "action_patterns" in matched_dims):
            match_type = "SEMANTIC_VARIANT"
            is_struct_equiv = bool("attack_path" in matched_dims and "action_patterns" in matched_dims)
            explanation = (
                f"Semantic variant exhibiting equivalent threat structure with alternative surface features "
                f"({', '.join(divergent[:3])})."
            )
        elif total_score >= 0.40 or (shared_families and len(q_stages.intersection(fp_stages)) >= 2):
            match_type = "RELATED_PATTERN"
            is_struct_equiv = False
            fam_desc = f" ({', '.join(shared_families)})" if shared_families else ""
            explanation = (
                f"Shares related threat mechanics or threat family{fam_desc}, "
                f"but action or claim sequences diverge."
            )
        else:
            match_type = "NO_MATCH"
            is_struct_equiv = False
            explanation = "Interaction structure does not meaningfully correspond to this stored fingerprint."

        return FingerprintMatch(
            fingerprint_id=fingerprint.fingerprint_id,
            match_type=match_type,
            structural_equivalence=is_struct_equiv,
            match_confidence=round(total_score, 2),
            matched_features=matched,
            divergent_features=divergent,
            matched_dimensions=matched_dims,
            explanation=explanation,
            threat_families=fingerprint.threat_families,
            attack_stages=fingerprint.attack_stages,
            observation_count=fingerprint.observation_count,
            first_seen=fingerprint.first_seen,
            last_seen=fingerprint.last_seen,
        )

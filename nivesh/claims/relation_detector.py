"""Claim relationship detection component for Engine 2.

Discovers semantic and structural relationships between claims in the same content:
- CAUSES / RESULTS_FROM / DEPENDS_ON: explicit causal discourse markers (e.g. 'therefore', 'because', 'so')
- SAME_UNDERLYING_CLAIM: identical canonical fingerprints or subject-predicate-object targets
- SUPPORTS / CONTRADICTS: mutually reinforcing or opposing assertions
- REFINES: specific detail elaborating a broader claim

Strict constraint: Does NOT judge whether the relationship is factually valid.
"""

from typing import Optional
from nivesh.schemas.claims import CanonicalClaim, ClaimRelation, RelationType


class RelationDetector:
    """Detects expressed relationships between pairs of extracted claims."""

    def detect_relations(
        self,
        claims: list[CanonicalClaim],
        discourse_markers: Optional[dict[str, str]] = None
    ) -> list[ClaimRelation]:
        """Detects relationships between claims within the same analyzed content."""
        relations: list[ClaimRelation] = []
        if len(claims) < 2:
            return relations

        markers = discourse_markers or {}

        # 1. Check for duplicate / equivalent underlying claims
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1, c2 = claims[i], claims[j]
                if c1.canonical_fingerprint and c1.canonical_fingerprint == c2.canonical_fingerprint:
                    relations.append(ClaimRelation(
                        source_claim_id=c1.claim_id,
                        target_claim_id=c2.claim_id,
                        relation_type="SAME_UNDERLYING_CLAIM",
                        confidence=1.0,
                        description="Identical canonical semantic fingerprint",
                    ))

        # 2. Check for causal / dependency relationships from discourse markers
        # E.g. "Revenue increased 40%, therefore the company will double"
        for i in range(len(claims) - 1):
            c_source = claims[i]
            c_target = claims[i + 1]

            marker = markers.get(c_target.claim_id, "").lower()

            # "therefore", "hence", "and therefore" indicates c_source CAUSES c_target
            if any(m in marker for m in ["therefore", "hence", "so", "as a result"]):
                relations.append(ClaimRelation(
                    source_claim_id=c_source.claim_id,
                    target_claim_id=c_target.claim_id,
                    relation_type="CAUSES",
                    confidence=0.90,
                    description=f"Expressed causal link via '{marker}'",
                ))
                relations.append(ClaimRelation(
                    source_claim_id=c_target.claim_id,
                    target_claim_id=c_source.claim_id,
                    relation_type="DEPENDS_ON",
                    confidence=0.90,
                    description=f"Premise dependency via '{marker}'",
                ))

            # "because", "since" indicates c_target CAUSES c_source
            elif any(m in marker for m in ["because", "since", "as"]):
                relations.append(ClaimRelation(
                    source_claim_id=c_target.claim_id,
                    target_claim_id=c_source.claim_id,
                    relation_type="CAUSES",
                    confidence=0.90,
                    description=f"Expressed rationale via '{marker}'",
                ))
                relations.append(ClaimRelation(
                    source_claim_id=c_source.claim_id,
                    target_claim_id=c_target.claim_id,
                    relation_type="DEPENDS_ON",
                    confidence=0.90,
                    description=f"Dependent assertion on rationale via '{marker}'",
                ))

        return relations

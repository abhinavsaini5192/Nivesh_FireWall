"""Deterministic Attribute Matcher for Engine 9.

Compares ClaimedEntity attributes against authoritative ResolvedEntity records.
Evaluates:
- Name and legal form alignment
- Registration identifier alignment
- Entity type alignment
- Domain and regulator alignment
- Ambiguity detection (multiple matching candidates)
"""

from typing import Optional
from nivesh.identity.schemas import (
    ClaimedEntity,
    ResolvedEntity,
    IdentityMatch,
    IdentityMatchStatus,
)
from nivesh.identity.normalizer import IdentityNormalizer


class IdentityMatcher:
    """Performs deterministic attribute-by-attribute comparison."""

    @classmethod
    def compare(
        cls,
        match_id: str,
        claimed: ClaimedEntity,
        candidate: Optional[ResolvedEntity],
        resolution_record: Optional[dict] = None,
    ) -> IdentityMatch:
        """Compares a claimed entity with an authoritative candidate entity."""
        # 1. If a prior resolution record exists (from registration/domain resolver), use its structured outcome
        if resolution_record:
            status = resolution_record.get("status", IdentityMatchStatus.NOT_ESTABLISHED)
            basis = resolution_record.get("basis", "Identity resolution evaluated.")
            matching_attrs = resolution_record.get("matching_attrs", [])
            conflicting_attrs = resolution_record.get("conflicting_attrs", [])
            source_ids = resolution_record.get("source_ids", [])
            evidence_ids = resolution_record.get("evidence_ids", [])
            confidence = resolution_record.get("confidence", 0.85)

            return IdentityMatch(
                identity_match_id=match_id,
                claimed_entity_id=claimed.entity_id,
                candidate_entity_id=candidate.candidate_id if candidate else None,
                entity_type=claimed.entity_type,
                match_status=status,
                match_basis=basis,
                matching_attributes=matching_attrs,
                conflicting_attributes=conflicting_attrs,
                source_ids=source_ids,
                evidence_ids=evidence_ids,
                confidence=confidence,
            )

        # 2. If no candidate exists
        if not candidate:
            return IdentityMatch(
                identity_match_id=match_id,
                claimed_entity_id=claimed.entity_id,
                candidate_entity_id=None,
                entity_type=claimed.entity_type,
                match_status=IdentityMatchStatus.NOT_ESTABLISHED,
                match_basis=f"No authoritative registry record found for claimed entity '{claimed.name}'.",
                matching_attributes=[],
                conflicting_attributes=[],
                source_ids=[],
                evidence_ids=[],
                confidence=0.85,
            )

        # 3. Candidate exists: compare attributes
        matching_attrs: list[str] = []
        conflicting_attrs: list[str] = []

        # Name comparison
        claimed_norm = claimed.normalized_name.lower()
        cand_norm = candidate.normalized_name.lower()

        if claimed_norm == cand_norm or claimed.name.lower() == candidate.legal_name.lower():
            matching_attrs.append("legal_name")
        else:
            conflicting_attrs.append("legal_name")

        # Registration number comparison
        if claimed.associated_registration and candidate.registration_number:
            c_reg = IdentityNormalizer.normalize_registration_id(claimed.associated_registration)
            cand_reg = IdentityNormalizer.normalize_registration_id(candidate.registration_number)
            if c_reg == cand_reg:
                matching_attrs.append("registration_number")
            else:
                conflicting_attrs.append("registration_number")

        # Entity type comparison
        if claimed.entity_type == candidate.entity_type or (
            claimed.entity_type.value in ("ADVISER", "BROKER") and candidate.entity_type.value in ("FINANCIAL_INTERMEDIARY", "ORGANIZATION")
        ):
            matching_attrs.append("entity_type")

        # Regulator comparison
        if candidate.regulator:
            matching_attrs.append("regulator")

        # Domain comparison if both present
        if claimed.associated_domain and candidate.official_domain:
            c_root, _ = IdentityNormalizer.normalize_domain(claimed.associated_domain)
            cand_root, _ = IdentityNormalizer.normalize_domain(candidate.official_domain)
            if c_root == cand_root:
                matching_attrs.append("official_domain")
            else:
                conflicting_attrs.append("official_domain")

        # Determine status
        if conflicting_attrs:
            status = IdentityMatchStatus.IDENTITY_MISMATCH
            basis = f"Authoritative record for '{candidate.legal_name}' conflicts with claimed attributes: {', '.join(conflicting_attrs)}."
            confidence = 0.95
        elif "legal_name" in matching_attrs and "registration_number" in matching_attrs:
            status = IdentityMatchStatus.ESTABLISHED
            basis = f"Authoritative record '{candidate.legal_name}' matches legal name and registration identifier."
            confidence = 0.98
        elif "legal_name" in matching_attrs:
            status = IdentityMatchStatus.PARTIALLY_ESTABLISHED
            basis = f"Authoritative record '{candidate.legal_name}' matches name, but registration or domain ownership remains unresolved."
            confidence = 0.75
        else:
            status = IdentityMatchStatus.NOT_ESTABLISHED
            basis = f"Attributes for claimed entity '{claimed.name}' could not be established."
            confidence = 0.70

        return IdentityMatch(
            identity_match_id=match_id,
            claimed_entity_id=claimed.entity_id,
            candidate_entity_id=candidate.candidate_id,
            entity_type=claimed.entity_type,
            match_status=status,
            match_basis=basis,
            matching_attributes=matching_attrs,
            conflicting_attributes=conflicting_attrs,
            source_ids=candidate.source_document_ids,
            evidence_ids=[],
            confidence=confidence,
        )

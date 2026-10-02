"""Authority Identity Resolver for Engine 9.

Evaluates regulatory authority claims and affiliations (SEBI, RBI, NSE, BSE).
Distinguishes:
- AUTHORITY_CLAIM: Mere reference or assertion of regulatory registration
- AUTHORITY_IDENTITY_NOT_ESTABLISHED: Registration asserted but not confirmed in authoritative records
- AUTHORITY_IDENTITY_MISMATCH: Registration conflicts with official registry records or impersonates authority
"""

from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.identity.schemas import (
    ClaimedEntity,
    ResolvedEntity,
    AuthorityAlignment,
    IdentityFindingType,
    IdentityMatchStatus,
)


class AuthorityResolver:
    """Evaluates regulatory authority representations and alignment with official registries."""

    RECOGNIZED_AUTHORITIES = {
        "sebi": "SEBI",
        "rbi": "RBI",
        "nse": "NSE",
        "bse": "BSE",
        "irdai": "IRDAI",
        "irda": "IRDAI",
        "pfrda": "PFRDA",
    }

    @classmethod
    def resolve_authorities(
        cls,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis],
        claimed_entities: list[ClaimedEntity],
        candidate_entities: list[ResolvedEntity],
        registration_records: list[dict[str, Any]],
        sources: Optional[SourceAnalysis] = None,
        evidence: Optional[EvidenceAnalysis] = None,
    ) -> tuple[list[AuthorityAlignment], list[dict[str, Any]]]:
        """Evaluates authority representations across content, claims, and registries.
        
        Returns:
            tuple[list[AuthorityAlignment], list[dict]]:
                - AuthorityAlignment records
                - Associated finding dictionaries
        """
        alignments: list[AuthorityAlignment] = []
        finding_records: list[dict[str, Any]] = []

        # 1. Identify which authorities are referenced or claimed
        referenced_authorities: set[str] = set()
        for r in content.entities.regulators:
            auth_canon = cls.RECOGNIZED_AUTHORITIES.get(r.text.lower(), r.text.upper())
            referenced_authorities.add(auth_canon)

        # Check content text for authority mentions
        norm_text = content.normalized.text.lower()
        for auth_key, auth_canon in cls.RECOGNIZED_AUTHORITIES.items():
            if auth_key in norm_text:
                referenced_authorities.add(auth_canon)

        if not referenced_authorities:
            return alignments, finding_records

        # 2. Extract claimed role and registration identifier
        claimed_role = None
        for e in claimed_entities:
            if e.entity_type.value in ("ADVISER", "BROKER", "FINANCIAL_INTERMEDIARY"):
                claimed_role = e.entity_type.value
                break

        primary_reg_id = None
        for e in claimed_entities:
            if e.associated_registration:
                primary_reg_id = e.associated_registration
                break

        # 3. Collect source IDs and evidence IDs
        source_ids = []
        if sources:
            for csr in sources.claim_sources:
                source_ids.extend([d.document_id for d in csr.documents])

        evidence_ids = []
        if evidence:
            evidence_ids.extend([vr.claim_id for vr in evidence.verifications])

        # 4. Check registration resolution records for authority verification status
        has_mismatch = any(r.get("status") == IdentityMatchStatus.IDENTITY_MISMATCH for r in registration_records)
        has_established = any(r.get("status") == IdentityMatchStatus.ESTABLISHED for r in registration_records)
        has_not_established = any(r.get("status") == IdentityMatchStatus.NOT_ESTABLISHED for r in registration_records)

        for authority in sorted(referenced_authorities):
            # Check for direct impersonation of the regulator itself
            impersonating_regulator = False
            for e in claimed_entities:
                if e.name.upper() == authority and e.entity_type.value != "REGULATOR":
                    impersonating_regulator = True
                    break

            if impersonating_regulator:
                alignments.append(AuthorityAlignment(
                    authority_name=authority,
                    alignment_status="MISMATCH",
                    claimed_role=claimed_role,
                    registration_number=primary_reg_id,
                    findings=[f"Interaction purports to represent the regulatory authority '{authority}' itself."],
                    source_ids=source_ids,
                    evidence_ids=evidence_ids,
                ))
                finding_records.append({
                    "entity_id": authority,
                    "status": IdentityMatchStatus.IDENTITY_MISMATCH,
                    "finding_type": IdentityFindingType.AUTHORITY_IDENTITY_MISMATCH,
                    "basis": f"Unverified entity represents itself directly as regulatory authority '{authority}'.",
                    "description": f"Improper representation of regulator '{authority}'.",
                    "source_ids": source_ids,
                    "evidence_ids": evidence_ids,
                })
            elif has_mismatch:
                # Registration claimed, but belongs to someone else
                alignments.append(AuthorityAlignment(
                    authority_name=authority,
                    alignment_status="MISMATCH",
                    claimed_role=claimed_role,
                    registration_number=primary_reg_id,
                    findings=[f"Claimed {authority} registration does not belong to the represented entity."],
                    source_ids=source_ids,
                    evidence_ids=evidence_ids,
                ))
                finding_records.append({
                    "entity_id": authority,
                    "status": IdentityMatchStatus.IDENTITY_MISMATCH,
                    "finding_type": IdentityFindingType.AUTHORITY_IDENTITY_MISMATCH,
                    "basis": f"Authoritative {authority} records conflict with claimed registration details.",
                    "description": f"Claimed registration with {authority} contradicted by official registry data.",
                    "source_ids": source_ids,
                    "evidence_ids": evidence_ids,
                })
            elif has_established:
                # Registration officially established with authority
                alignments.append(AuthorityAlignment(
                    authority_name=authority,
                    alignment_status="ALIGNED",
                    claimed_role=claimed_role,
                    registration_number=primary_reg_id,
                    findings=[f"Official registration with {authority} verified against registry records."],
                    source_ids=source_ids,
                    evidence_ids=evidence_ids,
                ))
                finding_records.append({
                    "entity_id": authority,
                    "status": IdentityMatchStatus.ESTABLISHED,
                    "finding_type": IdentityFindingType.REGISTRATION_ENTITY_MATCH,
                    "basis": f"Registration with {authority} confirmed in official records.",
                    "description": f"Intermediary is officially registered with {authority}.",
                    "source_ids": source_ids,
                    "evidence_ids": evidence_ids,
                })
            else:
                # Content asserts registration or references authority, but registry has NO_MATCH or unverified
                status_str = "NOT_ESTABLISHED" if has_not_established else "UNVERIFIED"
                alignments.append(AuthorityAlignment(
                    authority_name=authority,
                    alignment_status=status_str,
                    claimed_role=claimed_role,
                    registration_number=primary_reg_id,
                    findings=[f"Interaction references {authority} registration, but official registration is not established."],
                    source_ids=source_ids,
                    evidence_ids=evidence_ids,
                ))
                # Add baseline AUTHORITY_CLAIM finding
                finding_records.append({
                    "entity_id": authority,
                    "status": IdentityMatchStatus.NOT_ESTABLISHED,
                    "finding_type": IdentityFindingType.AUTHORITY_CLAIM,
                    "basis": f"Content makes an explicit regulatory reference to '{authority}'.",
                    "description": f"Interaction references regulatory authority '{authority}'.",
                    "source_ids": source_ids,
                    "evidence_ids": evidence_ids,
                })
                if has_not_established:
                    finding_records.append({
                        "entity_id": authority,
                        "status": IdentityMatchStatus.NOT_ESTABLISHED,
                        "finding_type": IdentityFindingType.AUTHORITY_IDENTITY_NOT_ESTABLISHED,
                        "basis": f"Asserted registration with '{authority}' could not be established using available registry evidence.",
                        "description": f"Registration with '{authority}' is not established in official records (does not automatically constitute fraud).",
                        "source_ids": source_ids,
                        "evidence_ids": evidence_ids,
                    })

        return alignments, finding_records

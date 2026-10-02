"""Social Account and Channel Identity Resolver for Engine 9.

Evaluates observed social handles, channels, and groups (Telegram, WhatsApp,
Twitter/X, Instagram, YouTube) against claimed entities and authoritative records.
Enforces the core principle:
- A matching username (e.g. @abcsecurities_official) does NOT establish ownership
  without authoritative verification.
- Returns SOCIAL_ACCOUNT_NOT_ESTABLISHED unless official evidence confirms association.
- Returns SOCIAL_ACCOUNT_IDENTITY_MISMATCH only if authoritative records specify a
  different official channel/handle.
"""

from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.sources import SourceAnalysis
from nivesh.identity.schemas import (
    ClaimedEntity,
    ResolvedEntity,
    IdentityFindingType,
    IdentityMatchStatus,
)
from nivesh.identity.normalizer import IdentityNormalizer


class SocialResolver:
    """Evaluates social channel representations and alignment with official entity records."""

    @classmethod
    def resolve_social_channels(
        cls,
        content: NormalizedContent,
        claimed_entities: list[ClaimedEntity],
        candidate_entities: list[ResolvedEntity],
        sources: Optional[SourceAnalysis] = None,
    ) -> list[dict[str, Any]]:
        """Evaluates social handles and communication channels.
        
        Returns:
            list[dict]: Finding records detailing social channel identity evaluations.
        """
        finding_records: list[dict[str, Any]] = []

        # 1. Collect observed social handles
        observed_handles = content.structured_signals.social_handles
        if not observed_handles:
            return finding_records

        # 2. Check candidate and source metadata for verified official social channels
        verified_social_map: dict[str, str] = {}  # platform:handle -> official_entity_name
        if sources:
            for csr in sources.claim_sources:
                for doc in csr.documents:
                    meta = doc.metadata or {}
                    official_social = meta.get("official_social_channels") or meta.get("social_handles")
                    if isinstance(official_social, dict):
                        for plat, h in official_social.items():
                            plat_norm, h_norm = IdentityNormalizer.normalize_social_handle(h, plat)
                            verified_social_map[f"{plat_norm}:{h_norm}"] = meta.get("legal_name", "Authoritative Source")
                    elif isinstance(official_social, list):
                        for item in official_social:
                            if isinstance(item, str):
                                plat_norm, h_norm = IdentityNormalizer.normalize_social_handle(item)
                                verified_social_map[f"{plat_norm}:{h_norm}"] = meta.get("legal_name", "Authoritative Source")

        # 3. Evaluate each observed social handle
        for sh in observed_handles:
            plat, handle = IdentityNormalizer.normalize_social_handle(sh.handle, sh.platform)
            channel_key = f"{plat}:{handle}"

            # Find matching claimed entity
            associated_entity = None
            for e in claimed_entities:
                if e.associated_channel == channel_key or (e.associated_channel and handle in e.associated_channel):
                    associated_entity = e
                    break
                elif e.entity_type.value in ("PERSON", "ADVISER", "ORGANIZATION", "COMPANY"):
                    associated_entity = e

            entity_id = associated_entity.entity_id if associated_entity else "UNKNOWN"
            entity_name = associated_entity.name if associated_entity else "Claimed Entity"

            if channel_key in verified_social_map:
                # Officially attested social handle
                finding_records.append({
                    "entity_id": entity_id,
                    "status": IdentityMatchStatus.ESTABLISHED,
                    "finding_type": IdentityFindingType.IDENTITY_ESTABLISHED,
                    "basis": f"Social channel '{plat}:@{handle}' is officially registered to '{verified_social_map[channel_key]}'.",
                    "description": f"Verified official channel on {plat.capitalize()}.",
                    "source_ids": [],
                })
            else:
                # NOT established: Even if handle contains entity name, ownership cannot be assumed without evidence
                finding_records.append({
                    "entity_id": entity_id,
                    "status": IdentityMatchStatus.NOT_ESTABLISHED,
                    "finding_type": IdentityFindingType.SOCIAL_ACCOUNT_NOT_ESTABLISHED,
                    "basis": f"Social channel '{plat}:@{handle}' cannot be authoritatively linked to '{entity_name}' from official records alone.",
                    "description": f"Unverified {plat.capitalize()} channel: matching username does not establish official ownership.",
                    "source_ids": [],
                })

        return finding_records

"""Domain and Brand Alignment Resolver for Engine 9.

Evaluates observed domains and URLs against claimed brands, organizations,
and authoritative official records. Distinguishes:
- ALIGNED: Observed domain matches authoritative domain on official record
- NOT_ESTABLISHED: Observed domain cannot be verified against official records
- MISMATCH: Authoritative domain is known, and observed domain conflicts or impersonates
- UNKNOWN: No domain or brand information available
"""

from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.sources import SourceAnalysis, SourceDocument
from nivesh.identity.schemas import (
    ClaimedEntity,
    ResolvedEntity,
    DomainAlignment,
    IdentityFindingType,
    IdentityMatchStatus,
)
from nivesh.identity.normalizer import IdentityNormalizer


class DomainResolver:
    """Evaluates domain alignment with claimed entities and authoritative records."""

    @classmethod
    def resolve_domains(
        cls,
        content: NormalizedContent,
        claimed_entities: list[ClaimedEntity],
        candidate_entities: list[ResolvedEntity],
        sources: Optional[SourceAnalysis] = None,
    ) -> tuple[list[DomainAlignment], list[dict[str, Any]]]:
        """Resolves all observed domains against claimed entities and authoritative records.
        
        Returns:
            tuple[list[DomainAlignment], list[dict]]:
                - Structured DomainAlignment objects
                - Finding/match record dicts for identity analysis aggregation
        """
        alignments: list[DomainAlignment] = []
        finding_records: list[dict[str, Any]] = []

        # 1. Collect all observed domains deduplicated by normalized root
        raw_domains: list[str] = []
        for d in content.structured_signals.domains:
            raw_domains.append(d.domain)
        for u in content.structured_signals.urls:
            raw_domains.append(u.domain)
        for e in claimed_entities:
            if e.associated_domain:
                raw_domains.append(e.associated_domain)

        seen_roots: set[str] = set()
        observed_domains: list[str] = []
        for rd in raw_domains:
            root_d, _ = IdentityNormalizer.normalize_domain(rd)
            if root_d and root_d not in seen_roots:
                seen_roots.add(root_d)
                observed_domains.append(root_d)

        if not observed_domains:
            return alignments, finding_records


        # 2. Build authoritative domain lookup map from sources and candidates
        auth_domain_map: dict[str, tuple[str, list[str]]] = {}  # entity_norm -> (auth_domain, source_ids)

        for cand in candidate_entities:
            if cand.official_domain:
                auth_norm_root, _ = IdentityNormalizer.normalize_domain(cand.official_domain)
                auth_domain_map[cand.normalized_name.lower()] = (auth_norm_root, cand.source_document_ids)

        if sources:
            for csr in sources.claim_sources:
                for doc in csr.documents:
                    meta = doc.metadata or {}
                    doc_domain = meta.get("official_domain") or meta.get("domain") or meta.get("website")
                    legal_name = meta.get("legal_name") or meta.get("name")
                    if doc_domain and legal_name:
                        auth_norm_root, _ = IdentityNormalizer.normalize_domain(doc_domain)
                        auth_domain_map[legal_name.lower()] = (auth_norm_root, [doc.document_id])
                        canon_org, _ = IdentityNormalizer.normalize_org_name(legal_name)
                        if canon_org:
                            auth_domain_map[canon_org.lower()] = (auth_norm_root, [doc.document_id])

        # 3. For each observed domain, evaluate alignment
        for obs_raw in sorted(observed_domains):
            obs_root, obs_host = IdentityNormalizer.normalize_domain(obs_raw)
            if not obs_root:
                continue

            # Identify the most relevant claimed organization or brand
            relevant_entity: Optional[ClaimedEntity] = None
            for e in claimed_entities:
                if e.associated_domain and (
                    obs_root in e.associated_domain or e.associated_domain in obs_root
                ):
                    relevant_entity = e
                    break
                elif e.entity_type.value in ("ORGANIZATION", "COMPANY", "BRAND", "FINANCIAL_INTERMEDIARY", "BROKER"):
                    relevant_entity = e
                    break

            claimed_name = relevant_entity.name if relevant_entity else None
            claimed_norm = relevant_entity.normalized_name.lower() if relevant_entity else ""

            # Check if we have an authoritative domain on record for this entity
            auth_tuple = auth_domain_map.get(claimed_norm)
            if not auth_tuple and relevant_entity:
                # Try raw name
                auth_tuple = auth_domain_map.get(relevant_entity.name.lower())

            if auth_tuple:
                auth_domain, source_ids = auth_tuple
                auth_root, _ = IdentityNormalizer.normalize_domain(auth_domain)

                if obs_root == auth_root:
                    # Verified match between observed domain and official registry record
                    alignments.append(DomainAlignment(
                        observed_domain=obs_raw,
                        claimed_brand_or_entity=claimed_name,
                        authoritative_domain=auth_domain,
                        alignment_status="ALIGNED",
                        evidence_basis=f"Observed domain '{obs_root}' matches authoritative registry domain '{auth_root}'.",
                        source_ids=source_ids,
                    ))
                    finding_records.append({
                        "entity_id": relevant_entity.entity_id if relevant_entity else "UNKNOWN",
                        "status": IdentityMatchStatus.ESTABLISHED,
                        "finding_type": IdentityFindingType.DOMAIN_ALIGNMENT_ESTABLISHED,
                        "basis": f"Domain '{obs_root}' is officially registered to '{claimed_name}'.",
                        "description": f"Domain alignment confirmed with authoritative record '{auth_domain}'.",
                        "source_ids": source_ids,
                    })
                else:
                    # Conflict: Authoritative domain exists on record, but observed domain is DIFFERENT!
                    alignments.append(DomainAlignment(
                        observed_domain=obs_raw,
                        claimed_brand_or_entity=claimed_name,
                        authoritative_domain=auth_domain,
                        alignment_status="MISMATCH",
                        evidence_basis=f"Observed domain '{obs_root}' conflicts with authoritative registry domain '{auth_root}'.",
                        source_ids=source_ids,
                    ))
                    finding_records.append({
                        "entity_id": relevant_entity.entity_id if relevant_entity else "UNKNOWN",
                        "status": IdentityMatchStatus.IDENTITY_MISMATCH,
                        "finding_type": IdentityFindingType.DOMAIN_IDENTITY_MISMATCH,
                        "basis": f"Content represents '{claimed_name}' using domain '{obs_root}', while official registry records specify '{auth_root}'.",
                        "description": f"Domain mismatch between observed '{obs_root}' and official '{auth_root}'.",
                        "source_ids": source_ids,
                    })
            else:
                # No authoritative domain record available
                alignments.append(DomainAlignment(
                    observed_domain=obs_raw,
                    claimed_brand_or_entity=claimed_name,
                    authoritative_domain=None,
                    alignment_status="NOT_ESTABLISHED",
                    evidence_basis=f"No authoritative domain record available for claimed entity '{claimed_name or obs_root}'.",
                    source_ids=[],
                ))
                finding_records.append({
                    "entity_id": relevant_entity.entity_id if relevant_entity else "UNKNOWN",
                    "status": IdentityMatchStatus.NOT_ESTABLISHED,
                    "finding_type": IdentityFindingType.DOMAIN_ALIGNMENT_NOT_ESTABLISHED,
                    "basis": f"Official domain ownership for '{obs_root}' could not be established from available authoritative records.",
                    "description": f"Domain '{obs_root}' remains unverified against official sources (not automatically malicious).",
                    "source_ids": [],
                })

        return alignments, finding_records

"""Registration-to-Entity Resolver for Engine 9.

Resolves claimed registration numbers (e.g. SEBI INA/INH/INZ, CIN, LLPIN)
against authoritative sources and evidence items. Distinguishes:
- Registration exists and matches claimed entity -> ESTABLISHED / REGISTRATION_ENTITY_MATCH
- Registration exists but belongs to a different entity -> IDENTITY_MISMATCH / REGISTRATION_ENTITY_MISMATCH
- Registration search returned NO_MATCH -> NOT_ESTABLISHED (NOT a mismatch)
- Registration claimed but identifier missing -> REGISTRATION_IDENTIFIER_UNRESOLVED
- Source retrieval failed / unavailable -> SOURCE_UNAVAILABLE
- Multiple matching candidate entities -> AMBIGUOUS
"""

import re
from typing import Optional, Any
from nivesh.schemas.sources import SourceAnalysis, SourceDocument
from nivesh.schemas.evidence import EvidenceAnalysis, VerificationResult
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.identity.schemas import (
    ClaimedEntity,
    ResolvedEntity,
    IdentityEntityType,
    IdentityMatchStatus,
    IdentityFindingType,
)
from nivesh.identity.normalizer import IdentityNormalizer


class RegistrationResolver:
    """Deterministic resolver for entity registration credentials against official records."""

    @classmethod
    def resolve_registrations(
        cls,
        claimed_entities: list[ClaimedEntity],
        sources: Optional[SourceAnalysis] = None,
        evidence: Optional[EvidenceAnalysis] = None,
        claims: Optional[ClaimAnalysis] = None,
    ) -> tuple[list[ResolvedEntity], list[dict[str, Any]]]:
        """Resolves registrations for all claimed entities.
        
        Returns:
            tuple[list[ResolvedEntity], list[dict]]:
                - Resolved authoritative candidates discovered
                - List of match evaluation dicts for downstream match construction
        """
        candidates: list[ResolvedEntity] = []
        resolution_records: list[dict[str, Any]] = []
        cand_counter = 1

        # Collect all source documents across claims
        source_docs: list[SourceDocument] = []
        source_unavailable = False
        if sources:
            for csr in sources.claim_sources:
                source_docs.extend(csr.documents)
                for doc in csr.documents:
                    if doc.retrieval.status in ("SOURCE_UNAVAILABLE", "RETRIEVAL_FAILED", "TIMEOUT"):
                        source_unavailable = True

        # Collect evidence verification items
        evidence_results: list[VerificationResult] = []
        if evidence:
            evidence_results.extend(evidence.verifications)

        for entity in claimed_entities:
            # Skip non-identifiable / pure domain / pure channel entities in registration check
            if entity.entity_type in (
                IdentityEntityType.DOMAIN,
                IdentityEntityType.CHANNEL,
                IdentityEntityType.SOCIAL_ACCOUNT,
                IdentityEntityType.WEBSITE,
                IdentityEntityType.REGULATOR,
            ):
                continue


            reg_id = entity.associated_registration
            entity_norm = entity.normalized_name

            # Check if entity claims registration in claims or text
            claims_registration = False
            relevant_claim_id = None
            if entity.associated_registration:
                claims_registration = True
            elif entity.entity_type in (
                IdentityEntityType.ADVISER,
                IdentityEntityType.BROKER,
                IdentityEntityType.FINANCIAL_INTERMEDIARY,
            ):
                claims_registration = True
            elif claims:
                for c in claims.claims:
                    c_text = c.text.normalized.lower()
                    if ("register" in c_text or "sebi" in c_text or "license" in c_text) and (
                        entity_norm.lower() in c_text or entity.name.lower() in c_text
                    ):
                        claims_registration = True
                        relevant_claim_id = c.claim_id
                        break

            # If no registration claimed or associated, skip registration resolution for this entity
            if not claims_registration and not reg_id:
                continue

            # Case 1: Registration claimed but NO identifier provided
            if not reg_id:
                # Check if source documents contain an authoritative lookup by name
                name_match_candidates = cls._find_candidates_by_name(entity, source_docs)
                if not name_match_candidates:
                    # Check if source retrieval was unavailable
                    if source_unavailable:
                        resolution_records.append({
                            "entity": entity,
                            "candidate": None,
                            "status": IdentityMatchStatus.SOURCE_UNAVAILABLE,
                            "finding_type": IdentityFindingType.SOURCE_UNAVAILABLE,
                            "basis": "Authoritative registry could not be retrieved to verify claimed registration.",
                            "source_ids": [doc.document_id for doc in source_docs],
                            "evidence_ids": [vr.claim_id for vr in evidence_results],
                            "claim_id": relevant_claim_id,
                            "matching_attrs": [],
                            "conflicting_attrs": [],
                            "confidence": 0.5,
                        })
                    else:
                        resolution_records.append({
                            "entity": entity,
                            "candidate": None,
                            "status": IdentityMatchStatus.NOT_ESTABLISHED,
                            "finding_type": IdentityFindingType.REGISTRATION_IDENTIFIER_UNRESOLVED,
                            "basis": f"Content asserts registration for '{entity.name}', but no registration identifier was provided and registry search yielded no matching entity.",
                            "source_ids": [doc.document_id for doc in source_docs],
                            "evidence_ids": [vr.claim_id for vr in evidence_results],
                            "claim_id": relevant_claim_id,
                            "matching_attrs": [],
                            "conflicting_attrs": [],
                            "confidence": 0.85,
                        })
                    continue
                else:
                    # Found candidate(s) by name
                    if len(name_match_candidates) > 1:
                        resolution_records.append({
                            "entity": entity,
                            "candidate": None,
                            "status": IdentityMatchStatus.AMBIGUOUS,
                            "finding_type": IdentityFindingType.IDENTITY_AMBIGUOUS,
                            "basis": f"Multiple authoritative records found matching name '{entity.name}' without distinguishing identifier.",
                            "source_ids": [doc.document_id for doc in source_docs],
                            "evidence_ids": [vr.claim_id for vr in evidence_results],
                            "claim_id": relevant_claim_id,
                            "matching_attrs": ["legal_name"],
                            "conflicting_attrs": [],
                            "confidence": 0.4,
                        })
                        continue
                    else:
                        cand = name_match_candidates[0]
                        candidates.append(cand)
                        resolution_records.append({
                            "entity": entity,
                            "candidate": cand,
                            "status": IdentityMatchStatus.ESTABLISHED,
                            "finding_type": IdentityFindingType.REGISTRATION_ENTITY_MATCH,
                            "basis": f"Authoritative registry record '{cand.legal_name}' matches claimed entity name.",
                            "source_ids": cand.source_document_ids,
                            "evidence_ids": [vr.claim_id for vr in evidence_results],
                            "claim_id": relevant_claim_id,
                            "matching_attrs": ["legal_name", "regulator"],
                            "conflicting_attrs": [],
                            "confidence": 0.9,
                        })
                        continue

            # Case 2: Specific registration identifier IS provided
            norm_reg_id = IdentityNormalizer.normalize_registration_id(reg_id)
            reg_candidates, mismatch_records = cls._evaluate_registration_id(
                entity=entity,
                norm_reg_id=norm_reg_id,
                source_docs=source_docs,
                evidence_results=evidence_results,
                cand_counter=cand_counter,
            )

            for cand in reg_candidates:
                candidates.append(cand)
                cand_counter += 1

            if mismatch_records:
                for rec in mismatch_records:
                    rec["claim_id"] = relevant_claim_id or (entity.source_claim_ids[0] if entity.source_claim_ids else None)
                    resolution_records.append(rec)
            elif not reg_candidates:
                # Registration number searched, but no records returned or source unavailable
                if source_unavailable:
                    resolution_records.append({
                        "entity": entity,
                        "candidate": None,
                        "status": IdentityMatchStatus.SOURCE_UNAVAILABLE,
                        "finding_type": IdentityFindingType.SOURCE_UNAVAILABLE,
                        "basis": f"Authoritative registry source was unavailable to verify registration '{reg_id}'.",
                        "source_ids": [doc.document_id for doc in source_docs],
                        "evidence_ids": [vr.claim_id for vr in evidence_results],
                        "claim_id": relevant_claim_id,
                        "matching_attrs": [],
                        "conflicting_attrs": [],
                        "confidence": 0.5,
                    })
                else:
                    # Registry search returned NO_MATCH -> NOT_ESTABLISHED (NOT IDENTITY_MISMATCH!)
                    resolution_records.append({
                        "entity": entity,
                        "candidate": None,
                        "status": IdentityMatchStatus.NOT_ESTABLISHED,
                        "finding_type": IdentityFindingType.AUTHORITY_IDENTITY_NOT_ESTABLISHED,
                        "basis": f"Authoritative registry search for registration '{reg_id}' yielded no matching records.",
                        "source_ids": [doc.document_id for doc in source_docs],
                        "evidence_ids": [vr.claim_id for vr in evidence_results],
                        "claim_id": relevant_claim_id,
                        "matching_attrs": [],
                        "conflicting_attrs": [],
                        "confidence": 0.9,
                    })

        return candidates, resolution_records

    @classmethod
    def _find_candidates_by_name(
        cls,
        entity: ClaimedEntity,
        source_docs: list[SourceDocument],
    ) -> list[ResolvedEntity]:
        """Finds authoritative candidates matching the claimed entity name."""
        candidates: list[ResolvedEntity] = []
        entity_norm = entity.normalized_name.lower()
        cand_idx = 1

        for doc in source_docs:
            if doc.retrieval.status != "SUCCESS":
                continue
            meta = doc.metadata or {}
            reg_name = meta.get("legal_name") or meta.get("name")
            if not reg_name and "Query:" in doc.content:
                # Parse fixture format if present
                m = re.search(r"Entity Legal Name:\s*([^\n]+)", doc.content, re.IGNORECASE)
                if m:
                    reg_name = m.group(1).strip()

            if reg_name:
                norm_reg_person = IdentityNormalizer.normalize_person_name(reg_name)
                canon_reg_org, clean_org = IdentityNormalizer.normalize_org_name(reg_name)

                # Check strict matching
                matched = False
                if entity.entity_type in (IdentityEntityType.PERSON, IdentityEntityType.ADVISER):
                    # Strict person comparison - do NOT merge initials
                    if norm_reg_person and norm_reg_person == entity_norm:
                        matched = True
                else:
                    if canon_reg_org and canon_reg_org.lower() == entity_norm.lower():
                        matched = True

                if matched:
                    candidates.append(ResolvedEntity(
                        candidate_id=f"CAND-{cand_idx:03d}",
                        legal_name=reg_name,
                        normalized_name=norm_reg_person or canon_reg_org,
                        entity_type=entity.entity_type,
                        registration_number=meta.get("registration_number"),
                        official_domain=meta.get("official_domain") or meta.get("domain"),
                        regulator=doc.organization or "SEBI",
                        source_document_ids=[doc.document_id],
                        attributes=meta,
                    ))
                    cand_idx += 1

        return candidates

    @classmethod
    def _evaluate_registration_id(
        cls,
        entity: ClaimedEntity,
        norm_reg_id: str,
        source_docs: list[SourceDocument],
        evidence_results: list[VerificationResult],
        cand_counter: int,
    ) -> tuple[list[ResolvedEntity], list[dict[str, Any]]]:
        """Evaluates a specific registration identifier against official source documents and evidence."""
        candidates: list[ResolvedEntity] = []
        records: list[dict[str, Any]] = []

        # 1. Search in source documents
        for doc in source_docs:
            meta = doc.metadata or {}
            doc_reg_id = IdentityNormalizer.normalize_registration_id(
                meta.get("registration_number") or ""
            )

            # Check doc content for registration identifier if not in metadata
            content_has_reg = (norm_reg_id in IdentityNormalizer.normalize_registration_id(doc.content)) if doc.content else False

            if doc_reg_id == norm_reg_id or content_has_reg:
                authoritative_legal_name = meta.get("legal_name")
                if not authoritative_legal_name and doc.content:
                    # Look for legal name in text (e.g. 'belongs to Alpha Wealth Advisors Private Limited, not Rahul Sharma')
                    m_legal = re.search(r"Entity Legal Name:\s*([^\n]+)", doc.content, re.IGNORECASE)
                    if m_legal:
                        authoritative_legal_name = m_legal.group(1).strip()
                    else:
                        m_belongs = re.search(r"belongs to ([^,\.]+)", doc.content, re.IGNORECASE)
                        if m_belongs:
                            authoritative_legal_name = m_belongs.group(1).strip()

                if authoritative_legal_name:
                    canon_auth, clean_auth = IdentityNormalizer.normalize_org_name(authoritative_legal_name)
                    norm_auth_person = IdentityNormalizer.normalize_person_name(authoritative_legal_name)

                    candidate = ResolvedEntity(
                        candidate_id=f"CAND-{cand_counter:03d}",
                        legal_name=authoritative_legal_name,
                        normalized_name=norm_auth_person or canon_auth,
                        entity_type=IdentityEntityType.ORGANIZATION if "LTD" in clean_auth or "LLP" in clean_auth else entity.entity_type,
                        registration_number=meta.get("registration_number") or norm_reg_id,
                        official_domain=meta.get("official_domain") or meta.get("domain"),
                        regulator=doc.organization or "SEBI",
                        source_document_ids=[doc.document_id],
                        attributes=meta,
                    )
                    candidates.append(candidate)

                    # Compare claimed entity with authoritative owner of registration
                    entity_norm = entity.normalized_name.lower()
                    auth_org_norm = canon_auth.lower()
                    auth_person_norm = norm_auth_person.lower()

                    name_matches = (
                        entity_norm == auth_person_norm
                        or entity_norm == auth_org_norm
                        or entity.name.lower() == authoritative_legal_name.lower()
                    )

                    if name_matches:
                        records.append({
                            "entity": entity,
                            "candidate": candidate,
                            "status": IdentityMatchStatus.ESTABLISHED,
                            "finding_type": IdentityFindingType.REGISTRATION_ENTITY_MATCH,
                            "basis": f"Registration '{norm_reg_id}' is officially registered to '{authoritative_legal_name}', which matches claimed entity.",
                            "source_ids": [doc.document_id],
                            "evidence_ids": [vr.claim_id for vr in evidence_results],
                            "matching_attrs": ["registration_number", "legal_name", "regulator"],
                            "conflicting_attrs": [],
                            "confidence": 0.95,
                        })
                    else:
                        # Genuine MISMATCH: Registration exists, but belongs to a DIFFERENT entity!
                        records.append({
                            "entity": entity,
                            "candidate": candidate,
                            "status": IdentityMatchStatus.IDENTITY_MISMATCH,
                            "finding_type": IdentityFindingType.REGISTRATION_ENTITY_MISMATCH,
                            "basis": f"Registration '{norm_reg_id}' belongs to '{authoritative_legal_name}', not claimed entity '{entity.name}'.",
                            "source_ids": [doc.document_id],
                            "evidence_ids": [vr.claim_id for vr in evidence_results],
                            "matching_attrs": ["registration_number"],
                            "conflicting_attrs": ["legal_name", "entity_identity"],
                            "confidence": 0.95,
                        })

        # 2. Check evidence reasoning trace for explicit registration mismatch findings if not already captured
        if not records:
            for vr in evidence_results:
                for trace in vr.reasoning_trace + [e.reasoning for e in vr.contradicting_evidence]:
                    if "belongs to" in trace.lower() and ("not " in trace.lower() or "different" in trace.lower()):
                        # Found evidence of registration mismatch
                        records.append({
                            "entity": entity,
                            "candidate": None,
                            "status": IdentityMatchStatus.IDENTITY_MISMATCH,
                            "finding_type": IdentityFindingType.REGISTRATION_ENTITY_MISMATCH,
                            "basis": trace,
                            "source_ids": [e.source_document_id for e in vr.contradicting_evidence if e.source_document_id],
                            "evidence_ids": [vr.claim_id],
                            "matching_attrs": ["registration_number"],
                            "conflicting_attrs": ["legal_name"],
                            "confidence": 0.95,
                        })
                        break

        return candidates, records

"""Canonical Service Interface for Engine 9: Identity Verification & Entity Resolution.

Coordinates:
- Entity extraction & normalization
- Registration identity matching
- Domain and brand alignment
- Authority and regulator identity verification
- Social channel identity verification
- Deterministic attribute matching
- Provenance tracking and finding generation
"""

import threading
from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.identity.schemas import (
    IdentityAnalysis,
    IdentityStatus,
    IdentityMatchStatus,
    IdentityMatch,
    ClaimedEntity,
    IdentityFindingType,
    ENGINE_VERSION,
)
from nivesh.identity.entity_resolver import EntityResolver
from nivesh.identity.registration_resolver import RegistrationResolver
from nivesh.identity.domain_resolver import DomainResolver
from nivesh.identity.authority_resolver import AuthorityResolver
from nivesh.identity.social_resolver import SocialResolver
from nivesh.identity.matcher import IdentityMatcher
from nivesh.identity.findings import IdentityFindingGenerator
from nivesh.identity.provenance import ProvenanceBuilder


class IdentityVerificationEngine:
    """Canonical Engine 9 implementation for Nivesh Firewall."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counter: int = 1
        self._analyses: dict[str, IdentityAnalysis] = {}
        self._entities: dict[str, ClaimedEntity] = {}

    def verify(
        self,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None,
        sources: Optional[SourceAnalysis] = None,
        evidence: Optional[EvidenceAnalysis] = None,
        threat: Optional[ThreatAnalysis] = None,
    ) -> IdentityAnalysis:
        """Verifies claimed entity identity consistency against authoritative evidence."""
        with self._lock:
            analysis_id = f"IDA-{self._counter:03d}"
            self._counter += 1

        # 1. Extract and normalize claimed entities
        claimed_entities = EntityResolver.resolve_claimed_entities(content, claims)

        # 2. Resolve registrations against official records
        candidates, reg_records = RegistrationResolver.resolve_registrations(
            claimed_entities=claimed_entities,
            sources=sources,
            evidence=evidence,
            claims=claims,
        )

        # 3. Resolve domains and brand alignments
        domain_alignments, domain_records = DomainResolver.resolve_domains(
            content=content,
            claimed_entities=claimed_entities,
            candidate_entities=candidates,
            sources=sources,
        )

        # 4. Resolve authority and regulatory alignment
        authority_alignments, authority_records = AuthorityResolver.resolve_authorities(
            content=content,
            claims=claims,
            claimed_entities=claimed_entities,
            candidate_entities=candidates,
            registration_records=reg_records,
            sources=sources,
            evidence=evidence,
        )

        # 5. Resolve social channels and handles
        social_records = SocialResolver.resolve_social_channels(
            content=content,
            claimed_entities=claimed_entities,
            candidate_entities=candidates,
            sources=sources,
        )

        # 6. Perform attribute-level deterministic matching for each claimed entity
        identity_matches: list[IdentityMatch] = []
        match_idx = 1
        for entity in claimed_entities:
            # Check if this entity has a specific registration or domain resolution record
            matching_record = None
            for rec in reg_records + domain_records:
                if rec.get("entity") == entity or rec.get("entity_id") == entity.entity_id:
                    matching_record = rec
                    break

            # Find candidate if available
            cand = next((c for c in candidates if c.candidate_id == (matching_record.get("candidate").candidate_id if matching_record and matching_record.get("candidate") else None)), None)
            if not cand and candidates:
                # Fallback to match by name
                cand = next((c for c in candidates if c.normalized_name.lower() == entity.normalized_name.lower()), None)

            match = IdentityMatcher.compare(
                match_id=f"IDM-{match_idx:03d}",
                claimed=entity,
                candidate=cand,
                resolution_record=matching_record,
            )
            identity_matches.append(match)
            match_idx += 1

        # 7. Aggregate all finding records and generate formal findings
        all_finding_records = reg_records + domain_records + authority_records + social_records
        findings = IdentityFindingGenerator.generate_findings(all_finding_records)

        # 8. Determine overall interaction identity status
        overall_status = self._determine_overall_status(
            claimed_entities=claimed_entities,
            matches=identity_matches,
            findings=findings,
            sources=sources,
        )

        # 9. Compute identity resolution confidence (NOT scam probability)
        confidence = self._compute_identity_confidence(identity_matches, overall_status)

        # 10. Generate provenance and upstream audit references
        provenance, upstream_refs = ProvenanceBuilder.build(
            content=content,
            claims=claims,
            sources=sources,
            evidence=evidence,
            threat=threat,
        )

        # 11. Instantiate canonical IdentityAnalysis
        analysis = IdentityAnalysis(
            analysis_id=analysis_id,
            entities=claimed_entities,
            identity_matches=identity_matches,
            identity_findings=findings,
            identity_status=overall_status,
            authority_alignments=authority_alignments,
            domain_alignments=domain_alignments,
            confidence=confidence,
            provenance=provenance,
            upstream_references=upstream_refs,
            engine_version=ENGINE_VERSION,
        )

        # 12. Save to in-memory store
        with self._lock:
            self._analyses[analysis_id] = analysis
            for e in claimed_entities:
                self._entities[e.entity_id] = e

        return analysis

    def _determine_overall_status(
        self,
        claimed_entities: list[ClaimedEntity],
        matches: list[IdentityMatch],
        findings: list[Any],
        sources: Optional[SourceAnalysis],
    ) -> IdentityStatus:
        """Determines the interaction-level identity status based on all evaluations."""
        if not claimed_entities:
            return IdentityStatus.NOT_APPLICABLE

        # Any mismatch triggers interaction-level IDENTITY_MISMATCH
        has_mismatch = any(
            m.match_status == IdentityMatchStatus.IDENTITY_MISMATCH for m in matches
        ) or any(
            f.finding_type in (
                IdentityFindingType.REGISTRATION_ENTITY_MISMATCH,
                IdentityFindingType.DOMAIN_IDENTITY_MISMATCH,
                IdentityFindingType.AUTHORITY_IDENTITY_MISMATCH,
                IdentityFindingType.BRAND_IDENTITY_MISMATCH,
                IdentityFindingType.IDENTITY_MISMATCH,
            ) for f in findings
        )
        if has_mismatch:
            return IdentityStatus.IDENTITY_MISMATCH

        # Check for ambiguity
        has_ambiguous = any(
            m.match_status == IdentityMatchStatus.AMBIGUOUS for m in matches
        ) or any(
            f.finding_type in (
                IdentityFindingType.IDENTITY_AMBIGUOUS,
            ) for f in findings
        )
        if has_ambiguous:
            return IdentityStatus.AMBIGUOUS

        # Check for source unavailable
        source_unavailable = any(
            m.match_status == IdentityMatchStatus.SOURCE_UNAVAILABLE for m in matches
        ) or any(
            f.finding_type == IdentityFindingType.SOURCE_UNAVAILABLE for f in findings
        )
        if source_unavailable:
            return IdentityStatus.SOURCE_UNAVAILABLE

        # Check for established / partial
        primary_matches = [
            m for m in matches
            if m.entity_type.value in ("PERSON", "ADVISER", "ORGANIZATION", "COMPANY", "FINANCIAL_INTERMEDIARY", "BROKER")
        ]
        if not primary_matches:
            primary_matches = matches

        if all(m.match_status == IdentityMatchStatus.ESTABLISHED for m in primary_matches):
            return IdentityStatus.ESTABLISHED

        if any(m.match_status in (IdentityMatchStatus.ESTABLISHED, IdentityMatchStatus.PARTIALLY_ESTABLISHED) for m in primary_matches):
            return IdentityStatus.PARTIALLY_ESTABLISHED

        return IdentityStatus.NOT_ESTABLISHED

    def _compute_identity_confidence(
        self,
        matches: list[IdentityMatch],
        status: IdentityStatus,
    ) -> float:
        """Calculates confidence in the identity resolution verdict (NOT scam probability)."""
        if not matches:
            return 0.5

        if status == IdentityStatus.ESTABLISHED:
            confidences = [m.confidence for m in matches if m.match_status == IdentityMatchStatus.ESTABLISHED]
            return round(sum(confidences) / len(confidences), 2) if confidences else 0.95

        if status == IdentityStatus.IDENTITY_MISMATCH:
            confidences = [m.confidence for m in matches if m.match_status == IdentityMatchStatus.IDENTITY_MISMATCH]
            return round(sum(confidences) / len(confidences), 2) if confidences else 0.95

        if status == IdentityStatus.AMBIGUOUS:
            return 0.40

        if status == IdentityStatus.SOURCE_UNAVAILABLE:
            return 0.50

        # NOT_ESTABLISHED
        return 0.85

    def get_analysis(self, analysis_id: str) -> Optional[IdentityAnalysis]:
        """Retrieves an IdentityAnalysis by ID from the in-memory cache."""
        with self._lock:
            return self._analyses.get(analysis_id)

    def get_entity(self, entity_id: str) -> Optional[ClaimedEntity]:
        """Retrieves a ClaimedEntity by ID from the in-memory cache."""
        with self._lock:
            return self._entities.get(entity_id)

    def reset(self) -> None:
        """Resets the engine state for testing and isolation."""
        with self._lock:
            self._counter = 1
            self._analyses.clear()
            self._entities.clear()

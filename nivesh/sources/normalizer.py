"""Source Document Normalizer and Evidence Candidate Extractor for Engine 4.

Processes retrieved SourceDocuments to produce focused, structured EvidenceCandidates:
- Extracts verbatim or focused excerpts relevant to a claim
- Identifies matched terms, entities, and dates
- Preserves full provenance audit trail
- CRITICAL: Always maintains verification_status = 'UNVERIFIED'.
"""

import re
from typing import Optional
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import (
    SourceDocument,
    EvidenceCandidate,
    EvidenceRelevance,
    EvidenceProvenance,
    AuthorityTier,
)


class SourceNormalizer:
    """Extracts structured evidence candidates from authoritative documents."""

    @classmethod
    def extract_evidence_candidates(
        cls,
        claim: CanonicalClaim,
        document: SourceDocument,
        authority_tier: AuthorityTier = "PRIMARY_OFFICIAL",
        candidate_index: int = 1,
    ) -> list[EvidenceCandidate]:
        """Extracts relevant source excerpts and generates EvidenceCandidates.
        
        Leaves truth evaluation entirely to Engine 5.
        """
        # If document retrieval was unsuccessful or no content
        if not document.content or document.retrieval.status in ("RETRIEVAL_FAILED", "SOURCE_UNAVAILABLE", "RATE_LIMITED", "INVALID_QUERY"):
            return []

        doc_text = document.content
        lines = [line.strip() for line in doc_text.split("\n") if line.strip()]

        matched_terms: list[str] = []
        matched_entities: list[str] = []
        matched_dates: list[str] = []

        # 1. Match claim subject / entities
        subject = claim.subject or ""
        if subject and subject != "unspecified_offer":
            if subject.lower() in doc_text.lower():
                matched_entities.append(subject)

        # 2. Match predicate / key financial or regulatory terms
        predicate_terms = claim.predicate.lower().replace("_", " ").split() if claim.predicate else []
        for term in predicate_terms:
            if len(term) > 3 and term in doc_text.lower():
                if term not in matched_terms:
                    matched_terms.append(term)

        # 3. Match claim object (e.g. ratio 1:1, 40%, SEBI)
        obj_str = str(claim.object or "").strip()
        if obj_str and obj_str.lower() != "sebi":
            if obj_str.lower() in doc_text.lower():
                matched_terms.append(obj_str)

        # 4. Match dates or temporal context
        if claim.temporal_context and claim.temporal_context.date:
            if claim.temporal_context.date in doc_text:
                matched_dates.append(claim.temporal_context.date)

        # Check for year matches (e.g. 2024, 2025)
        for year in re.findall(r"\b202\d\b", claim.text.original if claim.text else ""):
            if year in doc_text and year not in matched_dates:
                matched_dates.append(year)

        # Determine relevant lines for excerpt
        relevant_lines: list[str] = []
        for line in lines:
            line_lower = line.lower()
            if (
                any(e.lower() in line_lower for e in matched_entities)
                or any(t.lower() in line_lower for t in matched_terms)
                or any(d in line for d in matched_dates)
                or "prohibition" in line_lower
                or "registration number" in line_lower
                or "status" in line_lower
            ):
                relevant_lines.append(line)

        # If specific lines matched, combine them; otherwise take first 500 chars of normalized doc
        if relevant_lines:
            excerpt = "\n".join(relevant_lines[:8])
        else:
            excerpt = "\n".join(lines[:6]) if lines else doc_text[:400]

        # Calculate basic structural relevance score
        signals_matched = len(matched_entities) + len(matched_terms) + len(matched_dates)
        relevance_score = min(1.0, 0.4 + (0.2 * signals_matched)) if document.retrieval.status == "SUCCESS" else 0.2

        evidence_id = f"EVID-{document.document_id.replace('DOC-', '')}-{candidate_index:03d}"

        candidate = EvidenceCandidate(
            evidence_id=evidence_id,
            claim_id=claim.claim_id,
            source_document_id=document.document_id,
            excerpt=excerpt,
            relevance=EvidenceRelevance(
                matched_terms=matched_terms,
                matched_entities=matched_entities,
                matched_dates=matched_dates,
                relevance_score=relevance_score,
            ),
            source_type=document.source_type,
            authority_tier=authority_tier,
            provenance=EvidenceProvenance(
                retrieved_at=document.retrieved_at,
                retrieval_method=document.retrieval.method,
                source_mode=document.retrieval.mode,
                source_url=document.url,
            ),
            authoritative_provenance=document.authoritative_provenance,
            verification_status="UNVERIFIED",  # Strictly UNVERIFIED! Engine 5 decides.
        )

        return [candidate]

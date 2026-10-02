"""Claim Intelligence Engine (Engine 2 of Nivesh Firewall).

Converts Engine 1's NormalizedContent into structured, atomic, canonical claims.
Answers: 'What specific assertions are being made?'
Never performs truth evaluation, risk scoring, or blocking.
"""

import time
from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import (
    ClaimAnalysis,
    CanonicalClaim,
    ClaimRelation,
    ClaimAnalysisMetadata,
)
from nivesh.claims.segmenter import ClaimSegmenter
from nivesh.claims.canonicalizer import ClaimCanonicalizer
from nivesh.claims.relation_detector import RelationDetector
from nivesh.claims.deduplicator import ClaimDeduplicator
from nivesh.claims.llm_adapter import LlmClaimAdapter

ENGINE_VERSION = "1.0.0"


class ClaimIntelligenceEngine:
    """Core Engine 2 service interface."""

    def __init__(
        self,
        llm_adapter: Optional[LlmClaimAdapter] = None,
    ):
        self.segmenter = ClaimSegmenter()
        self.canonicalizer = ClaimCanonicalizer()
        self.relation_detector = RelationDetector()
        self.deduplicator = ClaimDeduplicator()
        self.llm_adapter = llm_adapter or LlmClaimAdapter()

    def analyze(self, content: NormalizedContent) -> ClaimAnalysis:
        """Analyzes NormalizedContent and outputs structured ClaimAnalysis.
        
        Directly callable from unit tests and service layer without HTTP.
        """
        start_time = time.perf_counter()
        content_id = content.content_id
        text = content.normalized.text if content.normalized else ""

        # Collect context entities from Engine 1
        context_entities = []
        if content.entities:
            context_entities.extend(p.normalized for p in content.entities.people)
            context_entities.extend(r.text for r in content.entities.regulators)
            context_entities.extend(o.normalized for o in content.entities.organizations)

        context_numbers = []
        if content.structured_signals:
            context_numbers.extend(str(a.value) for a in content.structured_signals.currency_amounts)
            context_numbers.extend(str(p.value) for p in content.structured_signals.percentages)

        # 1. Candidate Segmentation (with Action filtering)
        candidates, actions_filtered = self.segmenter.segment(text)

        # 2. Canonical Claim Construction
        raw_claims: list[CanonicalClaim] = []
        discourse_markers: dict[str, str] = {}
        claim_counter = 1

        for cand in candidates:
            claim = self.canonicalizer.canonicalize(
                candidate_text=cand.text,
                source_span=cand.span,
                source_content_id=content_id,
                claim_index=claim_counter,
                context_entities=context_entities,
                context_numbers=context_numbers,
            )
            if claim:
                raw_claims.append(claim)
                if cand.discourse_marker:
                    discourse_markers[claim.claim_id] = cand.discourse_marker
                claim_counter += 1

        # 3. Deduplication of identical underlying claims
        deduped_claims, duplicates_merged = self.deduplicator.deduplicate(raw_claims)

        # 4. Claim Relationship Detection
        relations = self.relation_detector.detect_relations(
            claims=deduped_claims,
            discourse_markers=discourse_markers
        )

        # 5. Metadata compilation
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        type_counts: dict[str, int] = {}
        for c in deduped_claims:
            type_counts[c.claim_type] = type_counts.get(c.claim_type, 0) + 1

        metadata = ClaimAnalysisMetadata(
            processing_time_ms=duration_ms,
            total_claims=len(deduped_claims),
            claim_types_count=type_counts,
            actions_filtered_count=actions_filtered,
            duplicate_claims_merged=duplicates_merged,
        )

        return ClaimAnalysis(
            content_id=content_id,
            claims=deduped_claims,
            claim_relations=relations,
            analysis_metadata=metadata,
        )

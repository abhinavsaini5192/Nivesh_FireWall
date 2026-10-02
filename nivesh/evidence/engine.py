"""Evidence Verification Engine (Engine 5 of Nivesh Firewall).

Evaluates whether retrieved source material supports, contradicts, partially supports,
or fails to establish structured financial and regulatory claims.
Answers: 'What does the retrieved evidence actually establish about this specific claim?'
Never calculates scam probability or investment decisions.
"""

import time
from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.sources import SourceAnalysis, ClaimSourceResult
from nivesh.schemas.evidence import (
    EvidenceAnalysis,
    VerificationResult,
    EvidenceAnalysisMetadata,
)
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator
from nivesh.evidence.llm_verifier import LlmEvidenceVerifier

ENGINE_VERSION = "1.0.0"


class EvidenceVerificationEngine:
    """Core Engine 5 service interface."""

    def __init__(
        self,
        evaluator: Optional[ClaimEvidenceEvaluator] = None,
        llm_verifier: Optional[LlmEvidenceVerifier] = None,
    ):
        self.llm_verifier = llm_verifier or LlmEvidenceVerifier()
        self.evaluator = evaluator or ClaimEvidenceEvaluator(self.llm_verifier)

    def verify(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        sources: SourceAnalysis,
    ) -> EvidenceAnalysis:
        """Main service interface for Engine 5.
        
        Consumes NormalizedContent, ClaimAnalysis, and SourceAnalysis.
        Produces structured EvidenceAnalysis with claim-level VerificationResult instances.
        """
        start_time = time.time()
        verifications: list[VerificationResult] = []

        supported_count = 0
        partially_supported_count = 0
        contradicted_count = 0
        insufficient_count = 0
        not_verifiable_count = 0
        source_conflict_count = 0

        # Map sources by claim_id for quick lookup
        sources_by_claim: dict[str, ClaimSourceResult] = {
            s.claim_id: s for s in sources.claim_sources
        }

        for claim in claims.claims:
            claim_source_res = sources_by_claim.get(claim.claim_id)
            v_res = self.evaluator.evaluate(claim, claim_source_res)
            verifications.append(v_res)

            # Track metadata statistics
            status = v_res.status
            if status == "SUPPORTED":
                supported_count += 1
            elif status == "PARTIALLY_SUPPORTED":
                partially_supported_count += 1
            elif status == "CONTRADICTED":
                contradicted_count += 1
            elif status in ("INSUFFICIENT_EVIDENCE", "NO_USABLE_EVIDENCE", "SOURCE_UNAVAILABLE"):
                insufficient_count += 1
            elif status == "NOT_VERIFIABLE":
                not_verifiable_count += 1
            elif status == "SOURCE_CONFLICT":
                source_conflict_count += 1

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        metadata = EvidenceAnalysisMetadata(
            total_claims=len(claims.claims),
            claims_supported=supported_count,
            claims_partially_supported=partially_supported_count,
            claims_contradicted=contradicted_count,
            claims_insufficient=insufficient_count,
            claims_not_verifiable=not_verifiable_count,
            claims_source_conflict=source_conflict_count,
            processing_time_ms=processing_time_ms,
        )

        return EvidenceAnalysis(
            content_id=content.content_id,
            verifications=verifications,
            analysis_metadata=metadata,
        )

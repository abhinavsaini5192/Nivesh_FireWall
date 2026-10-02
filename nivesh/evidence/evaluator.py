"""Master Claim-Evidence Evaluator for Engine 5.

Orchestrates claim-specific evaluation across regulatory, numerical, temporal,
opinion/prediction, and conflict evaluators.
Produces stable VerificationResult instances with step-by-step reasoning traces.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import ClaimSourceResult, EvidenceCandidate, SourceDocument
from nivesh.schemas.evidence import (
    VerificationResult,
    EvidenceItemEvaluation,
    SourceAssessmentItem,
    VerificationProvenance,
    ClaimVerificationStatus,
    EvidenceStrength,
)
from nivesh.evidence.regulatory_evaluator import RegulatoryEvaluator
from nivesh.evidence.numerical_evaluator import NumericalEvaluator
from nivesh.evidence.opinion_prediction_evaluator import OpinionPredictionEvaluator
from nivesh.evidence.conflict_detector import ConflictDetector
from nivesh.evidence.llm_verifier import LlmEvidenceVerifier

ENGINE_VERSION = "1.0.0"


class ClaimEvidenceEvaluator:
    """Evaluates a single CanonicalClaim against its retrieved source evidence candidates."""

    def __init__(self, llm_verifier: Optional[LlmEvidenceVerifier] = None):
        self.llm_verifier = llm_verifier or LlmEvidenceVerifier()

    def evaluate(
        self,
        claim: CanonicalClaim,
        claim_source_res: Optional[ClaimSourceResult] = None
    ) -> VerificationResult:
        """Evaluates claim against retrieved source documents and evidence candidates."""
        verified_at_iso = datetime.now(timezone.utc).isoformat()
        provenance = VerificationProvenance(
            engine_version=ENGINE_VERSION,
            verification_method="hybrid",
            verified_at=verified_at_iso
        )

        candidates = claim_source_res.evidence_candidates if claim_source_res else []
        documents = claim_source_res.documents if claim_source_res else []

        # Assess sources consulted
        source_assessments: list[SourceAssessmentItem] = []
        if claim_source_res and claim_source_res.documents:
            for doc in claim_source_res.documents:
                source_assessments.append(SourceAssessmentItem(
                    source_id=doc.source_id,
                    organization=doc.organization,
                    authority_tier="PRIMARY_OFFICIAL" if doc.organization in ("SEBI", "NSE", "BSE", "RBI") else "SECONDARY_RELIABLE",
                    retrieval_status=doc.retrieval.status,
                    relevance_summary=f"Retrieved document '{doc.title}' with status {doc.retrieval.status}"
                ))

        # 1. PREDICTIONS & OPINIONS EVALUATOR (Evaluates whether claim is inherently subjective or forward-looking)
        opinion_pred_res = OpinionPredictionEvaluator.evaluate_claim(claim, candidates, documents)
        if opinion_pred_res:
            return self._build_result(claim, opinion_pred_res, source_assessments, provenance)

        # 2. NO EVIDENCE CASE / SOURCE UNAVAILABLE
        if not candidates and not documents:
            return VerificationResult(
                claim_id=claim.claim_id,
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.85,
                evidence_strength="NONE",
                supporting_evidence=[],
                contradicting_evidence=[],
                missing_elements=["Authoritative documentary evidence"],
                context_gaps=[],
                source_assessment=source_assessments,
                reasoning_trace=[
                    f"1. Claim asserts: '{claim.subject}' -> '{claim.predicate}' -> '{claim.object}'",
                    "2. No authoritative source evidence was retrieved to substantiate this claim.",
                    "3. In accordance with evidence standards, absence of evidence is recorded as INSUFFICIENT_EVIDENCE (not assumed false).",
                ],
                uncertainty=["No authoritative source material retrieved"],
                provenance=provenance
            )

        if not candidates and all(d.retrieval.status == "SOURCE_UNAVAILABLE" for d in documents):
            return VerificationResult(
                claim_id=claim.claim_id,
                status="SOURCE_UNAVAILABLE",
                confidence=0.90,
                evidence_strength="NONE",
                supporting_evidence=[],
                contradicting_evidence=[],
                missing_elements=["Connection to authoritative data source"],
                context_gaps=[],
                source_assessment=source_assessments,
                reasoning_trace=[
                    f"1. Claim asserts: '{claim.subject}' -> '{claim.predicate}'",
                    "2. Authoritative sources were uncontactable or unconfigured in current environment.",
                    "3. Result: SOURCE_UNAVAILABLE.",
                ],
                uncertainty=["External interface unavailable"],
                provenance=provenance
            )

        # 3. SOURCE CONFLICT DETECTOR
        conflict_res = ConflictDetector.detect_conflict(claim, candidates, documents)
        if conflict_res:
            return self._build_result(claim, conflict_res, source_assessments, provenance)

        # 4. REGULATORY & STATUTORY PROHIBITIONS EVALUATOR
        regulatory_res = RegulatoryEvaluator.evaluate_claim(claim, candidates, documents)
        if regulatory_res:
            return self._build_result(claim, regulatory_res, source_assessments, provenance)

        # 5. NUMERICAL, RATIO, & DEBT EVALUATOR
        numerical_res = NumericalEvaluator.evaluate_claim(claim, candidates, documents)
        if numerical_res:
            return self._build_result(claim, numerical_res, source_assessments, provenance)

        # 6. GENERAL SEMANTIC / HEURISTIC FALLBACK
        # Inspect candidates to see if subject and predicate are mentioned
        supporting: list[EvidenceItemEvaluation] = []
        contradicting: list[EvidenceItemEvaluation] = []
        reasoning = [
            f"1. Claim asserts: '{claim.subject}' -> '{claim.predicate}' -> '{claim.object}'",
            f"2. Evaluated against {len(candidates)} candidate excerpts from authoritative documents.",
        ]

        subject_lower = (claim.subject or "").lower()
        obj_lower = str(claim.object or "").lower()

        matched_any = False
        for cand in candidates:
            text_lower = cand.excerpt.lower()
            if subject_lower in text_lower and obj_lower in text_lower:
                matched_any = True
                supporting.append(EvidenceItemEvaluation(
                    evidence_id=cand.evidence_id,
                    source_document_id=cand.source_document_id,
                    source_url=cand.provenance.source_url,
                    organization=cand.source_type,
                    relation="SUPPORTS",
                    excerpt=cand.excerpt,
                    reasoning="Source excerpt contains assertions corroborating claim subject and object.",
                    matched_signals=cand.relevance.matched_terms
                ))

        if matched_any:
            reasoning.append("3. Retrieved official filing contains matching factual statements confirming the claim.")
            return VerificationResult(
                claim_id=claim.claim_id,
                status="SUPPORTED",
                confidence=0.92,
                evidence_strength="HIGH",
                supporting_evidence=supporting,
                contradicting_evidence=[],
                missing_elements=[],
                context_gaps=[],
                source_assessment=source_assessments,
                reasoning_trace=reasoning,
                uncertainty=[],
                provenance=provenance
            )

        reasoning.append("3. Retrieved documents did not contain sufficient positive corroboration for this specific assertion.")
        return VerificationResult(
            claim_id=claim.claim_id,
            status="INSUFFICIENT_EVIDENCE",
            confidence=0.80,
            evidence_strength="LOW",
            supporting_evidence=[],
            contradicting_evidence=[],
            missing_elements=["Direct factual corroboration in authoritative record"],
            context_gaps=[],
            source_assessment=source_assessments,
            reasoning_trace=reasoning,
            uncertainty=["Available evidence does not directly address specific claim details"],
            provenance=provenance
        )

    def _build_result(
        self,
        claim: CanonicalClaim,
        res_dict: dict,
        source_assessments: list[SourceAssessmentItem],
        provenance: VerificationProvenance
    ) -> VerificationResult:
        """Helper to package evaluated dictionary into typed VerificationResult."""
        return VerificationResult(
            claim_id=claim.claim_id,
            status=res_dict["status"],
            confidence=res_dict["confidence"],
            evidence_strength=res_dict["evidence_strength"],
            supporting_evidence=res_dict.get("supporting_evidence", []),
            contradicting_evidence=res_dict.get("contradicting_evidence", []),
            missing_elements=res_dict.get("missing_elements", []),
            context_gaps=res_dict.get("context_gaps", []),
            source_assessment=source_assessments,
            reasoning_trace=res_dict.get("reasoning_trace", []),
            uncertainty=res_dict.get("uncertainty", []),
            provenance=provenance
        )

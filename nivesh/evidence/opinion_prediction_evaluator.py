"""Prediction, Opinion, and Subjective Claim Evaluator for Engine 5.

Handles non-verifiable or future-oriented assertions:
- Predictions: Future market performance cannot be established as a present fact
- Evaluative claims: Subjective opinions ("best", "safest", "undervalued") lack an objective verifiable threshold
- Avoids projecting investment advice or generating target price predictions.
"""

from typing import Optional
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument
from nivesh.schemas.evidence import (
    EvidenceItemEvaluation,
    ClaimVerificationStatus,
)


class OpinionPredictionEvaluator:
    """Evaluates forward-looking predictions and subjective opinions."""

    PREDICTION_TERMS = ("will reach", "will double", "will surge", "will hit", "target price", "next year", "six months", "future return")
    OPINION_TERMS = ("best investment", "safest investment", "undervalued", "overvalued", "great opportunity", "top pick", "superior choice")

    @classmethod
    def evaluate_claim(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate],
        documents: list[SourceDocument],
    ) -> Optional[dict]:
        """Evaluates prediction or opinion assertions."""
        modality = claim.modality.type if claim.modality else "assertion"
        claim_type = (claim.claim_type or "").upper()
        predicate = (claim.predicate or "").upper()
        claim_text = (claim.text.original if claim.text else "").lower()

        # 1. FORWARD-LOOKING PREDICTIONS
        is_prediction = (
            modality == "prediction"
            or claim_type == "PREDICTION"
            or predicate in ("REACH_PRICE", "PRICE_TARGET", "FUTURE_RETURN")
            or any(pt in claim_text for pt in cls.PREDICTION_TERMS)
            or (claim.temporal_context and claim.temporal_context.type == "future")
        )

        if is_prediction:
            reasoning_trace = [
                f"1. Claim identified as a forward-looking prediction: '{claim.text.original if claim.text else claim.predicate}'",
                "2. Forward-looking market price or return predictions cannot be established as present factual truths.",
                "3. Historical financial disclosures provide retrospective context but cannot verify future price outcomes.",
                "4. Result: INSUFFICIENT_EVIDENCE.",
            ]
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "confidence": 0.95,
                "evidence_strength": "LOW" if candidates else "NONE",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "missing_elements": ["Empirical verification of future market outcome (unverifiable in advance)"],
                "context_gaps": [],
                "reasoning_trace": reasoning_trace,
                "uncertainty": ["Future market performance is inherently unpredictable and cannot be proven by past data"],
            }

        # 2. SUBJECTIVE OPINIONS / EVALUATIVE CLAIMS
        is_opinion = (
            modality == "opinion"
            or claim_type == "OPINION"
            or predicate == "VALUATION_STATUS"
            or any(ot in claim_text for ot in cls.OPINION_TERMS)
        )

        if is_opinion:
            reasoning_trace = [
                f"1. Claim identified as an evaluative opinion: '{claim.text.original if claim.text else claim.predicate}'",
                "2. The statement expresses a subjective judgment rather than an objectively verifiable factual proposition.",
                "3. No statutory or empirical threshold exists to establish subjective terms such as 'best', 'safest', or ungrounded 'undervalued'.",
                "4. Result: NOT_VERIFIABLE.",
            ]
            return {
                "status": "NOT_VERIFIABLE",
                "confidence": 0.95,
                "evidence_strength": "NONE",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "missing_elements": ["Objective, verifiable factual criteria"],
                "context_gaps": [],
                "reasoning_trace": reasoning_trace,
                "uncertainty": ["Evaluative claims depend on individual investor risk tolerance and subjective methodology"],
            }

        return None

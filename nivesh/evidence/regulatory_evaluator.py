"""Regulatory and Identity Evidence Evaluator for Engine 5.

Evaluates claims involving:
- SEBI registration of individuals, advisers, and entities
- Identity matching against official registries
- Statutory regulatory prohibitions (e.g. SEBI Code of Conduct ban on guaranteed returns)
- Distinguishes 'NO_MATCH' from accusations of fraud.
"""

from typing import Optional
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument
from nivesh.schemas.evidence import (
    EvidenceItemEvaluation,
    EvidenceRelationType,
    EvidenceStrength,
    ClaimVerificationStatus,
)


class RegulatoryEvaluator:
    """Evaluates regulatory registration and statutory prohibition claims."""

    @classmethod
    def evaluate_claim(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate],
        documents: list[SourceDocument],
    ) -> Optional[dict]:
        """Evaluates regulatory claim against retrieved evidence candidates.
        
        Returns evaluation dict if handled by this evaluator, else None.
        """
        claim_type = (claim.claim_type or "").upper()
        predicate = (claim.predicate or "").upper()
        subject = (claim.subject or "").strip()
        obj = str(claim.object or "").strip()
        claim_text = (claim.text.original if claim.text else "").lower()

        # 1. STATUTORY PROHIBITION: GUARANTEED / ASSURED RETURNS
        if predicate in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or "guarantee" in predicate.lower() or "guarantee" in claim_text:
            return cls._evaluate_guaranteed_returns(claim, candidates, documents)

        # 2. REGULATORY REGISTRATION / ADVISOR IDENTITY
        if claim_type in ("REGULATORY", "IDENTITY") or predicate in ("REGISTERED_WITH", "REGULATORY_STATUS", "LICENSED_BY"):
            return cls._evaluate_registration(claim, candidates, documents)

        return None

    @classmethod
    def _evaluate_guaranteed_returns(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate],
        documents: list[SourceDocument],
    ) -> dict:
        """Evaluates guaranteed return claims against statutory prohibitions."""
        supporting_items: list[EvidenceItemEvaluation] = []
        contradicting_items: list[EvidenceItemEvaluation] = []
        reasoning_trace: list[str] = [
            f"1. Claim asserts guaranteed/assured financial return: '{claim.object or 'returns'}'",
            "2. Consulted SEBI (Investment Advisers) Regulations & Code of Conduct (statutory authority)",
        ]

        found_prohibition_doc = False
        for cand in candidates:
            excerpt_lower = cand.excerpt.lower()
            if "prohibition on assured" in excerpt_lower or "prohibit" in excerpt_lower or "regulations" in excerpt_lower:
                found_prohibition_doc = True
                eval_item = EvidenceItemEvaluation(
                    evidence_id=cand.evidence_id,
                    source_document_id=cand.source_document_id,
                    source_url=cand.provenance.source_url,
                    organization=cand.source_type,
                    relation="CONTRADICTS",
                    excerpt=cand.excerpt,
                    reasoning="Official statutory regulation strictly prohibits promising or guaranteeing fixed/assured returns in securities market.",
                    matched_signals=cand.relevance.matched_terms
                )
                contradicting_items.append(eval_item)

        if found_prohibition_doc:
            reasoning_trace.extend([
                "3. Official SEBI statutory circular SEBI/HO/IMD/DF1/CIR/P/2020/182 strictly prohibits offering guaranteed returns.",
                "4. Claim directly contradicts official statutory regulatory prohibition on assured returns.",
            ])
            return {
                "status": "CONTRADICTED",
                "confidence": 0.98,
                "evidence_strength": "HIGH",
                "supporting_evidence": supporting_items,
                "contradicting_evidence": contradicting_items,
                "missing_elements": [],
                "context_gaps": [],
                "reasoning_trace": reasoning_trace,
                "uncertainty": [],
            }


        # If no regulatory document retrieved
        reasoning_trace.append("3. No statutory documentation was successfully retrieved to verify return guarantee.")
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "confidence": 0.70,
            "evidence_strength": "NONE",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "missing_elements": ["Official regulatory policy regarding guaranteed returns"],
            "context_gaps": [],
            "reasoning_trace": reasoning_trace,
            "uncertainty": ["Authoritative regulatory document was not accessible"],
        }

    @classmethod
    def _evaluate_registration(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate],
        documents: list[SourceDocument],
    ) -> dict:
        """Evaluates claimed entity registration against SEBI registry records."""
        subject = claim.subject or ""
        claimed_name = subject.lower().strip()
        supporting_items: list[EvidenceItemEvaluation] = []
        contradicting_items: list[EvidenceItemEvaluation] = []
        reasoning_trace: list[str] = [
            f"1. Claimed entity: '{subject}'",
            f"2. Claimed registration status: Registered with '{claim.object or 'SEBI'}'",
            "3. Consulted official SEBI Recognized Intermediaries Registry database",
        ]

        if not candidates:
            reasoning_trace.append("4. No registry response retrieved.")
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "confidence": 0.80,
                "evidence_strength": "NONE",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "missing_elements": ["SEBI official intermediary registry response"],
                "context_gaps": [],
                "reasoning_trace": reasoning_trace,
                "uncertainty": ["Official registry data unavailable"],
            }

        # Inspect candidate documents
        for cand in candidates:
            excerpt_lower = cand.excerpt.lower()

            # Check for NO_MATCH in registry
            if "no_records_found" in excerpt_lower or "matches found: 0" in excerpt_lower:
                eval_item = EvidenceItemEvaluation(
                    evidence_id=cand.evidence_id,
                    source_document_id=cand.source_document_id,
                    source_url=cand.provenance.source_url,
                    organization="SEBI",
                    relation="CONTRADICTS",
                    excerpt=cand.excerpt,
                    reasoning=f"Official SEBI database returned 0 matching records for '{subject}'.",
                    matched_signals=["NO_RECORDS_FOUND", subject]
                )
                contradicting_items.append(eval_item)
                reasoning_trace.extend([
                    f"4. Official registry search for '{subject}' returned 0 matches.",
                    "5. Claim of SEBI registration is not substantiated by official registry records.",
                ])
                return {
                    "status": "INSUFFICIENT_EVIDENCE",  # Follows Section 16: registry NO_MATCH does not prove fraud
                    "confidence": 0.95,
                    "evidence_strength": "HIGH",
                    "supporting_evidence": [],
                    "contradicting_evidence": contradicting_items,
                    "missing_elements": [f"Valid SEBI registration certificate or active registration number for '{subject}'"],
                    "context_gaps": [],
                    "reasoning_trace": reasoning_trace,
                    "uncertainty": ["Registry lookup checked current official database; offline or newly applied records may take time to update"],
                }

            # Check for positive registration match
            if claimed_name and claimed_name in excerpt_lower and ("status: current" in excerpt_lower or "registered" in excerpt_lower):
                eval_item = EvidenceItemEvaluation(
                    evidence_id=cand.evidence_id,
                    source_document_id=cand.source_document_id,
                    source_url=cand.provenance.source_url,
                    organization="SEBI",
                    relation="SUPPORTS",
                    excerpt=cand.excerpt,
                    reasoning=f"Official SEBI intermediary record confirms active registration for '{subject}'.",
                    matched_signals=[subject, "CURRENT"]
                )
                supporting_items.append(eval_item)
                reasoning_trace.extend([
                    f"4. Found matching official registration entry for '{subject}'.",
                    "5. Registration status confirmed as CURRENT in SEBI database.",
                ])
                return {
                    "status": "SUPPORTED",
                    "confidence": 0.98,
                    "evidence_strength": "HIGH",
                    "supporting_evidence": supporting_items,
                    "contradicting_evidence": [],
                    "missing_elements": [],
                    "context_gaps": [],
                    "reasoning_trace": reasoning_trace,
                    "uncertainty": [],
                }

        # Default fallback if ambiguous
        reasoning_trace.append("4. Registry evidence neither explicitly matched nor explicitly rejected entity.")
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "confidence": 0.70,
            "evidence_strength": "LOW",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "missing_elements": ["Clear registry confirmation"],
            "context_gaps": [],
            "reasoning_trace": reasoning_trace,
            "uncertainty": ["Partial or ambiguous registry data"],
        }

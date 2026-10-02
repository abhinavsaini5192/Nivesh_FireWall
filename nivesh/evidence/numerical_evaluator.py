"""Numerical and Arithmetic Evidence Evaluator for Engine 5.

Performs deterministic numerical calculations, ratio verifications, tolerance/rounding
handling, debt comparisons, and context gap detections.
"""

import re
from typing import Optional
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument
from nivesh.schemas.evidence import (
    EvidenceItemEvaluation,
    EvidenceRelationType,
    EvidenceStrength,
    ClaimVerificationStatus,
)


class NumericalEvaluator:
    """Evaluates quantitative financial assertions against numerical evidence."""

    @classmethod
    def evaluate_claim(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate],
        documents: list[SourceDocument],
    ) -> Optional[dict]:
        """Evaluates numerical claims if applicable."""
        predicate = (claim.predicate or "").upper()
        obj_str = str(claim.object or "").strip().lower()
        claim_text = (claim.text.original if claim.text else "").lower()

        # 1. DEBT STATUS (e.g. "debt free", "zero debt")
        if predicate == "HAS_DEBT" or "debt" in claim_text or "debt free" in claim_text:
            return cls._evaluate_debt(claim, candidates)

        # 2. CORPORATE ACTION RATIO (e.g. 1:1, 2:1 bonus or split)
        if predicate in ("ANNOUNCED_BONUS", "STOCK_SPLIT") or re.search(r"\b\d+:\d+\b", obj_str):
            return cls._evaluate_ratio(claim, candidates)

        # 3. PERCENTAGE / GROWTH CLAIMS (e.g. "Revenue increased 40%", "Profit increased 200%")
        if "%" in obj_str or "increased" in claim_text or "growth" in predicate.lower() or "profit" in claim_text or "revenue" in claim_text:
            return cls._evaluate_growth_and_financials(claim, candidates)

        return None

    @classmethod
    def _evaluate_debt(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate]
    ) -> Optional[dict]:
        """Evaluates 'debt free' or zero-debt assertions."""
        claimed_debt_zero = any(z in str(claim.object).lower() for z in ("0", "zero", "none", "debt free", "no debt")) or "debt free" in (claim.text.original.lower() if claim.text else "")
        if not claimed_debt_zero:
            return None

        reasoning_trace = [
            f"1. Claim asserts: '{claim.subject}' carries zero debt / is debt-free",
            "2. Consulted official financial disclosures & balance sheet filings",
        ]

        for cand in candidates:
            text_lower = cand.excerpt.lower()

            # Case A: Source shows debt-free
            if "zero long-term debt" in text_lower or "debt-free" in text_lower or "zero debt" in text_lower:
                reasoning_trace.extend([
                    "3. Official disclosure confirms: 'Zero Long-Term Debt (Debt-Free Company)'",
                    "4. Assertion is directly supported by official financial filing."
                ])
                return {
                    "status": "SUPPORTED",
                    "confidence": 0.95,
                    "evidence_strength": "HIGH",
                    "supporting_evidence": [
                        EvidenceItemEvaluation(
                            evidence_id=cand.evidence_id,
                            source_document_id=cand.source_document_id,
                            source_url=cand.provenance.source_url,
                            organization=cand.source_type,
                            relation="SUPPORTS",
                            excerpt=cand.excerpt,
                            reasoning="Official exchange filing explicitly confirms company carries zero long-term debt.",
                            matched_signals=["debt-free"]
                        )
                    ],
                    "contradicting_evidence": [],
                    "missing_elements": [],
                    "context_gaps": [],
                    "reasoning_trace": reasoning_trace,
                    "uncertainty": [],
                }

            # Case B: Source shows outstanding borrowings (Contradiction)
            borrowings_match = re.search(r"(?:borrowings|debt|loans)\s*(?:as of.*?)?:\s*(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(crore|cr|lakh)?", text_lower)
            if borrowings_match or "outstanding borrowings" in text_lower:
                amount_str = borrowings_match.group(0) if borrowings_match else "reported borrowings"
                reasoning_trace.extend([
                    f"3. Official disclosure reports outstanding debt/borrowings: '{amount_str}'",
                    "4. Claim assertion: debt = 0 | Source assertion: debt exists and is greater than 0",
                    "5. Conflict detected: claim is contradicted by official filing.",
                ])
                return {
                    "status": "CONTRADICTED",
                    "confidence": 0.96,
                    "evidence_strength": "HIGH",
                    "supporting_evidence": [],
                    "contradicting_evidence": [
                        EvidenceItemEvaluation(
                            evidence_id=cand.evidence_id,
                            source_document_id=cand.source_document_id,
                            source_url=cand.provenance.source_url,
                            organization=cand.source_type,
                            relation="CONTRADICTS",
                            excerpt=cand.excerpt,
                            reasoning=f"Company reports {amount_str}, directly contradicting zero-debt claim.",
                            matched_signals=["borrowings"]
                        )
                    ],
                    "missing_elements": [],
                    "context_gaps": [],
                    "reasoning_trace": reasoning_trace,
                    "uncertainty": [],
                }

        return None

    @classmethod
    def _evaluate_ratio(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate]
    ) -> Optional[dict]:
        """Evaluates bonus / stock split ratios (e.g. 1:1, 2:1)."""
        ratio_match = re.search(r"(\d+:\d+)", str(claim.object) + " " + (claim.text.original if claim.text else ""))
        if not ratio_match:
            return None

        claimed_ratio = ratio_match.group(1)
        reasoning_trace = [
            f"1. Claim asserts corporate action with ratio: '{claimed_ratio}' for '{claim.subject}'",
            "2. Consulted official stock exchange corporate action filings",
        ]

        for cand in candidates:
            text = cand.excerpt
            if claimed_ratio in text and ("bonus" in text.lower() or "split" in text.lower() or "corporate action" in text.lower()):
                # Check for genuine date in claim (e.g. "1 June", "15-06-2026", etc.)
                months_pattern = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                date_pattern = rf"\b(?:\d{{1,2}}(?:st|nd|rd|th)?\s+{months_pattern}(?:\s+\d{{2,4}})?|{months_pattern}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:\s*,\s*\d{{2,4}})?|\d{{1,2}}[-/]\d{{1,2}}[-/]\d{{2,4}})\b"
                date_in_claim = re.search(date_pattern, claim.text.original if claim.text else "", re.IGNORECASE)
                date_established = False
                missing_elements = []

                if date_in_claim:
                    claimed_date = date_in_claim.group(0)
                    if claimed_date.lower() in text.lower():
                        date_established = True
                    else:
                        missing_elements.append(f"Specified announcement date '{claimed_date}'")

                if date_in_claim and not date_established:
                    # Partial support: ratio is confirmed, but date was not established!
                    reasoning_trace.extend([
                        f"3. Official filing confirms {claimed_ratio} bonus issue recommendation.",
                        f"4. Date '{date_in_claim.group(0)}' claimed in content was not confirmed in retrieved excerpt.",
                        "5. Result: PARTIALLY_SUPPORTED (ratio established, specific date not established).",
                    ])
                    return {
                        "status": "PARTIALLY_SUPPORTED",
                        "confidence": 0.94,
                        "evidence_strength": "HIGH",
                        "supporting_evidence": [
                            EvidenceItemEvaluation(
                                evidence_id=cand.evidence_id,
                                source_document_id=cand.source_document_id,
                                source_url=cand.provenance.source_url,
                                organization=cand.source_type,
                                relation="PARTIALLY_SUPPORTS",
                                excerpt=cand.excerpt,
                                reasoning=f"Exchange filing confirms {claimed_ratio} bonus issue, but does not establish claimed date.",
                                matched_signals=[claimed_ratio]
                            )
                        ],
                        "contradicting_evidence": [],
                        "missing_elements": missing_elements,
                        "context_gaps": [],
                        "reasoning_trace": reasoning_trace,
                        "uncertainty": ["Announcement date requires additional date-specific filing lookup"],
                    }

                # Full support
                reasoning_trace.extend([
                    f"3. Official filing confirms {claimed_ratio} bonus issue recommendation.",
                    "4. Claimed corporate action ratio is fully supported by exchange disclosure.",
                ])
                return {
                    "status": "SUPPORTED",
                    "confidence": 0.98,
                    "evidence_strength": "HIGH",
                    "supporting_evidence": [
                        EvidenceItemEvaluation(
                            evidence_id=cand.evidence_id,
                            source_document_id=cand.source_document_id,
                            source_url=cand.provenance.source_url,
                            organization=cand.source_type,
                            relation="SUPPORTS",
                            excerpt=cand.excerpt,
                            reasoning=f"Exchange filing explicitly verifies {claimed_ratio} bonus recommendation.",
                            matched_signals=[claimed_ratio]
                        )
                    ],
                    "contradicting_evidence": [],
                    "missing_elements": [],
                    "context_gaps": [],
                    "reasoning_trace": reasoning_trace,
                    "uncertainty": [],
                }

        return None

    @classmethod
    def _evaluate_growth_and_financials(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate]
    ) -> Optional[dict]:
        """Evaluates percentage growth, profit, and revenue figures."""
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(claim.object) + " " + (claim.text.original if claim.text else ""))
        if not pct_match:
            return None

        claimed_pct = float(pct_match.group(1))
        reasoning_trace = [
            f"1. Claim asserts quantitative change: '{claimed_pct}%' for '{claim.subject}'",
            "2. Inspecting financial filing figures to perform arithmetic verification",
        ]

        for cand in candidates:
            text = cand.excerpt
            # Look for financial figures in source: e.g. FY2025 = 100, FY2026 = 140 or similar
            # Pattern: 2 financial numbers
            numbers = [float(n) for n in re.findall(r"\b(\d+(?:\.\d+)?)\b", text)]
            # Also check if explicit percent is written in source
            source_pcts = [float(p) for p in re.findall(r"(\d+(?:\.\d+)?)\s*%", text)]

            # Check if source directly quotes the percentage (or within 0.5% tolerance)
            for sp in source_pcts:
                if abs(sp - claimed_pct) <= 0.5:
                    reasoning_trace.extend([
                        f"3. Source confirms percentage: '{sp}%' (within controlled 0.5% tolerance of claimed {claimed_pct}%).",
                        "4. Claimed figure is verified by authoritative filing.",
                    ])
                    # Check context gaps
                    context_gaps = []
                    if "reporting period" not in (claim.text.original.lower() if claim.text else "") and not (claim.temporal_context and claim.temporal_context.date):
                        context_gaps.append("Reporting period omitted from original content")

                    return {
                        "status": "SUPPORTED",
                        "confidence": 0.95,
                        "evidence_strength": "HIGH",
                        "supporting_evidence": [
                            EvidenceItemEvaluation(
                                evidence_id=cand.evidence_id,
                                source_document_id=cand.source_document_id,
                                source_url=cand.provenance.source_url,
                                organization=cand.source_type,
                                relation="SUPPORTS",
                                excerpt=cand.excerpt,
                                reasoning=f"Financial filing confirms {sp}% matching claimed {claimed_pct}%.",
                                matched_signals=[f"{sp}%"]
                            )
                        ],
                        "contradicting_evidence": [],
                        "missing_elements": [],
                        "context_gaps": context_gaps,
                        "reasoning_trace": reasoning_trace,
                        "uncertainty": [],
                    }

            # Arithmetic comparison: check if base and current values are found
            # e.g., FY2025 = 100, FY2026 = 140 -> (140 - 100) / 100 = 40%
            pairs = re.findall(r"(?:FY\s*\d+|\d{4})[^\n:=]*?[:=]\s*(?:₹|Rs\.?)?\s*(\d+(?:\.\d+)?)\s*(?:Cr|crore)?.*?(?:FY\s*\d+|\d{4})[^\n:=]*?[:=]\s*(?:₹|Rs\.?)?\s*(\d+(?:\.\d+)?)\s*(?:Cr|crore)?", text, re.IGNORECASE)
            for p in pairs:
                v1, v2 = float(p[0]), float(p[1])
                if v1 > 0:
                    calculated_change = round(((v2 - v1) / v1) * 100, 2)
                    reasoning_trace.extend([
                        f"3. Extracted baseline: {v1}, current: {v2}",
                        f"4. Calculation: ({v2} - {v1}) / {v1} * 100 = {calculated_change}%",
                    ])

                    # Within rounding/tolerance
                    if abs(calculated_change - claimed_pct) <= 0.5:
                        reasoning_trace.append(f"5. Calculated change ({calculated_change}%) matches claimed change ({claimed_pct}%).")
                        context_gaps = []
                        if "profit" in text.lower() or "revenue" in text.lower():
                            if not re.search(r"\b(FY\s*\d{2,4}|Q[1-4])\b", claim.text.original if claim.text else ""):
                                context_gaps.append("Reporting period omitted from original content")
                            if not re.search(r"₹\s*\d+", claim.text.original if claim.text else ""):
                                context_gaps.append("Absolute baseline financial figures omitted")

                        return {
                            "status": "SUPPORTED",
                            "confidence": 0.96,
                            "evidence_strength": "HIGH",
                            "supporting_evidence": [
                                EvidenceItemEvaluation(
                                    evidence_id=cand.evidence_id,
                                    source_document_id=cand.source_document_id,
                                    source_url=cand.provenance.source_url,
                                    organization=cand.source_type,
                                    relation="SUPPORTS",
                                    excerpt=cand.excerpt,
                                    reasoning=f"Arithmetic check: baseline {v1} to {v2} confirms {calculated_change}%.",
                                    matched_signals=[f"{calculated_change}%"]
                                )
                            ],
                            "contradicting_evidence": [],
                            "missing_elements": [],
                            "context_gaps": context_gaps,
                            "reasoning_trace": reasoning_trace,
                            "uncertainty": [],
                        }
                    else:
                        # Mismatch -> CONTRADICTION
                        reasoning_trace.extend([
                            f"5. Conflict detected: Claim asserts +{claimed_pct}%, but financial filing figures calculate to +{calculated_change}%.",
                            "6. Result: CONTRADICTED by arithmetic verification of filing figures."
                        ])
                        return {
                            "status": "CONTRADICTED",
                            "confidence": 0.96,
                            "evidence_strength": "HIGH",
                            "supporting_evidence": [],
                            "contradicting_evidence": [
                                EvidenceItemEvaluation(
                                    evidence_id=cand.evidence_id,
                                    source_document_id=cand.source_document_id,
                                    source_url=cand.provenance.source_url,
                                    organization=cand.source_type,
                                    relation="CONTRADICTS",
                                    excerpt=cand.excerpt,
                                    reasoning=f"Claim asserts +{claimed_pct}%, but source figures ({v1} to {v2}) yield +{calculated_change}%.",
                                    matched_signals=[f"{calculated_change}%"]
                                )
                            ],
                            "missing_elements": [],
                            "context_gaps": [],
                            "reasoning_trace": reasoning_trace,
                            "uncertainty": [],
                        }

        return None

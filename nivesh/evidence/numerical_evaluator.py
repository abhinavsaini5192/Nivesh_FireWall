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

        # 0. POLICY RATES & MACRO BENCHMARKS (e.g. "Repo Rate is 5.25%", "CRR is 3%")
        if (
            predicate in ("POLICY_RATE", "REPO_RATE", "POLICY_REPO_RATE", "CRR", "SLR", "BANK_RATE", "REVERSE_REPO_RATE", "INTEREST_RATE")
            or any(r in claim_text for r in ("repo rate", "reverse repo", "bank rate", "policy rate", "crr", "slr"))
            or ("rbi" in claim_text and "%" in claim_text)
        ):
            rate_res = cls._evaluate_policy_and_benchmark_rates(claim, candidates)
            if rate_res:
                return rate_res

        # 1. DEBT STATUS (e.g. "debt free", "zero debt")
        if predicate == "HAS_DEBT" or "debt" in claim_text or "debt free" in claim_text:
            return cls._evaluate_debt(claim, candidates)

        # 2. CORPORATE ACTION RATIO (e.g. 1:1, 2:1 bonus or split)
        if predicate in ("ANNOUNCED_BONUS", "STOCK_SPLIT") or re.search(r"\b\d+:\d+\b", obj_str):
            return cls._evaluate_ratio(claim, candidates)

        # 2b. DIVIDEND ANNOUNCEMENTS (e.g. ₹10 per share dividend)
        if predicate in ("DIVIDEND_ANNOUNCED", "INTERIM_DIVIDEND") or "dividend" in claim_text or "dividend" in predicate.lower():
            div_res = cls._evaluate_dividend(claim, candidates)
            if div_res:
                return div_res

        # 3. PERCENTAGE / GROWTH CLAIMS (e.g. "Revenue increased 40%", "Profit increased 200%")
        if "%" in obj_str or "increased" in claim_text or "growth" in predicate.lower() or "profit" in claim_text or "revenue" in claim_text:
            return cls._evaluate_growth_and_financials(claim, candidates)

        return None

    @classmethod
    def _evaluate_policy_and_benchmark_rates(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate]
    ) -> Optional[dict]:
        """Evaluates policy rates and benchmark assertions against authoritative regulatory disclosures."""
        obj_str = str(claim.object or "").strip().lower()
        claim_text = (claim.text.original if claim.text else "").lower()
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", obj_str + " " + claim_text)
        if not pct_match:
            return None

        claimed_rate = float(pct_match.group(1))

        # Determine which rate metric is asserted
        metric_patterns = [
            ("Policy Repo Rate", [r"repo\s*rate", r"policy\s*rate", r"policy\s*repo", r"\brepo\b"]),
            ("Standing Deposit Facility Rate", [r"\bsdf\b", r"standing\s*deposit\s*facility"]),
            ("Marginal Standing Facility Rate", [r"\bmsf\b", r"marginal\s*standing\s*facility"]),
            ("Bank Rate", [r"bank\s*rate"]),
            ("Fixed Reverse Repo Rate", [r"reverse\s*repo"]),
            ("Cash Reserve Ratio", [r"\bcrr\b", r"cash\s*reserve\s*ratio"]),
            ("Statutory Liquidity Ratio", [r"\bslr\b", r"statutory\s*liquidity\s*ratio"]),
        ]

        target_metric = None
        for metric_name, patterns in metric_patterns:
            if any(re.search(pat, claim_text, re.IGNORECASE) for pat in patterns):
                target_metric = metric_name
                break

        # If claim didn't specify a recognized benchmark rate (e.g. "car loan", "personal loan"), return None
        if not target_metric:
            return None

        reasoning_trace = [
            f"1. Claim asserts official RBI rate: '{target_metric}' = {claimed_rate}%",
            "2. Consulted authoritative Reserve Bank of India benchmark policy rates",
        ]

        for cand in candidates:
            text = cand.excerpt
            # Search for target metric in text, e.g. "Policy Repo Rate: 5.25%" or "Policy Repo Rate ... 5.25%"
            metric_search = re.search(
                rf"{re.escape(target_metric)}[^\d%:\n]*[:\s]+(\d+(?:\.\d+)?)\s*%",
                text,
                re.IGNORECASE
            )
            # Fallback for shorter variants e.g. "Repo Rate: 6.50%" or "CRR: 3.00%"
            if not metric_search:
                short_metric = target_metric.replace("Rate", "").replace("Ratio", "").replace("Policy", "").strip()
                if short_metric:
                    metric_search = re.search(
                        rf"\b{re.escape(short_metric)}\b[^\d%:\n]*[:\s]+(\d+(?:\.\d+)?)\s*%",
                        text,
                        re.IGNORECASE
                    )

            if metric_search:
                actual_rate = float(metric_search.group(1))
                reasoning_trace.append(f"3. Authoritative RBI publication establishes official {target_metric} as {actual_rate}%.")

                # Compare with tight numerical tolerance (0.05%)
                if abs(actual_rate - claimed_rate) <= 0.05:
                    reasoning_trace.extend([
                        f"4. Claimed rate ({claimed_rate}%) matches authoritative RBI rate ({actual_rate}%).",
                        "5. Result: SUPPORTED by authoritative regulatory publication.",
                    ])
                    return {
                        "status": "SUPPORTED",
                        "confidence": 0.98,
                        "evidence_strength": "HIGH",
                        "supporting_evidence": [
                            EvidenceItemEvaluation(
                                evidence_id=cand.evidence_id,
                                source_document_id=cand.source_document_id,
                                source_url=cand.provenance.source_url if cand.provenance else "",
                                organization=cand.source_type,
                                relation="SUPPORTS",
                                excerpt=cand.excerpt,
                                reasoning=f"Official RBI disclosure verifies {target_metric} is {actual_rate}%, matching claimed {claimed_rate}%.",
                                matched_signals=[f"{actual_rate}%", target_metric]
                            )
                        ],
                        "contradicting_evidence": [],
                        "missing_elements": [],
                        "context_gaps": [],
                        "reasoning_trace": reasoning_trace,
                        "uncertainty": [],
                    }
                else:
                    reasoning_trace.extend([
                        f"4. Conflict detected: Claim asserts {target_metric} is {claimed_rate}%, but authoritative RBI publication states {actual_rate}%.",
                        "5. Result: CONTRADICTED by authoritative regulatory publication.",
                    ])
                    return {
                        "status": "CONTRADICTED",
                        "confidence": 0.98,
                        "evidence_strength": "HIGH",
                        "supporting_evidence": [],
                        "contradicting_evidence": [
                            EvidenceItemEvaluation(
                                evidence_id=cand.evidence_id,
                                source_document_id=cand.source_document_id,
                                source_url=cand.provenance.source_url if cand.provenance else "",
                                organization=cand.source_type,
                                relation="CONTRADICTS",
                                excerpt=cand.excerpt,
                                reasoning=f"Authoritative RBI publication establishes {target_metric} as {actual_rate}%, contradicting claimed {claimed_rate}%.",
                                matched_signals=[f"{actual_rate}%", target_metric]
                            )
                        ],
                        "missing_elements": [],
                        "context_gaps": [],
                        "reasoning_trace": reasoning_trace,
                        "uncertainty": [],
                    }

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
                }

            # Check for conflicting ratio in official corporate action filing
            source_ratio_match = re.search(r"(?:bonus ratio|ratio|split ratio)[\s:]*(\d+:\d+)", text, re.IGNORECASE)
            if not source_ratio_match:
                source_ratio_match = re.search(r"\b(\d+:\d+)\b\s*(?:bonus|split|shares|equity shares)", text, re.IGNORECASE)
            if source_ratio_match:
                found_ratio = source_ratio_match.group(1)
                if found_ratio != claimed_ratio:
                    reasoning_trace.extend([
                        f"3. Official corporate filing reports ratio: '{found_ratio}'",
                        f"4. Claim assertion '{claimed_ratio}' materially contradicts official exchange disclosure '{found_ratio}'",
                        "5. Conflict detected: claim is contradicted by official filing.",
                    ])
                    return {
                        "status": "CONTRADICTED",
                        "confidence": 0.97,
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
                                reasoning=f"Official corporate filing records {found_ratio}, contradicting claimed {claimed_ratio}.",
                                matched_signals=[claimed_ratio, found_ratio],
                            )
                        ],
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

    @classmethod
    def _evaluate_dividend(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate]
    ) -> Optional[dict]:
        """Evaluates dividend announcements and per-share payout figures."""
        obj_str = str(claim.object or "").strip()
        claim_text = (claim.text.original if claim.text else "").lower()
        if not ("dividend" in claim_text or "dividend" in (claim.predicate or "").lower()):
            return None

        # Look for rupee or numeric dividend in claim e.g. "₹10", "Rs 10", "10"
        amt_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:per\s*share|per\s*equity\s*share|dividend|\/-\b)", claim_text, re.IGNORECASE)
        if not amt_match:
            amt_match = re.search(r"\b(\d+(?:\.\d+)?)\b", obj_str)
        if not amt_match:
            return None

        claimed_amt = float(amt_match.group(1))
        reasoning_trace = [
            f"1. Claim asserts dividend announcement of ₹{claimed_amt} per share for '{claim.subject}'",
            "2. Consulted official stock exchange corporate announcements and board meeting outcomes",
        ]

        for cand in candidates:
            text = cand.excerpt
            if "dividend" in text.lower():
                # Extract amounts associated with dividend in excerpt (e.g. ₹10, Rs 10)
                source_amts = re.findall(r"(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
                if not source_amts:
                    source_amts = re.findall(r"\b(\d+(?:\.\d+)?)\s*(?:per\s*equity\s*share|per\s*share)", text, re.IGNORECASE)

                for sa in source_amts:
                    actual_amt = float(sa)
                    if abs(actual_amt - claimed_amt) < 0.01:
                        reasoning_trace.extend([
                            f"3. Official corporate disclosure verifies dividend of ₹{actual_amt} per equity share.",
                            "4. Claimed corporate payout is fully supported by exchange disclosure."
                        ])
                        return {
                            "status": "SUPPORTED",
                            "confidence": 0.98,
                            "evidence_strength": "HIGH",
                            "supporting_evidence": [
                                EvidenceItemEvaluation(
                                    evidence_id=cand.evidence_id,
                                    source_document_id=cand.source_document_id,
                                    source_url=cand.provenance.source_url if cand.provenance else "",
                                    organization=cand.source_type,
                                    relation="SUPPORTS",
                                    excerpt=cand.excerpt,
                                    reasoning=f"Exchange filing explicitly verifies dividend of ₹{actual_amt} per share.",
                                    matched_signals=[f"₹{actual_amt}", "dividend"]
                                )
                            ],
                            "contradicting_evidence": [],
                            "missing_elements": [],
                            "context_gaps": [],
                            "reasoning_trace": reasoning_trace,
                            "uncertainty": [],
                        }
                    else:
                        reasoning_trace.extend([
                            f"3. Official disclosure reports dividend of ₹{actual_amt} per share, but claim asserts ₹{claimed_amt}.",
                            "4. Conflict detected: dividend amount is contradicted by authoritative exchange filing."
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
                                    source_url=cand.provenance.source_url if cand.provenance else "",
                                    organization=cand.source_type,
                                    relation="CONTRADICTS",
                                    excerpt=cand.excerpt,
                                    reasoning=f"Official exchange filing verifies dividend of ₹{actual_amt} per share, contradicting claimed ₹{claimed_amt}.",
                                    matched_signals=[f"₹{actual_amt}", "dividend"]
                                )
                            ],
                            "missing_elements": [],
                            "context_gaps": [],
                            "reasoning_trace": reasoning_trace,
                            "uncertainty": [],
                        }

        return None

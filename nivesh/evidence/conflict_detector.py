"""Source Conflict Detector for Engine 5.

Detects genuine factual conflicts between multiple retrieved authoritative sources:
- Compares values across distinct sources
- Exposes conflicting figures and claims without taking sides
- Sets status = 'SOURCE_CONFLICT'.
"""

import re
from typing import Optional
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.sources import EvidenceCandidate, SourceDocument
from nivesh.schemas.evidence import (
    EvidenceItemEvaluation,
    EvidenceRelationType,
    ClaimVerificationStatus,
)


class ConflictDetector:
    """Detects material discrepancies between multiple source candidates."""

    @classmethod
    def detect_conflict(
        cls,
        claim: CanonicalClaim,
        candidates: list[EvidenceCandidate],
        documents: list[SourceDocument],
    ) -> Optional[dict]:
        """Checks if multiple retrieved sources present conflicting facts."""
        if len(documents) < 2 or len(candidates) < 2:
            return None

        # Compare extracted values across distinct sources
        doc_values: dict[str, list[str]] = {}
        for doc in documents:
            if doc.retrieval.status != "SUCCESS":
                continue

            # Look for ratios (e.g. 1:1, 10:1, 2:1)
            ratios = re.findall(r"\b(\d+:\d+)\b", doc.content)
            # Look for numerical or assertion values in document
            vals = re.findall(r"(?:₹|Rs\.?)?\s*(\d+(?:\.\d+)?)\s*(?:Cr|crore|%|lakh)?", doc.content, re.IGNORECASE)
            
            all_vals = []
            if ratios:
                all_vals.extend(ratios)
            if vals:
                all_vals.extend([v.strip() for v in vals if v.strip()])
            
            if all_vals:
                doc_values[doc.document_id] = all_vals

        # If two documents have conflicting primary numbers/ratios for the same topic
        if len(doc_values) >= 2:
            doc_ids = list(doc_values.keys())
            d1, d2 = doc_ids[0], doc_ids[1]
            vals1 = doc_values[d1]
            vals2 = doc_values[d2]
            doc_1_obj = next(d for d in documents if d.document_id == d1)
            doc_2_obj = next(d for d in documents if d.document_id == d2)

            is_conflict = False
            discrepancy_desc = ""

            # Check explicit conflict keywords
            if "conflict" in (doc_1_obj.content + doc_2_obj.content).lower():
                is_conflict = True
                discrepancy_desc = f"Explicit conflict indicated between {doc_1_obj.organization} and {doc_2_obj.organization}"
            # Check ratio conflict (e.g. 1:1 vs 2:1)
            elif vals1 and vals2:
                r1 = [v for v in vals1 if ":" in v]
                r2 = [v for v in vals2 if ":" in v]
                if r1 and r2 and r1[0] != r2[0]:
                    is_conflict = True
                    discrepancy_desc = f"Source {doc_1_obj.organization} ({d1}) reports ratio '{r1[0]}', while Source {doc_2_obj.organization} ({d2}) reports ratio '{r2[0]}'"
                elif vals1 and vals2 and set(vals1[:2]) != set(vals2[:2]):
                    # Check numerical values if same financial metric mentioned
                    v1_str = vals1[0]
                    v2_str = vals2[0]
                    if v1_str != v2_str:
                        shared_topics = ("profit", "bonus", "dividend", "revenue", "rate", "cr", "crore", "%")
                        combined = (doc_1_obj.content + " " + doc_2_obj.content).lower()
                        if any(t in combined for t in shared_topics):
                            is_conflict = True
                            discrepancy_desc = f"Source {doc_1_obj.organization} ({d1}) reports '{v1_str}', while Source {doc_2_obj.organization} ({d2}) reports '{v2_str}'"

            if is_conflict:
                reasoning_trace = [
                    f"1. Claim subject: '{claim.subject}', asserting: '{claim.object}'",
                    f"2. Multiple authoritative documents retrieved: {doc_1_obj.organization} ({d1}) and {doc_2_obj.organization} ({d2})",
                    f"3. Discrepancy detected: {discrepancy_desc or f'Source {d1} reports {vals1[0]} vs Source {d2} reports {vals2[0]}'}",
                    "4. Authoritative sources materially conflict on this assertion.",
                    "5. Result: SOURCE_CONFLICT (system exposes discrepancy without arbitrary resolution).",
                ]
                return {
                    "status": "SOURCE_CONFLICT",
                    "confidence": 0.90,
                    "evidence_strength": "MEDIUM",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                    "missing_elements": ["Harmonized or audited reconciliation between conflicting sources"],
                    "context_gaps": [],
                    "reasoning_trace": reasoning_trace,
                    "uncertainty": [f"Source {d1} and Source {d2} present divergent figures"],
                }

        return None

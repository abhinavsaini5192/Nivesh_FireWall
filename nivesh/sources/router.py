"""Source Router for Engine 4 (Source Intelligence Engine).

Analyzes structured claims and normalized content to determine:
- Required source taxonomy types
- Preferred primary source catalog IDs
- Fallback source catalog IDs
- Deterministic search queries based strictly on structured claim fields and entities
"""

import re
from typing import Optional
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.sources import SourcePlan, SourceQuery, SourceTypeTaxonomy
from nivesh.sources.catalog import SourceCatalog


class SourceRouter:
    """Routes CanonicalClaims to appropriate authoritative sources."""

    def __init__(self, catalog: Optional[SourceCatalog] = None):
        self.catalog = catalog or SourceCatalog()

    def route_claim(
        self,
        claim: CanonicalClaim,
        content: Optional[NormalizedContent] = None
    ) -> SourcePlan:
        """Determines the authoritative source plan and structured query for a claim."""
        claim_type = (claim.claim_type or "UNKNOWN").upper()
        predicate = (claim.predicate or "").upper()
        subject = claim.subject or ""
        obj = claim.object or ""
        temporal_type = claim.temporal_context.type if claim.temporal_context else "unknown"

        # Attempt to find registration numbers from Engine 1 structured signals
        reg_number = None
        if content and content.structured_signals and content.structured_signals.registration_numbers:
            for reg in content.structured_signals.registration_numbers:
                code_val = getattr(reg, "code", getattr(reg, "value", None))
                if code_val:
                    reg_number = code_val
                    break

        # Check if subject/object contains a registration number pattern
        if not reg_number:
            for text_val in (subject, obj, claim.text.original if claim.text else ""):
                if any(p in text_val.upper() for p in ("INA", "INZ", "IN-DP", "CIN", "U6", "L6")):
                    # Simple heuristic pattern
                    words = text_val.split()
                    for w in words:
                        clean_w = w.strip(".,;:()")
                        if clean_w.startswith(("INA", "INZ", "IN-DP")):
                            reg_number = clean_w
                            break

        # Extract dates or timeframes
        date_range = None
        if claim.temporal_context and claim.temporal_context.date:
            date_range = (claim.temporal_context.date, claim.temporal_context.date)
        elif content and content.structured_signals and content.structured_signals.dates:
            d = content.structured_signals.dates[0].raw
            date_range = (d, d)

        text_lower = (claim.text.original.lower() if claim.text and claim.text.original else "")

        # 1. RBI POLICY RATES, BENCHMARKS, OR STATUTORY NOTICES
        if (
            "rbi" in text_lower
            or "reserve bank" in text_lower
            or "repo rate" in text_lower
            or "policy rate" in text_lower
            or "mpc" in text_lower
            or "deposit taking" in text_lower
            or "money circulation" in text_lower
            or "nbfc" in text_lower
            or (subject and "reserve bank" in subject.lower())
            or (obj and "rbi" in str(obj).lower())
        ):
            keywords = ["rbi"]
            if any(k in text_lower for k in ("rate", "repo", "mpc", "interest", "crr", "slr")):
                keywords.extend(["repo", "rate", "mpc"])
            elif any(k in text_lower for k in ("deposit", "mlm", "scheme", "circulation")):
                keywords.extend(["deposit", "mlm", "guarantee"])
            elif "nbfc" in text_lower:
                keywords.extend(["nbfc", "registration"])
            elif any(k in text_lower for k in ("press release", "press", "release", "publication", "announcement", "appointed", "appointment", "bulletin", "statement")):
                keywords.extend(["press release", "publication"])
                if subject and subject.lower() not in ("rbi", "reserve bank", "reserve bank of india", "unspecified_offer"):
                    keywords.append(subject)
                if obj and str(obj).lower() not in ("rbi", "reserve bank", "reserve bank of india"):
                    keywords.append(str(obj))
            if obj and str(obj) not in keywords:
                keywords.append(str(obj))

            return SourcePlan(
                primary=["rbi_regulatory_publications"],
                fallback=["sebi_public_regulatory_pages"],
                required_source_types=["STATUTORY_DOCUMENT", "REGULATOR"],
                query=SourceQuery(
                    company_name=subject if subject and subject != "unspecified_offer" else None,
                    registration_number=reg_number,
                    keywords=keywords,
                    temporal_focus=temporal_type,
                    attributes={"authority": "RBI", "metric": predicate, "value": obj}
                )
            )

        # 2. REGULATORY / REGISTRATION / IDENTITY CLAIMS (e.g. SEBI Intermediaries)
        if claim_type in ("REGULATORY", "IDENTITY") or predicate in ("REGISTERED_WITH", "REGULATORY_STATUS", "LICENSED_BY"):
            query_name = subject if subject and subject != "unspecified_offer" else None
            keywords = ["registration", "intermediary", "advisor"]
            if obj and obj.upper() != "SEBI":
                keywords.append(str(obj))

            return SourcePlan(
                primary=["sebi_recognised_intermediaries"],
                fallback=["sebi_public_regulatory_pages", "government_official_sources"],
                required_source_types=["REGULATORY_REGISTRY", "REGULATOR"],
                query=SourceQuery(
                    name=query_name,
                    registration_number=reg_number,
                    keywords=keywords,
                    temporal_focus=temporal_type,
                    attributes={"regulator": obj or "SEBI"}
                )
            )

        # 3. GUARANTEED RETURN / PROHIBITED FINANCIAL ADVICE CLAIMS
        if predicate in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or "guarantee" in predicate.lower() or "guarantee" in (claim.text.original.lower() if claim.text else ""):
            return SourcePlan(
                primary=["sebi_public_regulatory_pages"],
                fallback=["rbi_regulatory_publications"],
                required_source_types=["REGULATOR", "STATUTORY_DOCUMENT"],
                query=SourceQuery(
                    keywords=["guaranteed returns prohibition", "investment advisers regulations", "advertisement code"],
                    temporal_focus=temporal_type,
                    attributes={"promised_return": obj, "subject": subject}
                )
            )

        # 3. CORPORATE ACTIONS, ANNOUNCEMENTS, & BOARD MEETINGS
        if (
            claim_type in ("CORPORATE_EVENT", "CORPORATE_DISCLOSURE")
            or predicate in ("ANNOUNCED_BONUS", "STOCK_SPLIT", "DIVIDEND_ANNOUNCED", "RIGHTS_ISSUE", "BOARD_MEETING", "BOARD_MEETING_OUTCOME", "CORPORATE_ANNOUNCEMENT", "FILING")
            or any(w in text_lower for w in ("bonus issue", "stock split", "dividend", "board meeting", "corporate announcement", "corporate action", "filed with nse", "nse filing"))
        ):
            keywords = ["corporate action" if any(w in text_lower for w in ("bonus", "split", "dividend", "action")) else "corporate announcement"]
            if "BONUS" in predicate or "bonus" in text_lower:
                keywords.extend(["bonus", str(obj)])
            elif "SPLIT" in predicate or "split" in text_lower:
                keywords.extend(["stock split", str(obj)])
            elif "DIVIDEND" in predicate or "dividend" in text_lower:
                keywords.extend(["dividend", str(obj)])
            elif "BOARD_MEETING" in predicate or "board meeting" in text_lower:
                keywords.extend(["board meeting", str(obj)])
            if subject and subject.upper() not in [k.upper() for k in keywords]:
                keywords.append(subject)

            target_primary = "nse_corporate_actions" if any(w in text_lower for w in ("bonus", "split", "dividend")) else "nse_corporate_announcements"
            return SourcePlan(
                primary=[target_primary, "nse_corporate_announcements"],
                fallback=["bse_corporate_filings", "company_official_source"],
                required_source_types=["CORPORATE_ACTION", "CORPORATE_ANNOUNCEMENT"],
                query=SourceQuery(
                    company_name=subject if subject != "unspecified_offer" else None,
                    company_symbol=subject if subject != "unspecified_offer" else None,
                    keywords=keywords,
                    date_range=date_range,
                    temporal_focus=temporal_type,
                    attributes={"ratio": obj if "BONUS" in predicate or "SPLIT" in predicate else None}
                )
            )

        # 4. FINANCIAL FILINGS & PERFORMANCE (Profits, Revenue, Debt)
        if claim_type == "FINANCIAL" or predicate in ("REPORTED_PROFIT", "REVENUE_GROWTH", "HAS_DEBT", "VALUATION_STATUS", "REACH_PRICE"):
            keywords = ["financial results", predicate.lower().replace("_", " ")]
            if obj:
                keywords.append(str(obj))

            return SourcePlan(
                primary=["nse_company_filings", "nse_corporate_announcements"],
                fallback=["bse_corporate_filings", "company_official_source"],
                required_source_types=["FINANCIAL_FILING", "CORPORATE_ANNOUNCEMENT"],
                query=SourceQuery(
                    company_name=subject if subject != "unspecified_offer" else None,
                    company_symbol=subject if subject != "unspecified_offer" else None,
                    keywords=keywords,
                    date_range=date_range,
                    temporal_focus=temporal_type,
                    attributes={"metric": predicate, "value": obj}
                )
            )

        # 5. GENERAL / FALLBACK CLAIMS
        keywords = [predicate.lower().replace("_", " ")]
        if obj:
            keywords.append(str(obj))

        # Privacy guard: Strip sensitive tokens (passwords, OTPs, PINs, card numbers, bare OTP digits) from search keywords
        orig_text = (claim.text.original.lower() if claim.text and claim.text.original else "")
        clean_keywords = []
        for kw in keywords:
            kw_clean = str(kw).strip()
            if not kw_clean:
                continue
            if any(s in kw_clean.lower() for s in ("password", "passwd", "pwd", "otp", "pin", "cvv", "cvc", "secret", "card", "redacted")):
                continue
            if any(s in orig_text for s in ("otp", "pin", "cvv", "password", "passwd", "secret", "card")):
                kw_clean = re.sub(r"\b\d{3,19}\b", "", kw_clean).strip()
            if kw_clean:
                clean_keywords.append(kw_clean)

        return SourcePlan(
            primary=["sebi_public_regulatory_pages", "nse_corporate_announcements"],
            fallback=["company_official_source"],
            required_source_types=["REGULATOR", "CORPORATE_ANNOUNCEMENT"],
            query=SourceQuery(
                name=subject if subject != "unspecified_offer" else None,
                keywords=clean_keywords,
                temporal_focus=temporal_type,
                attributes={"claim_type": claim_type}
            )
        )

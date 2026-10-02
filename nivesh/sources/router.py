"""Source Router for Engine 4 (Source Intelligence Engine).

Analyzes structured claims and normalized content to determine:
- Required source taxonomy types
- Preferred primary source catalog IDs
- Fallback source catalog IDs
- Deterministic search queries based strictly on structured claim fields and entities
"""

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
                if reg.code:
                    reg_number = reg.code
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

        # 1. REGULATORY / REGISTRATION / IDENTITY CLAIMS
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

        # 2. GUARANTEED RETURN / PROHIBITED FINANCIAL ADVICE CLAIMS
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

        # 3. CORPORATE ACTIONS (Bonus, Splits, Dividends, Mergers)
        if claim_type == "CORPORATE_EVENT" or predicate in ("ANNOUNCED_BONUS", "STOCK_SPLIT", "DIVIDEND_ANNOUNCED", "RIGHTS_ISSUE"):
            keywords = ["corporate action"]
            if "BONUS" in predicate:
                keywords.extend(["bonus", str(obj)])
            elif "SPLIT" in predicate:
                keywords.extend(["stock split", str(obj)])
            elif "DIVIDEND" in predicate:
                keywords.extend(["dividend", str(obj)])

            return SourcePlan(
                primary=["nse_corporate_actions", "nse_corporate_announcements"],
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

        return SourcePlan(
            primary=["sebi_public_regulatory_pages", "nse_corporate_announcements"],
            fallback=["company_official_source"],
            required_source_types=["REGULATOR", "CORPORATE_ANNOUNCEMENT"],
            query=SourceQuery(
                name=subject if subject != "unspecified_offer" else None,
                keywords=keywords,
                temporal_focus=temporal_type,
                attributes={"claim_type": claim_type}
            )
        )

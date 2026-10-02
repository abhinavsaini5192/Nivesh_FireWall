"""Verification requirements generator for Engine 2.

Determines the objective checklist of evidentiary items required by downstream
engines (e.g. Evidence Verification Engine, Identity Verification Engine)
to verify the claim.

Never performs verification itself; only specifies WHAT would need to be checked.
"""

from typing import Optional
from nivesh.schemas.claims import ClaimType


class VerificationRequirementsGenerator:
    """Generates evidentiary verification requirements based on claim attributes."""

    def generate(
        self,
        claim_type: ClaimType,
        predicate: str,
        subject: str,
        obj: Optional[str] = None,
        temporal_type: str = "current",
        modality_type: str = "assertion"
    ) -> list[str]:
        """Produces a list of verification requirements for the claim."""
        reqs: list[str] = []

        # 1. Future predictions or speculative opinions
        if claim_type == "PREDICTION" or temporal_type == "future" or modality_type == "prediction":
            reqs.extend([
                "unverifiable_future_outcome",
                "analyst_research_basis",
                "historical_trend_support"
            ])
            return reqs

        if claim_type == "OPINION" or modality_type == "opinion":
            reqs.extend([
                "subjective_analyst_opinion",
                "valuation_methodology_disclosure",
                "peer_comparison_data"
            ])
            return reqs

        # 2. Regulatory & Identity Claims
        if claim_type in {"REGULATORY", "IDENTITY"} or "REGISTERED" in predicate or "APPROVED" in predicate:
            reqs.extend([
                "official_regulator_registry",
                "registration_number",
                "registered_entity_or_person",
                "registration_status",
                "validity_period"
            ])
            return reqs

        # 3. Guaranteed Return / Yield Claims
        if "GUARANTEE" in predicate or "RETURN" in predicate:
            subj_lower = (subject or "").lower()
            if not subject or subj_lower in {"unspecified_offer", "unspecified", "investment_offer", "this investment", "the investment"}:
                reqs.extend([
                    "statutory_regulatory_prohibition_check",
                    "return_terms",
                    "offer_documentation",
                    "advertising_disclosure_evidence",
                    "sebi_advertisement_code_compliance",
                ])
            else:
                reqs.extend([
                    "statutory_regulatory_prohibition_check",
                    "advisory_agreement_terms",
                    "sebi_advertisement_code_compliance",
                    "fund_offer_document_scheme_information"
                ])
            return reqs

        # 4. Corporate Events (Bonus, Dividend, Buyback, IPO)
        if claim_type == "CORPORATE_EVENT" or any(p in predicate for p in ["BONUS", "DIVIDEND", "BUYBACK", "IPO"]):
            reqs.extend([
                "official_company_announcement",
                "exchange_filing_bse_nse",
                "announcement_date",
                "record_date_and_ratio"
            ])
            return reqs

        # 5. Financial Metrics (Debt, Profit, Revenue, Earnings)
        if any(p in predicate for p in ["DEBT", "PROFIT", "REVENUE", "GROWTH", "LOSS", "MARGIN"]):
            reqs.extend([
                "audited_company_financial_statements",
                "reporting_period_q_fy",
                "comparison_period_prior_year",
                "official_regulatory_disclosure_filing"
            ])
            return reqs

        # 6. Recommendation / Advisory Claims
        if claim_type == "RECOMMENDATION":
            reqs.extend([
                "registered_investment_adviser_mandate",
                "risk_profiling_and_suitability_assessment",
                "disclosure_of_financial_interest"
            ])
            return reqs

        # Default factual checklist
        reqs.extend([
            "primary_source_verification",
            "corroborating_public_records"
        ])
        return reqs

"""Centralized Source Catalog for Engine 4 (Source Intelligence Engine).

Maintains metadata specifications for all authoritative sources (SEBI, NSE, BSE, RBI, MCA, etc.)
Allows programmatic routing, capability checking, and adapter binding without hardcoding
source lookups throughout the codebase.
"""

from typing import Optional
from nivesh.schemas.sources import SourceCatalogEntry, SourceTypeTaxonomy, AuthorityTier


class SourceCatalog:
    """Registry of known authoritative financial and regulatory sources."""

    def __init__(self):
        self._sources: dict[str, SourceCatalogEntry] = {}
        self._register_default_sources()

    def register(self, entry: SourceCatalogEntry) -> None:
        """Registers a new source catalog entry."""
        self._sources[entry.source_id] = entry

    def get(self, source_id: str) -> Optional[SourceCatalogEntry]:
        """Retrieves catalog entry by unique source_id."""
        return self._sources.get(source_id)

    def list_all(self) -> list[SourceCatalogEntry]:
        """Returns all registered catalog entries."""
        return list(self._sources.values())

    def find_by_claim_type(self, claim_type: str) -> list[SourceCatalogEntry]:
        """Finds sources supporting a specific claim type."""
        return [
            entry for entry in self._sources.values()
            if claim_type in entry.supported_claim_types
        ]

    def find_by_organization(self, org: str) -> list[SourceCatalogEntry]:
        """Finds all sources operated by a specific organization (e.g. SEBI, NSE)."""
        clean_org = org.upper()
        return [
            entry for entry in self._sources.values()
            if entry.organization.upper() == clean_org
        ]

    def _register_default_sources(self) -> None:
        """Initializes default catalog entries for Indian financial ecosystem."""
        # 1. SEBI Intermediaries Registry
        self.register(SourceCatalogEntry(
            source_id="sebi_recognised_intermediaries",
            organization="SEBI",
            type="REGULATORY_REGISTRY",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["REGULATORY", "IDENTITY"],
            capabilities=["search_by_registration", "search_by_name", "search_by_trade_name"],
            base_url="https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes",
            adapter_name="SEBIAdapter",
            description="Official SEBI registry of recognized investment advisers, research analysts, and brokers."
        ))

        # 2. SEBI Regulatory & Enforcement Pages
        self.register(SourceCatalogEntry(
            source_id="sebi_public_regulatory_pages",
            organization="SEBI",
            type="REGULATOR",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["REGULATORY", "FINANCIAL"],
            capabilities=["circulars", "statutory_prohibitions", "enforcement_orders"],
            base_url="https://www.sebi.gov.in/enforcement.html",
            adapter_name="SEBIAdapter",
            description="SEBI official regulations, advertisement codes, and statutory prohibitions (e.g. guaranteed return bans)."
        ))

        # 3. NSE Corporate Announcements
        self.register(SourceCatalogEntry(
            source_id="nse_corporate_announcements",
            organization="NSE",
            type="CORPORATE_ANNOUNCEMENT",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["CORPORATE_EVENT", "FINANCIAL", "FACTUAL"],
            capabilities=["search_by_company", "search_by_symbol", "search_by_keyword", "date_filtering"],
            base_url="https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            adapter_name="NSEAdapter",
            description="National Stock Exchange of India official corporate announcements and disclosures."
        ))

        # 4. NSE Corporate Actions
        self.register(SourceCatalogEntry(
            source_id="nse_corporate_actions",
            organization="NSE",
            type="CORPORATE_ACTION",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["CORPORATE_EVENT"],
            capabilities=["bonus_issues", "stock_splits", "dividends", "rights_issues"],
            base_url="https://www.nseindia.com/companies-listing/corporate-filings-actions",
            adapter_name="NSEAdapter",
            description="Official NSE corporate actions database tracking bonus issues, stock splits, and dividends."
        ))

        # 5. NSE Company Filings (Financials)
        self.register(SourceCatalogEntry(
            source_id="nse_company_filings",
            organization="NSE",
            type="FINANCIAL_FILING",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["FINANCIAL", "FACTUAL"],
            capabilities=["financial_results", "quarterly_profit", "balance_sheet_filings"],
            base_url="https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            adapter_name="NSEAdapter",
            description="Audited quarterly and annual financial result filings submitted to NSE."
        ))

        # 6. BSE Corporate Filings
        self.register(SourceCatalogEntry(
            source_id="bse_corporate_filings",
            organization="BSE",
            type="STOCK_EXCHANGE",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["CORPORATE_EVENT", "FINANCIAL"],
            capabilities=["search_by_scrip", "corporate_announcements"],
            base_url="https://www.bseindia.com/corporates/ann.html",
            adapter_name="BSEAdapter",
            description="Bombay Stock Exchange (BSE) corporate announcements and filings."
        ))

        # 7. RBI Regulatory & Publications
        self.register(SourceCatalogEntry(
            source_id="rbi_regulatory_publications",
            organization="RBI",
            type="REGULATOR",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["REGULATORY", "FINANCIAL"],
            capabilities=["banking_regulations", "nbfc_registry", "payment_system_operators"],
            base_url="https://www.rbi.org.in",
            adapter_name="RBIAdapter",
            description="Reserve Bank of India regulatory directives and registered financial entity lists."
        ))

        # 8. Official Company Source
        self.register(SourceCatalogEntry(
            source_id="company_official_source",
            organization="COMPANY",
            type="COMPANY_OFFICIAL",
            authority_tier="SECONDARY_RELIABLE",
            supported_claim_types=["CORPORATE_EVENT", "FINANCIAL", "PRODUCT"],
            capabilities=["press_releases", "investor_relations_disclosures"],
            base_url="https://official-company-ir.internal",
            adapter_name="CompanySourceAdapter",
            description="Official corporate investor relations and disclosure websites."
        ))

        # 9. Government Sources (MCA / Registrar)
        self.register(SourceCatalogEntry(
            source_id="government_official_sources",
            organization="GOVERNMENT",
            type="GOVERNMENT",
            authority_tier="PRIMARY_OFFICIAL",
            supported_claim_types=["IDENTITY", "STATUTORY_DOCUMENT"],
            capabilities=["mca_company_master_data", "director_identification"],
            base_url="https://www.mca.gov.in",
            adapter_name="GovernmentSourceAdapter",
            description="Ministry of Corporate Affairs (MCA21) registered company master records."
        ))

"""Adapter Boundaries for Secondary/Auxiliary Sources (BSE, RBI, Company Sources).

Maintains clean architectural boundaries for sources not yet fully wired for live scraping:
- Follows Section 11: returns explicit status = 'SOURCE_UNAVAILABLE'
- Never manufactures fake verified evidence
- Extensible when additional credentials or scrapers are added.
"""

import time
from datetime import datetime, timezone
from typing import Optional

from nivesh.schemas.sources import (
    SourceQuery,
    SourceSearchResult,
    SourceDocument,
    RetrievalMetadata,
    RetrievalMode,
    RetrievalStatus,
    SourceTypeTaxonomy,
)
from nivesh.sources.adapters.base import BaseSourceAdapter


class BSEAdapter(BaseSourceAdapter):
    """Adapter boundary for Bombay Stock Exchange (BSE) filings."""

    def search(self, query: SourceQuery) -> list[SourceSearchResult]:
        symbol = query.company_symbol or query.company_name or ""
        return [
            SourceSearchResult(
                result_id=f"BSE-SEARCH-{self.compute_hash(symbol)[:8].upper()}",
                source_id="bse_corporate_filings",
                title=f"BSE Corporate Filings: {symbol}",
                url=f"https://www.bseindia.com/corporates/ann.html?scrip={symbol}",
                snippet=f"BSE corporate announcement search for {symbol}",
                metadata={"symbol": symbol}
            )
        ]

    def retrieve(self, result: SourceSearchResult) -> SourceDocument:
        start = time.time()
        retrieved_at_iso = datetime.now(timezone.utc).isoformat()
        content = "BSE authoritative interface boundary: live scraper unconfigured in current prototype."

        return SourceDocument(
            document_id=f"DOC-BSE-{self.compute_hash(result.url)[:8].upper()}",
            source_id="bse_corporate_filings",
            organization="BSE",
            source_type="STOCK_EXCHANGE",
            title=result.title,
            url=result.url,
            retrieved_at=retrieved_at_iso,
            published_at=None,
            content=content,
            content_hash=self.compute_hash(content),
            metadata={"boundary": True},
            retrieval=RetrievalMetadata(
                status="SOURCE_UNAVAILABLE",
                http_status=None,
                method="BSEAdapter",
                mode=self.default_mode,
                response_time_ms=(time.time() - start) * 1000,
                error_message="BSE live interface is not configured in this prototype environment."
            )
        )


class RBIAdapter(BaseSourceAdapter):
    """Adapter boundary for Reserve Bank of India (RBI) publications."""

    def search(self, query: SourceQuery) -> list[SourceSearchResult]:
        return [
            SourceSearchResult(
                result_id="RBI-SEARCH-001",
                source_id="rbi_regulatory_publications",
                title="RBI Regulatory Publications Search",
                url="https://www.rbi.org.in/scripts/BS_CircularsDisplay.aspx",
                snippet="RBI regulatory circulars and notifications database",
                metadata={"keywords": query.keywords}
            )
        ]

    def retrieve(self, result: SourceSearchResult) -> SourceDocument:
        start = time.time()
        retrieved_at_iso = datetime.now(timezone.utc).isoformat()
        content = "RBI authoritative interface boundary: live scraper unconfigured in current prototype."

        return SourceDocument(
            document_id=f"DOC-RBI-{self.compute_hash(result.url)[:8].upper()}",
            source_id="rbi_regulatory_publications",
            organization="RBI",
            source_type="REGULATOR",
            title=result.title,
            url=result.url,
            retrieved_at=retrieved_at_iso,
            published_at=None,
            content=content,
            content_hash=self.compute_hash(content),
            metadata={"boundary": True},
            retrieval=RetrievalMetadata(
                status="SOURCE_UNAVAILABLE",
                http_status=None,
                method="RBIAdapter",
                mode=self.default_mode,
                response_time_ms=(time.time() - start) * 1000,
                error_message="RBI live interface is not configured in this prototype environment."
            )
        )


class CompanySourceAdapter(BaseSourceAdapter):
    """Adapter boundary for official corporate investor relations sources."""

    def search(self, query: SourceQuery) -> list[SourceSearchResult]:
        company = query.company_name or query.name or "Company"
        return [
            SourceSearchResult(
                result_id="COMP-SEARCH-001",
                source_id="company_official_source",
                title=f"{company} Official Investor Relations",
                url="https://official-company-ir.internal",
                snippet=f"Corporate disclosure search for {company}",
                metadata={"company": company}
            )
        ]

    def retrieve(self, result: SourceSearchResult) -> SourceDocument:
        start = time.time()
        retrieved_at_iso = datetime.now(timezone.utc).isoformat()
        content = "Official company IR boundary: live scraper unconfigured in current prototype."

        return SourceDocument(
            document_id=f"DOC-COMP-{self.compute_hash(result.url)[:8].upper()}",
            source_id="company_official_source",
            organization="COMPANY",
            source_type="COMPANY_OFFICIAL",
            title=result.title,
            url=result.url,
            retrieved_at=retrieved_at_iso,
            published_at=None,
            content=content,
            content_hash=self.compute_hash(content),
            metadata={"boundary": True},
            retrieval=RetrievalMetadata(
                status="SOURCE_UNAVAILABLE",
                http_status=None,
                method="CompanySourceAdapter",
                mode=self.default_mode,
                response_time_ms=(time.time() - start) * 1000,
                error_message="Company official IR live interface is not configured in this prototype environment."
            )
        )

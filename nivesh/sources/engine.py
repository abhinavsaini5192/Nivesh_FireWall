"""Source Intelligence Engine (Engine 4 of Nivesh Firewall).

Discovers, routes, searches, retrieves, and normalizes authoritative evidence sources
for claims identified by Engine 2, preserving complete provenance.
Answers: 'Where should we look for authoritative information, and what source material did we retrieve?'
Strictly preserves verification_status = UNVERIFIED.
"""

import time
from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import (
    SourceAnalysis,
    ClaimSourceResult,
    SourceAnalysisMetadata,
    SourcePlan,
    SourceDocument,
    SourceSearchResult,
    EvidenceCandidate,
    RetrievalMode,
)
from nivesh.sources.catalog import SourceCatalog
from nivesh.sources.router import SourceRouter
from nivesh.sources.cache import SourceCache
from nivesh.sources.rate_limiter import RateLimiter
from nivesh.sources.normalizer import SourceNormalizer
from nivesh.sources.adapters.base import BaseSourceAdapter
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.boundary_adapters import BSEAdapter, RBIAdapter, CompanySourceAdapter

ENGINE_VERSION = "1.0.0"


class SourceIntelligenceEngine:
    """Core Engine 4 service interface."""

    def __init__(
        self,
        catalog: Optional[SourceCatalog] = None,
        cache: Optional[SourceCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        default_mode: RetrievalMode = "LIVE",
    ):
        self.catalog = catalog or SourceCatalog()
        self.cache = cache or SourceCache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.default_mode = default_mode
        self.router = SourceRouter(self.catalog)

        # Initialize and bind adapters
        self._adapters: dict[str, BaseSourceAdapter] = {
            "SEBIAdapter": SEBIAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode),
            "NSEAdapter": NSEAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode),
            "BSEAdapter": BSEAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode),
            "RBIAdapter": RBIAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode),
            "CompanySourceAdapter": CompanySourceAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode),
        }

    def register_adapter(self, name: str, adapter: BaseSourceAdapter) -> None:
        """Allows registering custom or mock adapters for testing."""
        self._adapters[name] = adapter

    def get_adapter(self, adapter_name: str) -> Optional[BaseSourceAdapter]:
        """Retrieves an adapter instance by name."""
        return self._adapters.get(adapter_name)

    def discover_and_retrieve(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: Optional[ActionAnalysis] = None,
    ) -> SourceAnalysis:
        """Main service interface for Engine 4.
        
        Consumes NormalizedContent, ClaimAnalysis, and optional ActionAnalysis.
        Returns complete SourceAnalysis with source plans, documents, and evidence candidates.
        """
        start_time = time.time()
        claim_sources: list[ClaimSourceResult] = []

        total_sources_queried = 0
        total_documents_retrieved = 0
        total_candidates_count = 0
        total_retrieval_failures = 0
        cache_hits = 0

        # Note: Actions (from Engine 3) are action instructions and must NOT trigger unrelated source queries.
        # Only claims require authoritative source verification evidence.

        for claim in claims.claims:
            # 1. Route claim to authoritative sources
            source_plan: SourcePlan = self.router.route_claim(claim, content)

            claim_searches: list[SourceSearchResult] = []
            claim_documents: list[SourceDocument] = []
            claim_candidates: list[EvidenceCandidate] = []

            # 2. Query primary sources first
            sources_to_try = list(source_plan.primary)
            if not sources_to_try:
                sources_to_try = list(source_plan.fallback)

            candidate_idx = 1
            for source_id in sources_to_try:
                catalog_entry = self.catalog.get(source_id)
                if not catalog_entry:
                    continue

                adapter = self.get_adapter(catalog_entry.adapter_name)
                if not adapter:
                    continue

                total_sources_queried += 1

                # Execute search
                try:
                    search_results = adapter.search(source_plan.query)
                except Exception:
                    search_results = []

                if not search_results:
                    # If primary had no results, attempt fallback sources
                    continue

                claim_searches.extend(search_results)

                # For each search result, retrieve authoritative source document
                for s_res in search_results:
                    try:
                        doc = adapter.retrieve(s_res)
                        claim_documents.append(doc)
                        total_documents_retrieved += 1

                        if doc.retrieval.mode == "CACHE":
                            cache_hits += 1

                        if doc.retrieval.status in ("RETRIEVAL_FAILED", "SOURCE_UNAVAILABLE", "RATE_LIMITED"):
                            total_retrieval_failures += 1

                        # Extract structured evidence candidates
                        candidates = SourceNormalizer.extract_evidence_candidates(
                            claim=claim,
                            document=doc,
                            authority_tier=catalog_entry.authority_tier,
                            candidate_index=candidate_idx,
                        )
                        for cand in candidates:
                            claim_candidates.append(cand)
                            candidate_idx += 1
                            total_candidates_count += 1

                    except Exception as e:
                        total_retrieval_failures += 1

            # Fallback pass: If no documents retrieved and fallbacks exist
            if not claim_documents and source_plan.fallback:
                for fallback_id in source_plan.fallback:
                    if fallback_id in sources_to_try:
                        continue
                    catalog_entry = self.catalog.get(fallback_id)
                    if not catalog_entry:
                        continue
                    adapter = self.get_adapter(catalog_entry.adapter_name)
                    if not adapter:
                        continue

                    total_sources_queried += 1
                    try:
                        search_results = adapter.search(source_plan.query)
                        claim_searches.extend(search_results)
                        for s_res in search_results:
                            doc = adapter.retrieve(s_res)
                            claim_documents.append(doc)
                            total_documents_retrieved += 1
                            if doc.retrieval.status in ("RETRIEVAL_FAILED", "SOURCE_UNAVAILABLE"):
                                total_retrieval_failures += 1
                            candidates = SourceNormalizer.extract_evidence_candidates(
                                claim=claim,
                                document=doc,
                                authority_tier=catalog_entry.authority_tier,
                                candidate_index=candidate_idx,
                            )
                            for cand in candidates:
                                claim_candidates.append(cand)
                                candidate_idx += 1
                                total_candidates_count += 1
                    except Exception:
                        total_retrieval_failures += 1

            claim_sources.append(ClaimSourceResult(
                claim_id=claim.claim_id,
                source_plan=source_plan,
                searches=claim_searches,
                documents=claim_documents,
                evidence_candidates=claim_candidates,
            ))

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        metadata = SourceAnalysisMetadata(
            claims_processed=len(claims.claims),
            sources_queried=total_sources_queried,
            documents_retrieved=total_documents_retrieved,
            evidence_candidates_count=total_candidates_count,
            retrieval_failures=total_retrieval_failures,
            cache_hits=cache_hits,
            processing_time_ms=processing_time_ms,
        )

        return SourceAnalysis(
            content_id=content.content_id,
            claim_sources=claim_sources,
            analysis_metadata=metadata,
        )

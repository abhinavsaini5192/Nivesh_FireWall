"""Source Intelligence Engine (Engine 4 of Nivesh Firewall).

Phase 15.A: Authoritative Source Gateway & Live Verification Architecture.
Discovers, routes, searches, retrieves, and normalizes authoritative evidence sources
for claims identified by Engine 2, preserving complete provenance through the
Authoritative Source Gateway.

Answers: 'Where should we look for authoritative information, and what source material did we retrieve?'
Strictly preserves verification_status = UNVERIFIED.
"""

from datetime import datetime, timezone
import time
from typing import Optional, Any
from nivesh.config import get_settings, Settings
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
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter
from nivesh.sources.adapters.boundary_adapters import CompanySourceAdapter
from nivesh.sources.gateway import AuthoritativeSourceGateway

ENGINE_VERSION = "1.0.0"


class SourceIntelligenceEngine:
    """Core Engine 4 service interface coordinating authoritative source retrieval."""

    def __init__(
        self,
        catalog: Optional[SourceCatalog] = None,
        cache: Optional[SourceCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        default_mode: RetrievalMode = "LIVE",
        settings: Optional[Settings] = None,
        gateway: Optional[AuthoritativeSourceGateway] = None,
    ):
        self.settings = settings or get_settings()
        self.catalog = catalog or SourceCatalog()
        self.cache = cache or SourceCache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.default_mode = default_mode
        self.router = SourceRouter(self.catalog)

        # Initialize Authoritative Source Gateway
        self.gateway = gateway or AuthoritativeSourceGateway(
            catalog=self.catalog,
            cache=self.cache,
            rate_limiter=self.rate_limiter,
            settings=self.settings,
            default_mode=self.default_mode,
        )

        # Instantiate adapters with environment configuration
        sebi_adapter = SEBIAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode)
        nse_adapter = NSEAdapter(
            cache=self.cache,
            rate_limiter=self.rate_limiter,
            default_mode=self.default_mode,
            api_key=getattr(self.settings, "nse_api_key", None),
            api_secret=getattr(self.settings, "nse_api_secret", None),
        )
        bse_adapter = BSEAdapter(
            cache=self.cache,
            rate_limiter=self.rate_limiter,
            default_mode=self.default_mode,
            api_key=getattr(self.settings, "bse_api_key", None),
            api_secret=getattr(self.settings, "bse_api_secret", None),
        )
        rbi_adapter = RBIAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode)
        company_adapter = CompanySourceAdapter(cache=self.cache, rate_limiter=self.rate_limiter, default_mode=self.default_mode)

        self._adapters: dict[str, BaseSourceAdapter] = {
            "SEBIAdapter": sebi_adapter,
            "NSEAdapter": nse_adapter,
            "BSEAdapter": bse_adapter,
            "RBIAdapter": rbi_adapter,
            "CompanySourceAdapter": company_adapter,
        }

        # Register in gateway with capabilities
        for name, ad in self._adapters.items():
            self.gateway.register_adapter(name, ad, getattr(ad, "capabilities", []))

    def register_adapter(self, name: str, adapter: BaseSourceAdapter) -> None:
        """Allows registering custom or mock adapters for testing."""
        self._adapters[name] = adapter
        self.gateway.register_adapter(name, adapter, getattr(adapter, "capabilities", []))

    def get_adapter(self, adapter_name: str) -> Optional[BaseSourceAdapter]:
        """Retrieves an adapter instance by name."""
        return self._adapters.get(adapter_name)

    def discover_and_retrieve(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: Optional[ActionAnalysis] = None,
        require_cross_source: bool = False,
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
            # Delegate verification retrieval to unified AuthoritativeSourceGateway
            claim_res: ClaimSourceResult = self.gateway.execute_claim_verification(
                claim=claim,
                content=content,
                mode_override=self.default_mode,
                require_cross_source=require_cross_source,
            )
            claim_sources.append(claim_res)

            # Record metrics
            total_sources_queried += len(claim_res.source_plan.primary)
            total_documents_retrieved += len(claim_res.documents)
            total_candidates_count += len(claim_res.evidence_candidates)

            for doc in claim_res.documents:
                if doc.retrieval.mode == "CACHE":
                    cache_hits += 1
                    try:
                        from nivesh.observability import metrics
                        metrics.source_cache_hits_total.inc(source_name=doc.source_id)
                    except Exception:
                        pass
                else:
                    try:
                        from nivesh.observability import metrics
                        metrics.source_cache_misses_total.inc(source_name=doc.source_id)
                    except Exception:
                        pass

                if doc.retrieval.status in ("RETRIEVAL_FAILED", "SOURCE_UNAVAILABLE", "RATE_LIMITED"):
                    total_retrieval_failures += 1
                    try:
                        from nivesh.observability import metrics
                        metrics.source_unavailable_total.inc(source_name=doc.source_id)
                        metrics.source_requests_total.inc(source_name=doc.source_id, status="UNAVAILABLE")
                    except Exception:
                        pass
                else:
                    try:
                        from nivesh.observability import metrics
                        metrics.source_requests_total.inc(source_name=doc.source_id, status="SUCCESS")
                    except Exception:
                        pass

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

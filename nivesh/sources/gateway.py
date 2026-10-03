"""Authoritative Source Gateway for Nivesh Firewall.

Phase 15.A: Authoritative Source Gateway & Live Verification Architecture.
Coordinates discovery, routing, access mode selection, and unified provenance
across all primary regulatory and financial source adapters (SEBI, RBI, NSE, BSE).

Enforces strict separation of retrieval states:
- LIVE
- OFFICIAL_SNAPSHOT
- CACHE
- FIXTURE
- SOURCE_UNAVAILABLE

Never represents FIXTURE, CACHE, or OFFICIAL_SNAPSHOT as LIVE.
"""

from datetime import datetime, timezone
import time
from typing import Optional, Any

from nivesh.config import get_settings, Settings
from nivesh.schemas.claims import CanonicalClaim
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.sources import (
    SourceQuery,
    SourcePlan,
    SourceDocument,
    SourceSearchResult,
    EvidenceCandidate,
    ClaimSourceResult,
    RetrievalMode,
    RetrievalStatus,
    AuthoritativeProvenance,
    FreshnessStatus,
    ProviderAccessState,
    ProviderAccessConfig,
    SourceHealthReport,
)
from nivesh.sources.catalog import SourceCatalog
from nivesh.sources.router import SourceRouter
from nivesh.sources.cache import SourceCache
from nivesh.sources.rate_limiter import RateLimiter
from nivesh.sources.normalizer import SourceNormalizer
from nivesh.sources.adapters.base import BaseSourceAdapter


class AuthoritativeSourceGateway:
    """Unified Authoritative Source Gateway coordinating all external verification adapters."""

    def __init__(
        self,
        catalog: Optional[SourceCatalog] = None,
        cache: Optional[SourceCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        settings: Optional[Settings] = None,
        default_mode: Optional[RetrievalMode] = None,
    ):
        self.settings = settings or get_settings()
        self.catalog = catalog or SourceCatalog()
        self.cache = cache or SourceCache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.router = SourceRouter(self.catalog)
        self.default_mode: RetrievalMode = default_mode or getattr(self.settings, "source_mode", "FIXTURE")

        # Adapter registry
        self._adapters: dict[str, BaseSourceAdapter] = {}
        self._capabilities: dict[str, list[str]] = {}

    def register_adapter(
        self,
        name: str,
        adapter: BaseSourceAdapter,
        capabilities: Optional[list[str]] = None
    ) -> None:
        """Registers a source adapter and binds its verified capabilities."""
        self._adapters[name] = adapter
        self._capabilities[name] = capabilities or getattr(adapter, "capabilities", [])

    def get_adapter(self, name: str) -> Optional[BaseSourceAdapter]:
        """Retrieves an adapter by name."""
        return self._adapters.get(name)

    def get_capabilities(self, name: str) -> list[str]:
        """Returns declared capabilities for a source adapter."""
        return list(self._capabilities.get(name, []))

    def check_provider_health(
        self,
        source_name: str,
        probe_live: bool = False
    ) -> ProviderAccessConfig:
        """Evaluates operational access status and diagnostics for an authoritative source."""
        source_key = source_name.upper().strip()
        if source_key == "SEBI":
            live_on = bool(self.settings.live_sources_enabled or getattr(self.settings, "sebi_live_enabled", False))
            state: ProviderAccessState = "LIVE_AVAILABLE" if live_on else "DISABLED"
            diag = "Official Intermediary Registry live search active" if live_on else "Live SEBI queries disabled in config; snapshots available"
            if live_on and probe_live:
                adapter = self.get_adapter("SEBIAdapter")
                if adapter:
                    try:
                        code, _, _ = adapter.safe_http_fetch("https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13")
                        if code != 200:
                            state = "SOURCE_UNAVAILABLE"
                            diag = f"SEBI registry probe returned HTTP {code}"
                    except Exception as e:
                        state = "SOURCE_UNAVAILABLE"
                        diag = f"SEBI registry probe error: {str(e)}"
            return ProviderAccessConfig(
                source_identifier="SEBI",
                authority_name="Securities and Exchange Board of India",
                state=state,
                access_mechanism="Official Intermediary Registry Search (HTTPS GET)",
                credentials_required=False,
                has_credentials=True,
                live_supported=True,
                snapshot_fallback_available=True,
                limitations=[
                    "Public registry search rate-limited to 1 req/sec",
                    "Requires anti-bot header compliance",
                    "Personal contact PII redacted from evidence display",
                ],
                diagnostic_message=diag,
            )
        elif source_key == "RBI":
            live_on = bool(self.settings.live_sources_enabled or getattr(self.settings, "rbi_live_enabled", False))
            state = "LIVE_AVAILABLE" if live_on else "DISABLED"
            diag = "Official DBIE & policy rate publications active" if live_on else "Live RBI queries disabled in config; snapshots available"
            return ProviderAccessConfig(
                source_identifier="RBI",
                authority_name="Reserve Bank of India",
                state=state,
                access_mechanism="DBIE / Official Publications & Policy Rates (HTTPS GET)",
                credentials_required=False,
                has_credentials=True,
                live_supported=True,
                snapshot_fallback_available=True,
                limitations=[
                    "Public DBIE query endpoints subject to format shifts",
                    "Macroeconomic data strictly separated from intermediary licensing",
                ],
                diagnostic_message=diag,
            )
        elif source_key == "NSE":
            live_on = bool(self.settings.live_sources_enabled or getattr(self.settings, "nse_live_enabled", False))
            nse_adapter = self.get_adapter("NSEAdapter")
            if nse_adapter:
                if hasattr(nse_adapter, "nsepython_enabled"):
                    nse_adapter.nsepython_enabled = getattr(self.settings, "nsepython_enabled", False)
                if hasattr(nse_adapter, "provider_preference"):
                    nse_adapter.provider_preference = getattr(self.settings, "nse_provider_preference", "AUTO")

            active_p = getattr(nse_adapter, "resolve_active_provider", lambda: None)() if nse_adapter else None
            from nivesh.sources.adapters.nse_providers import NSEPythonProvider, PublicNSEProvider

            if active_p and isinstance(active_p, NSEPythonProvider):
                is_avail = active_p.is_available
                state = "LIVE_AVAILABLE" if (live_on and is_avail) else ("DISABLED" if not live_on else "SOURCE_UNAVAILABLE")
                diag = "NSE public data active (via optional sandboxed NSEPython provider)" if is_avail else "Optional package 'nsepython' not installed"
                access_mech = "NSE-originated public data (via sandboxed NSEPython provider)"
                creds_req = False
                has_creds = is_avail
            elif active_p and isinstance(active_p, PublicNSEProvider):
                state = "LIVE_AVAILABLE" if live_on else "DISABLED"
                diag = "NSE Public REST endpoint provider active (SSRF-safe client)"
                access_mech = "NSE Public REST Endpoint (SSRF-safe client)"
                creds_req = False
                has_creds = True
            else:
                has_creds = bool(getattr(self.settings, "nse_api_key", None))
                if not live_on:
                    state = "DISABLED"
                    diag = "Live NSE corporate filings disabled in configuration"
                elif not has_creds:
                    state = "CREDENTIALS_MISSING"
                    diag = "NSE API credentials missing (NSE_API_KEY unconfigured). Requires authorized product access."
                else:
                    state = "LIVE_AVAILABLE"
                    diag = "NSE Authorized Corporate Announcements API active"
                access_mech = "NSE Official Corporate Announcements API (Authorized HTTPS API)"
                creds_req = True

            return ProviderAccessConfig(
                source_identifier="NSE",
                authority_name="National Stock Exchange of India",
                state=state,
                access_mechanism=access_mech,
                credentials_required=creds_req,
                has_credentials=has_creds,
                live_supported=True,
                snapshot_fallback_available=True,
                limitations=[
                    "Authorized API product subscription required for official feed",
                    "Akamai / anti-bot controls prevent unauthorized web scraping",
                    "LIVE credentials differ from UAT credentials",
                ],
                diagnostic_message=diag,
            )
        elif source_key == "BSE":
            live_on = bool(self.settings.live_sources_enabled or getattr(self.settings, "bse_live_enabled", False))
            bse_adapter = self.get_adapter("BSEAdapter")
            if bse_adapter:
                if hasattr(bse_adapter, "provider_preference"):
                    bse_adapter.provider_preference = getattr(self.settings, "bse_provider_preference", "AUTO")
                if hasattr(bse_adapter, "public_enabled"):
                    bse_adapter.public_enabled = getattr(self.settings, "bse_public_enabled", False)
            active_p = getattr(bse_adapter, "resolve_active_provider", lambda: None)() if bse_adapter else None
            from nivesh.sources.adapters.bse_providers import PublicBSEProvider

            if active_p and isinstance(active_p, PublicBSEProvider):
                state = "LIVE_AVAILABLE" if live_on else "DISABLED"
                diag = "BSE Public Dissemination provider active (SSRF-safe client)"
                access_mech = "BSE Public Dissemination Endpoint (SSRF-safe client)"
                creds_req = False
                has_creds = True
            else:
                has_creds = bool(getattr(self.settings, "bse_api_key", None))
                if not live_on:
                    state = "DISABLED"
                    diag = "Live BSE corporate disclosures disabled in configuration"
                elif not has_creds:
                    state = "CREDENTIALS_MISSING"
                    diag = "BSE Corporate Data API credentials missing (BSE_API_KEY unconfigured). Requires authorized enterprise key."
                else:
                    state = "LIVE_AVAILABLE"
                    diag = "BSE Corporate Data API active"
                access_mech = "BSE Corporate Data API v1 (Authorized HTTPS API)"
                creds_req = True

            return ProviderAccessConfig(
                source_identifier="BSE",
                authority_name="Bombay Stock Exchange",
                state=state,
                access_mechanism=access_mech,
                credentials_required=creds_req,
                has_credentials=has_creds,
                live_supported=True,
                snapshot_fallback_available=True,
                limitations=[
                    "BSE Corporate Data API licensing required for enterprise feed",
                    "Akamai edge protection blocks unauthenticated automated scripts",
                    "Registered production IP restrictions apply",
                ],
                diagnostic_message=diag,
            )
        else:
            return ProviderAccessConfig(
                source_identifier=source_name,
                authority_name=f"{source_name} Authority",
                state="SOURCE_UNAVAILABLE",
                access_mechanism="Unknown",
                credentials_required=False,
                has_credentials=False,
                live_supported=False,
                snapshot_fallback_available=False,
                limitations=["Unrecognized regulatory authority"],
                diagnostic_message=f"No provider adapter registered for {source_name}",
            )

    def get_source_health_report(self, probe_live: bool = False) -> SourceHealthReport:
        """Compiles health and access diagnostics across all authoritative providers."""
        now_iso = datetime.now(timezone.utc).isoformat()
        sources_status: dict[str, ProviderAccessConfig] = {}
        summary: dict[str, str] = {}

        for src in ["SEBI", "RBI", "NSE", "BSE"]:
            cfg = self.check_provider_health(src, probe_live=probe_live)
            sources_status[src] = cfg
            summary[src] = cfg.state

        return SourceHealthReport(
            timestamp=now_iso,
            sources=sources_status,
            summary=summary,
        )

    def resolve_access_mode(self, source_id: str, requested_mode: Optional[RetrievalMode] = None) -> tuple[RetrievalMode, Optional[str]]:
        """Determines the exact legitimate access mode for a given source.
        
        Returns:
            (resolved_mode, reason_if_degraded_or_unavailable)
        """
        mode = requested_mode or self.default_mode

        # If FIXTURE or CACHE explicitly requested (e.g. test environment)
        if mode in ("FIXTURE", "CACHE"):
            return mode, None

        # Check source-specific live enablement
        live_enabled = False
        requires_credentials = False
        has_credentials = True
        missing_cred_name = None

        active_p = None
        if "sebi" in source_id.lower():
            live_enabled = self.settings.live_sources_enabled or getattr(self.settings, "sebi_live_enabled", False)
        elif "rbi" in source_id.lower():
            live_enabled = self.settings.live_sources_enabled or getattr(self.settings, "rbi_live_enabled", False)
        elif "nse" in source_id.lower():
            live_enabled = self.settings.live_sources_enabled or getattr(self.settings, "nse_live_enabled", False)
            nse_adapter = self.get_adapter("NSEAdapter")
            if nse_adapter:
                if hasattr(nse_adapter, "nsepython_enabled"):
                    nse_adapter.nsepython_enabled = getattr(self.settings, "nsepython_enabled", False)
                if hasattr(nse_adapter, "provider_preference"):
                    nse_adapter.provider_preference = getattr(self.settings, "nse_provider_preference", "AUTO")
                active_p = getattr(nse_adapter, "resolve_active_provider", lambda: None)()

            from nivesh.sources.adapters.nse_providers import NSEPythonProvider, PublicNSEProvider
            if active_p and isinstance(active_p, (NSEPythonProvider, PublicNSEProvider)):
                requires_credentials = False
                has_credentials = True
                if isinstance(active_p, NSEPythonProvider) and not active_p.is_available:
                    has_credentials = False
                    missing_cred_name = "nsepython optional package"
            else:
                requires_credentials = True
                if not getattr(self.settings, "nse_api_key", None):
                    has_credentials = False
                    missing_cred_name = "NSE_API_KEY"
        elif "bse" in source_id.lower():
            live_enabled = self.settings.live_sources_enabled or getattr(self.settings, "bse_live_enabled", False)
            bse_adapter = self.get_adapter("BSEAdapter")
            if bse_adapter:
                if hasattr(bse_adapter, "provider_preference"):
                    bse_adapter.provider_preference = getattr(self.settings, "bse_provider_preference", "AUTO")
                if hasattr(bse_adapter, "public_enabled"):
                    bse_adapter.public_enabled = getattr(self.settings, "bse_public_enabled", False)
                active_p = getattr(bse_adapter, "resolve_active_provider", lambda: None)()

            from nivesh.sources.adapters.bse_providers import PublicBSEProvider, OfficialSnapshotBSEProvider
            if active_p and isinstance(active_p, PublicBSEProvider):
                requires_credentials = False
                has_credentials = active_p.is_available
                if not has_credentials:
                    missing_cred_name = "BSE safe fetch client"
            elif active_p and isinstance(active_p, OfficialSnapshotBSEProvider):
                requires_credentials = False
                has_credentials = True
            else:
                requires_credentials = True
                if not getattr(self.settings, "bse_api_key", None):
                    has_credentials = False
                    missing_cred_name = "BSE_API_KEY"

        if mode in ("LIVE", "LIVE_PUBLIC", "LIVE_AUTHORIZED"):
            if not live_enabled:
                return "OFFICIAL_SNAPSHOT", f"Live queries disabled for {source_id}; using official regulatory snapshot."
            if requires_credentials and not has_credentials:
                return "SOURCE_UNAVAILABLE", f"Required server credentials ({missing_cred_name}) unconfigured for {source_id} (CREDENTIALS_MISSING)."
            if "nse" in source_id.lower() and active_p:
                return active_p.default_success_mode, None
            if "bse" in source_id.lower() and active_p:
                return active_p.default_success_mode, None
            return "LIVE", None

        if mode == "OFFICIAL_SNAPSHOT":
            return "OFFICIAL_SNAPSHOT", None

        return mode, None

    def execute_claim_verification(
        self,
        claim: CanonicalClaim,
        content: Optional[NormalizedContent] = None,
        mode_override: Optional[RetrievalMode] = None,
        require_cross_source: bool = False,
    ) -> ClaimSourceResult:
        """Executes targeted authoritative source query and evidence extraction for a claim."""
        # 1. Route claim to determine primary and fallback authoritative sources
        source_plan: SourcePlan = self.router.route_claim(claim, content)

        # 2. Determine target sources (supports cross-exchange corroboration if requested)
        target_source_ids = list(source_plan.primary)
        if require_cross_source and "bse_corporate_filings" not in target_source_ids:
            # If claim is corporate action/event on NSE, add BSE for corroboration
            if any("nse" in s for s in target_source_ids):
                target_source_ids.append("bse_corporate_filings")

        if not target_source_ids:
            target_source_ids = list(source_plan.fallback)

        claim_searches: list[SourceSearchResult] = []
        claim_documents: list[SourceDocument] = []
        claim_candidates: list[EvidenceCandidate] = []
        authoritative_provenances: list[AuthoritativeProvenance] = []

        candidate_counter = 1

        for source_id in target_source_ids:
            catalog_entry = self.catalog.get(source_id)
            if not catalog_entry:
                continue

            adapter = self.get_adapter(catalog_entry.adapter_name)
            if not adapter:
                continue

            # Determine operational mode for this specific adapter call
            access_mode, mode_reason = self.resolve_access_mode(source_id, mode_override)

            # Set adapter's active mode for this invocation
            adapter.default_mode = access_mode

            if access_mode == "SOURCE_UNAVAILABLE":
                # Create explicit UNAVAILABLE record preserving truthful provenance
                now_iso = datetime.now(timezone.utc).isoformat()
                is_missing_creds = "CREDENTIALS_MISSING" in str(mode_reason) or "unconfigured" in str(mode_reason).lower()
                doc_status: RetrievalStatus = "CREDENTIALS_MISSING" if is_missing_creds else "SOURCE_UNAVAILABLE"
                unavail_doc = SourceDocument(
                    document_id=f"DOC-{adapter.compute_hash(source_id + claim.claim_id)[:8].upper()}",
                    source_id=source_id,
                    organization=catalog_entry.organization,
                    source_type=catalog_entry.type,
                    title=f"{catalog_entry.organization} Official Query ({source_id})",
                    url=catalog_entry.base_url,
                    retrieved_at=now_iso,
                    published_at=None,
                    content=f"Authoritative source '{source_id}' is unavailable: {mode_reason or 'Access unconfigured'}",
                    content_hash=adapter.compute_hash("SOURCE_UNAVAILABLE"),
                    metadata={"error": mode_reason, "status": doc_status},
                    retrieval={
                        "status": doc_status,
                        "http_status": 401 if is_missing_creds else None,
                        "method": adapter.adapter_name,
                        "mode": "SOURCE_UNAVAILABLE",
                        "response_time_ms": 0.0,
                        "error_message": mode_reason,
                    },
                    authoritative_provenance=adapter.build_provenance(
                        source=catalog_entry.organization,
                        source_authority=f"{catalog_entry.organization} Authority",
                        retrieval_mode="SOURCE_UNAVAILABLE",
                        retrieved_at=now_iso,
                        adapter_name=adapter.adapter_name,
                        response_status=doc_status,
                        evidence=f"Source unavailable ({doc_status}): {mode_reason}",
                    )
                )
                claim_documents.append(unavail_doc)
                if unavail_doc.authoritative_provenance:
                    authoritative_provenances.append(unavail_doc.authoritative_provenance)
                continue

            # Search source
            try:
                search_results = adapter.search(source_plan.query)
            except Exception as e:
                search_results = []

            for s_res in search_results:
                claim_searches.append(s_res)

                # Retrieve authoritative document
                try:
                    doc = adapter.retrieve(s_res)
                except Exception as e:
                    now_iso = datetime.now(timezone.utc).isoformat()
                    doc = SourceDocument(
                        document_id=f"DOC-ERR-{adapter.compute_hash(s_res.url)[:8].upper()}",
                        source_id=s_res.source_id,
                        organization=catalog_entry.organization,
                        source_type=catalog_entry.type,
                        title=s_res.title,
                        url=s_res.url,
                        retrieved_at=now_iso,
                        published_at=None,
                        content=f"Retrieval error: {str(e)}",
                        content_hash=adapter.compute_hash("ERROR"),
                        metadata={"error": str(e)},
                        retrieval={
                            "status": "RETRIEVAL_FAILED",
                            "http_status": 500,
                            "method": adapter.adapter_name,
                            "mode": access_mode,
                            "response_time_ms": 0.0,
                            "error_message": str(e),
                        },
                        authoritative_provenance=adapter.build_provenance(
                            source=catalog_entry.organization,
                            source_authority=f"{catalog_entry.organization} Official Authority",
                            retrieval_mode="SOURCE_UNAVAILABLE",
                            retrieved_at=now_iso,
                            adapter_name=adapter.adapter_name,
                            response_status="RETRIEVAL_FAILED",
                            evidence=f"Failed to retrieve document: {str(e)}",
                        )
                    )

                claim_documents.append(doc)
                if doc.authoritative_provenance:
                    authoritative_provenances.append(doc.authoritative_provenance)

                # Extract structured evidence candidate
                cands = SourceNormalizer.extract_evidence_candidates(
                    claim=claim,
                    document=doc,
                    authority_tier=catalog_entry.authority_tier,
                    candidate_index=candidate_counter,
                )
                for c in cands:
                    c.authoritative_provenance = doc.authoritative_provenance
                    claim_candidates.append(c)
                    candidate_counter += 1

        # Fallback pass: If no documents retrieved and fallback sources exist
        if not claim_documents and source_plan.fallback:
            for fallback_id in source_plan.fallback:
                if fallback_id in target_source_ids:
                    continue
                catalog_entry = self.catalog.get(fallback_id)
                if not catalog_entry:
                    continue
                adapter = self.get_adapter(catalog_entry.adapter_name)
                if not adapter:
                    continue

                access_mode, mode_reason = self.resolve_access_mode(fallback_id, mode_override)
                adapter.default_mode = access_mode

                try:
                    search_results = adapter.search(source_plan.query)
                except Exception:
                    search_results = []

                for s_res in search_results:
                    claim_searches.append(s_res)
                    try:
                        doc = adapter.retrieve(s_res)
                        claim_documents.append(doc)
                        if doc.authoritative_provenance:
                            authoritative_provenances.append(doc.authoritative_provenance)
                        cands = SourceNormalizer.extract_evidence_candidates(
                            claim=claim,
                            document=doc,
                            authority_tier=catalog_entry.authority_tier,
                            candidate_index=candidate_counter,
                        )
                        for c in cands:
                            c.authoritative_provenance = doc.authoritative_provenance
                            claim_candidates.append(c)
                            candidate_counter += 1
                    except Exception:
                        pass

        return ClaimSourceResult(
            claim_id=claim.claim_id,
            source_plan=source_plan,
            searches=claim_searches,
            documents=claim_documents,
            evidence_candidates=claim_candidates,
            authoritative_provenances=authoritative_provenances,
        )

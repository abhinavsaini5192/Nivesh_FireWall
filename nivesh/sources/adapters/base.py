"""Base Source Adapter Interface and Safe HTTP Client for Engine 4.

Defines the contract for all external source integrations:
- search(query) -> list[SourceSearchResult]
- retrieve(result) -> SourceDocument
Enforces outbound SSRF validation, size caps, timeouts, and redirect controls.
"""

from abc import ABC, abstractmethod
import hashlib
import time
from typing import Optional, Any
from urllib.parse import urlparse
import httpx

from nivesh.schemas.sources import (
    SourceQuery,
    SourceSearchResult,
    SourceDocument,
    RetrievalMetadata,
    RetrievalMode,
    RetrievalStatus,
    SourceTypeTaxonomy,
    AuthoritativeProvenance,
    FreshnessStatus,
)
from nivesh.sources.ssrf import SsrfValidator, SsrfError
from nivesh.sources.cache import SourceCache
from nivesh.sources.rate_limiter import RateLimiter

MAX_SOURCE_DOC_BYTES = 5 * 1024 * 1024  # 5 MB limit
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_USER_AGENT = "NiveshFirewall-SourceEngine/1.0 (Authoritative Verification; +https://nivesh.internal)"
DEFAULT_CACHE_TTL_SECONDS = 3600


class BaseSourceAdapter(ABC):
    """Abstract base class for all authoritative data source adapters."""

    adapter_name: str = "BaseSourceAdapter"
    adapter_version: str = "1.0.0"
    source_identifier: str = "GENERIC"
    source_authority_name: str = "Authoritative Regulatory / Financial Body"
    capabilities: list[str] = []

    def __init__(
        self,
        cache: Optional[SourceCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        default_mode: RetrievalMode = "LIVE",
        freshness_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    ):
        self.cache = cache or SourceCache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.timeout = timeout
        self.default_mode: RetrievalMode = default_mode
        self.freshness_ttl_seconds = freshness_ttl_seconds

    def compute_freshness(
        self,
        retrieval_mode: RetrievalMode,
        retrieved_at: str,
        published_at: Optional[str] = None
    ) -> FreshnessStatus:
        """Determines explicit freshness status based on retrieval mode and timestamps."""
        if retrieval_mode == "LIVE":
            return "CURRENT"
        elif retrieval_mode == "OFFICIAL_SNAPSHOT":
            return "SNAPSHOT"
        elif retrieval_mode == "CACHE":
            try:
                # Check age of cache
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                ret_dt = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
                age_seconds = (now - ret_dt).total_seconds()
                return "CURRENT" if age_seconds <= self.freshness_ttl_seconds else "STALE"
            except Exception:
                return "CURRENT"
        elif retrieval_mode == "FIXTURE":
            return "HISTORICAL"
        else:
            return "UNKNOWN"

    def build_provenance(
        self,
        source: Optional[str] = None,
        source_authority: Optional[str] = None,
        retrieval_mode: Optional[RetrievalMode] = None,
        retrieved_at: Optional[str] = None,
        published_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        source_record_id: Optional[str] = None,
        source_reference: Optional[str] = None,
        adapter_name: Optional[str] = None,
        adapter_version: Optional[str] = None,
        response_status: RetrievalStatus = "SUCCESS",
        evidence: str = "",
        access_method: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> AuthoritativeProvenance:
        """Constructs a normalized AuthoritativeProvenance instance."""
        mode = retrieval_mode or self.default_mode
        from datetime import datetime, timezone
        ret_at = retrieved_at or datetime.now(timezone.utc).isoformat()
        freshness = self.compute_freshness(mode, ret_at, published_at)

        return AuthoritativeProvenance(
            source=source or self.source_identifier,
            source_authority=source_authority or self.source_authority_name,
            retrieval_mode=mode,
            retrieved_at=ret_at,
            published_at=published_at,
            updated_at=updated_at,
            source_record_id=source_record_id,
            source_reference=source_reference,
            adapter_name=adapter_name or self.adapter_name,
            adapter_version=adapter_version or self.adapter_version,
            freshness=freshness,
            response_status=response_status,
            evidence=evidence,
            access_method=access_method,
            provider=provider,
        )

    @abstractmethod
    def search(self, query: SourceQuery) -> list[SourceSearchResult]:
        """Searches the source catalog and returns candidate search hits."""
        pass

    @abstractmethod
    def retrieve(self, result: SourceSearchResult) -> SourceDocument:
        """Retrieves and normalizes the full authoritative source document."""
        pass

    def safe_http_fetch(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> tuple[int, str, dict[str, Any]]:
        """Performs SSRF-validated, size-capped HTTP GET request.
        
        Returns:
            (http_status_code, response_text, response_headers)
        Raises:
            SsrfError on restricted address
            httpx.HTTPError on network failure
            ValueError on size cap violation
        """
        # Validate root target URL
        safe_url = SsrfValidator.validate_or_raise(url)

        req_headers = {"User-Agent": DEFAULT_USER_AGENT}
        if headers:
            req_headers.update(headers)

        parsed_host = urlparse(safe_url).hostname or "external_source"
        self.rate_limiter.throttle(parsed_host)

        # Custom redirect validator to prevent SSRF through 30x redirects
        with httpx.Client(
            timeout=self.timeout,
            headers=req_headers,
            follow_redirects=False,
            verify=False
        ) as client:
            current_url = safe_url
            current_params = params
            redirect_count = 0
            max_redirects = 3

            while True:
                response = client.get(current_url, params=current_params)
                current_params = None  # only attach params to the first request

                if response.is_redirect:
                    redirect_count += 1
                    if redirect_count > max_redirects:
                        raise ValueError(f"Exceeded max redirects ({max_redirects}) for {url}")

                    location = response.headers.get("Location")
                    if not location:
                        break

                    # Resolve relative redirect if needed
                    redirect_url = str(response.url.join(location))
                    # Crucial: Validate redirect URL against SSRF
                    SsrfValidator.validate_or_raise(redirect_url)
                    current_url = redirect_url
                    continue

                break

            # Enforce size limit
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_SOURCE_DOC_BYTES:
                raise ValueError(f"Content length {content_length} exceeds 5MB limit")

            raw_bytes = response.content
            if len(raw_bytes) > MAX_SOURCE_DOC_BYTES:
                raise ValueError(f"Downloaded bytes {len(raw_bytes)} exceeds 5MB limit")

            text = response.text
            return response.status_code, text, dict(response.headers)

    def safe_http_post(
        self,
        url: str,
        json_body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> tuple[int, str, dict[str, Any]]:
        """Performs SSRF-validated, size-capped HTTP POST request."""
        safe_url = SsrfValidator.validate_or_raise(url)

        req_headers = {"User-Agent": DEFAULT_USER_AGENT, "Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        parsed_host = urlparse(safe_url).hostname or "external_source"
        self.rate_limiter.throttle(parsed_host)

        with httpx.Client(
            timeout=self.timeout,
            headers=req_headers,
            follow_redirects=False,
            verify=False
        ) as client:
            response = client.post(safe_url, json=json_body)

            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_SOURCE_DOC_BYTES:
                raise ValueError(f"Content length {content_length} exceeds 5MB limit")

            raw_bytes = response.content
            if len(raw_bytes) > MAX_SOURCE_DOC_BYTES:
                raise ValueError(f"Downloaded bytes {len(raw_bytes)} exceeds 5MB limit")

            return response.status_code, response.text, dict(response.headers)

    @staticmethod
    def compute_hash(text: str) -> str:
        """Computes SHA-256 hash of text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

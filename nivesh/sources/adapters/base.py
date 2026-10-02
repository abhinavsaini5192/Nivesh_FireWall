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
)
from nivesh.sources.ssrf import SsrfValidator, SsrfError
from nivesh.sources.cache import SourceCache
from nivesh.sources.rate_limiter import RateLimiter

MAX_SOURCE_DOC_BYTES = 5 * 1024 * 1024  # 5 MB limit
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_USER_AGENT = "NiveshFirewall-SourceEngine/1.0 (Authoritative Verification; +https://nivesh.internal)"


class BaseSourceAdapter(ABC):
    """Abstract base class for all authoritative data source adapters."""

    def __init__(
        self,
        cache: Optional[SourceCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        default_mode: RetrievalMode = "LIVE",
    ):
        self.cache = cache or SourceCache()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.timeout = timeout
        self.default_mode: RetrievalMode = default_mode

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

    @staticmethod
    def compute_hash(text: str) -> str:
        """Computes SHA-256 hash of text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

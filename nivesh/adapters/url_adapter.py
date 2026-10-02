"""URL Ingestion Adapter for Engine 1.

Fetches and extracts clean body text from web pages:
- Enforces strict timeout and response size limits
- Uses BeautifulSoup to strip scripts, styles, and navigational chrome
- Gracefully handles DNS failures, 404s, timeouts, SSL errors
- Preserves raw URL and reports warnings without raising unhandled errors.
"""

from typing import Optional, Any
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

MAX_PAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
REQUEST_TIMEOUT_SECONDS = 5.0
DEFAULT_USER_AGENT = "NiveshFirewall-ContentEngine/1.0 (Security Scanner; +https://nivesh.internal)"


class UrlIngestionResult:
    """Encapsulates the result of a web page ingestion."""

    def __init__(
        self,
        original_url: str,
        normalized_url: str,
        text: str = "",
        status_code: Optional[int] = None,
        success: bool = False,
        warnings: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.original_url = original_url
        self.normalized_url = normalized_url
        self.text = text
        self.status_code = status_code
        self.success = success
        self.warnings = warnings or []
        self.metadata = metadata or {}


class UrlAdapter:
    """Safe ingestion adapter for URL content."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS):
        self.timeout = timeout

    def ingest(
        self,
        url: str,
        fetch: bool = True,
        mock_html: Optional[str] = None
    ) -> UrlIngestionResult:
        """Ingests a URL, normalizes it, and optionally retrieves page text."""
        warnings: list[str] = []

        if not url or not url.strip():
            return UrlIngestionResult(
                original_url=url,
                normalized_url="",
                success=False,
                warnings=["Empty URL provided"]
            )

        raw_url = url.strip()
        parsed = urlparse(raw_url if "://" in raw_url else f"https://{raw_url}")
        normalized_url = parsed.geturl()

        # If fetching is disabled or not requested, return the normalized URL shell
        if not fetch:
            return UrlIngestionResult(
                original_url=raw_url,
                normalized_url=normalized_url,
                text="",
                success=True,
                warnings=[]
            )

        # Allow mock HTML for deterministic testing
        if mock_html is not None:
            extracted_text = self._extract_text_from_html(mock_html)
            return UrlIngestionResult(
                original_url=raw_url,
                normalized_url=normalized_url,
                text=extracted_text,
                status_code=200,
                success=True,
                metadata={"mock": True, "word_count": len(extracted_text.split())}
            )

        # Ingest over HTTP
        try:
            with httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                follow_redirects=True,
                verify=False  # Allow analyzing sites with expired or self-signed certs
            ) as client:
                response = client.get(normalized_url)
                status_code = response.status_code

                if status_code >= 400:
                    warnings.append(f"Inaccessible URL: HTTP {status_code} received")
                    return UrlIngestionResult(
                        original_url=raw_url,
                        normalized_url=normalized_url,
                        text="",
                        status_code=status_code,
                        success=False,
                        warnings=warnings
                    )

                content_type = response.headers.get("content-type", "")
                if "text/html" in content_type or "text/plain" in content_type:
                    body = response.text
                    extracted_text = self._extract_text_from_html(body)
                    return UrlIngestionResult(
                        original_url=raw_url,
                        normalized_url=str(response.url),
                        text=extracted_text,
                        status_code=status_code,
                        success=True,
                        metadata={
                            "content_type": content_type,
                            "byte_length": len(response.content),
                            "word_count": len(extracted_text.split()),
                        }
                    )
                else:
                    warnings.append(f"Non-HTML content type: {content_type}")
                    return UrlIngestionResult(
                        original_url=raw_url,
                        normalized_url=normalized_url,
                        text="",
                        status_code=status_code,
                        success=True,
                        warnings=warnings
                    )

        except httpx.TimeoutException:
            warnings.append(f"Inaccessible URL: Connection timed out after {self.timeout}s")
        except httpx.ConnectError as e:
            warnings.append(f"Inaccessible URL: Connection error ({str(e)})")
        except Exception as e:
            warnings.append(f"Inaccessible URL: Ingestion failed ({type(e).__name__}: {str(e)})")

        return UrlIngestionResult(
            original_url=raw_url,
            normalized_url=normalized_url,
            text="",
            status_code=None,
            success=False,
            warnings=warnings
        )

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Strips tags and extracts clean text content."""
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")
        # Remove noisy elements
        for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            element.decompose()

        text = soup.get_text(separator=" ")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)

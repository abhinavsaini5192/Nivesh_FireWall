"""NSE Data Provider Abstraction for NSEAdapter.

Phase 15.C.1: Conceptual Provider Boundary & Provenance Isolation.

Establishes explicit provider boundaries:
- OfficialAuthorizedProvider: Authorized exchange API product access (requires production credentials; LIVE_AUTHORIZED).
- PublicNSEProvider: Direct NSE-originated public endpoints via controlled SSRF-safe HTTP client (LIVE_PUBLIC).
- NSEPythonProvider: Optional third-party wrapper provider with sandbox & SSRF isolation (LIVE_PUBLIC, never LIVE_AUTHORIZED).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import logging
import time
from typing import Optional, Any
from urllib.parse import quote_plus

from nivesh.schemas.sources import RetrievalMode, RetrievalStatus
from nivesh.sources.ssrf import SsrfValidator, SsrfError

logger = logging.getLogger(__name__)

NSE_ANNOUNCEMENTS_ENDPOINT = "https://www.nseindia.com/api/corporate-announcements?index=equities"
NSE_ACTIONS_ENDPOINT = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
NSE_EVENTS_ENDPOINT = "https://www.nseindia.com/api/event-calendar"
NSE_RESULTS_ENDPOINT = "https://www.nseindia.com/api/corporates-financial-results?index=equities&period=Quarterly"
NSE_ANNUAL_REPORTS_ENDPOINT = "https://www.nseindia.com/api/annual-reports?index=cm&symbol="


class BaseNSEProvider(ABC):
    """Abstract interface for NSE data providers."""

    provider_name: str = "BaseNSEProvider"
    access_method: str = "GENERIC"
    default_success_mode: RetrievalMode = "LIVE_PUBLIC"
    source_authority: str = "National Stock Exchange of India"

    @abstractmethod
    def fetch_corporate_data(
        self,
        category: str,
        symbol: str,
        keywords: list[str]
    ) -> tuple[RetrievalStatus, Optional[dict[str, Any]], Optional[str]]:
        """Fetches and normalizes corporate data for a given category and symbol.
        
        Returns:
            (status, parsed_record_dict, error_message)
        """
        pass


class OfficialAuthorizedProvider(BaseNSEProvider):
    """Official authorized NSE API connector (requires production exchange subscription credentials)."""

    provider_name: str = "OfficialAuthorizedProvider"
    access_method: str = "NSE Authorized API"
    default_success_mode: RetrievalMode = "LIVE_AUTHORIZED"
    source_authority: str = "National Stock Exchange of India"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret

    def fetch_corporate_data(
        self,
        category: str,
        symbol: str,
        keywords: list[str]
    ) -> tuple[RetrievalStatus, Optional[dict[str, Any]], Optional[str]]:
        if not self.api_key:
            return (
                "CREDENTIALS_MISSING",
                None,
                "NSE API credentials missing (NSE_API_KEY unconfigured). Live exchange access requires legitimate production credentials."
            )
        # Production authorized API call would go here
        return ("SOURCE_UNAVAILABLE", None, "Official authorized exchange endpoint not configured in prototype.")


class PublicNSEProvider(BaseNSEProvider):
    """Direct connector to NSE-originated public REST endpoints using Nivesh's SSRF-safe HTTP client."""

    provider_name: str = "PublicNSEProvider"
    access_method: str = "NSE Public REST Endpoint"
    default_success_mode: RetrievalMode = "LIVE_PUBLIC"
    source_authority: str = "NSE-originated public endpoint"

    def __init__(self, safe_fetch_fn=None, timeout: float = 5.0):
        self.safe_fetch_fn = safe_fetch_fn
        self.timeout = timeout

    def fetch_corporate_data(
        self,
        category: str,
        symbol: str,
        keywords: list[str]
    ) -> tuple[RetrievalStatus, Optional[dict[str, Any]], Optional[str]]:
        endpoint = NSE_ACTIONS_ENDPOINT if category == "CORPORATE_ACTION" else NSE_ANNOUNCEMENTS_ENDPOINT
        try:
            # Validate URL against SSRF
            safe_url = SsrfValidator.validate_or_raise(endpoint)
            if self.safe_fetch_fn:
                code, text, _ = self.safe_fetch_fn(safe_url)
                if code == 200:
                    records = json.loads(text)
                    matched = self._find_matching_record(records, category, symbol, keywords)
                    if matched:
                        return ("SUCCESS", matched, None)
                    return ("NO_MATCH", None, None)
                elif code in (401, 403):
                    return ("ACCESS_UNAUTHORIZED", None, f"NSE edge protection blocked public request (HTTP {code})")
                elif code == 429:
                    return ("RATE_LIMITED", None, "NSE upstream rate limit exceeded")
                else:
                    return ("SOURCE_UNAVAILABLE", None, f"NSE upstream error HTTP {code}")
            return ("SOURCE_UNAVAILABLE", None, "Safe fetch client not configured")
        except SsrfError as e:
            return ("ACCESS_UNAUTHORIZED", None, f"SSRF validation blocked request: {e}")
        except Exception as e:
            return ("SOURCE_UNAVAILABLE", None, str(e))

    def _find_matching_record(self, raw_data: Any, category: str, symbol: str, keywords: list[str]) -> Optional[dict[str, Any]]:
        items = raw_data if isinstance(raw_data, list) else raw_data.get("data", [])
        for item in items:
            item_sym = (item.get("symbol") or item.get("sm_symbol") or "").upper().strip()
            item_comp = (item.get("companyName") or item.get("comp") or item.get("sm_name") or "").strip()
            if symbol and symbol != item_sym and symbol not in item_comp.upper():
                continue
            subject = str(item.get("desc") or item.get("subject") or item.get("attchmntText") or item.get("purpose") or "")
            text_to_check = (
                subject + " " +
                item_comp + " " +
                str(item.get("desc") or "") + " " +
                str(item.get("attchmntText") or "") + " " +
                str(item.get("bm_desc") or "")
            ).lower()
            if keywords and not any(kw.lower() in text_to_check for kw in keywords):
                continue
            return {
                "symbol": item_sym or symbol,
                "company_name": item_comp or symbol,
                "category": category,
                "subject": subject,
                "broadcast_date": item.get("an_dt") or item.get("caBroadcastDate") or item.get("date"),
                "accession_number": str(item.get("seq_id") or item.get("isin") or f"NSE-PUB-{int(time.time())}"),
                "details": f"NSE Official Disclosure: {subject} for {item_comp or item_sym}",
                "url": item.get("attchmntFile") or endpoint,
            }
        return None


class SecurityError(Exception):
    """Raised when an unsafe operational mode or security policy violation is detected."""
    pass


ALLOWED_NSE_HOSTS = frozenset({
    "nseindia.com",
    "www.nseindia.com",
    "archives.nseindia.com",
    "nsearchives.nseindia.com",
    "iislliveblob.niftyindices.com",
})
MAX_SOURCE_DOC_BYTES = 5 * 1024 * 1024  # 5 MB


class NSEPythonProvider(BaseNSEProvider):
    """Optional connector wrapping NSEPython library with strict sandboxing and SSRF enforcement.
    
    Security & Provenance Boundaries:
    1. NEVER assigns LIVE_AUTHORIZED (always LIVE_PUBLIC or offline state).
    2. Validates all target endpoints through SsrfValidator and HTTPS whitelist before execution.
    3. Blocks VPN mode, shell interpolation, and os.popen execution unconditionally.
    4. Handles missing package gracefully without crashing core Nivesh Firewall.
    5. Normalizes unofficial DataFrame/JSON representations into standard Nivesh records.
    """

    provider_name: str = "NSEPythonProvider"
    access_method: str = "NSEPython / NSE public endpoint"
    default_success_mode: RetrievalMode = "LIVE_PUBLIC"
    source_authority: str = "NSE-originated public endpoint"

    def __init__(self, timeout: float = 5.0, enforce_ssrf: bool = True, rate_limiter=None):
        self.timeout = timeout
        self.enforce_ssrf = enforce_ssrf
        self.rate_limiter = rate_limiter
        self._mode = "local"
        self._nsepython_module = None
        self._is_available = self._check_availability()
        self.enforce_safe_mode()

    def _check_availability(self) -> bool:
        """Dynamically checks if nsepython is importable without polluting core imports."""
        try:
            import nsepython  # noqa: F401
            self._nsepython_module = nsepython
            return True
        except ImportError:
            self._nsepython_module = None
            return False

    @property
    def is_available(self) -> bool:
        return self._is_available

    def enforce_safe_mode(self) -> None:
        """Strictly forbids unsafe execution modes (vpn mode, shell commands, os.popen)."""
        if self._mode != "local":
            raise SecurityError(f"Unsafe execution mode '{self._mode}' is strictly forbidden in Nivesh Firewall.")
        if self._nsepython_module:
            mod_mode = getattr(self._nsepython_module, "mode", "local")
            if isinstance(mod_mode, str) and mod_mode.lower() == "vpn":
                raise SecurityError(f"NSEPython unsafe mode '{mod_mode}' detected. Only 'local' safe mode is permitted.")
            rahu_mod = getattr(self._nsepython_module, "rahu", None)
            if rahu_mod and isinstance(getattr(rahu_mod, "mode", None), str) and getattr(rahu_mod, "mode").lower() == "vpn":
                raise SecurityError("NSEPython rahu submodule has non-local mode enabled.")

    def set_mode(self, mode: str) -> None:
        """Exposes mode setting; strictly forbids 'vpn' or non-local modes."""
        if str(mode).lower() != "local":
            raise SecurityError(f"Unsafe execution mode '{mode}' is forbidden in Nivesh Firewall. Only 'local' safe mode is permitted.")
        self._mode = "local"
        if self._nsepython_module and hasattr(self._nsepython_module, "mode"):
            self._nsepython_module.mode = "local"

    def validate_target_endpoint(self, url: str) -> str:
        """Validates that a URL is a legitimate public NSE endpoint and not an internal address."""
        if not self.enforce_ssrf:
            return url

        # 1. Require strict HTTPS
        if not url.lower().startswith("https://"):
            raise SsrfError(f"HTTPS is strictly required for authoritative NSE requests. Disallowed URL: {url}")

        # 2. General SSRF check (blocks 127.0.0.1, 10.0.0.0/8, 169.254.169.254, etc.)
        safe_url = SsrfValidator.validate_or_raise(url)

        # 3. Restrict host to allowed authoritative NSE domains
        from urllib.parse import urlparse
        hostname = (urlparse(safe_url).hostname or "").lower()
        if not any(hostname == d or hostname.endswith("." + d) for d in ALLOWED_NSE_HOSTS):
            raise SsrfError(f"NSEPythonProvider restricted to official NSE domains. Disallowed host: {hostname}")

        return safe_url

    def fetch_corporate_data(
        self,
        category: str,
        symbol: str,
        keywords: list[str]
    ) -> tuple[RetrievalStatus, Optional[dict[str, Any]], Optional[str]]:
        """Executes retrieval via NSEPython with SSRF safety and normalizes output."""
        if not self._is_available:
            return (
                "SOURCE_UNAVAILABLE",
                None,
                "Optional dependency 'nsepython' is not installed. To enable, install nsepython (GPLv3)."
            )

        # Validate operational safety
        try:
            self.enforce_safe_mode()
        except SecurityError as se:
            return ("ACCESS_UNAUTHORIZED", None, str(se))

        # Enforce rate limiting if configured
        if self.rate_limiter:
            try:
                self.rate_limiter.throttle("www.nseindia.com")
            except Exception:
                pass

        try:
            # Determine appropriate endpoint
            if category == "CORPORATE_ACTION":
                endpoint = NSE_ACTIONS_ENDPOINT
            elif category == "BOARD_MEETING":
                endpoint = NSE_EVENTS_ENDPOINT
            elif category == "FINANCIAL_RESULTS":
                endpoint = NSE_RESULTS_ENDPOINT
            else:
                endpoint = NSE_ANNOUNCEMENTS_ENDPOINT

            # Validate endpoint through SSRF firewall before invoking
            self.validate_target_endpoint(endpoint)

            # Invoke via nsepython.nsefetch with os.popen guard
            fetch_fn = getattr(self._nsepython_module, "nsefetch", None)
            if not callable(fetch_fn):
                return ("SOURCE_UNAVAILABLE", None, "nsepython does not export callable 'nsefetch'")

            # Guard against any os.popen shell execution during execution
            import os
            orig_popen = os.popen

            def _blocked_popen(*args, **kwargs):
                raise SecurityError("Shell execution via os.popen is strictly forbidden in Nivesh Firewall.")

            try:
                os.popen = _blocked_popen
                raw_output = fetch_fn(endpoint)
            finally:
                os.popen = orig_popen

            if not raw_output:
                return ("SOURCE_UNAVAILABLE", None, "Empty or unparseable response from NSE endpoint via nsepython")

            # Check response size bounds
            raw_str_len = len(str(raw_output))
            if raw_str_len > MAX_SOURCE_DOC_BYTES:
                return ("SOURCE_UNAVAILABLE", None, f"Response size ({raw_str_len} bytes) exceeds safety limit ({MAX_SOURCE_DOC_BYTES} bytes)")

            # In nsepython, pandas DataFrames are sometimes returned
            records: list[dict[str, Any]] = []
            if hasattr(raw_output, "to_dict"):
                records = raw_output.to_dict(orient="records")
            elif isinstance(raw_output, list):
                records = [r for r in raw_output if isinstance(r, dict)]
            elif isinstance(raw_output, dict):
                records = raw_output.get("data", [raw_output]) if "data" in raw_output else [raw_output]

            matched = self._normalize_and_match(records, category, symbol, keywords, endpoint)
            if matched:
                return ("SUCCESS", matched, None)
            return ("NO_MATCH", None, None)

        except SsrfError as e:
            return ("ACCESS_UNAUTHORIZED", None, f"Security violation: {e}")
        except SecurityError as e:
            return ("ACCESS_UNAUTHORIZED", None, f"Security violation: {e}")
        except Exception as e:
            logger.warning(f"NSEPythonProvider execution failed: {e}")
            return ("SOURCE_UNAVAILABLE", None, f"NSEPython execution error: {str(e)}")

    def _normalize_and_match(
        self,
        records: list[dict[str, Any]],
        category: str,
        symbol: str,
        keywords: list[str],
        source_url: str
    ) -> Optional[dict[str, Any]]:
        """Maps raw NSE records retrieved via NSEPython into standard normalized format."""
        symbol_upper = symbol.upper().strip() if symbol else ""

        for item in records:
            item_sym = str(item.get("symbol") or item.get("sm_symbol") or "").upper().strip()
            item_comp = str(item.get("companyName") or item.get("comp") or item.get("company") or item.get("sm_name") or "").strip()

            is_sym_match = (
                not symbol_upper
                or item_sym == symbol_upper
                or (symbol_upper and symbol_upper in item_comp.upper())
                or (item_sym and item_sym in symbol_upper)
            )
            if not is_sym_match:
                continue

            subject = str(
                item.get("desc")
                or item.get("subject")
                or item.get("purpose")
                or item.get("attchmntText")
                or item.get("resultDescription")
                or ""
            )
            combined_text = (
                subject + " " +
                item_comp + " " +
                str(item.get("desc") or "") + " " +
                str(item.get("attchmntText") or "") + " " +
                str(item.get("bm_desc") or "") + " " +
                str(item.get("resultDescription") or "")
            ).lower()
            if keywords and not any(kw.lower() in combined_text for kw in keywords):
                continue

            date_raw = str(
                item.get("an_dt")
                or item.get("exDate")
                or item.get("date")
                or item.get("broadCastDate")
                or item.get("filingDate")
                or ""
            )
            rec_id = str(
                item.get("seq_id")
                or item.get("seqNumber")
                or item.get("isin")
                or f"NSE-PY-{item_sym or symbol_upper}-{int(time.time())}"
            )
            attachment = item.get("attchmntFile") or item.get("resultDetailedDataLink") or source_url

            details = (
                f"NATIONAL STOCK EXCHANGE OF INDIA — PUBLIC CORPORATE DISCLOSURE (via NSEPython)\n"
                f"Company Symbol: {item_sym or symbol_upper}\n"
                f"Company Name: {item_comp or symbol_upper}\n"
                f"Filing Subject: {subject}\n"
                f"Broadcast/Event Date: {date_raw}\n"
                f"NSE Verification Reference: {rec_id}\n"
                f"Document Attachment: {attachment}\n"
                f"Source Authority: NSE-originated public endpoint"
            )

            return {
                "symbol": item_sym or symbol_upper,
                "company_name": item_comp or symbol_upper,
                "category": category,
                "subject": subject,
                "broadcast_date": date_raw,
                "accession_number": rec_id,
                "details": details,
                "url": attachment,
                "raw_fields": item,
            }

        return None

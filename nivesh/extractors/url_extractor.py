"""URL and domain extraction for Engine 1.

Extracts URLs from text, normalizes them, and parses domain structures:
- Preserves raw URL and normalized URL
- Extracts scheme, domain, effective domain, subdomain, port, path, query, fragment
- Handles bare domains (e.g., t.me/..., www..., bit.ly/...)
- Never evaluates whether a domain is legitimate or malicious.
"""

import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

from nivesh.schemas.normalized import UrlSignal, DomainSignal

# Comprehensive regex matching explicit URLs and common bare URLs
URL_PATTERN = re.compile(
    r"""(?xi)
    \b
    (?:
        # Explicit scheme
        (?:https?|ftp)://[^\s<>'"()]+
        |
        # Common domain patterns without scheme
        (?:www\d*|t\.me|telegram\.me|bit\.ly|tinyurl\.com|wa\.me)/[^\s<>'"()]+
        |
        (?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|org|net|edu|gov|io|co|in|ai|me|info|biz|vip|cc|xyz|top|app|online|tech|link|live|site|club|store|icu|buzz)(?::\d{1,5})?(?:/[^\s<>'"()]*)?
    )
    """
)

# Trailing punctuation to strip from extracted URLs
TRAILING_PUNCTUATION = re.compile(r"[.,;:!?)'\"\]>]+$")

# Known multi-part TLD suffixes (common in India and globally)
MULTI_PART_TLDS = {
    "co.in", "net.in", "org.in", "gen.in", "firm.in", "ind.in",
    "co.uk", "org.uk", "me.uk", "ltd.uk",
    "com.au", "net.au", "org.au",
    "com.sg", "edu.sg", "gov.in", "ac.in",
}


class UrlExtractor:
    """Extracts, normalizes, and decomposes URLs and domains."""

    def extract(self, text: str) -> tuple[list[UrlSignal], list[DomainSignal]]:
        """Extracts UrlSignals and DomainSignals from the text."""
        if not text:
            return [], []

        raw_matches = URL_PATTERN.findall(text)
        url_signals: list[UrlSignal] = []
        domain_signals: list[DomainSignal] = []
        seen_normalized_urls: set[str] = set()
        seen_domains: set[str] = set()

        for match in raw_matches:
            # Clean trailing punctuation
            original_url = TRAILING_PUNCTUATION.sub("", match.strip())
            if not original_url:
                continue

            # Ensure scheme for parsing
            parse_target = original_url
            has_scheme = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", original_url))
            if not has_scheme:
                parse_target = "https://" + original_url

            try:
                parsed = urlparse(parse_target)
            except Exception:
                continue

            scheme = parsed.scheme.lower() if has_scheme else "https"
            netloc = parsed.netloc.lower()

            # Separate host and port
            host = netloc
            port: Optional[int] = None
            if ":" in netloc:
                parts = netloc.split(":")
                host = parts[0]
                try:
                    port = int(parts[1])
                except ValueError:
                    port = None

            # Remove default ports
            if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
                port = None

            path = parsed.path if parsed.path else "/"
            query = parsed.query if parsed.query else None
            fragment = parsed.fragment if parsed.fragment else None

            # Construct normalized URL
            clean_netloc = host if port is None else f"{host}:{port}"
            normalized_url = urlunparse((
                scheme,
                clean_netloc,
                path,
                parsed.params,
                query or "",
                fragment or ""
            )).rstrip("/")

            if not normalized_url.startswith("http://") and not normalized_url.startswith("https://"):
                normalized_url = f"https://{normalized_url}"

            if normalized_url not in seen_normalized_urls:
                seen_normalized_urls.add(normalized_url)
                url_signal = UrlSignal(
                    original_url=original_url,
                    normalized_url=normalized_url,
                    scheme=scheme,
                    domain=host,
                    path=path,
                    query=query,
                    fragment=fragment,
                    port=port
                )
                url_signals.append(url_signal)

            # Domain extraction
            effective_domain, subdomain = self._extract_effective_domain(host)
            domain_key = f"{host}:{port}" if port else host

            if domain_key not in seen_domains and host:
                seen_domains.add(domain_key)
                domain_signals.append(DomainSignal(
                    domain=host,
                    effective_domain=effective_domain,
                    subdomain=subdomain,
                    port=port
                ))

        return url_signals, domain_signals

    @staticmethod
    def _extract_effective_domain(host: str) -> tuple[str, Optional[str]]:
        """Splits a host into effective domain and subdomain.
        
        Handles 'www.', multi-part TLDs (e.g. .co.in), and arbitrary subdomains.
        """
        if not host:
            return "", None

        # Remove www prefix if present
        clean_host = re.sub(r"^www\d*\.", "", host)
        labels = clean_host.split(".")

        if len(labels) <= 1:
            return clean_host, None

        # Check for two-part TLD like .co.in or .co.uk
        if len(labels) >= 3:
            potential_tld = f"{labels[-2]}.{labels[-1]}".lower()
            if potential_tld in MULTI_PART_TLDS:
                effective = ".".join(labels[-3:])
                subdomain = ".".join(labels[:-3]) if len(labels) > 3 else None
                return effective, subdomain

        # Standard TLD (e.g. .com, .net, .org)
        effective = ".".join(labels[-2:])
        subdomain = ".".join(labels[:-2]) if len(labels) > 2 else None
        return effective, subdomain

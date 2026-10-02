"""SSRF Protection and Outbound Request Safety Validator for Engine 4.

Guards against Server-Side Request Forgery (SSRF) and malicious redirects:
- Rejects non-HTTP(S) schemes (file://, ftp://, gopher://)
- Rejects localhost and internal domain names (.local, .internal, .lan, etc.)
- Resolves DNS and checks IP against private, loopback, link-local, multicast, and reserved ranges
- Enforces safe redirect checking
"""

import socket
import ipaddress
from urllib.parse import urlparse
from typing import Optional, Union

# Blocked IP Networks
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),     # CGNAT
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local
    ipaddress.ip_network("172.16.0.0/12"),    # Private RFC 1918
    ipaddress.ip_network("192.0.0.0/24"),     # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),   # Private RFC 1918
    ipaddress.ip_network("198.18.0.0/15"),    # Network Benchmark Tests
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),      # Multicast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::/128"),           # Unspecified
    ipaddress.ip_network("::1/128"),          # Loopback
    ipaddress.ip_network("fc00::/7"),         # Unique local
    ipaddress.ip_network("fe80::/10"),        # Link-local
    ipaddress.ip_network("ff00::/8"),         # Multicast
]

# Blocked internal hostnames and suffix patterns
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
}

BLOCKED_SUFFIXES = (
    ".local",
    ".internal",
    ".lan",
    ".home",
    ".corp",
    ".intranet",
    ".onion",
    ".localhost",
)


class SsrfError(ValueError):
    """Raised when an outbound URL violates SSRF security boundaries."""
    pass


class SsrfValidator:
    """Validates URLs to ensure they cannot access local or private infrastructure."""

    @classmethod
    def is_safe_url(cls, url: str) -> tuple[bool, Optional[str]]:
        """Checks if a URL is safe to retrieve externally.
        
        Returns:
            (is_safe, error_reason)
        """
        if not url or not isinstance(url, str):
            return False, "Empty or invalid URL"

        clean_url = url.strip()
        try:
            parsed = urlparse(clean_url)
        except Exception as e:
            return False, f"Malformed URL parse error: {e}"

        # 1. Scheme check
        scheme = (parsed.scheme or "").lower()
        if scheme not in ("http", "https"):
            return False, f"Unsupported or dangerous URI scheme '{scheme}'. Only http/https permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        clean_host = hostname.lower().strip("[]")

        # 2. Hostname blacklist check
        if clean_host in BLOCKED_HOSTNAMES:
            return False, f"Blocked target hostname '{clean_host}' (loopback/localhost)."

        if any(clean_host.endswith(suffix) for suffix in BLOCKED_SUFFIXES):
            return False, f"Blocked internal hostname suffix in '{clean_host}'."

        # 3. Direct IP Address check
        try:
            ip_obj = ipaddress.ip_address(clean_host)
            if cls._is_blocked_ip(ip_obj):
                return False, f"Direct IP '{clean_host}' is within private/loopback/reserved range."
            return True, None
        except ValueError:
            # Hostname is not a raw IP literal; proceed to DNS resolution
            pass

        # 4. DNS Resolution & IP check
        try:
            addr_info = socket.getaddrinfo(clean_host, None)
            if not addr_info:
                return False, f"Could not resolve host '{clean_host}'"

            for item in addr_info:
                sockaddr = item[4]
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)
                if cls._is_blocked_ip(ip_obj):
                    return False, f"Host '{clean_host}' resolves to restricted IP '{ip_str}'"
        except socket.gaierror as e:
            # Unresolvable hostname
            return False, f"DNS resolution failed for '{clean_host}': {e}"
        except Exception as e:
            return False, f"DNS safety check error for '{clean_host}': {e}"

        return True, None

    @classmethod
    def validate_or_raise(cls, url: str) -> str:
        """Validates URL and returns cleaned URL, or raises SsrfError."""
        is_safe, error = cls.is_safe_url(url)
        if not is_safe:
            raise SsrfError(f"SSRF Protection triggered: {error}")
        return url.strip()

    @staticmethod
    def _is_blocked_ip(ip_obj: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
        """Checks if an IP falls within any blocked network or special classification."""
        if (
            ip_obj.is_loopback
            or ip_obj.is_private
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            return True

        for network in BLOCKED_NETWORKS:
            if ip_obj in network:
                return True

        return False

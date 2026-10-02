"""Entity, Name, Domain, and Registration Normalizer for Engine 9.

Performs deterministic normalization while preserving original representations
for provenance. Avoids over-aggressive merging of person names.
"""

import re
import unicodedata
from typing import Optional
from urllib.parse import urlparse, parse_qs


class IdentityNormalizer:
    """Deterministic normalization utilities for entities, registrations, domains, and handles."""

    PERSON_TITLES = {
        "dr", "dr.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.",
        "ca", "ca.", "shri", "smt", "prof", "prof."
    }

    LEGAL_SUFFIX_MAP = {
        "private limited": "PVT LTD",
        "pvt ltd": "PVT LTD",
        "pvt. ltd.": "PVT LTD",
        "pvt. ltd": "PVT LTD",
        "pvt limited": "PVT LTD",
        "limited": "LTD",
        "ltd": "LTD",
        "ltd.": "LTD",
        "llp": "LLP",
        "l.l.p.": "LLP",
        "l.l.p": "LLP",
        "limited liability partnership": "LLP",
        "inc": "INC",
        "inc.": "INC",
        "incorporated": "INC",
        "corp": "CORP",
        "corp.": "CORP",
        "corporation": "CORP",
    }

    @classmethod
    def normalize_person_name(cls, name: str) -> str:
        """Normalizes a person's name for comparison without collapsing middle initials/names.
        
        'Rahul Sharma' != 'Rahul K Sharma' != 'Rahul Kumar Sharma'.
        """
        if not name:
            return ""
        # 1. Unicode NFKC normalization
        norm = unicodedata.normalize("NFKC", str(name)).strip()

        # 2. Split into tokens and remove titles/honorifics
        tokens = [t.strip(",.:;\"'()[]{}") for t in norm.split()]
        cleaned_tokens = [t for t in tokens if t.lower() not in cls.PERSON_TITLES and t]

        if not cleaned_tokens:
            return norm.lower()

        # 3. Standardize internal whitespace and lowercase
        return " ".join(cleaned_tokens).lower()

    @classmethod
    def normalize_org_name(cls, name: str) -> tuple[str, str]:
        """Normalizes an organization name.
        
        Returns:
            tuple[str, str]: (canonical_name, clean_legal_name)
            canonical_name has legal suffixes stripped for root matching.
            clean_legal_name preserves standard legal suffix (e.g. PVT LTD).
        """
        if not name:
            return "", ""
        norm = unicodedata.normalize("NFKC", str(name)).strip()
        tokens = norm.split()
        cleaned_str = " ".join(tokens)

        # Check for matching legal suffix
        lower_cleaned = cleaned_str.lower()
        matched_suffix_key = None
        for suffix_key in sorted(cls.LEGAL_SUFFIX_MAP.keys(), key=lambda s: len(s), reverse=True):
            pattern = r"(?:\b|_|\s)" + re.escape(suffix_key) + r"[\.\s]*$"
            if re.search(pattern, lower_cleaned):
                matched_suffix_key = suffix_key
                break

        if matched_suffix_key:
            pattern = r"(?:\b|_|\s)" + re.escape(matched_suffix_key) + r"[\.\s]*$"
            core_name = re.sub(pattern, "", cleaned_str, flags=re.IGNORECASE).strip()
            # Strip trailing commas/dots
            core_name = core_name.rstrip(",. ")
            std_suffix = cls.LEGAL_SUFFIX_MAP[matched_suffix_key]
            clean_legal = f"{core_name} {std_suffix}"
            canonical = core_name.upper()
        else:
            clean_legal = cleaned_str
            canonical = cleaned_str.upper()

        # Canonical stripping of non-alphanumeric except space
        canonical_clean = re.sub(r"[^\w\s]", "", canonical).strip()
        canonical_clean = " ".join(canonical_clean.split())

        return canonical_clean, clean_legal

    @classmethod
    def normalize_domain(cls, url_or_domain: str) -> tuple[str, str]:
        """Normalizes a URL or domain string.
        
        Returns:
            tuple[str, str]: (root_domain, full_host)
            Strips scheme, port, paths, query tracking parameters (utm_*, ref, etc.).
        """
        if not url_or_domain:
            return "", ""
        s = str(url_or_domain).strip().lower()

        # If bare domain or URL with scheme
        if "://" not in s:
            s_parsed = urlparse("http://" + s)
        else:
            s_parsed = urlparse(s)

        host = s_parsed.hostname or ""
        # Strip port if present
        host = host.split(":")[0].strip()

        # Remove leading www.
        if host.startswith("www."):
            host = host[4:]

        # Extract root domain (e.g. secure.abcsecurities.com -> abcsecurities.com)
        parts = host.split(".")
        if len(parts) >= 2:
            # Handle two-part TLDs (e.g. .co.in, .gov.in, .org.in, .com.au)
            if len(parts) >= 3 and parts[-2] in ("co", "gov", "org", "ac", "res", "nic", "net") and len(parts[-1]) == 2:
                root_domain = ".".join(parts[-3:])
            else:
                root_domain = ".".join(parts[-2:])
        else:
            root_domain = host

        return root_domain, host

    @classmethod
    def normalize_registration_id(cls, reg_id: str) -> str:
        """Normalizes a registration identifier for exact matching (e.g. SEBI INA000012345)."""
        if not reg_id:
            return ""
        norm = unicodedata.normalize("NFKC", str(reg_id)).upper().strip()
        # Remove common separators (hyphens, slashes, spaces)
        cleaned = re.sub(r"[\s\-\/]", "", norm)
        return cleaned

    @classmethod
    def normalize_social_handle(cls, handle_or_url: str, platform: Optional[str] = None) -> tuple[str, str]:
        """Normalizes a social channel/handle.
        
        Returns:
            tuple[str, str]: (platform, clean_handle)
        """
        if not handle_or_url:
            return platform or "unknown", ""
        s = str(handle_or_url).strip()

        # Detect platform from URL if present or fallback to parameter
        detected_plat = platform or "unknown"
        clean = s
        if "t.me/" in s.lower() or "telegram" in s.lower():
            detected_plat = "telegram"
            clean = re.sub(r"https?://(?:www\.)?t\.me/", "", s, flags=re.IGNORECASE)
        elif "chat.whatsapp.com/" in s.lower() or "wa.me/" in s.lower() or "whatsapp" in s.lower():
            detected_plat = "whatsapp"
            clean = re.sub(r"https?://(?:www\.)?chat\.whatsapp\.com/", "", s, flags=re.IGNORECASE)
            clean = re.sub(r"https?://(?:www\.)?wa\.me/", "", clean, flags=re.IGNORECASE)
        elif "twitter.com/" in s.lower() or "x.com/" in s.lower():
            detected_plat = "twitter"
            clean = re.sub(r"https?://(?:www\.)?(?:twitter|x)\.com/", "", s, flags=re.IGNORECASE)
        elif "instagram.com/" in s.lower():
            detected_plat = "instagram"
            clean = re.sub(r"https?://(?:www\.)?instagram\.com/", "", s, flags=re.IGNORECASE)
        elif "youtube.com/" in s.lower():
            detected_plat = "youtube"
            clean = re.sub(r"https?://(?:www\.)?youtube\.com/(?:c/|user/|@)?", "", s, flags=re.IGNORECASE)

        # Strip leading platform prefix like 'telegram:' or 'twitter:'
        for p in ("telegram", "whatsapp", "twitter", "x", "instagram", "youtube"):
            if clean.lower().startswith(f"{p}:"):
                detected_plat = p
                clean = clean[len(p)+1:]
                break

        # Strip query params, paths, leading @
        clean = clean.split("?")[0].split("/")[0].lstrip("@").strip().lower()
        return detected_plat, clean



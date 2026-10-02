"""Social handle extraction for Engine 1.

Detects social handles across platforms:
- @username (unknown platform)
- t.me/username, telegram.me/username (telegram)
- instagram.com/username (instagram)
- youtube.com/@username (youtube)
- twitter.com/username, x.com/username (twitter)
- wa.me/... (whatsapp)

Preserves raw match and normalized handle without asserting identity.
"""

import re
from typing import Literal
from nivesh.schemas.normalized import SocialHandleSignal

# Exclude matches embedded inside email addresses
EMAIL_GUARD_PATTERN = re.compile(r"[\w.-]+@[\w.-]+")

# Platform URL patterns
PLATFORM_PATTERNS: list[tuple[str, re.Pattern, Literal["telegram", "instagram", "youtube", "twitter", "whatsapp"]]] = [
    (
        "telegram",
        re.compile(r"(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(?:joinchat/)?([a-zA-Z0-9_]{3,32})\b", re.IGNORECASE),
        "telegram"
    ),
    (
        "instagram",
        re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)/?\b", re.IGNORECASE),
        "instagram"
    ),
    (
        "youtube",
        re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/(?:@|c/|user/)?([a-zA-Z0-9_.-]+)/?\b", re.IGNORECASE),
        "youtube"
    ),
    (
        "twitter",
        re.compile(r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})\b", re.IGNORECASE),
        "twitter"
    ),
    (
        "whatsapp",
        re.compile(r"(?:https?://)?(?:www\.)?wa\.me/([0-9+]+)\b", re.IGNORECASE),
        "whatsapp"
    ),
]

# Standalone @mention pattern (ensures not preceded by word char or dot to avoid email addresses)
GENERIC_HANDLE_PATTERN = re.compile(r"(?<![\w.-])@([a-zA-Z0-9_]{2,32})\b")


class SocialExtractor:
    """Extracts social media handles and channel references."""

    def extract(self, text: str) -> list[SocialHandleSignal]:
        """Extracts all social handles with platform identification."""
        if not text:
            return []

        results: list[SocialHandleSignal] = []
        seen_keys: set[tuple[str, str]] = set()

        # 1. Platform-specific URL handles
        for platform_name, pattern, platform_enum in PLATFORM_PATTERNS:
            for match in pattern.finditer(text):
                raw_match = match.group(0).rstrip("/")
                handle = match.group(1).lstrip("@").strip()
                # Exclude static paths
                if handle.lower() in {"about", "contact", "privacy", "terms", "explore", "watch", "channel", "playlist"}:
                    continue
                key = (platform_enum, handle.lower())
                if key not in seen_keys:
                    seen_keys.add(key)
                    results.append(SocialHandleSignal(
                        platform=platform_enum,
                        handle=handle,
                        raw=raw_match
                    ))

        # 2. Standalone @mentions (platform: unknown)
        # First remove email addresses from text slice consideration to avoid false matches
        text_without_emails = EMAIL_GUARD_PATTERN.sub(" ", text)

        for match in GENERIC_HANDLE_PATTERN.finditer(text_without_emails):
            raw_match = match.group(0)
            handle = match.group(1)
            key = ("unknown", handle.lower())
            if key not in seen_keys:
                seen_keys.add(key)
                results.append(SocialHandleSignal(
                    platform="unknown",
                    handle=handle,
                    raw=raw_match
                ))

        return results

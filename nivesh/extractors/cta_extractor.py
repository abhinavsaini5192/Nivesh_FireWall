"""Call-To-Action (CTA) extraction for Engine 1.

Detects explicit action requests without assessing risk or severity:
- Categories:
  - contact: 'contact me', 'contact rahul@example.com', 'dm me', 'call us'
  - click: 'click here', 'tap link', 'visit link'
  - join_channel: 'join our telegram vip group', 'join channel', 'join now'
  - download: 'download our app', 'download now'
  - install: 'install apk', 'install app'
  - upload: 'upload pan', 'upload aadhar', 'submit kyc'
  - credential_request: 'share otp', 'enter pin', 'send password'
  - payment: 'pay ₹5,000', 'send money', 'deposit fee'
  - transfer: 'transfer money', 'bank transfer'
  - share: 'forward to 5 friends', 'share with group'
  - unknown
"""

import re
from typing import Literal
from nivesh.schemas.normalized import CallToAction

CtaCategory = Literal[
    "contact",
    "click",
    "join_channel",
    "download",
    "install",
    "upload",
    "credential_request",
    "payment",
    "transfer",
    "share",
    "unknown"
]

# Category pattern definitions (regex + category)
CTA_RULES: list[tuple[re.Pattern, CtaCategory, float]] = [
    # Join channel / community
    (
        re.compile(
            r"""(?xi)\b(
                join\s+(?:our\s+)?(?:telegram|whatsapp|vip|free|premium|exclusive|trading)?\s*(?:vip\s+)?(?:group|channel|community|link)?|
                join\s+now|
                join\s+karein?|
                join\s+karo|
                subscribe\s+(?:now|to\s+channel)?
            )\b"""
        ),
        "join_channel",
        0.95
    ),
    # Download
    (
        re.compile(
            r"""(?xi)\b(
                download\s+(?:our\s+)?(?:app|apk|application|software|pdf|file)?(?:\s+now)?|
                download\s+karein?|
                download\s+karo|
                get\s+the\s+app
            )\b"""
        ),
        "download",
        0.95
    ),
    # Install
    (
        re.compile(
            r"""(?xi)\b(
                install\s+(?:apk|app|application|file|now)|
                install\s+karein?|
                install\s+karo
            )\b"""
        ),
        "install",
        0.95
    ),
    # Credential request
    (
        re.compile(
            r"""(?xi)\b(
                (?:share|send|provide|give|enter)\s+(?:your\s+)?(?:otp|pin|password|mpin|cvv|credentials?)|
                otp\s+(?:bhejo|bhejiye|share\s+karein)
            )\b"""
        ),
        "credential_request",
        0.98
    ),
    # Payment
    (
        re.compile(
            r"""(?xi)\b(
                pay\s+(?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?|
                pay\s+(?:now|fee|charges?|amount|money|advance)|
                make\s+(?:the\s+)?payment|
                send\s+(?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?|
                send\s+money|
                deposit\s+(?:money|funds?|fee|amount|(?:₹|rs\.?|inr|\$)?\s*[\d,]+)|
                paise\s+(?:bhejo|bhejiye|jama\s+karo)
            )\b"""
        ),
        "payment",
        0.95
    ),
    # Transfer
    (
        re.compile(
            r"""(?xi)\b(
                transfer\s+(?:funds?|money|amount|cash|to\s+account)|
                wire\s+money|
                bank\s+transfer
            )\b"""
        ),
        "transfer",
        0.92
    ),
    # Upload
    (
        re.compile(
            r"""(?xi)\b(
                upload\s+(?:your\s+)?(?:pan|aadhar|aadhaar|id|document|documents|kyc|photo)|
                submit\s+(?:your\s+)?(?:kyc|pan|documents?)|
                send\s+(?:your\s+)?(?:pan|aadhar|documents?)
            )\b"""
        ),
        "upload",
        0.95
    ),
    # Contact
    (
        re.compile(
            r"""(?xi)\b(
                contact\s+(?:me|us|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|on\s+whatsapp)?|
                dm\s+(?:me|us|for\s+details)?|
                reach\s+out\s+(?:to\s+us|to\s+me)?|
                call\s+(?:now|us|me)?|
                message\s+(?:me|us)?|
                chat\s+with\s+us|
                sampark\s+karein?
            )\b"""
        ),
        "contact",
        0.92
    ),
    # Click
    (
        re.compile(
            r"""(?xi)\b(
                click\s+(?:here|the\s+link|below|now|to\s+join|to\s+claim)|
                tap\s+(?:here|link|below|now)|
                visit\s+(?:link|our\s+website)
            )\b"""
        ),
        "click",
        0.90
    ),
    # Share
    (
        re.compile(
            r"""(?xi)\b(
                share\s+(?:with\s+friends|to\s+\d+\s+groups|this\s+link|this\s+message)|
                forward\s+(?:this\s+message|to\s+friends|to\s+groups)
            )\b"""
        ),
        "share",
        0.90
    ),
]


class CtaExtractor:
    """Extracts Call-To-Action (CTA) phrases and categorizes them."""

    def extract(self, text: str) -> list[CallToAction]:
        """Scans text for explicit action prompts and returns matched CallToAction objects."""
        if not text:
            return []

        results: list[CallToAction] = []
        seen_spans: list[tuple[int, int]] = []

        for pattern, category, confidence in CTA_RULES:
            for match in pattern.finditer(text):
                phrase = match.group(0).strip()
                start = match.start()
                end = match.end()

                # Check if this span is already covered by a longer/prior match
                if any(start < s[1] and end > s[0] for s in seen_spans):
                    continue

                seen_spans.append((start, end))
                results.append(CallToAction(
                    phrase=phrase,
                    category=category,
                    confidence=confidence,
                    span=[start, end]
                ))

        # Sort results by their position in text
        results.sort(key=lambda c: c.span[0] if c.span else 0)
        return results

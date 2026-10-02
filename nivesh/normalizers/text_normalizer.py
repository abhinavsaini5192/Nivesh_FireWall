"""Text normalization component for Engine 1.

Performs deterministic text normalization preserving the raw text while cleaning:
- Unicode compatibility & homoglyphs (NFKC, zero-width characters, smart quotes)
- Line breaks and whitespace formatting
- Repeated punctuation (e.g., '!!!!' -> '!')
- Obvious OCR artifacts (e.g. broken hyphenated line wraps, control characters)
"""

import re
import unicodedata
from typing import Optional

# Zero-width and invisible characters often injected to break keyword detectors
ZERO_WIDTH_CHARS = re.compile(r"[\u200B-\u200D\uFEFF\u2060\u00AD\u200E\u200F]")

# Smart quotes, apostrophes, dashes
QUOTE_REPLACEMENTS = {
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‛": "'",
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
    "«": '"',
    "»": '"',
    "–": "-",
    "—": "-",
    "−": "-",
    "‐": "-",
    "‑": "-",
}

# Control characters excluding standard newline and tab
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


class TextNormalizer:
    """Deterministic normalizer for input text."""

    def __init__(self):
        pass

    def normalize(self, text: Optional[str] = None) -> str:
        """Normalizes input text deterministically.
        
        Preserves natural casing while cleaning encoding, whitespace,
        repeated punctuation, and OCR line-break artifacts.
        """
        if not text:
            return ""

        # 1. Unicode NFKC normalization (unifies math bold/script/italics, fullwidth chars, ligatures)
        cleaned = unicodedata.normalize("NFKC", text)

        # 2. Strip zero-width & invisible characters
        cleaned = ZERO_WIDTH_CHARS.sub("", cleaned)

        # 3. Strip control characters
        cleaned = CONTROL_CHARS.sub("", cleaned)

        # 4. Standardize quotes, dashes
        for orig, replacement in QUOTE_REPLACEMENTS.items():
            cleaned = cleaned.replace(orig, replacement)

        # 5. Fix common OCR hyphenation across linebreaks (e.g., "inves-\ntor" -> "investor")
        cleaned = re.sub(r"(\b[A-Za-z]+)-\s*\n\s*([A-Za-z]+\b)", r"\1\2", cleaned)

        # 6. Normalize line breaks (\r\n and \r -> \n)
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # 7. Normalize whitespace per line (replace multiple spaces/tabs with single space)
        lines = cleaned.split("\n")
        normalized_lines = []
        for line in lines:
            line_clean = re.sub(r"[^\S\n]+", " ", line).strip()
            normalized_lines.append(line_clean)

        # 8. Collapse 3+ consecutive newlines down to 2
        joined = "\n".join(normalized_lines)
        joined = re.sub(r"\n{3,}", "\n\n", joined)

        # 9. Clean repeated punctuation (e.g. "!!!!" -> "!", "?????" -> "?", "....." -> "...")
        joined = re.sub(r"!{2,}", "!", joined)
        joined = re.sub(r"\?{2,}", "?", joined)
        joined = re.sub(r"\.{4,}", "...", joined)

        return joined.strip()

    @staticmethod
    def casefold(text: str) -> str:
        """Helper for case-insensitive matching without modifying text."""
        return text.casefold() if text else ""

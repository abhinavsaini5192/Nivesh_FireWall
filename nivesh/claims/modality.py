"""Linguistic modality and certainty language detection for Engine 2.

Determines the presentation strength of a candidate claim without assessing
risk, manipulation, or truth:
- assertion: definitive statement ('ABC is debt free', 'Guaranteed 40% returns')
- possibility: speculative/potential ('ABC may be debt free', 'could rise')
- prediction: forecast/future expectation ('ABC will reach ₹500', 'stock will double')
- opinion: personal viewpoint ('I think ABC is undervalued', 'in my view')
- conditional: dependent assertion ('If ABC receives funding, it may be debt free')
- question: interrogative form
"""

import re
from typing import Optional, Tuple
from nivesh.schemas.claims import ClaimModality, ModalityType

# Patterns for certainty language and modality types
OPINION_PATTERNS = [
    re.compile(r"\b(?:i\s+think|in\s+my\s+opinion|in\s+my\s+view|i\s+believe|i\s+feel|personally|to\s+me)\b", re.IGNORECASE),
    re.compile(r"\b(?:we\s+think|we\s+believe|we\s+expect|our\s+view)\b", re.IGNORECASE),
]

CONDITIONAL_PATTERNS = [
    re.compile(r"\b(?:if|unless|provided\s+that|assuming\s+that|in\s+case)\b", re.IGNORECASE),
]

POSSIBILITY_PATTERNS = [
    re.compile(r"\b(?:may|might|could|possibly|potential|potentially|perhaps|likely)\b", re.IGNORECASE),
]

PREDICTION_PATTERNS = [
    re.compile(r"\b(?:will\s+reach|will\s+double|will\s+grow|will\s+rise|will\s+fall|will\s+become|will\s+hit|target\s+price|projected\s+to|forecast\s+to|set\s+to|expected\s+to)\b", re.IGNORECASE),
    re.compile(r"\b(?:will\s+[a-z]+)\b", re.IGNORECASE),
]

ASSERTION_CERTAINTY_PATTERNS = [
    re.compile(r"\b(guaranteed|guarantee|definitely|certainly|surely|confirmed|officially|undoubtedly|proven|100%|sure\s+shot|pakka)\b", re.IGNORECASE),
]


class ModalityDetector:
    """Detects modality and certainty terms from claim text."""

    def detect(self, text: str) -> ClaimModality:
        """Determines modality type and extracts certainty phrasing."""
        if not text:
            return ClaimModality(type="assertion", certainty_language=None)

        clean = text.strip()

        # 1. Question
        if clean.endswith("?") or re.match(r"^(?:is|are|can|will|should|do|does)\s+", clean, re.IGNORECASE):
            return ClaimModality(type="question", certainty_language=None)

        # 2. Conditional
        for pat in CONDITIONAL_PATTERNS:
            match = pat.search(clean)
            if match:
                return ClaimModality(type="conditional", certainty_language=match.group(0))

        # 3. Opinion
        for pat in OPINION_PATTERNS:
            match = pat.search(clean)
            if match:
                return ClaimModality(type="opinion", certainty_language=match.group(0))

        # 4. Prediction
        for pat in PREDICTION_PATTERNS:
            match = pat.search(clean)
            if match:
                return ClaimModality(type="prediction", certainty_language=match.group(0))

        # 5. Possibility
        for pat in POSSIBILITY_PATTERNS:
            match = pat.search(clean)
            if match:
                return ClaimModality(type="possibility", certainty_language=match.group(0))

        # 6. Assertion with explicit certainty vocabulary
        for pat in ASSERTION_CERTAINTY_PATTERNS:
            match = pat.search(clean)
            if match:
                return ClaimModality(type="assertion", certainty_language=match.group(0))

        # Default factual assertion
        return ClaimModality(type="assertion", certainty_language=None)

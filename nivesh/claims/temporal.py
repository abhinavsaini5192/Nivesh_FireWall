"""Temporal context detection for Engine 2 claims.

Classifies claims into temporal frames without inferring absent dates:
- historical: past events, reported earnings ('reported ₹40 crore profit in FY2025', 'last year', 'was')
- current: ongoing states ('has ₹100 crore debt', 'is debt free', 'is SEBI registered')
- future: forecasts, forward projections ('will reach ₹500 next year', 'next month', 'target')
- unknown: unspecified temporal anchor
"""

import re
from typing import Optional
from nivesh.schemas.claims import TemporalContext, TemporalType

HISTORICAL_PATTERNS = [
    re.compile(r"\b(reported|achieved|generated|posted|announced|delivered|declared|recorded|was|were|had|prior|previous)\b", re.IGNORECASE),
    re.compile(r"\b(last\s+year|last\s+quarter|in\s+fy\d{2,4}|in\s+20\d{2}|in\s+19\d{2}|yesterday|historically|previously)\b", re.IGNORECASE),
    re.compile(r"\b(?:q[1-4]|fy\d{2,4})\b", re.IGNORECASE),
]

FUTURE_PATTERNS = [
    re.compile(r"\b(will|shall|upcoming|next\s+year|next\s+month|next\s+week|tomorrow|by\s+20\d{2}|target|projected|expected\s+to|forecast|in\s+the\s+future|coming\s+soon)\b", re.IGNORECASE),
]

CURRENT_PATTERNS = [
    re.compile(r"\b(is|are|has|carries|currently|now|today|presently|holds|maintains|stands\s+at)\b", re.IGNORECASE),
    re.compile(r"\b(sebi\s+registered|registered\s+advisor|debt\s+free|zero\s+debt)\b", re.IGNORECASE),
]

# Explicit year / date capture
DATE_REFERENCE_PATTERN = re.compile(
    r"\b(FY\s*\d{2,4}|20\d{2}|19\d{2}|Q[1-4]\s*(?:FY)?\d{2,4}|last\s+(?:year|month|quarter)|next\s+(?:year|month|quarter))\b",
    re.IGNORECASE
)


class TemporalDetector:
    """Detects temporal orientation and extracts explicit temporal indicators."""

    def detect(self, text: str, structured_dates: Optional[list[str]] = None) -> TemporalContext:
        """Determines temporal frame and returns populated TemporalContext."""
        if not text:
            return TemporalContext(type="unknown")

        clean = text.strip()
        matched_date_str: Optional[str] = None
        raw_temporal: Optional[str] = None

        # Check for explicit date tokens
        date_match = DATE_REFERENCE_PATTERN.search(clean)
        if date_match:
            raw_temporal = date_match.group(0)
            matched_date_str = raw_temporal

        if not matched_date_str and structured_dates:
            matched_date_str = structured_dates[0]

        # 1. Future checks
        for pat in FUTURE_PATTERNS:
            m = pat.search(clean)
            if m:
                return TemporalContext(
                    type="future",
                    date=matched_date_str,
                    raw_text=raw_temporal or m.group(0)
                )

        # 2. Historical checks
        for pat in HISTORICAL_PATTERNS:
            m = pat.search(clean)
            if m:
                return TemporalContext(
                    type="historical",
                    date=matched_date_str,
                    raw_text=raw_temporal or m.group(0)
                )

        # 3. Current checks
        for pat in CURRENT_PATTERNS:
            m = pat.search(clean)
            if m:
                return TemporalContext(
                    type="current",
                    date=matched_date_str,
                    raw_text=raw_temporal or m.group(0)
                )

        return TemporalContext(
            type="unknown",
            date=matched_date_str,
            raw_text=raw_temporal
        )

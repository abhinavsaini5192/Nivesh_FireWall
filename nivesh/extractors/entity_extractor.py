"""Entity extraction component for Engine 1.

Identifies mentioned:
- Regulators / institutions (SEBI, RBI, NSE, BSE, etc. with canonical expansions)
- People (e.g. 'Rahul Sharma')
- Organizations (e.g. 'ABC Investments', 'XYZ Ltd')
- Financial instruments (e.g. 'XYZ Ltd shares', 'mutual fund', 'bond')

Preserves:
- Exact text span
- Normalized entity name
- Entity type
- Confidence score
- Never asserts legitimacy or verification.
"""

import re
from typing import Optional
from nivesh.schemas.normalized import EntityItem, EntitiesContainer

# Canonical regulator lookup
REGULATORS_MAP: dict[str, str] = {
    "SEBI": "Securities and Exchange Board of India",
    "RBI": "Reserve Bank of India",
    "NSE": "National Stock Exchange of India",
    "BSE": "Bombay Stock Exchange",
    "IRDAI": "Insurance Regulatory and Development Authority of India",
    "PFRDA": "Pension Fund Regulatory and Development Authority",
    "AMFI": "Association of Mutual Funds in India",
    "SCORES": "SEBI Complaints Redress System",
    "MCX": "Multi Commodity Exchange of India",
    "NCDEX": "National Commodity & Derivatives Exchange",
    "FMC": "Forward Markets Commission",
    "SEC": "Securities and Exchange Commission",
}

# Known financial instruments & canonical forms
INSTRUMENTS_MAP: dict[str, str] = {
    "mutual fund": "Mutual Fund",
    "mutual funds": "Mutual Fund",
    "sip": "Systematic Investment Plan",
    "systematic investment plan": "Systematic Investment Plan",
    "ipo": "Initial Public Offering",
    "shares": "Equity Shares",
    "share": "Equity Shares",
    "stocks": "Stocks / Equities",
    "stock": "Stocks / Equities",
    "equity": "Equity",
    "derivative": "Derivatives",
    "derivatives": "Derivatives",
    "options": "Options Contract",
    "futures": "Futures Contract",
    "call option": "Call Option",
    "put option": "Put Option",
    "bond": "Bond",
    "bonds": "Bond",
    "debenture": "Debenture",
    "debentures": "Debenture",
    "fixed deposit": "Fixed Deposit",
    "fd": "Fixed Deposit",
    "recurring deposit": "Recurring Deposit",
    "rd": "Recurring Deposit",
    "sovereign gold bond": "Sovereign Gold Bond",
    "sgb": "Sovereign Gold Bond",
    "etf": "Exchange Traded Fund",
    "index fund": "Index Fund",
    "crypto": "Cryptocurrency",
    "cryptocurrency": "Cryptocurrency",
    "bitcoin": "Bitcoin",
}

# Honorifics and contextual titles preceding person names (title prefix is case-insensitive, name is case-sensitive)
PERSON_PREFIX_PATTERN = re.compile(
    r"\b(?i:advisor|adviser|analyst|expert|guru|trader|mentor|coach|dr\.?|mr\.?|ms\.?|mrs\.?|shri|smt|ca|cfa)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
)

# Common capitalized Indian and international 2-word person name pattern
GENERIC_PERSON_PATTERN = re.compile(
    r"\b([A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15})\b"
)

# Organization suffix patterns
ORG_SUFFIX_PATTERN = re.compile(
    r"""(?xi)
    \b([A-Z0-9][A-Za-z0-9&.\s]{1,30}?\s+
    (?:Investments?|Capital|Securities|Ventures|Broking|Wealth|Advisory|Asset\s+Management|AMC|Technologies|Fintech|Trading|Pvt\.?\s*Ltd\.?|Private\s+Limited|Ltd\.?|Limited|LLP|Corp\.?|Inc\.?))\b
    """
)

# Non-name words to reject from generic person matcher
REJECT_PERSON_WORDS = {
    "telegram", "whatsapp", "instagram", "youtube", "twitter", "google", "download",
    "join", "click", "contact", "registered", "advisor", "guaranteed", "returns",
    "market", "capital", "sebi", "investment", "investments", "financial",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "india", "jaipur", "delhi", "mumbai",
    "will", "guide", "shall", "can", "could", "would", "with", "from", "your", "their", "have", "been"
}


class EntityExtractor:
    """Deterministic, rules-based entity extractor with exact text span preservation."""

    def extract(self, text: str) -> EntitiesContainer:
        """Extracts people, organizations, regulators, and financial instruments."""
        if not text:
            return EntitiesContainer()

        regulators = self._extract_regulators(text)
        instruments = self._extract_instruments(text)
        organizations = self._extract_organizations(text)
        people = self._extract_people(text, exclude_spans=[r.span for r in regulators if r.span] + [o.span for o in organizations if o.span])

        return EntitiesContainer(
            people=people,
            organizations=organizations,
            regulators=regulators,
            financial_instruments=instruments,
        )

    def _extract_regulators(self, text: str) -> list[EntityItem]:
        """Identifies regulator and market institution mentions."""
        results: list[EntityItem] = []
        seen = set()

        for acronym, canonical in REGULATORS_MAP.items():
            pattern = re.compile(rf"\b{re.escape(acronym)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                raw = match.group(0)
                span = [match.start(), match.end()]
                key = (acronym.upper(), span[0])
                if key not in seen:
                    seen.add(key)
                    results.append(EntityItem(
                        text=raw,
                        normalized=canonical,
                        type="regulator",
                        confidence=0.99,
                        span=span,
                    ))

        return results

    def _extract_instruments(self, text: str) -> list[EntityItem]:
        """Identifies financial instruments."""
        results: list[EntityItem] = []
        seen_spans = set()

        # Sort instruments longest first
        sorted_keys = sorted(INSTRUMENTS_MAP.keys(), key=len, reverse=True)
        for key in sorted_keys:
            pattern = re.compile(rf"\b{re.escape(key)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                span = (match.start(), match.end())
                # Check for overlap
                if any(span[0] < s[1] and span[1] > s[0] for s in seen_spans):
                    continue
                seen_spans.add(span)
                results.append(EntityItem(
                    text=match.group(0),
                    normalized=INSTRUMENTS_MAP[key],
                    type="financial_instrument",
                    confidence=0.95,
                    span=[match.start(), match.end()],
                ))

        return results

    def _extract_organizations(self, text: str) -> list[EntityItem]:
        """Identifies commercial, corporate and advisory entities."""
        results: list[EntityItem] = []
        seen_spans = set()

        for match in ORG_SUFFIX_PATTERN.finditer(text):
            org_name = match.group(1).strip()
            span = (match.start(), match.end())
            # Basic validation
            words = org_name.split()
            if len(words) >= 2 and not any(w.lower() in {"join", "download", "pay"} for w in words):
                seen_spans.add(span)
                results.append(EntityItem(
                    text=org_name,
                    normalized=org_name,
                    type="organization",
                    confidence=0.90,
                    span=[match.start(), match.end()],
                ))

        return results

    def _extract_people(self, text: str, exclude_spans: Optional[list[list[int]]] = None) -> list[EntityItem]:
        """Identifies person names using context cues and proper noun patterns."""
        results: list[EntityItem] = []
        seen_names = set()
        occupied_spans: list[tuple[int, int]] = []
        if exclude_spans:
            occupied_spans.extend((s[0], s[1]) for s in exclude_spans if s and len(s) == 2)

        # 1. High-confidence contextual pattern: "advisor Rahul Sharma"
        for match in PERSON_PREFIX_PATTERN.finditer(text):
            name = match.group(1).strip()
            span_start = match.start(1)
            span_end = match.end(1)
            span = (span_start, span_end)

            if not self._is_valid_person_name(name):
                continue

            seen_names.add(name.lower())
            occupied_spans.append(span)
            results.append(EntityItem(
                text=name,
                normalized=name,
                type="person",
                confidence=0.96,
                span=[span_start, span_end],
            ))

        # 2. General capitalized two-word names
        for match in GENERIC_PERSON_PATTERN.finditer(text):
            name = match.group(1).strip()
            span = (match.start(), match.end())

            # Check overlap with existing entities
            if any(span[0] < s[1] and span[1] > s[0] for s in occupied_spans):
                continue

            if not self._is_valid_person_name(name):
                continue

            if name.lower() not in seen_names:
                seen_names.add(name.lower())
                occupied_spans.append(span)
                results.append(EntityItem(
                    text=name,
                    normalized=name,
                    type="person",
                    confidence=0.85,
                    span=[span[0], span[1]],
                ))

        return results

    @staticmethod
    def _is_valid_person_name(name: str) -> bool:
        """Filters out non-person words that happen to be capitalized."""
        words = name.split()
        if len(words) < 2 or len(words) > 3:
            return False
        for w in words:
            if w.lower() in REJECT_PERSON_WORDS:
                return False
            if len(w) < 2:
                return False
        return True

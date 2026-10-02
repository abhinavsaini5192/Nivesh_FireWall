"""Financial signal extraction for Engine 1.

Detects and extracts:
- Currency amounts (₹, Rs, INR, $, USD, EUR, etc., Indian numbering lakh/crore)
- Percentages (40%, 15.5 percent, etc.)
- Financial registration numbers (SEBI registration codes, GSTIN, CIN, PAN)
- Dates mentioned in financial context
- Financial terminology catalog (English + Hindi/Hinglish terms)
"""

import re
from typing import Optional
from nivesh.schemas.normalized import (
    CurrencyAmountSignal,
    PercentageSignal,
    RegistrationNumberSignal,
    DateSignal,
)

# Currency symbol mapping
CURRENCY_MAP = {
    "₹": "INR",
    "rs": "INR",
    "rs.": "INR",
    "inr": "INR",
    "rupees": "INR",
    "rupee": "INR",
    "$": "USD",
    "usd": "USD",
    "dollars": "USD",
    "dollar": "USD",
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    "¥": "JPY",
    "jpy": "JPY",
    "a$": "AUD",
    "aud": "AUD",
    "c$": "CAD",
    "cad": "CAD",
    "usdt": "USDT",
    "btc": "BTC",
    "eth": "ETH",
}

# Regex for currency amounts:
# Handles: ₹5,000, ₹ 5,000, Rs. 5,000, 5,000 INR, $100, 5000 rupees, 10 lakh, 1.5 crore
CURRENCY_PATTERN = re.compile(
    r"""(?xi)
    (?:
        # Prefix currency: ₹5,000 or Rs. 5000 or $100 or INR 5,000
        (?P<prefix_curr>₹|rs\.?|inr|\$|usd|€|eur|£|gbp|¥|jpy|usdt|btc|eth)
        \s*
        (?P<prefix_val>\d+(?:,\d{2,3})*(?:\.\d+)?)
        \s*
        (?P<prefix_multiplier>k|lac|lakh|lakhs|cr|crore|crores|m|million|b|billion)?
        \b
    )
    |
    (?:
        # Postfix currency or Indian multipliers: 5,000 INR or 5000 rupees or 10 lakh
        \b
        (?P<postfix_val>\d+(?:,\d{2,3})*(?:\.\d+)?)
        \s*
        (?P<postfix_multiplier>k|lac|lakh|lakhs|cr|crore|crores|m|million|b|billion)?
        \s*
        (?P<postfix_curr>₹|rs\.?|inr|rupees?|\$|usd|dollars?|€|eur|euros?|£|gbp|pounds?|¥|jpy|usdt|btc|eth)
        \b
    )
    |
    (?:
        # Explicit Indian unit without symbol: 5 lakh, 2.5 crore (financial context)
        \b
        (?P<unit_val>\d+(?:\.\d+)?)
        \s*
        (?P<unit_name>lac|lakh|lakhs|cr|crore|crores)
        \b
    )
    """
)

# Regex for percentages: 40%, 40 %, 40.5 percent, 10-15%, 40%!
PERCENTAGE_PATTERN = re.compile(
    r"""(?xi)
    (?<!\w)
    (?P<val>\d+(?:\.\d+)?)
    \s*
    (?P<unit>%|\bpercent(?:age)?\b)
    """
)

# Registration number patterns (SEBI, GSTIN, CIN, PAN)
REGISTRATION_PATTERNS = [
    (
        "SEBI",
        re.compile(r"\b(?:SEBI[\s:]+)?(IN[A-Z]{1,2}\d{8,10}|IN-DP-\d+)\b", re.IGNORECASE),
    ),
    (
        "SEBI",
        re.compile(r"\bSEBI\s*(?:Reg(?:istration)?\s*(?:No\.?|Number|#)\s*:?|Registration\s*:\s*)([A-Za-z0-9/-]{6,20})\b", re.IGNORECASE),
    ),
    (
        "GSTIN",
        re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b"),
    ),
    (
        "CIN",
        re.compile(r"\b[LUu]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b"),
    ),
    (
        "PAN",
        re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    ),
]

# Date patterns (DD/MM/YYYY, YYYY-MM-DD, DD-Mon-YYYY)
DATE_PATTERN = re.compile(
    r"""(?xi)
    \b
    (?:
        \d{4}[-/]\d{1,2}[-/]\d{1,2}
        |
        \d{1,2}[-/]\d{1,2}[-/]\d{2,4}
        |
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
        \s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}
    )
    \b
    """
)

# Multipliers
MULTIPLIERS = {
    "k": 1_000,
    "lac": 100_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "cr": 10_000_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
    "m": 1_000_000,
    "million": 1_000_000,
    "b": 1_000_000_000,
    "billion": 1_000_000_000,
}

# Financial vocabulary catalog (English + Hindi/Hinglish financial terms)
FINANCIAL_TERMS_CATALOG = [
    # Regulators & bodies
    "sebi", "nse", "bse", "rbi", "irdai", "pfrda", "amfi", "scores", "mcx", "ncdex",
    # Core investment terms
    "advisor", "adviser", "registered advisor", "sebi registered", "registered", "returns", "profit",
    "loss", "guaranteed", "guaranteed return", "guaranteed returns", "investment",
    "investments", "invest", "investor", "investing", "trading", "trader", "portfolio",
    "dividend", "bonus", "buyback", "nominee", "demat", "demat account", "kyc",
    "broker", "sub-broker", "sub broker", "brokerage", "margin", "leverage",
    # Channels & action terms related to financial offers
    "telegram", "vip group", "app", "pay", "payment",
    # Instruments
    "mutual fund", "mutual funds", "ipo", "equity", "share", "shares", "stock",
    "stocks", "derivative", "derivatives", "options", "futures", "intraday",
    "call option", "put option", "nifty", "banknifty", "sensex", "sip",
    "systematic investment plan", "index fund", "etf", "exchange traded fund",
    "debenture", "bond", "bonds", "sovereign gold bond", "sgb", "fixed deposit",
    "fd", "recurring deposit", "rd", "forex", "crypto", "bitcoin", "cryptocurrency",
    "arbitrage", "hedging", "capital gain", "nav", "asset management", "amc",
    "wealth management", "pms", "portfolio management service", "aif",
    # Actions & claims
    "multibagger", "jackpot call", "sure shot", "tips", "stock tips",
    "trading call", "target price", "stop loss", "stoploss", "stop-loss",
    # Hindi / Hinglish financial terms
    "nivesh", "munafa", "fayda", "kamai", "byaj", "bima", "paisa", "paise",
    "dhan", "rakam", "khata", "dhanrashi", "bachat"
]


class FinancialExtractor:
    """Extracts structured financial signals without evaluating legitimacy or risk."""

    def __init__(self):
        # Sort terms by length descending to match longest phrases first (e.g. "mutual fund" before "fund")
        sorted_terms = sorted(FINANCIAL_TERMS_CATALOG, key=len, reverse=True)
        # Build regex for word boundary matching
        pattern_str = r"\b(" + "|".join(re.escape(t) for t in sorted_terms) + r")\b"
        self._terms_regex = re.compile(pattern_str, re.IGNORECASE)

    def extract_currency_amounts(self, text: str) -> list[CurrencyAmountSignal]:
        """Extracts normalized currency amounts with currency code and raw span."""
        if not text:
            return []

        results: list[CurrencyAmountSignal] = []
        for match in CURRENCY_PATTERN.finditer(text):
            raw = match.group(0).strip()
            span = [match.start(), match.end()]

            # Determine value and currency
            prefix_curr = match.group("prefix_curr")
            postfix_curr = match.group("postfix_curr")
            unit_name = match.group("unit_name")

            currency_code = "INR"  # default for Indian market context
            multiplier = 1.0

            if prefix_curr:
                curr_key = prefix_curr.lower().strip(".:")
                currency_code = CURRENCY_MAP.get(curr_key, "INR")
                raw_num = match.group("prefix_val").replace(",", "")
                mult_key = (match.group("prefix_multiplier") or "").lower()
                if mult_key in MULTIPLIERS:
                    multiplier = MULTIPLIERS[mult_key]
                value = float(raw_num) * multiplier

            elif postfix_curr:
                curr_key = postfix_curr.lower().strip(".:")
                currency_code = CURRENCY_MAP.get(curr_key, "INR")
                raw_num = match.group("postfix_val").replace(",", "")
                mult_key = (match.group("postfix_multiplier") or "").lower()
                if mult_key in MULTIPLIERS:
                    multiplier = MULTIPLIERS[mult_key]
                value = float(raw_num) * multiplier

            elif unit_name:
                currency_code = "INR"
                raw_num = match.group("unit_val")
                mult_key = unit_name.lower()
                if mult_key in MULTIPLIERS:
                    multiplier = MULTIPLIERS[mult_key]
                value = float(raw_num) * multiplier
            else:
                continue

            results.append(CurrencyAmountSignal(
                value=round(value, 2),
                currency=currency_code,
                raw=raw,
                span=span
            ))

        return results

    def extract_percentages(self, text: str) -> list[PercentageSignal]:
        """Extracts percentages with numeric value and raw span."""
        if not text:
            return []

        results: list[PercentageSignal] = []
        for match in PERCENTAGE_PATTERN.finditer(text):
            raw = match.group(0).strip()
            span = [match.start(), match.end()]
            val_str = match.group("val")
            try:
                val = float(val_str)
                results.append(PercentageSignal(
                    value=val,
                    raw=raw,
                    span=span
                ))
            except ValueError:
                continue

        return results

    def extract_registration_numbers(self, text: str) -> list[RegistrationNumberSignal]:
        """Extracts formal financial/corporate registration numbers."""
        if not text:
            return []

        results: list[RegistrationNumberSignal] = []
        seen = set()

        for reg_type, pattern in REGISTRATION_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(0).strip()
                # If groups exist, take the captured value
                val = match.group(1).strip() if match.groups() else raw
                key = (reg_type, val.upper())
                if key not in seen:
                    seen.add(key)
                    results.append(RegistrationNumberSignal(
                        type=reg_type,
                        value=val.upper(),
                        raw=raw
                    ))

        return results

    def extract_dates(self, text: str) -> list[DateSignal]:
        """Extracts dates mentioned in text."""
        if not text:
            return []

        results: list[DateSignal] = []
        seen = set()

        for match in DATE_PATTERN.finditer(text):
            raw = match.group(0).strip()
            if raw not in seen:
                seen.add(raw)
                results.append(DateSignal(
                    value=raw,
                    raw=raw,
                    span=[match.start(), match.end()]
                ))

        return results

    def extract_financial_terms(self, text: str) -> list[str]:
        """Extracts matched financial vocabulary preserving distinct terms detected."""
        if not text:
            return []

        matches = self._terms_regex.findall(text)
        # Deduplicate while preserving order of occurrence
        seen = set()
        deduped: list[str] = []
        catalog_set = set(t.lower() for t in FINANCIAL_TERMS_CATALOG)

        for m in matches:
            term_clean = m.strip()
            lower = term_clean.lower()
            if lower not in seen:
                seen.add(lower)
                deduped.append(term_clean)

            # If multi-word phrase, also include recognized constituent financial terms
            if " " in term_clean:
                words = term_clean.split()
                for w in words:
                    w_lower = w.lower()
                    if w_lower in catalog_set and w_lower not in seen:
                        seen.add(w_lower)
                        deduped.append(w)

        return deduped

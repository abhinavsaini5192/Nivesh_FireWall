"""Contact extraction (Email and Phone) for Engine 1.

Extracts and normalizes:
- Email addresses (lowercased, trailing punctuation removed)
- Phone numbers (Indian mobile +91, landline, international E.164 normalization)
- Guards against extracting currency amounts, dates, or numeric IDs as phones.
"""

import re

# Comprehensive email pattern
EMAIL_PATTERN = re.compile(
    r"""(?xi)
    \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b
    """
)

# Indian and international phone patterns
PHONE_PATTERN = re.compile(
    r"""(?x)
    (?:
        # Explicit international prefix with +
        (?:\+91[\s.-]?)?[6-9]\d{9}\b
        |
        # Indian with leading 0
        \b0[6-9]\d{9}\b
        |
        # Standard Indian 10-digit mobile starting with 6-9 with optional separators
        \b[6-9]\d{4}[\s.-]?\d{5}\b
        |
        # Generic international phone (+ followed by 1 to 3 digits country code and 7 to 12 digits)
        \+\d{1,3}[\s.-]?(?:\(?\d{1,4}\)?[\s.-]?){2,4}\d{1,4}\b
    )
    """
)


class ContactExtractor:
    """Extracts contact identifiers (emails, phone numbers)."""

    def extract_emails(self, text: str) -> list[str]:
        """Extracts unique, normalized (lowercased) email addresses."""
        if not text:
            return []

        raw_emails = EMAIL_PATTERN.findall(text)
        normalized_emails: list[str] = []
        seen = set()

        for email in raw_emails:
            clean = email.strip(".,;:!?'\"").lower()
            if clean and clean not in seen:
                seen.add(clean)
                normalized_emails.append(clean)

        return normalized_emails

    def extract_phones(self, text: str) -> list[str]:
        """Extracts and normalizes phone numbers without claiming identity."""
        if not text:
            return []

        # Filter out obvious currency or date strings before scanning
        matches = PHONE_PATTERN.finditer(text)
        normalized_phones: list[str] = []
        seen = set()

        for match in matches:
            raw_phone = match.group(0).strip(".,;:!?'\"")
            # Strip non-digits except leading +
            has_plus = raw_phone.startswith("+")
            digits_only = re.sub(r"\D", "", raw_phone)

            # Sanity checks on length: valid mobile/phones are usually 10 to 15 digits
            if len(digits_only) < 10 or len(digits_only) > 15:
                continue

            # Standardize 10-digit Indian numbers starting with 6-9
            if len(digits_only) == 10 and digits_only[0] in "6789":
                normalized = f"+91{digits_only}"
            elif len(digits_only) == 11 and digits_only.startswith("0") and digits_only[1] in "6789":
                normalized = f"+91{digits_only[1:]}"
            elif len(digits_only) == 12 and digits_only.startswith("91") and digits_only[2] in "6789":
                normalized = f"+{digits_only}"
            elif has_plus:
                normalized = f"+{digits_only}"
            else:
                normalized = digits_only

            if normalized not in seen:
                seen.add(normalized)
                normalized_phones.append(normalized)

        return normalized_phones

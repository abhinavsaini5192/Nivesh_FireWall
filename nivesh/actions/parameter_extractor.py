"""Parameter extraction component for Engine 3.

Extracts structured financial, temporal, and situational parameters for actions.
Strictly enforces privacy safeguards:
- Never collects or stores raw passwords, PINs, or OTP values.
- Never retains complete sensitive banking or payment card credentials.
"""

import re
from typing import Any, Optional
from nivesh.schemas.actions import ActionType
from nivesh.schemas.normalized import NormalizedContent


class ActionParameterExtractor:
    """Extracts parameters from action text with strict privacy guards."""

    def extract_parameters(
        self,
        action_text: str,
        action_type: ActionType,
        content: Optional[NormalizedContent] = None,
    ) -> dict[str, Any]:
        """Extracts safe, non-sensitive parameters from the action snippet."""
        params: dict[str, Any] = {}
        clean = action_text.strip()
        lower = clean.lower()

        # 1. Financial amounts and currencies
        if action_type in {"PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY", "WITHDRAW_MONEY", "BUY", "SELL"}:
            # Check for currency amount in action text
            amt_match = re.search(r"(?:₹|rs\.?|inr|\$)\s*([\d,]+(?:\.\d+)?)\s*(crore|lakh)?", clean, re.IGNORECASE)
            if amt_match:
                raw_num = amt_match.group(1).replace(",", "")
                multiplier = 1.0
                unit = (amt_match.group(2) or "").lower()
                if unit == "lakh":
                    multiplier = 100000.0
                elif unit == "crore":
                    multiplier = 10000000.0
                try:
                    val = float(raw_num) * multiplier
                    curr = "USD" if "$" in amt_match.group(0) else "INR"
                    params["amount"] = val
                    params["currency"] = curr
                except ValueError:
                    pass
            elif content and content.structured_signals and content.structured_signals.currency_amounts:
                # Find matching currency amount from Engine 1
                for c_amt in content.structured_signals.currency_amounts:
                    if str(c_amt.value) in clean or c_amt.raw in clean:
                        params["amount"] = c_amt.value
                        params["currency"] = c_amt.currency
                        break

        # 2. Deadlines and time constraints
        deadline_match = re.search(r"\bbefore\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}\s*[ap]m)\b", lower)
        if deadline_match:
            params["deadline"] = deadline_match.group(1).strip().upper()

        timeframe_match = re.search(r"\bwithin\s+(\d+\s+(?:hours?|days?|minutes?))\b", lower)
        if timeframe_match:
            params["timeframe"] = timeframe_match.group(1).strip()

        if any(w in lower for w in ["immediately", "right now", "urgently", "hurry"]):
            params["urgency"] = "immediate"

        # 3. Privacy Safeguard Audit:
        # Strip any accidental secrets from params
        for sensitive_key in ["password", "otp", "pin", "cvv", "card_number", "secret"]:
            if sensitive_key in params:
                del params[sensitive_key]

        return params

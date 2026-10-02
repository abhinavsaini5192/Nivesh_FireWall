"""Financial relevance classification for Engine 1.

Conservative classifier determining whether content is finance-related.
- Clearly financial: True (e.g., 'Guaranteed 30% returns. Send ₹5,000.')
- Clearly unrelated: False (e.g., 'Best pizza near Jaipur.')
- Ambiguous: False (e.g., 'Rahul Sharma' alone)
- Strictly neutral: Never generates risk or scam judgments.
"""

from typing import Optional
from nivesh.schemas.normalized import (
    ContentFeatures,
    CurrencyAmountSignal,
    PercentageSignal,
    EntityItem,
    CallToAction,
)


class FinancialRelevanceClassifier:
    """Lightweight, conservative financial relevance classifier."""

    def classify(
        self,
        text: str,
        financial_terms: list[str],
        currency_amounts: list[CurrencyAmountSignal],
        percentages: list[PercentageSignal],
        regulators: list[EntityItem],
        instruments: list[EntityItem],
        ctas: list[CallToAction],
    ) -> ContentFeatures:
        """Evaluates financial relevance and returns populated ContentFeatures."""
        detected_signals: list[str] = []

        # 1. Financial terms found
        for term in financial_terms:
            detected_signals.append(term)

        # 2. Currency amounts found
        for curr in currency_amounts:
            detected_signals.append(curr.raw)

        # 3. Regulators found
        for reg in regulators:
            if reg.text not in detected_signals:
                detected_signals.append(reg.text)

        # 4. Instruments found
        for inst in instruments:
            if inst.text not in detected_signals:
                detected_signals.append(inst.text)

        # 5. Percentages found (if in context)
        for pct in percentages:
            detected_signals.append(pct.raw)

        # Unique detected list preserving order
        seen = set()
        unique_detected: list[str] = []
        for s in detected_signals:
            low = s.lower()
            if low not in seen:
                seen.add(low)
                unique_detected.append(s)

        # Conservative Decision Logic:
        # We need genuine financial signals.
        has_currency = len(currency_amounts) > 0
        has_regulator = len(regulators) > 0
        has_instrument = len(instruments) > 0
        has_terms = len(financial_terms) > 0

        # Discard generic terms that might appear in normal life if isolated
        strong_terms = [
            t for t in financial_terms
            if t.lower() not in {"tips", "group", "call", "bonus"}
        ]

        is_financial = False
        confidence = 0.90

        if has_regulator or has_instrument or has_currency or len(strong_terms) >= 1:
            is_financial = True
            score = 0.85 + min(0.14, len(unique_detected) * 0.03)
            confidence = round(score, 2)
        elif len(percentages) > 0 and len(financial_terms) > 0:
            is_financial = True
            confidence = 0.92
        else:
            # Conservative: ambiguous or clearly non-financial
            is_financial = False
            confidence = 0.95 if not text or len(text.split()) > 2 else 0.75

        call_to_action_present = len(ctas) > 0

        return ContentFeatures(
            contains_financial_content=is_financial,
            confidence=confidence,
            financial_terms_detected=unique_detected if is_financial else [],
            call_to_action_present=call_to_action_present,
            calls_to_action=ctas,
        )

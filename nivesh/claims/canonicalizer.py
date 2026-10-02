"""Canonicalizer and Fingerprint generation component for Engine 2.

Transforms candidate assertion text and Engine 1 structured signals into
canonical Subject-Predicate-Object structures, assigning standard claim types,
canonicalizing equivalent assertions (e.g. 'zero debt' == 'debt free'),
and generating deterministic fingerprints for Engine 8.
"""

import re
from typing import Optional, Any
from nivesh.schemas.claims import (
    CanonicalClaim,
    ClaimText,
    ClaimType,
    SourceSpan,
)
from nivesh.claims.modality import ModalityDetector
from nivesh.claims.temporal import TemporalDetector
from nivesh.claims.verification_reqs import VerificationRequirementsGenerator

# Canonical mapping rules: (regex pattern, claim_type, predicate, subject_group, object_group, canonical_obj)
CANONICAL_PATTERNS = [
    # Debt-free variations (XYZ is debt free / zero debt / carries no debt)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+(?:is\s+debt\s*free|has\s+(?:zero|no|0)\s+debt|carries\s+no\s+debt|is\s+free\s+of\s+debt)\b", re.IGNORECASE),
        "FINANCIAL",
        "HAS_DEBT",
        1,  # subject
        None,
        "0"  # canonical object
    ),
    # Explicit debt amounts (ABC has ₹100 crore debt)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+has\s+((?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?\s*(?:crore|lakh|million|billion)?)\s+debt\b", re.IGNORECASE),
        "FINANCIAL",
        "HAS_DEBT",
        1,
        2,
        None
    ),
    # Regulatory registration (Rahul Sharma is a SEBI registered advisor / Rahul Sharma is SEBI registered)
    (
        re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+is\s+(?:a\s+)?(SEBI|RBI|NSE|BSE)\s+registered(?:\s+(advisor|adviser|analyst|broker|representative))?\b", re.IGNORECASE),
        "REGULATORY",
        "REGISTERED_WITH",
        1,
        2,
        None
    ),
    # Reverse regulatory registration (SEBI registered advisor Rahul Sharma)
    (
        re.compile(r"\b(SEBI|RBI|NSE|BSE)\s+registered\s+(?:advisor|adviser|analyst|broker|representative)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", re.IGNORECASE),
        "REGULATORY",
        "REGISTERED_WITH",
        2,  # subject is name
        1,  # object is regulator
        None
    ),
    # Official approval (SEBI approved XYZ / ABC is officially approved)
    (
        re.compile(r"\b(SEBI|RBI|NSE|BSE)\s+(?:has\s+)?approved\s+([A-Za-z0-9&.\s]{1,30})\b", re.IGNORECASE),
        "REGULATORY",
        "OFFICIALLY_APPROVED",
        2,  # subject is company/group
        1,  # object is regulator
        None
    ),
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+is\s+(?:officially\s+)?approved(?:\s+by\s+(SEBI|RBI|NSE|BSE))?\b", re.IGNORECASE),
        "REGULATORY",
        "OFFICIALLY_APPROVED",
        1,
        2,
        "SEBI"  # default regulator if not explicit
    ),
    # Return guarantees (Guaranteed 40% returns / 40% returns are guaranteed / guarantees 40% returns)
    (
        re.compile(r"\b(?:guaranteed|guarantees)\s+(\d+(?:\.\d+)?\s*%(?:\s+returns?)?)\b", re.IGNORECASE),
        "FINANCIAL",
        "GUARANTEED_RETURN",
        None,
        1,
        None
    ),
    (
        re.compile(r"\b(\d+(?:\.\d+)?\s*%)\s+returns?\s+(?:are\s+)?guaranteed\b", re.IGNORECASE),
        "FINANCIAL",
        "GUARANTEED_RETURN",
        None,
        1,
        None
    ),
    # Corporate events: Bonus (ABC announced a 1:1 bonus)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+announced\s+(?:a\s+)?(\d+:\d+)\s+bonus\b", re.IGNORECASE),
        "CORPORATE_EVENT",
        "ANNOUNCED_BONUS",
        1,
        2,
        None
    ),
    # Corporate events: Dividend (ABC announced dividend of ₹10)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+announced\s+dividend\s+(?:of\s+)?((?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?)\b", re.IGNORECASE),
        "CORPORATE_EVENT",
        "ANNOUNCED_DIVIDEND",
        1,
        2,
        None
    ),
    # Financial metrics: Reported profit (XYZ reported ₹40 crore profit in FY2025)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+reported\s+((?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?\s*(?:crore|lakh|million|billion)?)\s+profit\b", re.IGNORECASE),
        "FINANCIAL",
        "REPORTED_PROFIT",
        1,
        2,
        None
    ),
    # Financial metrics: Reported revenue (ABC reported ₹50 crore revenue)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+reported\s+((?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?\s*(?:crore|lakh|million|billion)?)\s+revenue\b", re.IGNORECASE),
        "FACTUAL",
        "REPORTED_REVENUE",
        1,
        2,
        None
    ),
    # Price predictions (ABC will reach ₹500 next year / stock will reach ₹500)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+will\s+reach\s+((?:₹|rs\.?|inr|\$)?\s*[\d,]+(?:\.\d+)?)\b", re.IGNORECASE),
        "PREDICTION",
        "REACH_PRICE",
        1,
        2,
        None
    ),
    # Growth predictions (revenue increased 40% / company will double)
    (
        re.compile(r"\b(revenue|profit|sales|earnings)\s+increased\s+(?:by\s+)?(\d+(?:\.\d+)?\s*%)", re.IGNORECASE),
        "FINANCIAL",
        "INCREASED",
        1,
        2,
        None
    ),
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+will\s+double\b", re.IGNORECASE),
        "PREDICTION",
        "GROWTH_PREDICTION",
        1,
        None,
        "double"
    ),
    # Opinions: Undervalued / Overvalued (I think ABC is undervalued)
    (
        re.compile(r"\b(?:i\s+think|in\s+my\s+view)?\s*([A-Za-z0-9&.\s]{1,30}?)\s+is\s+(undervalued|overvalued|a\s+multibagger)\b", re.IGNORECASE),
        "OPINION",
        "VALUATION_STATUS",
        1,
        2,
        None
    ),
    # Recommendations (You should invest in ABC / Recommend ABC)
    (
        re.compile(r"\b(?:you\s+should\s+invest\s+in|recommend\s+buying|strong\s+buy\s+on)\s+([A-Za-z0-9&.\s]{1,30})\b", re.IGNORECASE),
        "RECOMMENDATION",
        "RECOMMENDS_INVESTMENT",
        1,
        1,
        None
    ),
    # Promotional (ABC is a once-in-a-lifetime opportunity)
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+is\s+(?:a\s+)?(once-in-a-lifetime\s+opportunity|risk-free\s+jackpot|guaranteed\s+wealth)\b", re.IGNORECASE),
        "PROMOTIONAL",
        "PROMOTIONAL_CLAIM",
        1,
        2,
        None
    ),
]


class ClaimCanonicalizer:
    """Standardizes candidate assertions into canonical Subject-Predicate-Object representations."""

    def __init__(self):
        self.modality_detector = ModalityDetector()
        self.temporal_detector = TemporalDetector()
        self.verification_gen = VerificationRequirementsGenerator()

    def canonicalize(
        self,
        candidate_text: str,
        source_span: SourceSpan,
        source_content_id: str,
        claim_index: int,
        context_entities: Optional[list[str]] = None,
        context_numbers: Optional[list[str]] = None,
    ) -> Optional[CanonicalClaim]:
        """Attempts to structure and canonicalize candidate text into a CanonicalClaim."""
        clean = candidate_text.strip().rstrip(".!?")
        if not clean:
            return None

        # Detect modality and temporal framing
        modality = self.modality_detector.detect(clean)
        temporal = self.temporal_detector.detect(clean)

        matched_claim: Optional[CanonicalClaim] = None

        # 1. Match against deterministic canonical patterns
        for pattern, claim_type, predicate, subj_idx, obj_idx, canonical_obj in CANONICAL_PATTERNS:
            m = pattern.search(clean)
            if m:
                # Extract subject
                if subj_idx is not None and subj_idx <= len(m.groups()):
                    subject = m.group(subj_idx).strip()
                elif context_entities:
                    subject = context_entities[0]
                else:
                    subject = "returns" if "RETURN" in predicate else "entity"

                # Extract object
                if canonical_obj is not None:
                    obj = canonical_obj
                elif obj_idx is not None and obj_idx <= len(m.groups()):
                    obj = m.group(obj_idx).strip()
                else:
                    obj = None

                # Clean subject
                subject = re.sub(r"^(?:that|says|therefore|and)\s+", "", subject, flags=re.IGNORECASE).strip()
                if not subject:
                    subject = "entity"

                # Standardize normalized sentence
                normalized_sentence = self._format_normalized_sentence(subject, predicate, obj, claim_type)

                # Verification requirements
                reqs = self.verification_gen.generate(
                    claim_type=claim_type,
                    predicate=predicate,
                    subject=subject,
                    obj=obj,
                    temporal_type=temporal.type,
                    modality_type=modality.type
                )

                fingerprint = self._build_fingerprint(subject, predicate, obj, temporal.type, modality.type)

                claim_id = f"CLAIM-{claim_index:03d}"
                return CanonicalClaim(
                    claim_id=claim_id,
                    source_content_id=source_content_id,
                    text=ClaimText(original=candidate_text.strip(), normalized=normalized_sentence),
                    claim_type=claim_type,
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    attributes={"pattern_matched": True},
                    temporal_context=temporal,
                    modality=modality,
                    source_span=source_span,
                    confidence=0.95,
                    canonical_fingerprint=fingerprint,
                    verification_requirements=reqs,
                )

        # 2. Heuristic fallback for other assertions
        return self._heuristic_fallback(
            clean,
            source_span,
            source_content_id,
            claim_index,
            modality,
            temporal,
            context_entities
        )

    def _heuristic_fallback(
        self,
        text: str,
        span: SourceSpan,
        content_id: str,
        index: int,
        modality,
        temporal,
        entities: Optional[list[str]],
    ) -> Optional[CanonicalClaim]:
        """Provides generalized fallback for claims not fitting strict regex patterns."""
        # Determine fallback claim type
        claim_type: ClaimType = "UNKNOWN"
        if modality.type == "opinion":
            claim_type = "OPINION"
        elif modality.type == "prediction" or temporal.type == "future":
            claim_type = "PREDICTION"
        elif any(w in text.lower() for w in ["return", "profit", "invest", "bonus", "dividend", "debt"]):
            claim_type = "FINANCIAL"
        elif any(w in text.lower() for w in ["approved", "licensed", "registered", "sebi", "rbi"]):
            claim_type = "REGULATORY"
        else:
            claim_type = "FACTUAL"

        # Extract subject from first words or entity
        words = text.split()
        if not words:
            return None

        subject = entities[0] if entities else words[0]
        predicate = "ASSERTS"
        obj = " ".join(words[1:]) if len(words) > 1 else None

        normalized_sentence = text
        reqs = self.verification_gen.generate(
            claim_type=claim_type,
            predicate=predicate,
            subject=subject,
            obj=obj,
            temporal_type=temporal.type,
            modality_type=modality.type
        )
        fingerprint = self._build_fingerprint(subject, predicate, obj, temporal.type, modality.type)

        return CanonicalClaim(
            claim_id=f"CLAIM-{index:03d}",
            source_content_id=content_id,
            text=ClaimText(original=text, normalized=normalized_sentence),
            claim_type=claim_type,
            subject=subject,
            predicate=predicate,
            object=obj,
            attributes={"heuristic": True},
            temporal_context=temporal,
            modality=modality,
            source_span=span,
            confidence=0.75,
            canonical_fingerprint=fingerprint,
            verification_requirements=reqs,
        )

    @staticmethod
    def _format_normalized_sentence(subject: str, predicate: str, obj: Optional[str], claim_type: str) -> str:
        """Constructs a clean, canonical English statement."""
        if predicate == "REGISTERED_WITH":
            return f"{subject} is registered with {obj or 'regulator'}."
        elif predicate == "HAS_DEBT":
            if obj in {"0", "zero", "no debt"}:
                return f"{subject} is debt free."
            return f"{subject} has {obj} debt."
        elif predicate == "GUARANTEED_RETURN":
            clean_val = re.sub(r"\s+returns?$", "", obj or "", flags=re.IGNORECASE).strip()
            return f"{clean_val or 'High'} returns are guaranteed."
        elif predicate == "OFFICIALLY_APPROVED":
            return f"{subject} is officially approved by {obj or 'regulator'}."
        elif predicate == "ANNOUNCED_BONUS":
            return f"{subject} announced a {obj} bonus."
        elif predicate == "REPORTED_PROFIT":
            return f"{subject} reported {obj} profit."
        elif predicate == "REPORTED_REVENUE":
            return f"{subject} reported {obj} revenue."
        elif predicate == "REACH_PRICE":
            return f"{subject} will reach price of {obj}."
        elif predicate == "VALUATION_STATUS":
            return f"{subject} is {obj}."
        elif predicate == "RECOMMENDS_INVESTMENT":
            return f"Investment in {subject} is recommended."
        return f"{subject} {predicate.lower().replace('_', ' ')} {obj or ''}".strip() + "."

    @staticmethod
    def _build_fingerprint(subject: str, predicate: str, obj: Optional[str], temporal: str, modality: str) -> str:
        """Builds a deterministic canonical fingerprint for Engine 8."""
        s = re.sub(r"[^\w]", "_", subject.strip().upper())
        p = predicate.strip().upper()
        o = re.sub(r"[^\w]", "_", (obj or "NONE").strip().upper())
        t = temporal.strip().upper()
        m = modality.strip().upper()
        return f"ENTITY:{s}|PREDICATE:{p}|OBJECT:{o}|TEMPORAL:{t}|MODALITY:{m}"

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
    ClaimAttribution,
)
from nivesh.claims.modality import ModalityDetector
from nivesh.claims.temporal import TemporalDetector
from nivesh.claims.verification_reqs import VerificationRequirementsGenerator

# Explicit attribution prefix patterns
ATTRIBUTION_PATTERNS = [
    re.compile(r"^\s*According\s+to\s+([A-Za-z0-9&.\s]{1,40}?)(?:,\s*|:\s*|\s+that\s+)\s*(.+)$", re.IGNORECASE),
    re.compile(r"^\s*([A-Za-z0-9&.\s]{1,40}?)\s+(?:says|claims|stated|states)(?:\s+that|:|,)?\s+(.+)$", re.IGNORECASE),
]

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
    # Explicit guarantor / offeror return promises
    # e.g. "Rahul Sharma guarantees 40% returns", "This investment guarantees 40% returns",
    # "ABC Investments offers guaranteed 40% returns"
    (
        re.compile(r"\b([A-Za-z0-9&.\s]{1,40}?)\s+(?:guarantees|offers\s+guaranteed|provides\s+guaranteed|promises\s+guaranteed)\s+(\d+(?:\.\d+)?\s*%(?:\s+returns?)?)\b", re.IGNORECASE),
        "FINANCIAL",
        "GUARANTEED_RETURN",
        1,
        2,
        None
    ),
    # Passive or impersonal guaranteed returns (no explicit subject attached in sentence)
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
        re.compile(r"\b([A-Za-z0-9&.\s]{1,30}?)\s+(?:announced|approved|declared)\s+(?:a\s+)?(?:massive\s+)?(\d+:\d+)\s+bonus\b", re.IGNORECASE),
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

        # Check for explicit speaker attribution prefix (e.g. "According to Rahul Sharma, ...")
        attribution: Optional[ClaimAttribution] = None
        statement_text = clean
        for attr_pat in ATTRIBUTION_PATTERNS:
            attr_m = attr_pat.match(clean)
            if attr_m:
                attr_entity = attr_m.group(1).strip()
                statement_text = attr_m.group(2).strip()
                # Determine entity type
                org_keywords = ["inc", "ltd", "corp", "investments", "capital", "securities", "fund", "holdings", "group", "bank"]
                ent_type = "organization" if any(k in attr_entity.lower() for k in org_keywords) else "person"
                
                # Source span for attributing phrase
                attr_end = source_span.start + clean.lower().find(attr_entity.lower()) + len(attr_entity)
                attribution = ClaimAttribution(
                    entity=attr_entity,
                    type=ent_type,
                    explicit=True,
                    source_span=[source_span.start, attr_end]
                )
                break

        # Detect modality and temporal framing on statement
        modality = self.modality_detector.detect(statement_text)
        temporal = self.temporal_detector.detect(statement_text)

        # 1. Match against deterministic canonical patterns
        for pattern, claim_type, predicate, subj_idx, obj_idx, canonical_obj in CANONICAL_PATTERNS:
            m = pattern.search(statement_text)
            if m:
                # Extract subject
                if subj_idx is not None and subj_idx <= len(m.groups()):
                    subject = m.group(subj_idx).strip()
                    # Clean subject leading conjunctions/markers
                    subject = re.sub(r"^(?:that|says|therefore|and)\s+", "", subject, flags=re.IGNORECASE).strip()
                    if subject.lower() == "this investment":
                        subject = "this investment"
                    elif subject.lower() == "the investment":
                        subject = "the investment"
                else:
                    # Never use context_entities from outside this text snippet!
                    # Only assign an entity if the candidate text explicitly mentions it.
                    explicit_entity = self._find_entity_in_text(statement_text, context_entities)
                    if explicit_entity:
                        subject = explicit_entity
                    else:
                        subject = "unspecified_offer" if "RETURN" in predicate else "unspecified"

                if not subject:
                    subject = "unspecified_offer" if "RETURN" in predicate else "unspecified"

                # Extract object
                if canonical_obj is not None:
                    obj = canonical_obj
                elif obj_idx is not None and obj_idx <= len(m.groups()):
                    obj = m.group(obj_idx).strip()
                else:
                    obj = None

                # Standardize normalized sentence
                normalized_sentence = self._format_normalized_sentence(subject, predicate, obj, claim_type, attribution)

                # Verification requirements
                reqs = self.verification_gen.generate(
                    claim_type=claim_type,
                    predicate=predicate,
                    subject=subject,
                    obj=obj,
                    temporal_type=temporal.type,
                    modality_type=modality.type
                )

                fingerprint = self._build_fingerprint(subject, predicate, obj, temporal.type, modality.type, attribution)

                claim_id = f"CLAIM-{claim_index:03d}"
                return CanonicalClaim(
                    claim_id=claim_id,
                    source_content_id=source_content_id,
                    text=ClaimText(original=candidate_text.strip(), normalized=normalized_sentence),
                    claim_type=claim_type,
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    attribution=attribution,
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
            statement_text,
            source_span,
            source_content_id,
            claim_index,
            modality,
            temporal,
            context_entities,
            attribution=attribution,
            original_text=candidate_text.strip()
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
        attribution: Optional[ClaimAttribution] = None,
        original_text: Optional[str] = None
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

        words = text.split()
        if not words:
            return None

        # Check if an entity appears in this candidate text itself
        explicit_entity = self._find_entity_in_text(text, entities)
        if explicit_entity:
            subject = explicit_entity
        elif words[0].lower() in {"guaranteed", "offers", "promises", "high", "unspecified"}:
            subject = "unspecified_offer"
        else:
            subject = words[0]

        predicate = "ASSERTS"
        obj = " ".join(words[1:]) if len(words) > 1 else None

        normalized_sentence = self._format_normalized_sentence(subject, predicate, obj, claim_type, attribution)
        reqs = self.verification_gen.generate(
            claim_type=claim_type,
            predicate=predicate,
            subject=subject,
            obj=obj,
            temporal_type=temporal.type,
            modality_type=modality.type
        )
        fingerprint = self._build_fingerprint(subject, predicate, obj, temporal.type, modality.type, attribution)

        return CanonicalClaim(
            claim_id=f"CLAIM-{index:03d}",
            source_content_id=content_id,
            text=ClaimText(original=original_text or text, normalized=normalized_sentence),
            claim_type=claim_type,
            subject=subject,
            predicate=predicate,
            object=obj,
            attribution=attribution,
            attributes={"heuristic": True},
            temporal_context=temporal,
            modality=modality,
            source_span=span,
            confidence=0.75,
            canonical_fingerprint=fingerprint,
            verification_requirements=reqs,
        )

    @staticmethod
    def _find_entity_in_text(text: str, entities: Optional[list[str]]) -> Optional[str]:
        """Finds if an entity from context is explicitly present in the candidate text."""
        if not entities or not text:
            return None
        text_lower = text.lower()
        for ent in entities:
            if not ent or not ent.strip():
                continue
            pattern = r"\b" + re.escape(ent.lower().strip()) + r"\b"
            if re.search(pattern, text_lower):
                return ent.strip()
        return None

    @staticmethod
    def _format_normalized_sentence(
        subject: Optional[str],
        predicate: str,
        obj: Optional[str],
        claim_type: str,
        attribution: Optional[ClaimAttribution] = None
    ) -> str:
        """Constructs a clean, canonical English statement."""
        stmt: str
        if predicate == "REGISTERED_WITH":
            stmt = f"{subject} is registered with {obj or 'regulator'}."
        elif predicate == "HAS_DEBT":
            if obj in {"0", "zero", "no debt"}:
                stmt = f"{subject} is debt free."
            else:
                stmt = f"{subject} has {obj} debt."
        elif predicate == "GUARANTEED_RETURN":
            clean_val = re.sub(r"\s+returns?$", "", obj or "", flags=re.IGNORECASE).strip()
            if subject in {"unspecified_offer", "unspecified", "investment_offer", None}:
                stmt = f"{clean_val or 'High'} returns are guaranteed."
            else:
                stmt = f"{subject} guarantees {clean_val or 'high'} returns."
        elif predicate == "OFFICIALLY_APPROVED":
            stmt = f"{subject} is officially approved by {obj or 'regulator'}."
        elif predicate == "ANNOUNCED_BONUS":
            stmt = f"{subject} announced a {obj} bonus."
        elif predicate == "REPORTED_PROFIT":
            stmt = f"{subject} reported {obj} profit."
        elif predicate == "REPORTED_REVENUE":
            stmt = f"{subject} reported {obj} revenue."
        elif predicate == "REACH_PRICE":
            stmt = f"{subject} will reach price of {obj}."
        elif predicate == "VALUATION_STATUS":
            stmt = f"{subject} is {obj}."
        elif predicate == "RECOMMENDS_INVESTMENT":
            stmt = f"Investment in {subject} is recommended."
        else:
            s_str = subject or "unspecified"
            stmt = f"{s_str} {predicate.lower().replace('_', ' ')} {obj or ''}".strip() + "."

        if attribution and attribution.entity:
            return f"According to {attribution.entity}, {stmt}"
        return stmt

    @staticmethod
    def _build_fingerprint(
        subject: Optional[str],
        predicate: str,
        obj: Optional[str],
        temporal: str,
        modality: str,
        attribution: Optional[ClaimAttribution] = None
    ) -> str:
        """Builds a deterministic canonical fingerprint for Engine 8."""
        s = re.sub(r"[^\w]", "_", (subject or "UNSPECIFIED_OFFER").strip().upper())
        p = predicate.strip().upper()
        o = re.sub(r"[^\w]", "_", (obj or "NONE").strip().upper())
        t = temporal.strip().upper()
        m = modality.strip().upper()
        fp = f"ENTITY:{s}|PREDICATE:{p}|OBJECT:{o}|TEMPORAL:{t}|MODALITY:{m}"
        if attribution and attribution.entity:
            a = re.sub(r"[^\w]", "_", attribution.entity.strip().upper())
            fp += f"|ATTRIBUTION:{a}"
        return fp

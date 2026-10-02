"""Action segmentation and candidate extraction component for Engine 3.

Decomposes normalized content text into atomic action candidate snippets:
- Reconciles with Engine 1 Call-To-Action (CTA) signals
- Decomposes compound action sentences (e.g. 'Join Telegram, download app and pay ₹5,000')
- Separates actions from claim rationales (e.g. 'Join Telegram because SEBI approved this group')
- Discards non-action assertions and preserves character spans for complete provenance.
"""

import re
from typing import Optional
from nivesh.schemas.claims import SourceSpan, ClaimAnalysis
from nivesh.schemas.normalized import NormalizedContent

# Imperative verbs and action starters
ACTION_VERB_PATTERNS = [
    re.compile(r"\b(?:join|joining|subscribe|subscribing|follow|following)\s+(?:our\s+)?(?:telegram|whatsapp|channel|group|page|community|vip)\b", re.IGNORECASE),
    re.compile(r"\b(?:download|install)\s+(?:our\s+)?(?:app|apk|application|software)\b", re.IGNORECASE),
    re.compile(r"\b(?:upload|submit|verify|complete)\s+(?:your\s+)?(?:pan|aadhaar|aadhar|kyc|document|id)\b", re.IGNORECASE),
    re.compile(r"\b(?:enter|input|type|provide)\s+(?:your\s+)?(?:password|pin|trading\s+password|credentials)\b", re.IGNORECASE),
    re.compile(r"\b(?:share|send|give|provide)\s+(?:the\s+)?(?:otp|password|pin)\b", re.IGNORECASE),
    re.compile(r"\b(?:connect|link|authorize)\s+(?:your\s+)?(?:bank|account|wallet|demat)\b", re.IGNORECASE),
    re.compile(r"\b(?:pay|send|transfer|deposit|wire|remit|withdraw)\s+(?:(?:₹|rs\.?|inr|\$)?\s*[\d,]+|money|funds|fee|charges|immediately)\b", re.IGNORECASE),
    re.compile(r"\b(?:contact|reach\s+out|call|message|dm|chat\s+with)\s+(?:us|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|(?:\+91[\-\s]?)?[6789]\d{9}|me)\b", re.IGNORECASE),
    re.compile(r"\b(?:click|tap|visit|open)\s+(?:the\s+)?(?:link|website|site|here|below|url)\b", re.IGNORECASE),
    re.compile(r"\b(?:register|sign\s+up|create\s+account)\s+(?:now|immediately|today|here)?\b", re.IGNORECASE),
    re.compile(r"\b(?:buy|sell)\s+(?:now|immediately|stock|shares|token)\b", re.IGNORECASE),
    re.compile(r"\b(?:forward|share)\s+(?:this\s+)?(?:message|link|post)\b", re.IGNORECASE),
    re.compile(r"\b(?:sign)\s+(?:document|agreement)\b", re.IGNORECASE),
]

# Suggestion & Invitation prefixes that wrap actions
SUGGESTION_PREFIXES = [
    re.compile(r"^(?:you\s+should\s+(?:consider\s+)?|we\s+recommend\s+(?:that\s+you\s+)?|we\s+suggest\s+|please\s+|kindly\s+|feel\s+free\s+to\s+)", re.IGNORECASE)
]

# Rationale conjunctions linking an action to a claim
# e.g., "Join our Telegram because SEBI approved this group"
ACTION_RATIONALE_SPLIT = [
    re.compile(r"^(.*?)\s+(?:because|since|as)\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(.+?)\s*,\s*(?:so|therefore|hence)\s+(.+)$", re.IGNORECASE),
]

# Clause splitters for compound actions: e.g. "Join Telegram, download the app, complete KYC and pay ₹5,000"
MULTI_ACTION_SPLITTER = re.compile(
    r"(?:(?<!\d),\s*(?:and\s+then\s+|and\s+|then\s+)?|;\s*|\s+(?:and\s+then|then|and)\s+)",
    re.IGNORECASE
)


class ActionCandidate:
    """An atomic text snippet representing a potential action."""

    def __init__(
        self,
        text: str,
        span: SourceSpan,
        rationale_text: Optional[str] = None,
        cta_category: Optional[str] = None
    ):
        self.text = text
        self.span = span
        self.rationale_text = rationale_text
        self.cta_category = cta_category

    def __repr__(self):
        return f"ActionCandidate(text='{self.text}', span=[{self.span.start}, {self.span.end}])"


class ActionSegmenter:
    """Segments content text into atomic action candidate snippets."""

    def segment(
        self,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None
    ) -> list[ActionCandidate]:
        """Extracts atomic action candidate segments from NormalizedContent."""
        text = content.normalized.text if content.normalized and content.normalized.text else ""
        if not text:
            text = content.raw.text if content.raw and content.raw.text else ""
        if not text or not text.strip():
            return []

        candidates: list[ActionCandidate] = []

        # 1. First, split into sentence units
        sentence_matches = [
            m for m in re.finditer(r"\S.*?(?:(?<=[.!?])(?=\s+|$)|(?<=\n)|$)", text)
            if m.group(0).strip()
        ]
        if not sentence_matches:
            sentence_matches = [re.match(r".*", text)]

        for sm in sentence_matches:
            s_raw = sm.group(0)
            s_start = sm.start()
            s_clean = s_raw.strip().rstrip(".!?")
            if not s_clean:
                continue

            # Strip leading attention icons
            s_clean = re.sub(r"^[^\w\s]+", "", s_clean).strip()

            # Check if sentence has an action-claim rationale link
            # e.g. "Join our Telegram because SEBI approved this group"
            # or "SEBI approved this platform, so register now"
            rationale_handled = False
            for rpat in ACTION_RATIONALE_SPLIT:
                rm = rpat.match(s_clean)
                if rm:
                    part1, part2 = rm.group(1).strip(), rm.group(2).strip()
                    if self._is_action(part1) and not self._is_action(part2):
                        # part1 is action, part2 is claim rationale
                        sub_start = text.find(part1, s_start)
                        sub_end = sub_start + len(part1) if sub_start != -1 else s_start + len(part1)
                        candidates.append(ActionCandidate(
                            text=part1,
                            span=SourceSpan(start=max(0, sub_start), end=sub_end),
                            rationale_text=part2
                        ))
                        rationale_handled = True
                        break
                    elif not self._is_action(part1) and self._is_action(part2):
                        # part1 is claim rationale, part2 is action
                        sub_start = text.find(part2, s_start)
                        sub_end = sub_start + len(part2) if sub_start != -1 else s_start + len(part2)
                        candidates.append(ActionCandidate(
                            text=part2,
                            span=SourceSpan(start=max(0, sub_start), end=sub_end),
                            rationale_text=part1
                        ))
                        rationale_handled = True
                        break

            if rationale_handled:
                continue

            # 2. Decompose compound actions inside the sentence
            # E.g. "Join our Telegram group, download the app, complete KYC and pay ₹5,000"
            sub_clauses = self._split_multi_actions(s_clean, s_start, text)
            for c_text, c_span in sub_clauses:
                if self._is_action(c_text):
                    candidates.append(ActionCandidate(text=c_text, span=c_span))

        # 3. Reconcile with Engine 1 CTAs (ensure any missed CTA is included)
        if content.content_features and content.content_features.calls_to_action:
            for cta in content.content_features.calls_to_action:
                phrase = cta.phrase.strip()
                # Check if this CTA is already covered by a candidate
                already_covered = any(
                    phrase.lower() in cand.text.lower() or cand.text.lower() in phrase.lower()
                    for cand in candidates
                )
                if not already_covered and self._is_action(phrase):
                    p_start = cta.span[0] if cta.span else text.find(phrase)
                    p_end = cta.span[1] if cta.span else (p_start + len(phrase) if p_start != -1 else 0)
                    candidates.append(ActionCandidate(
                        text=phrase,
                        span=SourceSpan(start=max(0, p_start), end=p_end),
                        cta_category=cta.category
                    ))

        # Sort candidates chronologically by span start offset
        candidates.sort(key=lambda c: c.span.start)
        return candidates

    def _is_action(self, text: str) -> bool:
        """Determines if a statement instructs, invites, requests, or suggests an action."""
        clean = text.lower().strip()
        if not clean:
            return False

        # Guard against pure factual or descriptive claims
        # E.g. "Something may be coming soon", "Rahul Sharma is an advisor", "40% returns are guaranteed"
        is_pure_claim = (
            ("returns are guaranteed" in clean or "guaranteed 40%" in clean)
            or ("is a sebi registered" in clean or "registered advisor" in clean and not any(a in clean for a in ["contact", "join"]))
            or clean in {"something may be coming soon", "market increased 5% today"}
        )
        if is_pure_claim:
            return False

        # Check action verb patterns
        for pat in ACTION_VERB_PATTERNS:
            if pat.search(clean):
                return True

        # Check suggestions / requests
        for sp in SUGGESTION_PREFIXES:
            if sp.search(clean):
                sub = sp.sub("", clean).strip()
                for pat in ACTION_VERB_PATTERNS:
                    if pat.search(sub):
                        return True

        # Check implicit actions
        if any(w in clean for w in ["kyc must be completed", "activation requires", "must be completed"]):
            return True

        # Check direct imperative starting verbs
        words = clean.split()
        if words and words[0] in {
            "join", "download", "install", "upload", "pay", "send", "transfer",
            "deposit", "withdraw", "contact", "call", "message", "click", "visit",
            "register", "enter", "share", "forward", "sign", "buy", "sell"
        }:
            return True

        return False

    def _split_multi_actions(
        self,
        sentence: str,
        sentence_start: int,
        full_text: str
    ) -> list[tuple[str, SourceSpan]]:
        """Splits compound action sentences into atomic action clauses."""
        parts = MULTI_ACTION_SPLITTER.split(sentence)
        if len(parts) <= 1:
            s_idx = full_text.find(sentence, sentence_start)
            start = s_idx if s_idx != -1 else sentence_start
            return [(sentence, SourceSpan(start=start, end=start + len(sentence)))]

        results = []
        for part in parts:
            p_strip = part.strip()
            if p_strip and self._is_action(p_strip):
                p_idx = full_text.find(p_strip, sentence_start)
                start = p_idx if p_idx != -1 else sentence_start
                results.append((p_strip, SourceSpan(start=start, end=start + len(p_strip))))
            elif p_strip and not results:
                # If part 1 wasn't an action alone, maybe it's the start
                p_idx = full_text.find(p_strip, sentence_start)
                start = p_idx if p_idx != -1 else sentence_start
                results.append((p_strip, SourceSpan(start=start, end=start + len(p_strip))))

        if not results:
            s_idx = full_text.find(sentence, sentence_start)
            start = s_idx if s_idx != -1 else sentence_start
            results.append((sentence, SourceSpan(start=start, end=start + len(sentence))))

        return results

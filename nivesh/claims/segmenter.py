"""Candidate claim segmentation and Action-filtering component for Engine 2.

Decomposes normalized content text into atomic assertion candidates:
- Breaks compound sentences on conjunctions and discourse markers
- Strips pure Call-To-Action (CTA) imperatives (e.g. 'Join our Telegram', 'Download our app', 'Pay ₹5,000')
- Extracts embedded assertions from compound action-claim sentences (e.g. 'Join Telegram because SEBI approved this group')
- Tracks source character spans for complete traceability.
"""

import re
from typing import Optional
from nivesh.schemas.claims import SourceSpan

# Action imperative verbs that typically start pure CTAs
ACTION_IMPERATIVES = [
    re.compile(r"^\s*(?:join|download|install|pay|send|contact|reach\s+out|call|message|chat|click|tap|visit|subscribe|share|forward|buy|sell|deposit|wire)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:join\s+(?:our\s+)?(?:telegram|whatsapp|vip|group|channel))\b", re.IGNORECASE),
    re.compile(r"^\s*(?:download\s+(?:our\s+)?(?:app|apk))\b", re.IGNORECASE),
    re.compile(r"^\s*(?:pay\s+(?:₹|rs\.?|inr|\$)?\s*[\d,]+)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:contact\s+[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)\b", re.IGNORECASE),
]

# Action conjunctions linking an action with a rationale
# e.g., "Join our Telegram because SEBI approved this group" -> Claim: "SEBI approved this group"
# e.g., "ABC is officially approved, so buy immediately" -> Claim: "ABC is officially approved"
ACTION_RATIONALE_PATTERNS = [
    re.compile(r"^(.*?)\s+(?:because|as|since)\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(.+?)\s*,\s*(?:so|therefore|hence)\s+(?:buy|invest|join|download|pay)\s*(.*)$", re.IGNORECASE),
]

# Conjunctions splitting independent compound assertions
COMPOUND_SPLIT_PATTERN = re.compile(
    r"\s+(?:and\s+therefore|therefore|hence|and\s+says|and\s+announced|and\s+reported|\bbut\b|\bwhereas\b|\bwhile\b)\s+",
    re.IGNORECASE
)


class CandidateSegment:
    """Represents an atomic text segment candidate for claim structuring."""
    def __init__(self, text: str, span: SourceSpan, discourse_marker: Optional[str] = None):
        self.text = text
        self.span = span
        self.discourse_marker = discourse_marker

    def __repr__(self):
        return f"CandidateSegment(text='{self.text}', span=[{self.span.start}, {self.span.end}])"


class ClaimSegmenter:
    """Segments normalized text into atomic claim candidate units."""

    def segment(self, text: str) -> tuple[list[CandidateSegment], int]:
        """Segments text into atomic assertion candidates, filtering pure actions.
        
        Returns:
            (candidate_segments, actions_filtered_count)
        """
        if not text or not text.strip():
            return [], 0

        candidates: list[CandidateSegment] = []
        actions_filtered = 0

        # Split text into major sentence units while tracking offsets
        # Avoid splitting on dots inside URLs (t.me), emails (example.com), or decimal numbers
        sentence_matches = [m for m in re.finditer(r"\S.*?(?:(?<=[.!?])(?=\s+|$)|(?<=\n)|$)", text) if m.group(0).strip()]
        if not sentence_matches:
            sentence_matches = [re.match(r".*", text)]

        for match in sentence_matches:
            raw_sentence = match.group(0)
            base_start = match.start()
            sentence = raw_sentence.strip()
            if not sentence:
                continue

            # Strip leading emoji or attention markers e.g. 🚨
            clean_sentence = re.sub(r"^[^\w\s]+", "", sentence).strip()
            if not clean_sentence:
                continue

            # Check if this sentence has an action clause and a claim clause
            # e.g. "Join our Telegram because SEBI approved this group"
            rationale_match = False
            for pat in ACTION_RATIONALE_PATTERNS:
                rm = pat.match(clean_sentence)
                if rm:
                    part1, part2 = rm.group(1).strip(), rm.group(2).strip()
                    # Check which part is the action and which is the claim
                    if self._is_pure_action(part1) and not self._is_pure_action(part2):
                        actions_filtered += 1
                        claim_text = part2
                        sub_start = text.find(claim_text, base_start)
                        sub_end = sub_start + len(claim_text) if sub_start != -1 else base_start + len(sentence)
                        candidates.append(CandidateSegment(claim_text, SourceSpan(start=max(0, sub_start), end=sub_end)))
                        rationale_match = True
                        break
                    elif not self._is_pure_action(part1) and self._is_pure_action(part2):
                        actions_filtered += 1
                        claim_text = part1
                        sub_start = text.find(claim_text, base_start)
                        sub_end = sub_start + len(claim_text) if sub_start != -1 else base_start + len(sentence)
                        candidates.append(CandidateSegment(claim_text, SourceSpan(start=max(0, sub_start), end=sub_end)))
                        rationale_match = True
                        break

            if rationale_match:
                continue

            # Check if entire sentence is a pure action
            if self._is_pure_action(clean_sentence):
                actions_filtered += 1
                continue

            # Check for compound conjunction splits (e.g. "Revenue increased 40% and therefore the company will double")
            parts = self._split_compound(clean_sentence, sentence, base_start, text)
            for part_text, part_span, marker in parts:
                if self._is_pure_action(part_text):
                    actions_filtered += 1
                    continue
                # Also check sub-clauses like "SEBI registered advisor Rahul Sharma guarantees 40% returns"
                # which can be split into identity ("Rahul Sharma is a SEBI registered advisor") and financial ("Rahul Sharma guarantees 40% returns")
                sub_assertions = self._decompose_appositive_assertions(part_text, part_span, text)
                if sub_assertions:
                    candidates.extend(sub_assertions)
                else:
                    candidates.append(CandidateSegment(part_text, part_span, marker))

        return candidates, actions_filtered

    def _is_pure_action(self, text: str) -> bool:
        """Determines if a statement is purely an action request with no verifiable claim."""
        clean = text.strip().rstrip(".!?")
        # Direct URL or email alone
        if re.match(r"^(?:https?://|t\.me/|www\.)\S+$", clean, re.IGNORECASE):
            return True
        if re.match(r"^Contact\s+[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", clean, re.IGNORECASE):
            return True

        for pat in ACTION_IMPERATIVES:
            if pat.search(clean):
                # Ensure it doesn't contain a regulatory or financial assertion
                # E.g. "Join our Telegram group: https://t.me/rahulinvest" is pure action
                # E.g. "Download our app and pay ₹5,000" is pure action
                # E.g. "Buy now and join our Telegram" is pure action
                has_substantive_claim = any(w in clean.lower() for w in ["because", "since", "approved", "licensed", "debt free", "reported", "increased"])
                if not has_substantive_claim:
                    return True
        return False

    def _split_compound(self, clean_sentence: str, full_sentence: str, base_start: int, full_text: str) -> list[tuple[str, SourceSpan, Optional[str]]]:
        """Splits sentences connected by causal or independent conjunctions."""
        splits = list(COMPOUND_SPLIT_PATTERN.finditer(clean_sentence))
        if not splits:
            return [(clean_sentence, SourceSpan(start=base_start, end=base_start + len(full_sentence)), None)]

        results = []
        last_idx = 0
        for m in splits:
            part = clean_sentence[last_idx:m.start()].strip()
            marker = m.group(0).strip()
            if part:
                idx = full_text.find(part, base_start)
                span = SourceSpan(start=idx if idx != -1 else base_start, end=(idx + len(part)) if idx != -1 else base_start + len(part))
                results.append((part, span, None))
            last_idx = m.end()

        tail = clean_sentence[last_idx:].strip()
        if tail:
            idx = full_text.find(tail, base_start)
            span = SourceSpan(start=idx if idx != -1 else base_start, end=(idx + len(tail)) if idx != -1 else base_start + len(tail))
            # The tail is associated with the preceding marker (e.g. therefore / because)
            results.append((tail, span, splits[-1].group(0).strip()))

        return results

    def _decompose_appositive_assertions(self, text: str, span: SourceSpan, full_text: str) -> Optional[list[CandidateSegment]]:
        """Decomposes sentences with combined regulatory titles and return guarantees.
        
        Example:
        'SEBI registered advisor Rahul Sharma guarantees 40% returns'
        Splits into:
        1. 'Rahul Sharma is a SEBI registered advisor'
        2. 'Rahul Sharma guarantees 40% returns'
        """
        # Pattern: Title/Regulator prefix + Person name + guarantees/offers + returns
        m = re.match(
            r"^(SEBI\s+registered\s+(?:advisor|adviser))\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:!|\.)?\s*(guarantees?\s+.*|guaranteed\s+.*)?$",
            text.strip(),
            re.IGNORECASE
        )
        if m:
            title_part = m.group(1).strip()
            name_part = m.group(2).strip()
            guarantee_part = (m.group(3) or "").strip()

            c1_text = f"{name_part} is a {title_part}"
            # Match span in full text
            s_idx = full_text.find(name_part)
            span1 = SourceSpan(start=span.start, end=s_idx + len(name_part) if s_idx != -1 else span.end)
            res = [CandidateSegment(c1_text, span1)]

            if guarantee_part:
                c2_text = f"{guarantee_part}"
                g_idx = full_text.find(guarantee_part)
                span2 = SourceSpan(start=g_idx if g_idx != -1 else span.start, end=g_idx + len(guarantee_part) if g_idx != -1 else span.end)
                res.append(CandidateSegment(c2_text, span2))

            return res

        return None

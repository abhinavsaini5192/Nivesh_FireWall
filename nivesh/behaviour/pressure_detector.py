"""Pressure and urgency detection for Engine 10: Behavioural Signal Intelligence.

Detects explicit urgency, time pressure, FOMO pressure, repeated urgency,
and urgency escalation across content and interaction history.
Outputs objective behavioral signals without accusatory psychological judgment.
"""

import re
from typing import Optional, Sequence
from nivesh.behaviour.schemas import (
    BehaviouralSignal,
    BehaviouralSignalType,
    BehaviouralSignalSeverity,
)
from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionEventType,
    InteractionHistory,
)
from nivesh.behaviour.temporal import TemporalThresholds, DEFAULT_TEMPORAL_THRESHOLDS
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis


TIME_PRESSURE_PATTERNS = [
    re.compile(r"\bact\s+now\b", re.IGNORECASE),
    re.compile(r"\bhurry\b", re.IGNORECASE),
    re.compile(r"\bpay\s+immediately\b", re.IGNORECASE),
    re.compile(r"\bimmediate(?:ly)?\b", re.IGNORECASE),
    re.compile(r"\bright\s+now\b", re.IGNORECASE),
    re.compile(r"\blast\s+chance\b", re.IGNORECASE),
    re.compile(r"\bfinal\s+(?:call|notice|reminder)\b", re.IGNORECASE),
    re.compile(r"\bonly\s+\d+\s*(?:min(?:ute)?s?|sec(?:ond)?s?|hours?)\s+left\b", re.IGNORECASE),
    re.compile(r"\btime\s+is\s+running\s+out\b", re.IGNORECASE),
    re.compile(r"\bexpires?\s*(?:in|soon|today)\b", re.IGNORECASE),
    re.compile(r"\bwill\s+expire\b", re.IGNORECASE),
    re.compile(r"\baccess\s+will\s+expire\b", re.IGNORECASE),
    re.compile(r"\bclosing\s+soon\b", re.IGNORECASE),
    re.compile(r"\blimited\s+time\b", re.IGNORECASE),
    re.compile(r"\bpay\s+now\b", re.IGNORECASE),
    re.compile(r"\bjaldi\s+karo\b", re.IGNORECASE),
    re.compile(r"\babhi\s+karo\b", re.IGNORECASE),
]

FOMO_PRESSURE_PATTERNS = [
    re.compile(r"\bdon'?t\s+miss\s+(?:this|out)\b", re.IGNORECASE),
    re.compile(r"\bmiss\s+this\s+chance\b", re.IGNORECASE),
    re.compile(r"\blimited\s+(?:slots?|seats?|spots?|entry|availability)\b", re.IGNORECASE),
    re.compile(r"\bonly\s+\d+\s+(?:slots?|seats?|spots?)\s+left\b", re.IGNORECASE),
    re.compile(r"\bexclusive\s+(?:opportunity|offer|access|membership)\b", re.IGNORECASE),
    re.compile(r"\bonce\s+in\s+a\s+lifetime\b", re.IGNORECASE),
    re.compile(r"\bgrab\s+(?:your\s+slot|it|this\s+deal)\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+profit\s+for\s+first\s+\d+\b", re.IGNORECASE),
]


class PressureDetector:
    """Detects pressure patterns (time, FOMO, repeated urgency) in financial interactions."""

    def __init__(self, thresholds: Optional[TemporalThresholds] = None):
        self.thresholds = thresholds or DEFAULT_TEMPORAL_THRESHOLDS

    def detect(
        self,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None,
        interaction_history: Optional[InteractionHistory] = None,
    ) -> list[BehaviouralSignal]:
        """Analyze text and history to identify pressure signals."""
        signals: list[BehaviouralSignal] = []
        observed_texts: list[tuple[str, Optional[str], Optional[str]]] = []  # (text, event_id, claim_id)

        # 1. Primary content text
        content_text = ""
        if content:
            if hasattr(content, "normalized") and hasattr(content.normalized, "text") and content.normalized.text:
                content_text = content.normalized.text
            elif hasattr(content, "raw") and hasattr(content.raw, "text") and content.raw.text:
                content_text = content.raw.text
            elif hasattr(content, "text"):
                content_text = str(getattr(content, "text") or "")
        if content_text:
            observed_texts.append((content_text, None, None))

        # 2. Associated claims
        if claims and claims.claims:
            for claim in claims.claims:
                if hasattr(claim, "text"):
                    if isinstance(claim.text, str):
                        c_text = claim.text
                    else:
                        c_text = f"{getattr(claim.text, 'original', '')} {getattr(claim.text, 'normalized', '')}"
                else:
                    c_text = ""
                observed_texts.append((c_text, None, getattr(claim, "claim_id", None)))

        # 3. Events from history that carry metadata text or descriptions
        if interaction_history and interaction_history.events:
            for evt in interaction_history.events:
                evt_text = evt.metadata.get("text") or evt.metadata.get("prompt") or ""
                if evt_text:
                    observed_texts.append((str(evt_text), evt.event_id, evt.claim_id))

        time_pressure_matches: list[tuple[str, str, Optional[str], Optional[str]]] = []
        fomo_pressure_matches: list[tuple[str, str, Optional[str], Optional[str]]] = []

        for text, event_id, claim_id in observed_texts:
            for pat in TIME_PRESSURE_PATTERNS:
                m = pat.search(text)
                if m:
                    time_pressure_matches.append((m.group(0), text, event_id, claim_id))
            for pat in FOMO_PRESSURE_PATTERNS:
                m = pat.search(text)
                if m:
                    fomo_pressure_matches.append((m.group(0), text, event_id, claim_id))

        # Deduplicate matched phrases
        unique_time_phrases = {match[0].lower() for match in time_pressure_matches}
        unique_fomo_phrases = {match[0].lower() for match in fomo_pressure_matches}

        # Signal: TIME_PRESSURE
        if time_pressure_matches:
            ev_ids = [m[2] for m in time_pressure_matches if m[2]]
            cl_ids = [m[3] for m in time_pressure_matches if m[3]]
            matched_snippets = [f'"{m[0]}"' for m in time_pressure_matches[:3]]
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PRS-TIME-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.TIME_PRESSURE,
                    description=f"Time-limited pressure observed in interaction: {', '.join(matched_snippets)}",
                    severity=BehaviouralSignalSeverity.MEDIUM,
                    confidence=0.92,
                    event_ids=list(dict.fromkeys(ev_ids)),
                    claim_ids=list(dict.fromkeys(cl_ids)),
                    evidence=[f"Detected time pressure phrase: {m[0]}" for m in time_pressure_matches[:3]],
                    metadata={"matched_phrases": list(unique_time_phrases)},
                )
            )

        # Signal: FOMO_PRESSURE
        if fomo_pressure_matches:
            ev_ids = [m[2] for m in fomo_pressure_matches if m[2]]
            cl_ids = [m[3] for m in fomo_pressure_matches if m[3]]
            matched_snippets = [f'"{m[0]}"' for m in fomo_pressure_matches[:3]]
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PRS-FOMO-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.FOMO_PRESSURE,
                    description=f"FOMO (fear-of-missing-out) pressure observed in interaction: {', '.join(matched_snippets)}",
                    severity=BehaviouralSignalSeverity.LOW,
                    confidence=0.90,
                    event_ids=list(dict.fromkeys(ev_ids)),
                    claim_ids=list(dict.fromkeys(cl_ids)),
                    evidence=[f"Detected FOMO phrase: {m[0]}" for m in fomo_pressure_matches[:3]],
                    metadata={"matched_phrases": list(unique_fomo_phrases)},
                )
            )

        # Signal: REPEATED_URGENCY (Requires >= urgency_repetition_threshold occurrences across events or distinct phrases)
        event_match_count = len({m[2] for m in time_pressure_matches if m[2]})
        phrase_match_count = len(unique_time_phrases)
        is_repeated = (
            phrase_match_count >= self.thresholds.urgency_repetition_threshold
            or event_match_count >= self.thresholds.urgency_repetition_threshold
        )
        total_urgency_occurrences = max(phrase_match_count, event_match_count)
        if is_repeated:
            ev_ids = [m[2] for m in time_pressure_matches if m[2]]
            cl_ids = [m[3] for m in time_pressure_matches if m[3]]
            signals.append(
                BehaviouralSignal(
                    signal_id=f"BHS-PRS-REP-{len(signals) + 1:03d}",
                    signal_type=BehaviouralSignalType.REPEATED_URGENCY,
                    description=f"Urgency calls were repeated {total_urgency_occurrences} times across interaction steps",
                    severity=BehaviouralSignalSeverity.HIGH,
                    confidence=0.94,
                    event_ids=list(dict.fromkeys(ev_ids)),
                    claim_ids=list(dict.fromkeys(cl_ids)),
                    evidence=[
                        f"Urgency observed {total_urgency_occurrences} times (threshold: {self.thresholds.urgency_repetition_threshold})"
                    ],
                    metadata={"occurrence_count": total_urgency_occurrences},
                )
            )

        # Signal: URGENCY_ESCALATION
        # If historical sequence shows later events introducing more severe urgency after earlier neutral steps
        if interaction_history and len(interaction_history.events) >= 2:
            events = interaction_history.get_sorted_events()
            has_early_neutral = any(
                e.event_type in (InteractionEventType.CONTENT_VIEW, InteractionEventType.CLAIM_PRESENTED)
                and not any(pat.search(str(e.metadata.get("text", ""))) for pat in TIME_PRESSURE_PATTERNS)
                for e in events[:len(events) // 2]
            )
            has_late_urgency = any(
                any(pat.search(str(e.metadata.get("text", ""))) for pat in TIME_PRESSURE_PATTERNS)
                for e in events[len(events) // 2:]
            )
            if has_early_neutral and has_late_urgency:
                signals.append(
                    BehaviouralSignal(
                        signal_id=f"BHS-PRS-ESC-{len(signals) + 1:03d}",
                        signal_type=BehaviouralSignalType.URGENCY_ESCALATION,
                        description="Urgency escalated over time following initially neutral or informational interaction",
                        severity=BehaviouralSignalSeverity.HIGH,
                        confidence=0.88,
                        event_ids=[e.event_id for e in events if e.event_id],
                        evidence=["Interaction progressed from neutral content to time-pressured prompts"],
                    )
                )

        return signals

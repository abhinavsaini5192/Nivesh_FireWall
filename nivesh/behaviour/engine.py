"""Canonical Service Interface for Engine 10: Behavioural Signal Intelligence.

Coordinates:
- Interaction sequence tracking and event ingestion
- Temporal progression and timing analysis
- Pressure and urgency detection
- Progressive commitment and escalation analysis
- Persistence and retry detection
- Channel migration analysis
- Session behavioural summary and policy hints generation
"""

import threading
from typing import Optional, Any

from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis
from nivesh.identity.schemas import IdentityAnalysis

from nivesh.behaviour.schemas import (
    BehaviouralAnalysis,
    ENGINE_VERSION,
)
from nivesh.behaviour.event_model import (
    InteractionEvent,
    InteractionHistory,
)
from nivesh.behaviour.temporal import TemporalThresholds, DEFAULT_TEMPORAL_THRESHOLDS
from nivesh.behaviour.sequence_analyzer import SequenceAnalyzer
from nivesh.behaviour.provenance import build_provenance, extract_upstream_references


class BehaviouralSignalEngine:
    """Canonical Engine 10 service implementation for Nivesh Firewall.

    Operates as a supporting intelligence component that identifies behavioral
    and interaction-pattern signals across content and action sequences.
    Provides structured observations to Engine 8 without making final policy decisions.
    """

    def __init__(self, thresholds: Optional[TemporalThresholds] = None):
        self.thresholds = thresholds or DEFAULT_TEMPORAL_THRESHOLDS
        self._lock = threading.Lock()
        self._counter: int = 1
        self._analyses: dict[str, BehaviouralAnalysis] = {}
        self._sessions: dict[str, InteractionHistory] = {}
        self.sequence_analyzer = SequenceAnalyzer(self.thresholds)

    def analyze(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        threat: Optional[ThreatAnalysis] = None,
        fingerprint: Optional[FingerprintAnalysis] = None,
        identity: Optional[IdentityAnalysis] = None,
        interaction_history: Optional[InteractionHistory] = None,
    ) -> BehaviouralAnalysis:
        """Analyze interaction sequence and content to detect emergent behavioural signals.

        Works with current interaction even when historical interaction data is absent.
        Does not determine legal fraud, label individuals as scammers, generate scam
        probabilities, or make direct BLOCK/WARN/PAUSE decisions.
        """
        with self._lock:
            analysis_id = f"BHA-{self._counter:03d}"
            self._counter += 1

        # Use provided history or check if session history is tracked in-memory
        history_to_use = interaction_history
        if not history_to_use and content and hasattr(content, "metadata") and content.metadata:
            sess_id = content.metadata.get("session_id")
            if sess_id and sess_id in self._sessions:
                history_to_use = self._sessions[sess_id]

        # Execute sequence analysis across all behavioural dimensions
        signals, findings, session_summary, policy_hints, confidence = (
            self.sequence_analyzer.analyze_sequence(
                content=content,
                claims=claims,
                actions=actions,
                interaction_history=history_to_use,
            )
        )

        provenance = build_provenance(
            content=content,
            claims=claims,
            actions=actions,
            interaction_history=history_to_use,
        )

        upstream_refs = extract_upstream_references(
            content=content,
            claims=claims,
            actions=actions,
            threat=threat,
            fingerprint=fingerprint,
            identity=identity,
            interaction_history=history_to_use,
        )

        analysis = BehaviouralAnalysis(
            analysis_id=analysis_id,
            signals=signals,
            findings=findings,
            session_summary=session_summary,
            policy_hints=policy_hints,
            confidence=confidence,
            provenance=provenance,
            upstream_references=upstream_refs,
            engine_version=ENGINE_VERSION,
        )

        with self._lock:
            self._analyses[analysis_id] = analysis
            if history_to_use and history_to_use.session_id:
                self._sessions[history_to_use.session_id] = history_to_use

        return analysis

    def record_event(self, session_id: str, event: InteractionEvent) -> InteractionHistory:
        """Record a structured interaction event into a session history."""
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = InteractionHistory(session_id=session_id)
            history = self._sessions[session_id]
            history.add_event(event)
            return history

    def get_session(self, session_id: str) -> Optional[InteractionHistory]:
        """Retrieve recorded session history by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def get_analysis(self, analysis_id: str) -> Optional[BehaviouralAnalysis]:
        """Retrieve prior behavioural analysis by ID."""
        with self._lock:
            return self._analyses.get(analysis_id)

    def clear(self) -> None:
        """Reset in-memory storage for test isolation."""
        with self._lock:
            self._counter = 1
            self._analyses.clear()
            self._sessions.clear()

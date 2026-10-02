"""Engine 10: Behavioural Signal Intelligence Engine.

Identifies behavioural and interaction-pattern signals that emerge across a sequence
of financial content and user actions without making legal fraud determinations,
diagnosing psychological conditions, or issuing direct policy interventions.
"""

from nivesh.behaviour.schemas import (
    ENGINE_VERSION,
    BehaviouralSignalType,
    BehaviouralFindingType,
    BehaviouralSignalSeverity,
    BehaviouralSignal,
    BehaviouralFinding,
    SessionBehaviourSummary,
    BehaviouralPolicyHints,
    BehaviouralProvenance,
    BehaviouralAnalysis,
)
from nivesh.behaviour.event_model import (
    InteractionEventType,
    InteractionEvent,
    InteractionHistory,
)
from nivesh.behaviour.temporal import (
    TemporalThresholds,
    DEFAULT_TEMPORAL_THRESHOLDS,
    compute_duration_seconds,
    parse_timestamp,
    is_rapid_interval,
)
from nivesh.behaviour.pressure_detector import PressureDetector
from nivesh.behaviour.escalation_detector import EscalationDetector
from nivesh.behaviour.persistence_detector import PersistenceDetector
from nivesh.behaviour.channel_detector import ChannelDetector
from nivesh.behaviour.sequence_analyzer import SequenceAnalyzer
from nivesh.behaviour.findings import FindingsBuilder
from nivesh.behaviour.provenance import build_provenance, extract_upstream_references
from nivesh.behaviour.engine import BehaviouralSignalEngine

__all__ = [
    "ENGINE_VERSION",
    "BehaviouralSignalType",
    "BehaviouralFindingType",
    "BehaviouralSignalSeverity",
    "BehaviouralSignal",
    "BehaviouralFinding",
    "SessionBehaviourSummary",
    "BehaviouralPolicyHints",
    "BehaviouralProvenance",
    "BehaviouralAnalysis",
    "InteractionEventType",
    "InteractionEvent",
    "InteractionHistory",
    "TemporalThresholds",
    "DEFAULT_TEMPORAL_THRESHOLDS",
    "compute_duration_seconds",
    "parse_timestamp",
    "is_rapid_interval",
    "PressureDetector",
    "EscalationDetector",
    "PersistenceDetector",
    "ChannelDetector",
    "SequenceAnalyzer",
    "FindingsBuilder",
    "build_provenance",
    "extract_upstream_references",
    "BehaviouralSignalEngine",
]

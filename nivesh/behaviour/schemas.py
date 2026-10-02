"""Typed schemas for Engine 10: Behavioural Signal Intelligence Engine.

Defines signal types, finding types, severities, session summaries, policy hints,
and the canonical BehaviouralAnalysis output schema.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


ENGINE_VERSION = "1.0.0"


class BehaviouralSignalType(str, Enum):
    """Controlled taxonomy of behavioural signals across interaction sequences."""

    # Pressure / Urgency
    URGENCY_ESCALATION = "URGENCY_ESCALATION"
    REPEATED_URGENCY = "REPEATED_URGENCY"
    TIME_PRESSURE = "TIME_PRESSURE"
    FOMO_PRESSURE = "FOMO_PRESSURE"

    # Action Progression
    PROGRESSIVE_COMMITMENT = "PROGRESSIVE_COMMITMENT"
    RAPID_ACTION_ESCALATION = "RAPID_ACTION_ESCALATION"
    LOW_TO_HIGH_IMPACT_TRANSITION = "LOW_TO_HIGH_IMPACT_TRANSITION"
    INFORMATION_TO_TRANSACTION_SHIFT = "INFORMATION_TO_TRANSACTION_SHIFT"

    # Interaction Persistence
    REPEATED_ACTION_REQUEST = "REPEATED_ACTION_REQUEST"
    RETRY_AFTER_DECLINE = "RETRY_AFTER_DECLINE"
    PERSISTENT_PAYMENT_REQUEST = "PERSISTENT_PAYMENT_REQUEST"
    PERSISTENT_CREDENTIAL_REQUEST = "PERSISTENT_CREDENTIAL_REQUEST"

    # Channel Behaviour
    CHANNEL_MIGRATION = "CHANNEL_MIGRATION"
    RAPID_CHANNEL_MIGRATION = "RAPID_CHANNEL_MIGRATION"
    PRIVATE_CHANNEL_ESCALATION = "PRIVATE_CHANNEL_ESCALATION"

    # User-Response Pattern
    USER_HESITATION = "USER_HESITATION"
    USER_DECLINE = "USER_DECLINE"
    USER_OVERRIDE = "USER_OVERRIDE"
    WARNING_OVERRIDE = "WARNING_OVERRIDE"
    REPEATED_WARNING_OVERRIDE = "REPEATED_WARNING_OVERRIDE"


class BehaviouralFindingType(str, Enum):
    """Stable identifiers for structured behavioural findings."""

    URGENCY_ESCALATION = "URGENCY_ESCALATION"
    REPEATED_URGENCY = "REPEATED_URGENCY"
    TIME_PRESSURE = "TIME_PRESSURE"
    FOMO_PRESSURE = "FOMO_PRESSURE"

    PROGRESSIVE_COMMITMENT = "PROGRESSIVE_COMMITMENT"
    RAPID_ACTION_ESCALATION = "RAPID_ACTION_ESCALATION"
    LOW_TO_HIGH_IMPACT_TRANSITION = "LOW_TO_HIGH_IMPACT_TRANSITION"
    INFORMATION_TO_TRANSACTION_SHIFT = "INFORMATION_TO_TRANSACTION_SHIFT"

    REPEATED_ACTION_REQUEST = "REPEATED_ACTION_REQUEST"
    RETRY_AFTER_DECLINE = "RETRY_AFTER_DECLINE"
    PERSISTENT_PAYMENT_REQUEST = "PERSISTENT_PAYMENT_REQUEST"
    PERSISTENT_CREDENTIAL_REQUEST = "PERSISTENT_CREDENTIAL_REQUEST"

    CHANNEL_MIGRATION = "CHANNEL_MIGRATION"
    RAPID_CHANNEL_MIGRATION = "RAPID_CHANNEL_MIGRATION"
    PRIVATE_CHANNEL_ESCALATION = "PRIVATE_CHANNEL_ESCALATION"

    USER_HESITATION = "USER_HESITATION"
    USER_DECLINE = "USER_DECLINE"
    USER_OVERRIDE = "USER_OVERRIDE"
    WARNING_OVERRIDE = "WARNING_OVERRIDE"
    REPEATED_WARNING_OVERRIDE = "REPEATED_WARNING_OVERRIDE"


class BehaviouralSignalSeverity(str, Enum):
    """Categorical severity tier of an observed behavioural pattern."""
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ELEVATED = "ELEVATED"


class BehaviouralSignal(BaseModel):
    """Atomic behavioural signal detected within an interaction or interaction sequence."""
    signal_id: str = Field(description="Unique signal identifier (e.g. BHS-001)")
    signal_type: BehaviouralSignalType = Field(description="Categorical behavioural signal type")
    description: str = Field(description="Objective factual description of observed behaviour")
    severity: BehaviouralSignalSeverity = Field(default=BehaviouralSignalSeverity.MEDIUM, description="Severity tier")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence that the behavioural pattern exists (NOT scam probability)",
    )
    event_ids: list[str] = Field(default_factory=list, description="IDs of supporting interaction events")
    action_ids: list[str] = Field(default_factory=list, description="IDs of associated actions")
    claim_ids: list[str] = Field(default_factory=list, description="IDs of associated claims")
    evidence: list[str] = Field(default_factory=list, description="Objective factual evidence basis")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Structured attributes without PII")


class BehaviouralFinding(BaseModel):
    """High-level structured finding derived from one or more behavioural signals."""
    finding_id: str = Field(description="Unique finding identifier (e.g. BHF-001)")
    finding_type: BehaviouralFindingType = Field(description="Machine-readable finding category")
    description: str = Field(description="Non-accusatory objective summary of the finding")
    basis: str = Field(description="Factual sequence basis for this finding")
    supporting_signal_ids: list[str] = Field(default_factory=list, description="IDs of supporting signals")
    event_ids: list[str] = Field(default_factory=list, description="IDs of referenced interaction events")
    action_ids: list[str] = Field(default_factory=list, description="IDs of referenced actions")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the behavioural pattern")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Provenance tracking metadata")


class SessionBehaviourSummary(BaseModel):
    """Statistical and sequence summary of the interaction session without user grading."""
    session_id: Optional[str] = Field(default=None, description="Session ID if historical tracking is active")
    event_count: int = Field(default=0, description="Total interaction events observed")
    duration_seconds: Optional[float] = Field(default=None, description="Observed interaction duration in seconds")
    action_count: int = Field(default=0, description="Count of requested actions")
    high_impact_action_count: int = Field(default=0, description="Count of high-impact actions (payment, cred, download)")
    channel_changes: int = Field(default=0, description="Count of observed channel transitions")
    warning_count: int = Field(default=0, description="Count of safety warnings previously shown")
    override_count: int = Field(default=0, description="Count of user overrides recorded")
    behavioural_signals: list[str] = Field(default_factory=list, description="List of signal types present")
    sequence_summary: list[str] = Field(default_factory=list, description="Ordered summary of action/event stages")


class BehaviouralPolicyHints(BaseModel):
    """Structured objective observations consumed by Engine 8 Policy Engine."""
    high_impact_action_progression: bool = Field(
        default=False, description="True if action sequence stepped up from low to high consequence",
    )
    pressure_present: bool = Field(
        default=False, description="True if time pressure or FOMO language is present",
    )
    repeated_request_present: bool = Field(
        default=False, description="True if an action request was repeated across sequence",
    )
    user_override_present: bool = Field(
        default=False, description="True if user previously confirmed continuing past a warning",
    )
    rapid_escalation_present: bool = Field(
        default=False, description="True if escalation occurred within rapid escalation threshold",
    )
    information_to_transaction_shift: bool = Field(
        default=False, description="True if interaction shifted from information to financial extraction",
    )
    persistent_payment_present: bool = Field(
        default=False, description="True if payment was requested repeatedly or after decline",
    )
    persistent_credential_present: bool = Field(
        default=False, description="True if credential access was requested repeatedly",
    )


class BehaviouralProvenance(BaseModel):
    """Audit metadata for Engine 10 execution."""
    engine_version: str = Field(default=ENGINE_VERSION, description="Engine 10 release version")
    analyzed_at: str = Field(description="ISO 8601 execution timestamp")
    content_id: Optional[str] = Field(default=None, description="NormalizedContent ID processed")
    claims_count: int = Field(default=0, description="Number of claims evaluated")
    actions_count: int = Field(default=0, description="Number of actions evaluated")
    events_count: int = Field(default=0, description="Number of session events evaluated")
    session_id: Optional[str] = Field(default=None, description="Referenced session ID if any")


class BehaviouralAnalysis(BaseModel):
    """Canonical output schema for Engine 10: Behavioural Signal Intelligence Engine."""
    analysis_id: str = Field(description="Unique behavioural analysis identifier (e.g. BHA-001)")
    signals: list[BehaviouralSignal] = Field(default_factory=list, description="Atomic behavioural signals detected")
    findings: list[BehaviouralFinding] = Field(default_factory=list, description="Structured behavioural findings")
    session_summary: SessionBehaviourSummary = Field(description="Statistical and chronological session summary")
    policy_hints: BehaviouralPolicyHints = Field(description="Structured objective observations for Engine 8")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence that identified behavioural patterns exist (NOT scam probability)",
    )
    provenance: BehaviouralProvenance = Field(description="Provenance and execution audit trail")
    upstream_references: dict[str, Any] = Field(default_factory=dict, description="Referenced upstream IDs")
    engine_version: str = Field(default=ENGINE_VERSION, description="Engine 10 release version")

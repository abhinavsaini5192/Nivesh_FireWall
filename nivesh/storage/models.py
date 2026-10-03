"""SQLAlchemy persistent data models for Nivesh Firewall.

Defines normalized relational entities for:
- Analyses and telemetry
- Engine 8 Policy Decisions
- Structured Analysis Results
- Engine 7 Scam Fingerprints & Collective Threat Intelligence
- Engine 10 Sessions & Interaction Sequences
- Security Audit Records

Strict Privacy Safeguards:
- No raw passwords, OTPs, PINs, CVVs, card numbers, or bank account credentials.
- No continuous keystroke or unrestricted browsing history logging.
- Structural threat intelligence is strictly isolated from user/session identities.
"""

from typing import Optional, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AnalysisModel(Base):
    """Persistent representation of a completed or degraded Nivesh analysis."""
    __tablename__ = "analyses"

    analysis_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), nullable=True, index=True)
    pipeline_status = Column(String(32), nullable=False, index=True)
    created_at = Column(String(64), nullable=False, index=True)
    completed_at = Column(String(64), nullable=True)
    duration_ms = Column(Float, default=0.0)
    input_type = Column(String(32), nullable=False)
    channel = Column(String(64), nullable=False, index=True)
    content_id = Column(String(64), nullable=True)
    content_summary = Column(Text, nullable=True)  # Up to 200 chars normalized summary
    contains_financial_content = Column(Boolean, default=True)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)

    # 1:1 Relationships
    policy_decision = relationship(
        "PolicyDecisionModel",
        uselist=False,
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    result = relationship(
        "AnalysisResultModel",
        uselist=False,
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    # 1:N Relationships
    engine_executions = relationship(
        "EngineExecutionModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class PolicyDecisionModel(Base):
    """Persistent Engine 8 safety policy decision snapshot."""
    __tablename__ = "policy_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision_id = Column(String(64), unique=True, nullable=True, index=True)
    analysis_id = Column(
        String(64),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    decision = Column(String(32), nullable=False, index=True)
    severity = Column(String(32), nullable=False)
    primary_reason = Column(Text, nullable=False)
    reason_codes = Column(JSON, nullable=False, default=list)
    user_message = Column(Text, nullable=False)
    technical_message = Column(Text, nullable=False)
    actions_required = Column(JSON, nullable=False, default=list)
    required_user_confirmation = Column(Boolean, default=False)
    cooldown_seconds = Column(Integer, nullable=True)
    policy_version = Column(String(32), nullable=False, default="8.0.0")
    created_at = Column(String(64), nullable=False)

    analysis = relationship("AnalysisModel", back_populates="policy_decision")


class AnalysisResultModel(Base):
    """Persisted structured intelligence snapshot across all engines."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        String(64),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    content_summary_json = Column(JSON, nullable=False, default=dict)
    claims_json = Column(JSON, nullable=False, default=list)
    actions_json = Column(JSON, nullable=False, default=list)
    evidence_json = Column(JSON, nullable=False, default=dict)
    identity_json = Column(JSON, nullable=False, default=dict)
    threat_json = Column(JSON, nullable=False, default=dict)
    fingerprint_json = Column(JSON, nullable=False, default=dict)
    behaviour_json = Column(JSON, nullable=False, default=dict)
    provenance_json = Column(JSON, nullable=False, default=dict)
    warnings_json = Column(JSON, nullable=False, default=list)
    errors_json = Column(JSON, nullable=False, default=list)

    analysis = relationship("AnalysisModel", back_populates="result")


class EngineExecutionModel(Base):
    """Engine telemetry and execution audit record."""
    __tablename__ = "engine_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        String(64),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engine_key = Column(String(64), nullable=False, index=True)
    engine_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    started_at = Column(String(64), nullable=False)
    completed_at = Column(String(64), nullable=True)
    duration_ms = Column(Float, default=0.0)
    output_id = Column(String(128), nullable=True)
    error_type = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=False, default=dict)

    analysis = relationship("AnalysisModel", back_populates="engine_executions")


class FingerprintModel(Base):
    """Structural collective threat memory for Engine 7.
    
    Contains NO personal identifiers, contact details, credentials, or raw message bodies.
    """
    __tablename__ = "fingerprints"

    fingerprint_id = Column(String(64), primary_key=True)
    schema_version = Column(String(16), default="1.0")

    # Structural patterns
    identity_patterns = Column(JSON, nullable=False, default=list)
    claim_patterns = Column(JSON, nullable=False, default=list)
    action_patterns = Column(JSON, nullable=False, default=list)
    channel_patterns = Column(JSON, nullable=False, default=list)
    technical_patterns = Column(JSON, nullable=False, default=list)
    threat_patterns = Column(JSON, nullable=False, default=list)
    attack_stages = Column(JSON, nullable=False, default=list)
    attack_transitions = Column(JSON, nullable=False, default=list)
    evidence_patterns = Column(JSON, nullable=False, default=list)
    threat_families = Column(JSON, nullable=False, default=list)

    # Canonical Features & Signatures
    canonical_features = Column(JSON, nullable=False, default=list)
    exact_signature = Column(String(128), nullable=False, index=True)
    semantic_signature = Column(String(128), nullable=False, index=True)
    attack_path_signature = Column(String(256), nullable=False, index=True)

    # Observation metadata
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)
    first_seen = Column(String(64), nullable=False)
    last_seen = Column(String(64), nullable=False)
    observation_count = Column(Integer, nullable=False, default=1)
    distinct_channels = Column(JSON, nullable=False, default=list)
    distinct_variants = Column(Integer, nullable=False, default=1)

    # Lifecycle & Disputes
    status = Column(String(32), nullable=False, default="NEW", index=True)
    dispute_count = Column(Integer, nullable=False, default=0)
    dispute_notes = Column(JSON, nullable=False, default=list)
    status_change_history = Column(JSON, nullable=False, default=list)
    related_fingerprint_ids = Column(JSON, nullable=False, default=list)
    content_hashes = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=False, default="")

    observations = relationship(
        "FingerprintObservationModel",
        back_populates="fingerprint",
        cascade="all, delete-orphan",
    )


class FingerprintObservationModel(Base):
    """Individual observation tied to a structural fingerprint."""
    __tablename__ = "fingerprint_observations"

    observation_id = Column(String(64), primary_key=True)
    fingerprint_id = Column(
        String(64),
        ForeignKey("fingerprints.fingerprint_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id = Column(String(64), nullable=False)
    observed_at = Column(String(64), nullable=False, index=True)
    channel = Column(String(64), nullable=True)
    features = Column(JSON, nullable=False, default=list)
    content_hash = Column(String(128), nullable=True, index=True)
    is_duplicate_origin = Column(Boolean, default=False)
    match_type = Column(String(32), nullable=False)
    match_confidence = Column(Float, nullable=False)
    matched_dimensions = Column(JSON, nullable=False, default=list)
    provenance = Column(JSON, nullable=False, default=dict)

    fingerprint = relationship("FingerprintModel", back_populates="observations")


class SessionModel(Base):
    """Engine 10 interaction session metadata container."""
    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True)
    started_at = Column(String(64), nullable=True)
    last_event_at = Column(String(64), nullable=True)
    event_count = Column(Integer, default=0)
    source_type = Column(String(64), nullable=True)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    events = relationship(
        "SessionEventModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionEventModel.sequence_index",
    )


class SessionEventModel(Base):
    """Sanitized interaction step event within a session sequence."""
    __tablename__ = "session_events"

    event_id = Column(String(64), primary_key=True)
    session_id = Column(
        String(64),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    action_id = Column(String(64), nullable=True)
    claim_id = Column(String(64), nullable=True)
    decision_id = Column(String(64), nullable=True)
    channel = Column(String(64), nullable=True)
    sequence_index = Column(Integer, default=0)
    user_initiated = Column(Boolean, default=False)
    system_initiated = Column(Boolean, default=True)
    source_type = Column(String(64), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    session = relationship("SessionModel", back_populates="events")


class AuditRecordModel(Base):
    """Security and compliance audit trail."""
    __tablename__ = "audit_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    actor = Column(String(64), nullable=False, default="system")
    details = Column(JSON, nullable=False, default=dict)
    timestamp = Column(String(64), nullable=False, index=True)

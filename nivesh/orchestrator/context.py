"""Canonical Unified Analysis Context for Nivesh Firewall (Phase 11.2).

Represents the single case record for one analyzed financial interaction:
from raw input ingestion through content, claim, action, source, evidence,
threat, fingerprint, identity, behavioural intelligence, and final policy decision.

Coordinates existing engine outputs without duplicating engine intelligence.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator

from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis
from nivesh.identity.schemas import IdentityAnalysis
from nivesh.behaviour.schemas import BehaviouralAnalysis
from nivesh.policy.schemas import PolicyDecision

from .state import FORBIDDEN_METADATA_KEYS


class PipelineStatus(str, Enum):
    """Overall status of an orchestration analysis pipeline run."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EngineStatus(str, Enum):
    """Execution status of an individual intelligence engine."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ContextLifecycleStage(str, Enum):
    """Lifecycle progress stage of the unified analysis context."""
    CREATED = "CREATED"
    CONTENT_READY = "CONTENT_READY"
    CLAIMS_READY = "CLAIMS_READY"
    ACTIONS_READY = "ACTIONS_READY"
    SOURCES_READY = "SOURCES_READY"
    EVIDENCE_READY = "EVIDENCE_READY"
    DOWNSTREAM_INTELLIGENCE_READY = "DOWNSTREAM_INTELLIGENCE_READY"
    BEHAVIOUR_READY = "BEHAVIOUR_READY"
    POLICY_READY = "POLICY_READY"
    COMPLETED = "COMPLETED"


ALL_ENGINE_KEYS: list[str] = [
    "engine_1_content",
    "engine_2_claims",
    "engine_3_actions",
    "engine_4_sources",
    "engine_5_evidence",
    "engine_6_threat",
    "engine_7_fingerprint",
    "engine_9_identity",
    "engine_10_behaviour",
    "engine_8_policy",
]

ENGINE_NAMES: dict[str, str] = {
    "engine_1_content": "Engine 1: Content Intelligence Engine",
    "engine_2_claims": "Engine 2: Claim Intelligence Engine",
    "engine_3_actions": "Engine 3: Action Intelligence Engine",
    "engine_4_sources": "Engine 4: Source Intelligence Engine",
    "engine_5_evidence": "Engine 5: Evidence Verification Engine",
    "engine_6_threat": "Engine 6: Threat & Attack-Path Intelligence",
    "engine_7_fingerprint": "Engine 7: Scam Fingerprint & Collective Intelligence",
    "engine_9_identity": "Engine 9: Identity Verification & Entity Resolution",
    "engine_10_behaviour": "Engine 10: Behavioural Signal Intelligence",
    "engine_8_policy": "Engine 8: Policy & Intervention Engine",
}


class EngineExecutionState(BaseModel):
    """Tracks execution details for an individual intelligence engine within the context."""
    engine_name: str = Field(description="Human-readable engine name")
    engine_key: str = Field(description="Machine-readable engine key e.g. engine_1_content")
    status: EngineStatus = Field(default=EngineStatus.PENDING, description="Execution status")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp when engine execution started")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp when engine execution finished")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    result_id: Optional[str] = Field(default=None, description="Produced result identifier if completed")
    analytical_result: Optional[str] = Field(default=None, description="Expected analytical outcome (e.g. NO_MATCH, SOURCE_UNAVAILABLE)")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code if failed")
    error_message: Optional[str] = Field(default=None, description="Sanitized error description if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe execution metadata")


class ContextSnapshot(BaseModel):
    """Lightweight, safe structural snapshot of analysis state for observability and monitoring."""
    analysis_id: str
    session_id: Optional[str] = None
    status: PipelineStatus
    stage: ContextLifecycleStage
    completed_engines: list[str] = Field(default_factory=list)
    pending_engines: list[str] = Field(default_factory=list)
    failed_engines: list[str] = Field(default_factory=list)
    skipped_engines: list[str] = Field(default_factory=list)
    partial_engines: list[str] = Field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0
    policy_decision: Optional[str] = None


def is_sensitive_key(key: str) -> bool:
    """Check if a metadata or payload key represents sensitive credential/financial information."""
    kl = key.lower()
    if kl in FORBIDDEN_METADATA_KEYS:
        return True
    for sensitive_term in (
        "password", "passwd", "otp", "pin", "cvv", "card_number",
        "account_number", "bearer", "secret", "api_key", "apikey",
        "private_key", "token", "credential", "keystroke",
    ):
        if sensitive_term in kl:
            return True
    return False


class AnalysisContext(BaseModel):
    """The canonical Unified Analysis Context representing one complete Nivesh Firewall analysis.

    Acts as the single case record connecting all 10 intelligence engines from
    raw input to final intervention decision without duplicating engine intelligence.
    """
    # 1. Identity & Lifecycle
    analysis_id: str = Field(description="Unique correlation identifier for this analysis request")
    session_id: Optional[str] = Field(default=None, description="Optional interaction session identifier")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: PipelineStatus = Field(default=PipelineStatus.CREATED, description="Overall pipeline status")
    stage: ContextLifecycleStage = Field(default=ContextLifecycleStage.CREATED, description="Current lifecycle stage")

    # 2. Input & Reference Information
    input_type: str = Field(default="text", description="Input type: text, url, or image")
    channel: str = Field(default="unknown", description="Ingestion channel e.g. web, telegram, whatsapp")
    content_reference: Optional[str] = Field(default=None, description="Reference ID to normalized content")
    request_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Sanitized request metadata without PII or credentials"
    )

    # 3. Canonical Engine Outputs (Strongly Typed)
    content: Optional[NormalizedContent] = Field(default=None, description="Engine 1: Normalized input content")
    claims: Optional[ClaimAnalysis] = Field(default=None, description="Engine 2: Extracted canonical claims")
    actions: Optional[ActionAnalysis] = Field(default=None, description="Engine 3: Extracted canonical actions")
    sources: Optional[SourceAnalysis] = Field(default=None, description="Engine 4: Retrieved source documents")
    evidence: Optional[EvidenceAnalysis] = Field(default=None, description="Engine 5: Verified evidence results")
    threat: Optional[ThreatAnalysis] = Field(default=None, description="Engine 6: Threat signals & attack path")
    fingerprint: Optional[FingerprintAnalysis] = Field(default=None, description="Engine 7: Scam fingerprint analysis")
    identity: Optional[IdentityAnalysis] = Field(default=None, description="Engine 9: Identity verification results")
    behaviour: Optional[BehaviouralAnalysis] = Field(default=None, description="Engine 10: Behavioural sequence signals")
    policy: Optional[PolicyDecision] = Field(default=None, description="Engine 8: Final policy intervention decision")

    # 4. Execution State & Telemetry
    engine_states: dict[str, EngineExecutionState] = Field(
        default_factory=dict, description="Execution status for each engine"
    )
    execution_metadata: dict[str, Any] = Field(default_factory=dict, description="Pipeline execution metadata")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings recorded during execution")
    errors: list[str] = Field(default_factory=list, description="Errors recorded if any engine failed")

    # 5. Traceability & Correlation
    upstream_references: dict[str, list[str]] = Field(
        default_factory=dict, description="Mapping of engine key to input result IDs consumed"
    )
    engine_result_ids: dict[str, str] = Field(
        default_factory=dict, description="Correlated result IDs from all completed engines"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Provenance audit trail"
    )

    def model_post_init(self, __context: Any) -> None:
        """Initialize engine states and scrub sensitive request metadata."""
        # Ensure request metadata is sanitized
        if self.request_metadata:
            bad_keys = [k for k in self.request_metadata if is_sensitive_key(k)]
            for k in bad_keys:
                self.request_metadata.pop(k, None)

        # Initialize engine execution states for all 10 canonical engines
        for key in ALL_ENGINE_KEYS:
            if key not in self.engine_states:
                self.engine_states[key] = EngineExecutionState(
                    engine_name=ENGINE_NAMES.get(key, key),
                    engine_key=key,
                    status=EngineStatus.PENDING,
                )

        if not self.engine_result_ids:
            self.engine_result_ids["analysis_id"] = self.analysis_id

    # --------------------------------------------------------------------------
    # Controlled Execution State Transitions (Section 15)
    # --------------------------------------------------------------------------

    def mark_engine_started(self, engine_key: str, engine_name: Optional[str] = None) -> None:
        """Record that an engine invocation has started."""
        now_iso = datetime.now(timezone.utc).isoformat()
        if engine_key not in self.engine_states:
            self.engine_states[engine_key] = EngineExecutionState(
                engine_name=engine_name or ENGINE_NAMES.get(engine_key, engine_key),
                engine_key=engine_key,
            )
        state = self.engine_states[engine_key]
        state.status = EngineStatus.RUNNING
        state.started_at = now_iso
        self.updated_at = now_iso

        if self.status == PipelineStatus.CREATED:
            self.status = PipelineStatus.RUNNING

    def mark_engine_completed(
        self,
        engine_key: str,
        result_id: Optional[str] = None,
        analytical_result: Optional[str] = None,
        duration_ms: float = 0.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record successful completion of an engine invocation."""
        now_iso = datetime.now(timezone.utc).isoformat()
        state = self.engine_states.get(engine_key)
        if not state:
            state = EngineExecutionState(
                engine_name=ENGINE_NAMES.get(engine_key, engine_key),
                engine_key=engine_key,
            )
            self.engine_states[engine_key] = state

        state.status = EngineStatus.COMPLETED
        state.completed_at = now_iso
        state.duration_ms = duration_ms
        if result_id:
            state.result_id = result_id
            self.engine_result_ids[engine_key] = result_id
        if analytical_result:
            state.analytical_result = analytical_result
        if metadata:
            state.metadata.update(metadata)

        self.updated_at = now_iso

    def mark_engine_failed(
        self,
        engine_key: str,
        error_message: str,
        error_code: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """Record an engine failure (recoverable or fatal)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        state = self.engine_states.get(engine_key)
        if not state:
            state = EngineExecutionState(
                engine_name=ENGINE_NAMES.get(engine_key, engine_key),
                engine_key=engine_key,
            )
            self.engine_states[engine_key] = state

        state.status = EngineStatus.FAILED
        state.completed_at = now_iso
        state.duration_ms = duration_ms
        state.error_message = error_message
        state.error_code = error_code or "ENGINE_ERROR"
        self.errors.append(f"{state.engine_name}: {error_message}")
        self.updated_at = now_iso

    def mark_engine_skipped(self, engine_key: str, reason: Optional[str] = None) -> None:
        """Record that an optional or downstream engine was skipped."""
        now_iso = datetime.now(timezone.utc).isoformat()
        state = self.engine_states.get(engine_key)
        if not state:
            state = EngineExecutionState(
                engine_name=ENGINE_NAMES.get(engine_key, engine_key),
                engine_key=engine_key,
            )
            self.engine_states[engine_key] = state

        state.status = EngineStatus.SKIPPED
        state.completed_at = now_iso
        if reason:
            state.metadata["skip_reason"] = reason
            self.warnings.append(f"{state.engine_name} skipped: {reason}")
        self.updated_at = now_iso

    # --------------------------------------------------------------------------
    # Controlled Engine Result Setters (Section 15)
    # --------------------------------------------------------------------------

    def set_content_result(self, content: NormalizedContent) -> None:
        """Attach Engine 1 NormalizedContent."""
        self.content = content
        self.content_reference = content.content_id
        self.engine_result_ids["content_id"] = content.content_id
        self.engine_result_ids["engine_1_content"] = content.content_id
        self.stage = ContextLifecycleStage.CONTENT_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_claim_result(self, claims: ClaimAnalysis) -> None:
        """Attach Engine 2 ClaimAnalysis."""
        self.claims = claims
        cid = getattr(claims, "analysis_id", getattr(claims, "content_id", "CLAIMS"))
        self.engine_result_ids["claims_id"] = cid
        self.engine_result_ids["engine_2_claims"] = cid
        if self.content:
            self.upstream_references["engine_2_claims"] = [self.content.content_id]
        self.stage = ContextLifecycleStage.CLAIMS_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_action_result(self, actions: ActionAnalysis) -> None:
        """Attach Engine 3 ActionAnalysis."""
        self.actions = actions
        aid = getattr(actions, "analysis_id", getattr(actions, "content_id", "ACTIONS"))
        self.engine_result_ids["actions_id"] = aid
        self.engine_result_ids["engine_3_actions"] = aid
        upstream = []
        if self.content:
            upstream.append(self.content.content_id)
        if self.claims:
            upstream.append(getattr(self.claims, "content_id", "CLAIMS"))
        self.upstream_references["engine_3_actions"] = upstream
        self.stage = ContextLifecycleStage.ACTIONS_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_source_result(self, sources: SourceAnalysis) -> None:
        """Attach Engine 4 SourceAnalysis."""
        self.sources = sources
        sid = getattr(sources, "analysis_id", getattr(sources, "content_id", "SOURCES"))
        self.engine_result_ids["sources_id"] = sid
        self.engine_result_ids["engine_4_sources"] = sid
        upstream = []
        if self.content:
            upstream.append(self.content.content_id)
        if self.claims:
            upstream.append(getattr(self.claims, "content_id", "CLAIMS"))
        if self.actions:
            upstream.append(getattr(self.actions, "content_id", "ACTIONS"))
        self.upstream_references["engine_4_sources"] = upstream
        self.stage = ContextLifecycleStage.SOURCES_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_evidence_result(self, evidence: EvidenceAnalysis) -> None:
        """Attach Engine 5 EvidenceAnalysis."""
        self.evidence = evidence
        eid = getattr(evidence, "analysis_id", getattr(evidence, "content_id", "EVIDENCE"))
        self.engine_result_ids["evidence_id"] = eid
        self.engine_result_ids["engine_5_evidence"] = eid
        upstream = []
        if self.content:
            upstream.append(self.content.content_id)
        if self.claims:
            upstream.append(getattr(self.claims, "content_id", "CLAIMS"))
        if self.sources:
            upstream.append(getattr(self.sources, "content_id", "SOURCES"))
        self.upstream_references["engine_5_evidence"] = upstream
        self.stage = ContextLifecycleStage.EVIDENCE_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_threat_result(self, threat: ThreatAnalysis) -> None:
        """Attach Engine 6 ThreatAnalysis."""
        self.threat = threat
        self.engine_result_ids["threat_id"] = threat.content_id
        self.engine_result_ids["engine_6_threat"] = threat.content_id
        self.stage = ContextLifecycleStage.DOWNSTREAM_INTELLIGENCE_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_fingerprint_result(self, fingerprint: FingerprintAnalysis) -> None:
        """Attach Engine 7 FingerprintAnalysis."""
        self.fingerprint = fingerprint
        fpid = fingerprint.fingerprint.fingerprint_id
        self.engine_result_ids["fingerprint_id"] = fpid
        self.engine_result_ids["engine_7_fingerprint"] = fpid
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_identity_result(self, identity: IdentityAnalysis) -> None:
        """Attach Engine 9 IdentityAnalysis."""
        self.identity = identity
        self.engine_result_ids["identity_id"] = identity.analysis_id
        self.engine_result_ids["engine_9_identity"] = identity.analysis_id
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_behaviour_result(self, behaviour: BehaviouralAnalysis) -> None:
        """Attach Engine 10 BehaviouralAnalysis."""
        # Consistency check for session correlation
        bh_session = getattr(behaviour, "session_id", None)
        if not bh_session and hasattr(behaviour, "session_summary") and behaviour.session_summary:
            bh_session = getattr(behaviour.session_summary, "session_id", None)
        if not bh_session and hasattr(behaviour, "provenance") and behaviour.provenance:
            bh_session = getattr(behaviour.provenance, "session_id", None)

        if self.session_id and bh_session:
            if bh_session != self.session_id:
                raise ValueError(
                    f"Session correlation mismatch: context session '{self.session_id}' "
                    f"does not match behaviour session '{bh_session}'"
                )
        self.behaviour = behaviour
        self.engine_result_ids["behaviour_id"] = behaviour.analysis_id
        self.engine_result_ids["engine_10_behaviour"] = behaviour.analysis_id
        self.stage = ContextLifecycleStage.BEHAVIOUR_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_policy_result(self, policy: PolicyDecision) -> None:
        """Attach Engine 8 PolicyDecision with validation enforcement."""
        # Enforce consistency: Policy cannot be finalized without required upstream intelligence
        if not self.content:
            raise ValueError("Policy cannot be finalized: Engine 1 content is missing.")
        if not self.claims:
            raise ValueError("Policy cannot be finalized: Engine 2 claims are missing.")
        if not self.actions:
            raise ValueError("Policy cannot be finalized: Engine 3 actions are missing.")
        if not self.sources:
            raise ValueError("Policy cannot be finalized: Engine 4 sources are missing.")
        if not self.evidence:
            raise ValueError("Policy cannot be finalized: Engine 5 evidence is missing.")

        self.policy = policy
        self.engine_result_ids["policy_id"] = policy.decision_id
        self.engine_result_ids["engine_8_policy"] = policy.decision_id
        self.stage = ContextLifecycleStage.POLICY_READY
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def finalize_pipeline(self) -> None:
        """Finalize pipeline lifecycle status."""
        if self.errors and not self.policy:
            self.status = PipelineStatus.FAILED
        elif self.errors:
            self.status = PipelineStatus.PARTIAL
        else:
            self.status = PipelineStatus.COMPLETED

        self.stage = ContextLifecycleStage.COMPLETED
        self.updated_at = datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------------------------------
    # Observability, Snapshot & Safe Serialization (Sections 17 & 18)
    # --------------------------------------------------------------------------

    def get_snapshot(self) -> ContextSnapshot:
        """Generate a lightweight, safe structural snapshot of the current analysis state."""
        completed: list[str] = []
        pending: list[str] = []
        failed: list[str] = []
        skipped: list[str] = []
        partial: list[str] = []

        for key in ALL_ENGINE_KEYS:
            st = self.engine_states.get(key)
            if not st or st.status == EngineStatus.PENDING:
                pending.append(key)
            elif st.status == EngineStatus.COMPLETED:
                completed.append(key)
            elif st.status == EngineStatus.FAILED:
                failed.append(key)
            elif st.status == EngineStatus.SKIPPED:
                skipped.append(key)
            elif st.status == EngineStatus.PARTIAL:
                partial.append(key)

        decision_str = self.policy.decision.value if self.policy else None

        return ContextSnapshot(
            analysis_id=self.analysis_id,
            session_id=self.session_id,
            status=self.status,
            stage=self.stage,
            completed_engines=completed,
            pending_engines=pending,
            failed_engines=failed,
            skipped_engines=skipped,
            partial_engines=partial,
            warnings_count=len(self.warnings),
            errors_count=len(self.errors),
            policy_decision=decision_str,
        )

    def to_safe_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary while strictly preventing credential/PII leakage."""
        data = self.model_dump()
        self._scrub_sensitive(data)
        return data

    @classmethod
    def _scrub_sensitive(cls, obj: Any) -> None:
        """Recursively scrub any prohibited keys from dictionary data."""
        if isinstance(obj, dict):
            keys_to_remove = [k for k in obj if is_sensitive_key(k)]
            for k in keys_to_remove:
                del obj[k]
            for v in obj.values():
                cls._scrub_sensitive(v)
        elif isinstance(obj, list):
            for item in obj:
                cls._scrub_sensitive(item)

    def validate_consistency(self) -> None:
        """Verify internal consistency of analysis state."""
        # 1. Status consistency: No engine can be both COMPLETED and FAILED
        for key, st in self.engine_states.items():
            if st.status == EngineStatus.FAILED and st.result_id and not st.error_message:
                raise ValueError(f"Inconsistent state for {key}: marked FAILED but has valid result_id without error.")

        # 2. Policy consistency: Policy requires upstream presence
        if self.policy and not (self.content and self.claims and self.actions and self.sources and self.evidence):
            raise ValueError("Policy decision is present without required upstream intelligence engines.")

        # 3. Correlation consistency: Output IDs must align with attached objects
        if self.content and self.engine_result_ids.get("content_id") != self.content.content_id:
            raise ValueError("content_id in engine_result_ids does not match attached content object.")
        if self.policy and self.engine_result_ids.get("policy_id") != self.policy.decision_id:
            raise ValueError("policy_id in engine_result_ids does not match attached policy object.")

"""Product-level orchestration result for Nivesh Firewall.

Provides unified access to the final policy decision, intermediate engine results,
correlation IDs, execution telemetry, provenance, and error metadata.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field

from nivesh.policy.schemas import PolicyDecision, PolicyDecisionType
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis
from nivesh.identity.schemas import IdentityAnalysis
from nivesh.behaviour.schemas import BehaviouralAnalysis
from .state import OrchestrationState
from .telemetry import PipelineTelemetry
from .context import AnalysisContext


class OrchestrationResult(BaseModel):
    """Unified result produced by the Product Orchestrator."""
    analysis_id: str = Field(description="Unique correlation identifier for the analysis")
    session_id: Optional[str] = Field(default=None, description="Interaction session identifier if tracked")
    pipeline_status: str = Field(
        default="COMPLETED",
        description="Overall pipeline completion status: COMPLETED, DEGRADED, FAILED",
    )
    policy_decision: Optional[PolicyDecision] = Field(
        default=None,
        description="Engine 8 policy decision (sole final policy authority)",
    )
    state: OrchestrationState = Field(
        description="Full structured execution state holding intermediate engine objects",
    )
    context: Optional[AnalysisContext] = Field(
        default=None,
        description="Canonical Unified Analysis Context representing the complete case record",
    )
    engine_output_ids: dict[str, str] = Field(
        default_factory=dict,
        description="Correlated identifiers of all completed engine outputs",
    )
    telemetry: PipelineTelemetry = Field(
        description="Timing and status telemetry for all invoked engines",
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance audit trail (engines executed, versions, timestamps)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings recorded during execution",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Error summaries if any engine failed recoverably or fatally",
    )

    @property
    def is_success(self) -> bool:
        """True if pipeline completed without errors and produced a policy decision."""
        return self.pipeline_status in ("COMPLETED", "DEGRADED") and self.policy_decision is not None

    @property
    def is_degraded(self) -> bool:
        """True if one or more engines failed recoverably but a policy decision was reached."""
        return self.pipeline_status == "DEGRADED"

    @property
    def decision(self) -> Optional[PolicyDecisionType]:
        """Convenience accessor for Engine 8's final policy decision."""
        return self.policy_decision.decision if self.policy_decision else None

    @property
    def reason_codes(self) -> list[str]:
        """Convenience accessor for Engine 8 reason codes."""
        return self.policy_decision.reason_codes if self.policy_decision else []

    @property
    def primary_reason(self) -> Optional[str]:
        """Convenience accessor for Engine 8 primary reason message."""
        return self.policy_decision.primary_reason if self.policy_decision else None

    @property
    def user_message(self) -> Optional[str]:
        """Convenience accessor for Engine 8 user explanation."""
        return self.policy_decision.user_message if self.policy_decision else None

    @property
    def content(self) -> Optional[NormalizedContent]:
        """Engine 1: Normalized content."""
        return self.state.content

    @property
    def claims(self) -> Optional[ClaimAnalysis]:
        """Engine 2: Extracted canonical claims."""
        return self.state.claims

    @property
    def actions(self) -> Optional[ActionAnalysis]:
        """Engine 3: Extracted canonical actions."""
        return self.state.actions

    @property
    def sources(self) -> Optional[SourceAnalysis]:
        """Engine 4: Retrieved source documents."""
        return self.state.sources

    @property
    def evidence(self) -> Optional[EvidenceAnalysis]:
        """Engine 5: Verified evidence results."""
        return self.state.evidence

    @property
    def threat(self) -> Optional[ThreatAnalysis]:
        """Engine 6: Threat signals & attack path."""
        return self.state.threat

    @property
    def fingerprint(self) -> Optional[FingerprintAnalysis]:
        """Engine 7: Scam fingerprint analysis."""
        return self.state.fingerprint

    @property
    def identity(self) -> Optional[IdentityAnalysis]:
        """Engine 9: Identity verification results."""
        return self.state.identity

    @property
    def behaviour(self) -> Optional[BehaviouralAnalysis]:
        """Engine 10: Behavioural sequence signals."""
        return self.state.behaviour


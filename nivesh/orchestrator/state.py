"""Shared execution state for the Product Orchestrator.

Holds structured references to all intermediate and final engine analyses,
correlation identifiers, session metadata, execution status, and telemetry.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field

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
from .telemetry import PipelineTelemetry


# Prohibited metadata keys to prevent sensitive credential storage in state
FORBIDDEN_METADATA_KEYS = frozenset({
    "password", "passwd", "pwd", "otp", "pin", "cvv", "cvv2", "card_number",
    "card_numbers", "account_number", "account_numbers", "bank_account",
    "bank_account_number", "bank_account_numbers", "secret", "token", "auth_token",
    "api_key", "apikey", "access_token", "bearer", "authorization",
    "private_key", "credential", "credentials", "raw_credentials",
    "keystrokes", "keystroke", "raw_message", "message_body", "sms_body", "contact_list",
})


class OrchestrationState(BaseModel):
    """Encapsulates the full execution lifecycle and intermediate outputs of a pipeline run."""
    analysis_id: str = Field(description="Unique correlation identifier for this orchestration run")
    session_id: Optional[str] = Field(default=None, description="Optional interaction session identifier")
    request_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Sanitized client request metadata without PII or credentials"
    )
    started_at: str = Field(description="ISO 8601 start timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO 8601 completion timestamp")
    status: str = Field(
        default="RUNNING",
        description="Overall pipeline status: PENDING, RUNNING, COMPLETED, DEGRADED, FAILED",
    )

    # Engine Intermediate & Final Outputs
    content: Optional[NormalizedContent] = Field(default=None, description="Engine 1: Normalized content")
    claims: Optional[ClaimAnalysis] = Field(default=None, description="Engine 2: Extracted canonical claims")
    actions: Optional[ActionAnalysis] = Field(default=None, description="Engine 3: Extracted canonical actions")
    sources: Optional[SourceAnalysis] = Field(default=None, description="Engine 4: Retrieved source documents")
    evidence: Optional[EvidenceAnalysis] = Field(default=None, description="Engine 5: Verified evidence results")
    threat: Optional[ThreatAnalysis] = Field(default=None, description="Engine 6: Threat signals & attack path")
    fingerprint: Optional[FingerprintAnalysis] = Field(default=None, description="Engine 7: Scam fingerprint analysis")
    identity: Optional[IdentityAnalysis] = Field(default=None, description="Engine 9: Identity verification results")
    behaviour: Optional[BehaviouralAnalysis] = Field(default=None, description="Engine 10: Behavioural sequence signals")
    policy: Optional[PolicyDecision] = Field(default=None, description="Engine 8: Final policy intervention decision")

    # Observability & Errors
    telemetry: PipelineTelemetry = Field(default_factory=PipelineTelemetry, description="Per-engine execution telemetry")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warning messages")
    errors: list[str] = Field(default_factory=list, description="Recoverable or fatal error summaries")

    def model_post_init(self, __context: Any) -> None:
        """Sanitize request metadata to prevent sensitive key retention."""
        if self.request_metadata:
            lowered = {k.lower(): k for k in self.request_metadata}
            for forbidden in FORBIDDEN_METADATA_KEYS:
                if forbidden in lowered:
                    self.request_metadata.pop(lowered[forbidden], None)

    def get_output_ids(self) -> dict[str, str]:
        """Return a mapping of engine keys to their produced output identifiers."""
        ids: dict[str, str] = {"analysis_id": self.analysis_id}
        if self.content and hasattr(self.content, "content_id"):
            ids["content_id"] = self.content.content_id
            ids["engine_1_content"] = self.content.content_id
        if self.claims and hasattr(self.claims, "content_id"):
            ids["claims_id"] = self.claims.content_id
            ids["engine_2_claims"] = self.claims.content_id
        if self.actions and hasattr(self.actions, "content_id"):
            ids["actions_id"] = self.actions.content_id
            ids["engine_3_actions"] = self.actions.content_id
        if self.sources and hasattr(self.sources, "content_id"):
            ids["sources_id"] = self.sources.content_id
            ids["engine_4_sources"] = self.sources.content_id
        if self.evidence and hasattr(self.evidence, "content_id"):
            ids["evidence_id"] = self.evidence.content_id
            ids["engine_5_evidence"] = self.evidence.content_id
        if self.threat and hasattr(self.threat, "content_id"):
            ids["threat_id"] = self.threat.content_id
            ids["engine_6_threat"] = self.threat.content_id
        if self.fingerprint and hasattr(self.fingerprint, "fingerprint"):
            ids["fingerprint_id"] = self.fingerprint.fingerprint.fingerprint_id
            ids["engine_7_fingerprint"] = self.fingerprint.fingerprint.fingerprint_id
        if self.identity and hasattr(self.identity, "analysis_id"):
            ids["identity_id"] = self.identity.analysis_id
            ids["engine_9_identity"] = self.identity.analysis_id
        if self.behaviour and hasattr(self.behaviour, "analysis_id"):
            ids["behaviour_id"] = self.behaviour.analysis_id
            ids["engine_10_behaviour"] = self.behaviour.analysis_id
        if self.policy and hasattr(self.policy, "decision_id"):
            ids["policy_id"] = self.policy.decision_id
            ids["engine_8_policy"] = self.policy.decision_id
        return ids

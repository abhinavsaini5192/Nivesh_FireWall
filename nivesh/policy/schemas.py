"""Typed schemas for Engine 8: Policy & Intervention Engine.

Defines decision types, intervention scopes, severity tiers, input contexts,
and the canonical PolicyDecision model.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from nivesh.policy.config import POLICY_VERSION


class PolicyDecisionType(str, Enum):
    """Allowed intervention levels for user protection."""
    ALLOW = "ALLOW"
    INFORM = "INFORM"
    WARN = "WARN"
    PAUSE = "PAUSE"
    BLOCK = "BLOCK"


class InterventionScope(str, Enum):
    """Granularity of the safety intervention."""
    INFORMATION_ONLY = "INFORMATION_ONLY"
    CURRENT_ACTION = "CURRENT_ACTION"
    CURRENT_FLOW = "CURRENT_FLOW"
    CURRENT_CHANNEL = "CURRENT_CHANNEL"


class PolicySeverity(str, Enum):
    """Severity tier associated with the intervention."""
    NONE = "NONE"
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyContext(BaseModel):
    """Optional contextual parameters for policy evaluation."""
    user_override: Optional[bool] = Field(default=None, description="Explicit user override preference")
    previous_decision: Optional[str] = Field(default=None, description="Previous decision ID in the current session")
    interaction_state: Optional[str] = Field(default=None, description="State of the interaction flow (e.g., BROWSING, CHECKOUT, DOWNLOADING)")
    enforcement_capabilities: Optional[list[str]] = Field(default=None, description="Capabilities supported by the local client adapter")


class PolicyRuleResult(BaseModel):
    """Result produced by an individual policy rule evaluation."""
    rule_id: str = Field(description="Unique policy rule identifier")
    rule_name: str = Field(description="Human-readable rule name")
    decision: PolicyDecisionType = Field(description="Intervention level recommended by this rule")
    severity: PolicySeverity = Field(description="Severity tier")
    scope: InterventionScope = Field(description="Intervention scope")
    reason_codes: list[str] = Field(default_factory=list, description="Reason codes activated by this rule")
    primary_reason: str = Field(description="Main rationale for this rule firing")
    supporting_reasons: list[str] = Field(default_factory=list, description="Detailed explanatory points")
    triggered_signals: list[str] = Field(default_factory=list, description="Signals matching the rule condition")
    required_user_confirmation: bool = Field(default=False, description="Whether confirmation is required")
    cooldown_seconds: Optional[int] = Field(default=None, description="Recommended cooldown seconds")


class PolicyDecision(BaseModel):
    """Canonical output of Engine 8: Policy & Intervention Engine.

    Designed for consumption by downstream browser/desktop enforcement adapters
    and structured auditing systems.
    """
    decision_id: str = Field(description="Unique identifier for this policy decision (e.g., DEC-001)")
    decision: PolicyDecisionType = Field(description="Intervention level: ALLOW, INFORM, WARN, PAUSE, BLOCK")
    severity: str = Field(description="Severity tier: NONE, LOW, MEDIUM, HIGH, CRITICAL")
    reason_codes: list[str] = Field(default_factory=list, description="Machine-readable stable reason codes")
    primary_reason: str = Field(description="Primary explanation for the selected decision")
    supporting_reasons: list[str] = Field(default_factory=list, description="Detailed bullet points justifying the intervention")
    triggered_signals: list[str] = Field(default_factory=list, description="Threat signals and evidence codes that triggered the policy")
    relevant_claim_ids: list[str] = Field(default_factory=list, description="IDs of claims involved in the decision")
    relevant_action_ids: list[str] = Field(default_factory=list, description="IDs of actions involved in the decision")
    relevant_source_ids: list[str] = Field(default_factory=list, description="IDs of authoritative sources consulted")
    relevant_evidence_ids: list[str] = Field(default_factory=list, description="IDs of verification results involved")
    relevant_fingerprint_id: Optional[str] = Field(default=None, description="Matched collective threat fingerprint ID if any")
    intervention_scope: InterventionScope = Field(default=InterventionScope.CURRENT_ACTION, description="Scope of the safety intervention")
    required_user_confirmation: bool = Field(default=False, description="True if explicit user confirmation is required to proceed (True for PAUSE)")
    cooldown_seconds: Optional[int] = Field(default=None, description="Recommended cooldown/timeout before action can proceed")
    user_message: str = Field(description="Clear, non-accusatory message explaining the intervention to the user")
    technical_message: str = Field(description="Structured technical breakdown for auditing and enforcement adapters")
    policy_version: str = Field(default=POLICY_VERSION, description="Policy engine version (e.g. 8.0.0)")
    created_at: str = Field(description="ISO timestamp of policy decision")
    audit_metadata: dict[str, Any] = Field(default_factory=dict, description="Privacy-safe audit record without PII or credentials")

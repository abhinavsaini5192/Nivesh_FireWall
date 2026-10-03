"""Unified Firewall API Schemas for Nivesh Firewall (Phase 11.4).

Defines canonical product-level request, response, and error models
for the frontend-facing /api/v1/firewall endpoints:
- FirewallAnalyzeRequest
- FirewallAnalysisResponse
- FirewallApiError
- Structured summaries for Decision, Content, Claims, Actions, Evidence,
  Identity, Threat, Fingerprint, and Behaviour.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from nivesh.policy.schemas import PolicyContext
from nivesh.behaviour.event_model import InteractionHistory


class FirewallAnalyzeRequest(BaseModel):
    """Canonical request payload for the unified Nivesh Firewall API."""
    input_type: str = Field(
        default="text",
        description="Type of input: text, url, or image"
    )
    text: Optional[str] = Field(
        default=None,
        description="Raw unstructured text content to analyze"
    )
    url: Optional[str] = Field(
        default=None,
        description="Target URL to inspect and analyze"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded image bytes for multi-modal OCR analysis"
    )
    image_path: Optional[str] = Field(
        default=None,
        description="Local filesystem path to image (server use)"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Correlation identifier for multi-turn user session"
    )
    channel: str = Field(
        default="unknown",
        description="Origin channel: telegram, whatsapp, sms, web, email, etc."
    )
    interaction_history: Optional[InteractionHistory] = Field(
        default=None,
        description="Optional prior interaction sequence events"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional client metadata (scrubbed of secrets)"
    )
    policy_context: Optional[PolicyContext] = Field(
        default=None,
        description="Optional client policy context (user override, enforcement caps)"
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Optional idempotency key to prevent duplicate persistent side-effects"
    )


class FirewallExplanation(BaseModel):
    """Structured, non-accusatory explanation suitable for the frontend."""
    decision: str = Field(description="Intervention level (ALLOW, INFORM, WARN, PAUSE, BLOCK)")
    user_message: str = Field(description="Clear, non-accusatory message explaining the intervention to the user")
    technical_message: str = Field(description="Structured technical breakdown for auditing and enforcement adapters")
    primary_reason: str = Field(description="Primary explanation for the selected decision")
    supporting_signals: list[str] = Field(default_factory=list, description="Threat signals and evidence codes that triggered policy")


class FirewallDecisionSummary(BaseModel):
    """Canonical final decision section coming directly from Engine 8."""
    decision: str = Field(description="ALLOW, INFORM, WARN, PAUSE, BLOCK")
    severity: str = Field(description="NONE, INFORMATIONAL, LOW, MEDIUM, HIGH, CRITICAL")
    primary_reason: str = Field(description="Primary explanation for the selected decision")
    reason_codes: list[str] = Field(default_factory=list, description="Machine-readable policy reason codes")
    explanation: FirewallExplanation = Field(description="Human-readable and technical explanation")
    actions_required: list[str] = Field(default_factory=list, description="Action required by client adapter")
    required_user_confirmation: bool = Field(default=False, description="True if explicit user confirmation required to proceed")
    cooldown_seconds: Optional[int] = Field(default=None, description="Recommended cooldown before action can proceed")
    policy_version: str = Field(default="8.0.0", description="Engine 8 policy version")
    decision_id: Optional[str] = Field(default=None, description="Unique policy decision identifier")


class FirewallContentSummary(BaseModel):
    """High-level summary of parsed and normalized content."""
    content_id: str = Field(description="UUID of source NormalizedContent")
    input_type: str = Field(description="text, url, or image")
    channel: str = Field(description="Channel of origin")
    summary: str = Field(description="Normalized content snippet")
    contains_financial_content: bool = Field(default=False, description="Whether financial terminology or concepts are present")
    language: Optional[str] = Field(default=None, description="Detected language code")
    language_confidence: Optional[float] = Field(default=None, description="Confidence in detected language")
    entities: dict[str, list[str]] = Field(default_factory=dict, description="Extracted entities by category")


class FirewallClaimSummary(BaseModel):
    """Structured summary of an atomic claim for frontend display."""
    claim_id: str = Field(description="Canonical claim identifier")
    text: str = Field(description="Raw text assertion")
    topic: str = Field(description="Claim topic category")
    predicate: str = Field(description="Canonical predicate")
    modality: str = Field(description="Modality of assertion")
    verification_status: Optional[str] = Field(default=None, description="Verification status from Engine 5")


class FirewallActionSummary(BaseModel):
    """Structured summary of a requested action for frontend display."""
    action_id: str = Field(description="Canonical action identifier")
    action_type: str = Field(description="Categorical action type")
    target: Optional[str] = Field(default=None, description="Action target e.g. URL, app, account")
    impact_category: str = Field(description="Exposure level of requested action")
    reversibility: str = Field(description="Reversibility rating: REVERSIBLE, DIFFICULT, IRREVERSIBLE")
    urgency_detected: bool = Field(default=False, description="Whether action demands immediate execution")


class FirewallEvidenceSummary(BaseModel):
    """Evidence verification overview preserving nuanced domain states."""
    overall_status: str = Field(description="SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE, SOURCE_UNAVAILABLE, NOT_ESTABLISHED")
    verification_count: int = Field(default=0, description="Total verified claim-evidence relationships")
    supported_claims_count: int = Field(default=0, description="Count of claims verified as SUPPORTED")
    contradicted_claims_count: int = Field(default=0, description="Count of claims verified as CONTRADICTED")
    insufficient_claims_count: int = Field(default=0, description="Count of claims with INSUFFICIENT_EVIDENCE")
    source_documents_count: int = Field(default=0, description="Total authoritative documents retrieved")
    retrieval_status: str = Field(default="COMPLETED", description="COMPLETED, SOURCE_UNAVAILABLE, FAILED, SKIPPED")
    authoritative_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Authoritative source provenances checked (source, authority, retrieval_mode, freshness, reference, status)"
    )


class FirewallIdentitySummary(BaseModel):
    """Identity resolution overview preserving status distinction."""
    identity_status: str = Field(description="ESTABLISHED, NOT_ESTABLISHED, IDENTITY_MISMATCH, AMBIGUOUS")
    claimed_entities: list[str] = Field(default_factory=list, description="Claimed entity names in content")
    findings_count: int = Field(default=0, description="Count of identity findings")
    findings_summary: list[str] = Field(default_factory=list, description="Summary descriptions of top findings")
    confidence: float = Field(default=0.0, description="Entity resolution confidence")


class FirewallThreatSummary(BaseModel):
    """Threat analysis and attack-path overview."""
    threat_signals: list[str] = Field(default_factory=list, description="Identified threat signals")
    attack_stage: Optional[str] = Field(default=None, description="Initial detected attack stage")
    terminal_stage: Optional[str] = Field(default=None, description="Furthest reached attack stage")
    threat_families: list[str] = Field(default_factory=list, description="Identified threat family classifications")
    high_impact_action_count: int = Field(default=0, description="Count of high consequence actions")
    confidence: float = Field(default=0.0, description="Threat pattern confidence")


class FirewallFingerprintSummary(BaseModel):
    """Collective threat intelligence and structural fingerprint match."""
    match_type: str = Field(description="EXACT_MATCH, SEMANTIC_VARIANT, STRUCTURAL_MATCH, NO_MATCH")
    fingerprint_id: Optional[str] = Field(default=None, description="Fingerprint identifier if matched")
    match_confidence: float = Field(default=0.0, description="Match confidence")
    observation_count: int = Field(default=0, description="Total observed sightings across network")
    distinct_channels_count: int = Field(default=0, description="Number of distinct channels observed")
    attack_path_signature: Optional[str] = Field(default=None, description="Normalized structural path signature")


class FirewallBehaviourSummary(BaseModel):
    """Behavioural signals and temporal escalation patterns."""
    signals: list[str] = Field(default_factory=list, description="Detected behavioural signal types")
    findings: list[str] = Field(default_factory=list, description="Descriptive behavioural findings")
    session_id: Optional[str] = Field(default=None, description="Session ID correlated with analysis")
    events_in_session: int = Field(default=0, description="Number of observable events tracked in session")
    time_pressure_detected: bool = Field(default=False, description="Whether artificial urgency or countdown detected")
    rapid_escalation_detected: bool = Field(default=False, description="Whether rapid escalation across stages detected")
    channel_migration_detected: bool = Field(default=False, description="Whether off-platform migration detected")


class FirewallAnalysisResponse(BaseModel):
    """Canonical unified response for Nivesh Firewall analysis."""
    analysis_id: str = Field(description="Unique product analysis identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier if session-correlated")
    pipeline_status: str = Field(description="Pipeline status: COMPLETED, DEGRADED, PARTIAL, FAILED, CANCELLED")
    created_at: str = Field(description="ISO timestamp when analysis was created")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp when analysis completed")
    duration_ms: float = Field(default=0.0, description="Total pipeline execution duration in milliseconds")

    # Final Decision (sole authority: Engine 8)
    decision: FirewallDecisionSummary = Field(description="Final safety policy decision from Engine 8")

    # Detailed Intelligence Sections for Accordions/Drilldowns
    content: FirewallContentSummary = Field(description="Content understanding and entity normalization")
    claims: list[FirewallClaimSummary] = Field(default_factory=list, description="Structured claims")
    actions: list[FirewallActionSummary] = Field(default_factory=list, description="Requested user actions")
    evidence: FirewallEvidenceSummary = Field(description="Evidence verification summary")
    identity: FirewallIdentitySummary = Field(description="Identity verification and entity resolution")
    threat: FirewallThreatSummary = Field(description="Threat & attack-path intelligence")
    fingerprint: FirewallFingerprintSummary = Field(description="Scam fingerprint & collective intelligence")
    behaviour: FirewallBehaviourSummary = Field(description="Behavioural signals & interaction sequences")

    # Provenance & Audit Information
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit provenance metadata")
    warnings: list[str] = Field(default_factory=list, description="Pipeline non-fatal degradation warnings")
    errors: list[str] = Field(default_factory=list, description="Execution errors if degraded or failed")


class FirewallApiError(BaseModel):
    """Consistent product-level API error model."""
    error_code: str = Field(
        description="Machine-readable error code: INVALID_REQUEST, UNSUPPORTED_INPUT, INPUT_TOO_LARGE, INVALID_URL, INVALID_SESSION, ANALYSIS_NOT_FOUND, PIPELINE_FAILURE"
    )
    message: str = Field(description="Sanitized, human-readable error description")
    analysis_id: Optional[str] = Field(default=None, description="Analysis identifier if available")
    details: dict[str, Any] = Field(default_factory=dict, description="Safe context-specific error details")

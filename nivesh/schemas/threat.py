"""Threat and Attack-Path Intelligence schemas for Engine 6.

Represents attack paths, stage transitions, threat signals, claim-action linkages,
evidence weaknesses, high-impact actions, and threat families without generating
final intervention policies or calculating arbitrary scam probabilities.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

ThreatSignalType = Literal[
    "AUTHORITY_IMPERSONATION",
    "IDENTITY_MISMATCH",
    "IDENTITY_NOT_ESTABLISHED",
    "UNSUPPORTED_CLAIM",
    "REGULATORY_CONFLICT",
    "REGULATORY_CLAIM_CONFLICT",
    "GUARANTEED_RETURN_LANGUAGE",
    "URGENCY",
    "FOMO",
    "PRIVATE_CHANNEL_MIGRATION",
    "EXTERNAL_DOMAIN",
    "LOOKALIKE_DOMAIN",
    "EXTERNAL_APP",
    "CREDENTIAL_REQUEST",
    "IDENTITY_DOCUMENT_REQUEST",
    "ACCOUNT_ACCESS_REQUEST",
    "PAYMENT_REQUEST",
    "UPFRONT_FEE",
    "OTP_REQUEST",
    "ISOLATION_LANGUAGE",
    "SECRECY_REQUEST",
]

SignalSource = Literal[
    "content",
    "claim",
    "action",
    "source_verification",
    "evidence_verification",
    "fingerprint_database",
]

AttackStage = Literal[
    "DISCOVERY",
    "TRUST_BUILDING",
    "CHANNEL_MIGRATION",
    "NAVIGATION",
    "SOFTWARE_INSTALLATION",
    "DATA_COLLECTION",
    "CREDENTIAL_CAPTURE",
    "ACCOUNT_ACCESS",
    "FINANCIAL_REQUEST",
    "FINANCIAL_TRANSFER",
]

ClaimActionLinkType = Literal[
    "RATIONALE_FOR",
    "JUSTIFIES",
    "ENABLES",
    "PRECEDES",
    "LEADS_TO",
    "REQUESTS",
]

ActionImpactCategory = Literal[
    "CREDENTIAL",
    "IDENTITY",
    "DEVICE",
    "FINANCIAL",
]

ActionReversibility = Literal[
    "REVERSIBLE",
    "DIFFICULT_TO_REVERSE",
    "IRREVERSIBLE",
    "UNKNOWN",
]

ThreatFamily = Literal[
    "IDENTITY_IMPERSONATION",
    "INVESTMENT_PROMOTION_SCAM",
    "CREDENTIAL_HARVESTING",
    "PAYMENT_FRAUD",
    "MALICIOUS_SOFTWARE",
    "ACCOUNT_TAKEOVER",
    "REGULATORY_IMPERSONATION",
    "SOCIAL_ENGINEERING",
]


class ThreatSignal(BaseModel):
    """An explainable, structured signal contributing to threat evaluation."""
    signal_id: str = Field(description="Unique signal identifier (e.g. SIG-001)")
    type: ThreatSignalType = Field(description="Standardized threat signal category")
    source: SignalSource = Field(description="Origin layer of the signal")
    evidence: str = Field(description="Specific excerpt, fact, or parameter grounding the signal")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence of this signal")
    description: str = Field(description="Human-readable explanation of why this signal was identified")
    claim_id: Optional[str] = Field(default=None, description="Linked claim ID if originating from a claim")
    action_id: Optional[str] = Field(default=None, description="Linked action ID if originating from an action")
    source_document_id: Optional[str] = Field(default=None, description="Linked document ID from Engine 4")
    evidence_id: Optional[str] = Field(default=None, description="Linked evidence ID from Engine 5")


class AttackNode(BaseModel):
    """A discrete node representing an interaction stage in the attack graph."""
    node_id: str = Field(description="Unique node identifier (e.g. NODE-01)")
    stage: AttackStage = Field(description="Normalized interaction stage")
    type: str = Field(description="Descriptor of the node content or action")
    label: str = Field(description="Brief human-readable node title")
    linked_claim_ids: list[str] = Field(default_factory=list, description="Claims associated with this stage")
    linked_action_ids: list[str] = Field(default_factory=list, description="Actions associated with this stage")
    evidence_ids: list[str] = Field(default_factory=list, description="Evidence items supporting this stage")


class AttackTransition(BaseModel):
    """Represents progression from one interaction stage to the next."""
    from_stage: AttackStage = Field(description="Source stage")
    to_stage: AttackStage = Field(description="Destination stage")
    supporting_actions: list[str] = Field(default_factory=list, description="Action IDs driving the transition")
    supporting_claims: list[str] = Field(default_factory=list, description="Claim IDs justifying the transition")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in transition progression")
    description: str = Field(description="Explanation of the transition dynamics")


class AttackPath(BaseModel):
    """Structured graph representing the observed sequence of interaction stages."""
    nodes: list[AttackNode] = Field(default_factory=list, description="Ordered interaction nodes")
    transitions: list[AttackTransition] = Field(default_factory=list, description="Stage transitions")
    entry_stage: Optional[AttackStage] = Field(default=None, description="Initial detected stage")
    terminal_stage: Optional[AttackStage] = Field(default=None, description="Furthest reached stage")


class ClaimActionLink(BaseModel):
    """Explicit semantic connection between a claim and an action."""
    link_id: str = Field(description="Unique link identifier (e.g. CAL-001)")
    claim_id: str = Field(description="Supporting or justifying claim ID")
    action_id: str = Field(description="Requested action ID")
    type: ClaimActionLinkType = Field(description="Nature of the claim-action connection")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the link relationship")
    explanation: str = Field(description="Auditable explanation of how the claim connects to the action")


class EvidenceWeakness(BaseModel):
    """A critical evidence limitation or failure identified in Engine 5."""
    weakness_id: str = Field(description="Unique weakness identifier (e.g. EW-001)")
    claim_id: str = Field(description="Target claim ID")
    weakness_type: str = Field(description="IDENTITY_NOT_ESTABLISHED, REGULATORY_CONFLICT, etc.")
    description: str = Field(description="Specific finding from evidence verification")
    evidence_status: str = Field(description="Engine 5 verification status")
    severity: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Impact of this weakness on path safety")


class HighImpactAction(BaseModel):
    """An action that produces significant, potentially irreversible harm or exposure."""
    action_id: str = Field(description="Target action ID from Engine 3")
    action_type: str = Field(description="Canonical action type")
    impact_category: ActionImpactCategory = Field(description="Category of exposure")
    reversibility: ActionReversibility = Field(description="Degree of reversibility")
    description: str = Field(description="Explanation of why this action carries elevated consequence")


class ThreatCombination(BaseModel):
    """A multi-signal combination forming an identifiable threat mechanism."""
    combination: list[str] = Field(description="Signal types participating in the combination")
    mechanism: str = Field(description="Descriptor of the combined threat mechanism")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the composite pattern")
    description: str = Field(description="Detailed explanation of the combination risk")


class ThreatExplanation(BaseModel):
    """Synthesized, auditable explanation of the interaction's threat structure."""
    summary: str = Field(description="Concise description of the overall observed structure")
    mechanisms: list[str] = Field(default_factory=list, description="Identified threat mechanisms")
    key_factors: list[str] = Field(default_factory=list, description="Primary structural risk factors")


class FingerprintPreparation(BaseModel):
    """Normalized structural components prepared for Engine 7 (Scam Fingerprint Engine)."""
    normalized_claim_patterns: list[str] = Field(default_factory=list)
    normalized_action_patterns: list[str] = Field(default_factory=list)
    normalized_identity_patterns: list[str] = Field(default_factory=list)
    normalized_channel_patterns: list[str] = Field(default_factory=list)
    normalized_threat_families: list[str] = Field(default_factory=list)
    normalized_attack_stages: list[str] = Field(default_factory=list)
    normalized_transitions: list[str] = Field(default_factory=list)


class ThreatProvenance(BaseModel):
    """Audit metadata for Engine 6 threat analysis."""
    engine_version: str = Field(description="Engine 6 version")
    engine_name: str = Field(default="Threat & Attack-Path Intelligence Engine")
    analysis_method: Literal["rule", "hybrid", "llm"] = Field(description="Processing approach")
    analyzed_at: str = Field(description="ISO 8601 timestamp")
    upstream_engine_versions: dict[str, str] = Field(default_factory=dict)


class ThreatAnalysisMetadata(BaseModel):
    """Summary execution metrics for Engine 6."""
    total_signals: int = 0
    stages_detected: int = 0
    transitions_detected: int = 0
    high_impact_action_count: int = 0
    threat_families_count: int = 0
    processing_time_ms: float = 0.0


class ThreatAnalysis(BaseModel):
    """Top-level output schema for Engine 6: Threat & Attack-Path Intelligence Engine."""
    content_id: str = Field(description="UUID of source NormalizedContent")
    threat_signals: list[ThreatSignal] = Field(default_factory=list, description="Identified threat signals")
    attack_path: AttackPath = Field(description="Constructed interaction attack path graph")
    transitions: list[AttackTransition] = Field(default_factory=list, description="Detected stage transitions")
    claim_action_links: list[ClaimActionLink] = Field(default_factory=list, description="Claim-to-action connections")
    evidence_weaknesses: list[EvidenceWeakness] = Field(default_factory=list, description="Evidence gaps and conflicts")
    high_impact_actions: list[HighImpactAction] = Field(default_factory=list, description="High consequence actions")
    threat_combinations: list[ThreatCombination] = Field(default_factory=list, description="Composite threat patterns")
    threat_families: list[ThreatFamily] = Field(default_factory=list, description="Identified threat families")
    fingerprint_prep: FingerprintPreparation = Field(default_factory=FingerprintPreparation, description="Prepared data for Engine 7 fingerprinting")
    fingerprint_preparation: FingerprintPreparation = Field(default_factory=FingerprintPreparation, description="Prepared data for Engine 7 fingerprinting")
    explanation: ThreatExplanation = Field(description="Auditable non-accusatory structural explanation")
    uncertainty: list[str] = Field(default_factory=list, description="Explicit evidentiary and inferential limits")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall pattern match confidence")
    provenance: ThreatProvenance = Field(description="Execution provenance metadata")
    analysis_metadata: ThreatAnalysisMetadata = Field(description="Summary metrics")

    @property
    def combinations(self) -> list[ThreatCombination]:
        return self.threat_combinations

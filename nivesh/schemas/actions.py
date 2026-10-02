"""Action schemas for Engine 3 (Action Intelligence Engine).

Represents structured, canonical actions that financial content asks, encourages,
instructs, or attempts to make the user perform.
Preserves action type, hierarchy category, actor, target, parameters, sequence,
modality, rationale claim linkage, and canonical fingerprints without making
scam, risk, or policy decisions.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
from nivesh.schemas.claims import SourceSpan

ActionType = Literal[
    "CONTACT",
    "CLICK_LINK",
    "OPEN_WEBSITE",
    "JOIN_CHANNEL",
    "JOIN_GROUP",
    "FOLLOW_ACCOUNT",
    "MESSAGE_PERSON",
    "CALL_PERSON",
    "DOWNLOAD",
    "INSTALL",
    "UPLOAD_DOCUMENT",
    "UPLOAD_IDENTITY",
    "ENTER_CREDENTIALS",
    "SHARE_PERSONAL_INFORMATION",
    "SHARE_FINANCIAL_INFORMATION",
    "SHARE_OTP",
    "CONNECT_ACCOUNT",
    "CONNECT_BANK",
    "AUTHORIZE_ACCESS",
    "PAYMENT",
    "TRANSFER_MONEY",
    "DEPOSIT_MONEY",
    "WITHDRAW_MONEY",
    "BUY",
    "SELL",
    "SHARE",
    "FORWARD",
    "SIGN_DOCUMENT",
    "OTHER",
]

ActionCategory = Literal[
    "INFORMATIONAL",
    "COMMUNICATION",
    "CHANNEL_MIGRATION",
    "NAVIGATION",
    "SOFTWARE_INSTALLATION",
    "DATA_DISCLOSURE",
    "CREDENTIAL_ACCESS",
    "ACCOUNT_AUTHORIZATION",
    "FINANCIAL_TRANSACTION",
]

ActorType = Literal["user", "content_author", "unknown"]

TargetType = Literal[
    "person",
    "organization",
    "website",
    "channel",
    "application",
    "account",
    "unknown",
]

ActionModalityType = Literal[
    "instruction",
    "request",
    "suggestion",
    "invitation",
    "warning",
    "implicit",
    "unknown",
]

ModalityStrength = Literal["direct", "indirect"]

ActionRelationType = Literal[
    "ENABLES",
    "PRECEDES",
    "ALTERNATIVE_TO",
    "CONDITIONAL_ON",
    "SAME_UNDERLYING_ACTION",
]


class ActionActor(BaseModel):
    """The entity performing or intended to perform the action."""
    type: ActorType = "user"
    name: Optional[str] = None


class ActionTarget(BaseModel):
    """The entity, platform, channel, or recipient receiving or target of the action."""
    type: TargetType = "unknown"
    value: Optional[str] = None


class ActionModality(BaseModel):
    """The presentation strength and intent type of the requested action."""
    type: ActionModalityType = "instruction"
    strength: ModalityStrength = "direct"


class ActionSequence(BaseModel):
    """Chronological or presentation order of the action."""
    index: int = 1


class ActionText(BaseModel):
    """Original source snippet and standardized canonical action phrase."""
    original: str = Field(description="Exact snippet from normalized content")
    normalized: str = Field(description="Clean standardized imperative action statement")


class ActionProvenance(BaseModel):
    """Traceability of action extraction."""
    extraction_method: Literal["rule", "llm", "hybrid"] = "hybrid"
    processing_version: str = "1.0.0"


class ActionRelation(BaseModel):
    """Relationship between two extracted actions."""
    source_action_id: str
    target_action_id: str
    relation_type: ActionRelationType
    confidence: float = 1.0
    description: Optional[str] = None


class CanonicalAction(BaseModel):
    """Structured, atomic action extracted from content."""
    action_id: str = Field(description="Unique action identifier e.g. ACTION-001")
    source_content_id: str = Field(description="Reference to origin NormalizedContent content_id")
    text: ActionText
    action_type: ActionType
    category: ActionCategory
    actor: ActionActor = Field(default_factory=ActionActor)
    target: ActionTarget = Field(default_factory=ActionTarget)
    objects: list[str] = Field(default_factory=list, description="Target items e.g. ['APK'], ['PAN'], ['trading password']")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Structured parameters e.g. amount, currency, deadline")
    sequence: ActionSequence = Field(default_factory=lambda: ActionSequence(index=1))
    modality: ActionModality = Field(default_factory=ActionModality)
    source_span: SourceSpan = Field(default_factory=SourceSpan, description="Primary character span in normalized text")
    source_spans: list[SourceSpan] = Field(default_factory=list, description="All spans for merged recurring actions")
    confidence: float = Field(default=1.0, description="Extraction confidence (NOT threat or scam score)")
    canonical_fingerprint: str = Field(
        default="",
        description="Deterministic representation for downstream engines e.g. ACTION:JOIN_CHANNEL|TARGET:TELEGRAM"
    )
    rationale_claim_ids: list[str] = Field(
        default_factory=list,
        description="IDs of claims from ClaimAnalysis that provide justification or rationale for this action"
    )
    provenance: ActionProvenance = Field(default_factory=ActionProvenance)


class ActionAnalysisMetadata(BaseModel):
    """Metadata regarding action extraction run."""
    processing_time_ms: float = 0.0
    total_actions: int = 0
    action_types_count: dict[str, int] = Field(default_factory=dict)
    duplicate_actions_merged: int = 0


class ActionAnalysis(BaseModel):
    """Complete output of Action Intelligence Engine (Engine 3)."""
    content_id: str = Field(description="Source content identifier")
    actions: list[CanonicalAction] = Field(default_factory=list)
    action_relations: list[ActionRelation] = Field(default_factory=list)
    analysis_metadata: ActionAnalysisMetadata = Field(default_factory=ActionAnalysisMetadata)

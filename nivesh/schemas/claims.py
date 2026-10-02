"""Claim schemas for Engine 2 (Claim Intelligence Engine).

Represents atomic, canonical financial and regulatory claims extracted from
NormalizedContent. Preserves semantic structure (Subject-Predicate-Object),
modality, temporal context, fingerprint inputs, and verification requirements
without making truth or risk decisions.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

ClaimType = Literal[
    "FACTUAL",
    "REGULATORY",
    "IDENTITY",
    "FINANCIAL",
    "CORPORATE_EVENT",
    "PRODUCT",
    "EDUCATIONAL",
    "OPINION",
    "PREDICTION",
    "RECOMMENDATION",
    "PROMOTIONAL",
    "COMPARATIVE",
    "CAUSAL",
    "UNKNOWN",
]

TemporalType = Literal["current", "historical", "future", "unknown"]

ModalityType = Literal[
    "assertion",
    "possibility",
    "prediction",
    "opinion",
    "question",
    "conditional",
]

RelationType = Literal[
    "SUPPORTS",
    "CONTRADICTS",
    "REFINES",
    "DEPENDS_ON",
    "CAUSES",
    "RESULTS_FROM",
    "SAME_UNDERLYING_CLAIM",
]


class ClaimText(BaseModel):
    """Pair of original source text snippet and normalized canonical text."""
    original: str = Field(description="Exact snippet from normalized content")
    normalized: str = Field(description="Normalized canonical assertion sentence")


class SourceSpan(BaseModel):
    """Character offset span in normalized text."""
    start: int = 0
    end: int = 0


class TemporalContext(BaseModel):
    """Temporal classification and any detected dates or temporal expressions."""
    type: TemporalType = "unknown"
    date: Optional[str] = None
    raw_text: Optional[str] = None


class ClaimModality(BaseModel):
    """Linguistic presentation strength and certainty language."""
    type: ModalityType = "assertion"
    certainty_language: Optional[str] = None


class ClaimProvenance(BaseModel):
    """Traceability of claim extraction."""
    extraction_method: Literal["rule", "llm", "hybrid"] = "hybrid"
    processing_version: str = "1.0.0"


class CanonicalClaim(BaseModel):
    """Structured, atomic assertion extracted from content."""
    claim_id: str = Field(description="Unique claim identifier e.g. CLAIM-001")
    source_content_id: str = Field(description="Reference to origin NormalizedContent content_id")
    text: ClaimText
    claim_type: ClaimType
    subject: str = Field(description="Subject entity or concept e.g. 'Rahul Sharma', 'ABC', 'returns'")
    predicate: str = Field(description="Canonical uppercase predicate e.g. 'REGISTERED_WITH', 'HAS_DEBT'")
    object: Optional[str] = Field(default=None, description="Object, value or target e.g. 'SEBI', '0', '40%'")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Structured attributes, roles, numbers")
    temporal_context: TemporalContext = Field(default_factory=TemporalContext)
    modality: ClaimModality = Field(default_factory=ClaimModality)
    source_span: SourceSpan = Field(default_factory=SourceSpan)
    confidence: float = Field(default=1.0, description="Extraction confidence (NOT truth probability)")
    canonical_fingerprint: str = Field(
        default="",
        description="Deterministic representation for Engine 8 (e.g. ENTITY:XYZ|PREDICATE:HAS_DEBT|VALUE:0)"
    )
    verification_requirements: list[str] = Field(
        default_factory=list,
        description="Checklist of artifacts/registries required by Evidence Verification Engine"
    )
    provenance: ClaimProvenance = Field(default_factory=ClaimProvenance)


class ClaimRelation(BaseModel):
    """Relationship between two extracted claims."""
    source_claim_id: str
    target_claim_id: str
    relation_type: RelationType
    confidence: float = 1.0
    description: Optional[str] = None


class ClaimAnalysisMetadata(BaseModel):
    """Metadata regarding claim extraction run."""
    processing_time_ms: float = 0.0
    total_claims: int = 0
    claim_types_count: dict[str, int] = Field(default_factory=dict)
    actions_filtered_count: int = 0
    duplicate_claims_merged: int = 0


class ClaimAnalysis(BaseModel):
    """Complete output of Claim Intelligence Engine (Engine 2)."""
    content_id: str = Field(description="Source content identifier")
    claims: list[CanonicalClaim] = Field(default_factory=list)
    claim_relations: list[ClaimRelation] = Field(default_factory=list)
    analysis_metadata: ClaimAnalysisMetadata = Field(default_factory=ClaimAnalysisMetadata)

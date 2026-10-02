"""Evidence Verification schemas for Engine 5 (Evidence Verification Engine).

Represents claim-level verification results, evidence item evaluations,
reasoning traces, context gaps, and confidence metrics without making
investment recommendations or scam probability calculations.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

ClaimVerificationStatus = Literal[
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "CONTRADICTED",
    "INSUFFICIENT_EVIDENCE",
    "NOT_VERIFIABLE",
    "SOURCE_CONFLICT",
    "NO_USABLE_EVIDENCE",
    "SOURCE_UNAVAILABLE",
]

EvidenceRelationType = Literal[
    "SUPPORTS",
    "PARTIALLY_SUPPORTS",
    "CONTRADICTS",
    "IRRELEVANT",
    "DOES_NOT_ADDRESS",
]

EvidenceStrength = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
    "NONE",
]

VerificationMethod = Literal[
    "rule",
    "hybrid",
    "llm",
]


class EvidenceItemEvaluation(BaseModel):
    """Detailed evaluation of an individual piece of evidence relative to a claim."""
    evidence_id: str = Field(description="Evidence candidate ID (from Engine 4)")
    source_document_id: str = Field(description="Source document ID")
    source_url: str = Field(description="Canonical URL of source")
    organization: str = Field(description="Source organization (e.g. SEBI, NSE)")
    relation: EvidenceRelationType = Field(description="SUPPORTS, CONTRADICTS, etc.")
    excerpt: str = Field(description="Relevant quotation from source document")
    reasoning: str = Field(description="Concise rationale explaining the evidence relation")
    matched_signals: list[str] = Field(default_factory=list, description="Terms, entities, or dates matched")


class SourceAssessmentItem(BaseModel):
    """Assessment of an authoritative source used during verification."""
    source_id: str = Field(description="Catalog source ID")
    organization: str = Field(description="Organization operating the source")
    authority_tier: str = Field(description="PRIMARY_OFFICIAL, SECONDARY_RELIABLE, etc.")
    retrieval_status: str = Field(description="SUCCESS, NO_MATCH, SOURCE_UNAVAILABLE, etc.")
    relevance_summary: str = Field(description="Summary of source relevance to claim")


class VerificationProvenance(BaseModel):
    """Audit trail of verification execution."""
    engine_version: str = Field(description="Version of Engine 5")
    verification_method: VerificationMethod = Field(description="rule, hybrid, or llm")
    verified_at: str = Field(description="ISO 8601 timestamp of verification")


class RegulatoryFinding(BaseModel):
    """Structured finding when evidence establishes a regulatory rule or prohibition."""
    type: Literal["REGULATORY_CONFLICT", "REGULATORY_COMPLIANCE", "REGULATORY_WARNING"] = Field(
        default="REGULATORY_CONFLICT",
        description="Type of regulatory finding"
    )
    source_document_id: Optional[str] = Field(default=None, description="Referenced source document ID")
    source_url: Optional[str] = Field(default=None, description="URL of regulatory source")
    organization: Optional[str] = Field(default=None, description="Regulatory authority e.g. SEBI")
    excerpt: Optional[str] = Field(default=None, description="Direct regulatory text excerpt")
    retrieved_at: Optional[str] = Field(default=None, description="Timestamp of retrieval")
    description: str = Field(description="Explanation of the regulatory conflict or finding")


class VerificationResult(BaseModel):
    """Structured claim-level verification result."""
    claim_id: str = Field(description="Target CanonicalClaim ID")
    status: ClaimVerificationStatus = Field(description="Verification status (SUPPORTED, CONTRADICTED, etc.)")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the verification comparison (NOT real-world scam probability)"
    )
    evidence_strength: EvidenceStrength = Field(description="HIGH, MEDIUM, LOW, or NONE")
    supporting_evidence: list[EvidenceItemEvaluation] = Field(
        default_factory=list,
        description="Evidence candidates supporting the claim"
    )
    contradicting_evidence: list[EvidenceItemEvaluation] = Field(
        default_factory=list,
        description="Evidence candidates contradicting the claim"
    )
    regulatory_findings: list[RegulatoryFinding] = Field(
        default_factory=list,
        description="Structured regulatory findings (e.g. REGULATORY_CONFLICT) without falsely claiming factual contradiction"
    )
    missing_elements: list[str] = Field(
        default_factory=list,
        description="Claimed elements not established by evidence (e.g. specific date, ratio)"
    )
    context_gaps: list[str] = Field(
        default_factory=list,
        description="Important omitted contextual factors (e.g. reporting period, one-off gain)"
    )
    source_assessment: list[SourceAssessmentItem] = Field(
        default_factory=list,
        description="Sources consulted and their relevance assessment"
    )
    reasoning_trace: list[str] = Field(
        default_factory=list,
        description="Step-by-step evidence comparison reasoning steps"
    )
    uncertainty: list[str] = Field(
        default_factory=list,
        description="Explicit uncertainties, assumptions, or evidence limitations"
    )
    provenance: VerificationProvenance = Field(description="Verification audit metadata")


class EvidenceAnalysisMetadata(BaseModel):
    """Summary execution metrics for Engine 5."""
    total_claims: int = 0
    claims_supported: int = 0
    claims_partially_supported: int = 0
    claims_contradicted: int = 0
    claims_insufficient: int = 0
    claims_not_verifiable: int = 0
    claims_source_conflict: int = 0
    processing_time_ms: float = 0.0


class EvidenceAnalysis(BaseModel):
    """Top-level output schema for Engine 5."""
    content_id: str = Field(description="UUID of source NormalizedContent")
    verifications: list[VerificationResult] = Field(
        default_factory=list,
        description="Verification result for each canonical claim"
    )
    analysis_metadata: EvidenceAnalysisMetadata = Field(description="Aggregate execution metrics")

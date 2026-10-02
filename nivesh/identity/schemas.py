"""Typed schemas for Engine 9: Identity Verification & Entity Resolution Engine.

Defines identity entity types, match statuses, findings, alignments,
and the canonical IdentityAnalysis schema.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


ENGINE_VERSION = "1.0.0"


class IdentityEntityType(str, Enum):
    """Categorization of entities involved in financial interactions."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    REGULATOR = "REGULATOR"
    FINANCIAL_INTERMEDIARY = "FINANCIAL_INTERMEDIARY"
    BROKER = "BROKER"
    ADVISER = "ADVISER"
    COMPANY = "COMPANY"
    BRAND = "BRAND"
    WEBSITE = "WEBSITE"
    DOMAIN = "DOMAIN"
    SOCIAL_ACCOUNT = "SOCIAL_ACCOUNT"
    CHANNEL = "CHANNEL"


class IdentityStatus(str, Enum):
    """Overall identity verification status for the interaction."""
    ESTABLISHED = "ESTABLISHED"
    PARTIALLY_ESTABLISHED = "PARTIALLY_ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class IdentityMatchStatus(str, Enum):
    """Status of an individual entity identity match."""
    ESTABLISHED = "ESTABLISHED"
    PARTIALLY_ESTABLISHED = "PARTIALLY_ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class IdentityFindingType(str, Enum):
    """Stable reason codes describing verifiable identity observations."""
    IDENTITY_ESTABLISHED = "IDENTITY_ESTABLISHED"
    IDENTITY_PARTIALLY_ESTABLISHED = "IDENTITY_PARTIALLY_ESTABLISHED"
    IDENTITY_NOT_ESTABLISHED = "IDENTITY_NOT_ESTABLISHED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"

    REGISTRATION_ENTITY_MATCH = "REGISTRATION_ENTITY_MATCH"
    REGISTRATION_ENTITY_MISMATCH = "REGISTRATION_ENTITY_MISMATCH"
    REGISTRATION_IDENTIFIER_UNRESOLVED = "REGISTRATION_IDENTIFIER_UNRESOLVED"

    DOMAIN_ALIGNMENT_ESTABLISHED = "DOMAIN_ALIGNMENT_ESTABLISHED"
    DOMAIN_ALIGNMENT_NOT_ESTABLISHED = "DOMAIN_ALIGNMENT_NOT_ESTABLISHED"
    DOMAIN_IDENTITY_MISMATCH = "DOMAIN_IDENTITY_MISMATCH"

    BRAND_IDENTITY_UNRESOLVED = "BRAND_IDENTITY_UNRESOLVED"
    BRAND_IDENTITY_MISMATCH = "BRAND_IDENTITY_MISMATCH"

    AUTHORITY_CLAIM = "AUTHORITY_CLAIM"
    AUTHORITY_IDENTITY_NOT_ESTABLISHED = "AUTHORITY_IDENTITY_NOT_ESTABLISHED"
    AUTHORITY_IDENTITY_MISMATCH = "AUTHORITY_IDENTITY_MISMATCH"

    SOCIAL_ACCOUNT_NOT_ESTABLISHED = "SOCIAL_ACCOUNT_NOT_ESTABLISHED"
    SOCIAL_ACCOUNT_IDENTITY_MISMATCH = "SOCIAL_ACCOUNT_IDENTITY_MISMATCH"

    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    INSUFFICIENT_IDENTITY_EVIDENCE = "INSUFFICIENT_IDENTITY_EVIDENCE"


class IdentityRelationshipType(str, Enum):
    """Formal relationships between entities."""
    CLAIMED_TO_REPRESENT = "CLAIMED_TO_REPRESENT"
    REGISTERED_WITH = "REGISTERED_WITH"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    OWNS_DOMAIN = "OWNS_DOMAIN"
    OPERATES_BRAND = "OPERATES_BRAND"
    OPERATES_CHANNEL = "OPERATES_CHANNEL"
    CLAIMED_TO_BE_OFFICIAL_FOR = "CLAIMED_TO_BE_OFFICIAL_FOR"


class ClaimedEntity(BaseModel):
    """Structured representation of an entity claimed or observed in the content."""
    entity_id: str = Field(description="Unique claimed entity identifier (e.g. ENT-001)")
    name: str = Field(description="Raw name as observed in the content")
    normalized_name: str = Field(description="Normalized canonical form for resolution")
    entity_type: IdentityEntityType = Field(description="Categorical entity type")
    original_form: Optional[str] = Field(default=None, description="Preserved legal or raw string for provenance")
    associated_registration: Optional[str] = Field(default=None, description="Claimed registration number (e.g. SEBI INA...)")
    associated_domain: Optional[str] = Field(default=None, description="Observed domain associated with entity")
    associated_channel: Optional[str] = Field(default=None, description="Observed social handle or channel")
    source_claim_ids: list[str] = Field(default_factory=list, description="IDs of claims referencing this entity")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Additional structured attributes")


class ResolvedEntity(BaseModel):
    """Authoritative entity record discovered in official sources."""
    candidate_id: str = Field(description="Unique candidate identifier (e.g. CAND-001)")
    legal_name: str = Field(description="Official legal name from registry")
    normalized_name: str = Field(description="Normalized form for matching")
    entity_type: IdentityEntityType = Field(description="Entity type in authoritative source")
    registration_number: Optional[str] = Field(default=None, description="Official registration number")
    official_domain: Optional[str] = Field(default=None, description="Official domain on record")
    regulator: Optional[str] = Field(default=None, description="Overseeing regulatory body (e.g. SEBI)")
    jurisdiction: str = Field(default="IN", description="Country/jurisdiction code")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Registry details")
    source_document_ids: list[str] = Field(default_factory=list, description="Authoritative document IDs")


class IdentityMatch(BaseModel):
    """Detailed comparison between a claimed entity and an authoritative record."""
    identity_match_id: str = Field(description="Unique match comparison identifier")
    claimed_entity_id: str = Field(description="ID of the claimed entity")
    candidate_entity_id: Optional[str] = Field(default=None, description="ID of authoritative candidate entity")
    entity_type: IdentityEntityType = Field(description="Entity type under comparison")
    match_status: IdentityMatchStatus = Field(description="Resolution verdict (ESTABLISHED, MISMATCH, etc.)")
    match_basis: str = Field(description="Concise description of the resolution rationale")
    matching_attributes: list[str] = Field(default_factory=list, description="Attributes that positively matched")
    conflicting_attributes: list[str] = Field(default_factory=list, description="Attributes that directly conflicted")
    source_ids: list[str] = Field(default_factory=list, description="Authoritative source document IDs")
    evidence_ids: list[str] = Field(default_factory=list, description="Verification result IDs")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the identity resolution comparison (NOT scam probability)")


class AuthorityAlignment(BaseModel):
    """Assessment of regulatory authority representation and registration validity."""
    authority_name: str = Field(description="Name of regulator (SEBI, RBI, NSE, BSE)")
    alignment_status: str = Field(description="ALIGNED, NOT_ESTABLISHED, MISMATCH, UNVERIFIED")
    claimed_role: Optional[str] = Field(default=None, description="Claimed intermediary role (ADVISER, BROKER, etc.)")
    registration_number: Optional[str] = Field(default=None, description="Registration identifier evaluated")
    findings: list[str] = Field(default_factory=list, description="Key observations regarding authority alignment")
    source_ids: list[str] = Field(default_factory=list, description="Referenced source document IDs")
    evidence_ids: list[str] = Field(default_factory=list, description="Referenced evidence verification IDs")


class DomainAlignment(BaseModel):
    """Assessment of observed domain ownership relative to claimed brand/organization."""
    observed_domain: str = Field(description="Domain extracted from message or action")
    claimed_brand_or_entity: Optional[str] = Field(default=None, description="Name of claimed brand or organization")
    authoritative_domain: Optional[str] = Field(default=None, description="Official domain on record")
    alignment_status: str = Field(description="ALIGNED, NOT_ESTABLISHED, MISMATCH, UNKNOWN")
    evidence_basis: str = Field(description="Rationale explaining domain alignment assessment")
    source_ids: list[str] = Field(default_factory=list, description="Authoritative source document IDs")


class IdentityFinding(BaseModel):
    """Structured identity finding with complete upstream provenance."""
    finding_id: str = Field(description="Unique finding identifier (e.g. IDF-001)")
    finding_type: IdentityFindingType = Field(description="Machine-readable stable finding code")
    entity_id: str = Field(description="ID of entity associated with finding")
    claim_id: Optional[str] = Field(default=None, description="Associated CanonicalClaim ID")
    source_ids: list[str] = Field(default_factory=list, description="Supporting authoritative source IDs")
    evidence_ids: list[str] = Field(default_factory=list, description="Supporting evidence verification IDs")
    basis: str = Field(description="Factual basis for this finding")
    description: str = Field(description="Non-accusatory objective description of finding")


class IdentityProvenance(BaseModel):
    """Traceability metadata for the identity resolution process."""
    engine_version: str = Field(default=ENGINE_VERSION, description="Engine 9 version")
    verified_at: str = Field(description="ISO 8601 execution timestamp")
    input_content_id: str = Field(description="NormalizedContent ID processed")
    claim_count: int = Field(default=0, description="Number of claims processed")
    source_document_count: int = Field(default=0, description="Authoritative source documents inspected")
    evidence_count: int = Field(default=0, description="Evidence verification results evaluated")


class IdentityAnalysis(BaseModel):
    """Canonical output schema for Engine 9: Identity Verification & Entity Resolution."""
    analysis_id: str = Field(description="Unique identity analysis identifier (e.g. IDA-001)")
    entities: list[ClaimedEntity] = Field(default_factory=list, description="Entities extracted and analyzed")
    identity_matches: list[IdentityMatch] = Field(default_factory=list, description="Entity resolution matches")
    identity_findings: list[IdentityFinding] = Field(default_factory=list, description="Structured identity findings")
    identity_status: IdentityStatus = Field(description="Overall interaction identity status")
    authority_alignments: list[AuthorityAlignment] = Field(default_factory=list, description="Regulatory authority checks")
    domain_alignments: list[DomainAlignment] = Field(default_factory=list, description="Domain and brand alignment checks")
    confidence: float = Field(ge=0.0, le=1.0, description="Identity resolution confidence (NOT scam probability)")
    provenance: IdentityProvenance = Field(description="Provenance and execution audit trail")
    upstream_references: dict[str, Any] = Field(default_factory=dict, description="Referenced upstream IDs")
    engine_version: str = Field(default=ENGINE_VERSION, description="Engine 9 release version")

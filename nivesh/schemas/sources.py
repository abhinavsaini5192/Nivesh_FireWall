"""Source Intelligence schemas for Engine 4 (Source Intelligence Engine).

Represents authoritative source discovery, retrieval metadata, normalized source documents,
and structured evidence candidates.
Engine 4 answers: 'Where should we look for authoritative information about this claim,
and what source material did we retrieve?'
It preserves full provenance and leaves verification_status as UNVERIFIED.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

SourceTypeTaxonomy = Literal[
    "REGULATOR",
    "REGULATORY_REGISTRY",
    "STOCK_EXCHANGE",
    "GOVERNMENT",
    "COMPANY_OFFICIAL",
    "STATUTORY_DOCUMENT",
    "FINANCIAL_FILING",
    "CORPORATE_ANNOUNCEMENT",
    "CORPORATE_ACTION",
    "LEGAL_DOCUMENT",
    "DOMAIN_SOURCE",
    "PUBLIC_DATABASE",
    "NEWS",
    "OTHER",
]

AuthorityTier = Literal[
    "PRIMARY_OFFICIAL",
    "SECONDARY_RELIABLE",
    "SECONDARY",
    "UNKNOWN",
]

RetrievalStatus = Literal[
    "SUCCESS",
    "NO_MATCH",
    "SOURCE_UNAVAILABLE",
    "UNAUTHORIZED",
    "ACCESS_UNAUTHORIZED",
    "CREDENTIALS_MISSING",
    "RETRIEVAL_FAILED",
    "RATE_LIMITED",
    "INVALID_QUERY",
    "PARTIAL",
    "TIMEOUT",
]

RetrievalMode = Literal[
    "LIVE",
    "LIVE_AUTHORIZED",
    "LIVE_PUBLIC",
    "OFFICIAL_SNAPSHOT",
    "CACHE",
    "FIXTURE",
    "SOURCE_UNAVAILABLE",
]

FreshnessStatus = Literal[
    "CURRENT",
    "HISTORICAL",
    "STALE",
    "SNAPSHOT",
    "UNKNOWN",
]

ProviderAccessState = Literal[
    "ENABLED",
    "DISABLED",
    "CREDENTIALS_MISSING",
    "ACCESS_UNAUTHORIZED",
    "LIVE_AVAILABLE",
    "SOURCE_UNAVAILABLE",
]


class ProviderAccessConfig(BaseModel):
    """Configuration, access mode, and operational status for an authoritative provider."""
    provider_name: str = Field(description="Short identifier of the provider (e.g. SEBI, RBI, NSE, BSE)")
    authority_name: str = Field(description="Full legal authority name")
    access_mechanism: str = Field(description="Access method (e.g. Public Web Registry, DBIE, Corporate API)")
    requires_credentials: bool = Field(description="Whether this source requires API key or subscription credentials")
    credentials_configured: bool = Field(description="Whether server-side credentials are currently present")
    live_enabled: bool = Field(description="Whether live querying is enabled in configuration")
    status: ProviderAccessState = Field(description="Operational status of the provider")
    supported_capabilities: list[str] = Field(default_factory=list, description="Capabilities supported by the adapter")
    endpoint_reference: str = Field(description="Base URL or API endpoint for this provider")
    limitation_note: str = Field(description="Documented access constraints and limitations")
    last_verified_at: Optional[str] = Field(None, description="ISO timestamp of last live probe")


class SourceHealthReport(BaseModel):
    """System health report covering all authoritative providers."""
    timestamp: str = Field(description="ISO timestamp of diagnostic generation")
    overall_status: str = Field(description="Summary status across all providers")
    providers: dict[str, ProviderAccessConfig] = Field(description="Provider diagnostic mapping")


class AuthoritativeProvenance(BaseModel):
    """Common provenance structure for authoritative source verification results."""
    source: str = Field(description="Source identifier (e.g. SEBI, RBI, NSE, BSE)")
    source_authority: str = Field(description="Full legal authority name (e.g. Securities and Exchange Board of India)")
    retrieval_mode: RetrievalMode = Field(description="LIVE, OFFICIAL_SNAPSHOT, CACHE, FIXTURE, or SOURCE_UNAVAILABLE")
    retrieved_at: str = Field(description="ISO 8601 timestamp of retrieval")
    published_at: Optional[str] = Field(None, description="ISO 8601 timestamp of publication")
    updated_at: Optional[str] = Field(None, description="ISO 8601 timestamp of dataset update")
    source_record_id: Optional[str] = Field(None, description="Official registration or filing ID")
    source_reference: Optional[str] = Field(None, description="Official URL, circular ref, or accession number")
    adapter_name: str = Field(description="Adapter class name")
    adapter_version: str = Field(default="1.0.0", description="Adapter version string")
    freshness: FreshnessStatus = Field(default="UNKNOWN", description="Freshness evaluation")
    response_status: RetrievalStatus = Field(description="Retrieval status")
    evidence: str = Field(description="Factual summary of what was retrieved or confirmed")
    access_method: Optional[str] = Field(default=None, description="Access method or connector used (e.g. NSEPython, Official API, Public REST)")
    provider: Optional[str] = Field(default=None, description="Active provider class or identifier, e.g. NSEPythonProvider, OfficialAuthorizedProvider, PublicNSEProvider")


class SourceQuery(BaseModel):
    """Structured query parameters derived deterministically from claim fields."""
    name: Optional[str] = Field(None, description="Person, advisor, or entity name to search")
    registration_number: Optional[str] = Field(None, description="Official registration ID (e.g. INA, INZ, CIN)")
    company_name: Optional[str] = Field(None, description="Company or issuer legal name")
    company_symbol: Optional[str] = Field(None, description="Exchange trading symbol (e.g. ABC, RELIANCE)")
    keywords: list[str] = Field(default_factory=list, description="Keywords for filing or announcement search")
    date_range: Optional[tuple[Optional[str], Optional[str]]] = Field(None, description="(start_date, end_date) in ISO format")
    temporal_focus: Optional[str] = Field(None, description="current, historical, future, or specific year/quarter")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Additional structured parameters")


class SourcePlan(BaseModel):
    """Routing plan defining primary and fallback sources for a claim."""
    primary: list[str] = Field(default_factory=list, description="List of preferred source IDs from catalog")
    fallback: list[str] = Field(default_factory=list, description="Fallback source IDs if primary is unavailable")
    query: SourceQuery = Field(description="Structured search query")
    required_source_types: list[SourceTypeTaxonomy] = Field(default_factory=list, description="Taxonomy types required")


class SourceSearchResult(BaseModel):
    """Individual candidate record or match from a source search before full document retrieval."""
    result_id: str = Field(description="Unique candidate result ID")
    source_id: str = Field(description="Catalog source ID (e.g. sebi_recognised_intermediaries)")
    title: str = Field(description="Title or headline of candidate record")
    url: str = Field(description="Direct URL to candidate source document")
    snippet: Optional[str] = Field(None, description="Summary or snippet text")
    published_at: Optional[str] = Field(None, description="Publication timestamp if available")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional search metadata")


class RetrievalMetadata(BaseModel):
    """Technical metadata about the retrieval operation."""
    status: RetrievalStatus = Field(description="Explicit retrieval status")
    http_status: Optional[int] = Field(None, description="HTTP response code if HTTP was attempted")
    method: str = Field(description="Adapter class or method used")
    mode: RetrievalMode = Field(description="LIVE, CACHE, or FIXTURE")
    response_time_ms: float = Field(0.0, description="Network or lookup duration in milliseconds")
    error_message: Optional[str] = Field(None, description="Error or reason if retrieval failed")


class SourceDocument(BaseModel):
    """Normalized representation of a retrieved authoritative document."""
    document_id: str = Field(description="Unique source document ID (e.g. DOC-001)")
    source_id: str = Field(description="Catalog source ID")
    organization: str = Field(description="Authoritative organization (e.g. SEBI, NSE, BSE, RBI)")
    source_type: SourceTypeTaxonomy = Field(description="Taxonomy classification")
    title: str = Field(description="Official title or filing header")
    url: str = Field(description="Canonical URL of source document")
    retrieved_at: str = Field(description="ISO 8601 timestamp of retrieval")
    published_at: Optional[str] = Field(None, description="ISO 8601 timestamp of publication if known")
    content: str = Field(description="Normalized document text content")
    content_hash: str = Field(description="SHA-256 hash of normalized content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Source-specific fields (e.g. registration details)")
    retrieval: RetrievalMetadata = Field(description="Retrieval execution details")
    authoritative_provenance: Optional[AuthoritativeProvenance] = Field(default=None, description="Common authoritative source provenance")


class EvidenceRelevance(BaseModel):
    """Structured relevance breakdown for an evidence candidate."""
    matched_terms: list[str] = Field(default_factory=list, description="Terms from claim matched in source")
    matched_entities: list[str] = Field(default_factory=list, description="Entities matched in source")
    matched_dates: list[str] = Field(default_factory=list, description="Dates or time periods matched")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Structural similarity/relevance score")


class EvidenceProvenance(BaseModel):
    """Audit trail of how and when evidence was retrieved."""
    retrieved_at: str = Field(description="ISO 8601 timestamp")
    retrieval_method: str = Field(description="Adapter name")
    source_mode: RetrievalMode = Field(description="LIVE, OFFICIAL_SNAPSHOT, CACHE, FIXTURE, or SOURCE_UNAVAILABLE")
    source_url: str = Field(description="Authoritative source URL")


class EvidenceCandidate(BaseModel):
    """Candidate evidence excerpt extracted from an authoritative source.
    
    CRITICAL: verification_status remains UNVERIFIED. Engine 5 evaluates truth.
    """
    evidence_id: str = Field(description="Unique evidence ID (e.g. EVID-001)")
    claim_id: str = Field(description="Associated canonical claim ID")
    source_document_id: str = Field(description="Originating SourceDocument ID")
    excerpt: str = Field(description="Verbatim or focused excerpt from source document")
    relevance: EvidenceRelevance = Field(description="Relevance signals")
    source_type: SourceTypeTaxonomy = Field(description="Source taxonomy category")
    authority_tier: AuthorityTier = Field(description="Authority rating of the source")
    provenance: EvidenceProvenance = Field(description="Provenance and retrieval audit trail")
    authoritative_provenance: Optional[AuthoritativeProvenance] = Field(default=None, description="Common authoritative provenance")
    verification_status: Literal["UNVERIFIED"] = Field(
        default="UNVERIFIED",
        description="Must always be UNVERIFIED in Engine 4"
    )


class ClaimSourceResult(BaseModel):
    """Complete source discovery and retrieval result for a single claim."""
    claim_id: str = Field(description="Canonical claim ID")
    source_plan: SourcePlan = Field(description="Routing plan constructed for this claim")
    searches: list[SourceSearchResult] = Field(default_factory=list, description="Search hits before retrieval")
    documents: list[SourceDocument] = Field(default_factory=list, description="Retrieved full source documents")
    evidence_candidates: list[EvidenceCandidate] = Field(default_factory=list, description="Structured evidence excerpts")
    authoritative_provenances: list[AuthoritativeProvenance] = Field(default_factory=list, description="Authoritative provenances per source")


class SourceAnalysisMetadata(BaseModel):
    """Aggregate statistics for Source Intelligence execution."""
    claims_processed: int = 0
    sources_queried: int = 0
    documents_retrieved: int = 0
    evidence_candidates_count: int = 0
    retrieval_failures: int = 0
    cache_hits: int = 0
    processing_time_ms: float = 0.0


class SourceAnalysis(BaseModel):
    """Top-level output schema for Engine 4."""
    content_id: str = Field(description="UUID of source NormalizedContent")
    claim_sources: list[ClaimSourceResult] = Field(default_factory=list, description="Source results per claim")
    analysis_metadata: SourceAnalysisMetadata = Field(description="Execution summary metadata")


class SourceCatalogEntry(BaseModel):
    """Metadata specification for a source registered in the Source Catalog."""
    source_id: str = Field(description="Unique machine identifier for source")
    organization: str = Field(description="Operating entity (e.g. SEBI, NSE, BSE)")
    type: SourceTypeTaxonomy = Field(description="Taxonomy classification")
    authority_tier: AuthorityTier = Field(description="Source authority level")
    supported_claim_types: list[str] = Field(default_factory=list, description="Claim types handled")
    capabilities: list[str] = Field(default_factory=list, description="Search capabilities supported")
    base_url: str = Field(description="Official root or search URL")
    adapter_name: str = Field(description="Name of Python adapter class")
    description: str = Field(description="Human readable description")


ProviderAccessState = Literal[
    "ENABLED",
    "DISABLED",
    "CREDENTIALS_MISSING",
    "ACCESS_UNAUTHORIZED",
    "LIVE_AVAILABLE",
    "SOURCE_UNAVAILABLE",
]


class ProviderAccessConfig(BaseModel):
    """Server-side provider access configuration status.
    
    CRITICAL: Never exposes secrets or API keys.
    """
    source_identifier: str = Field(description="Unique source ID (e.g. SEBI, RBI, NSE, BSE)")
    authority_name: str = Field(description="Full regulatory authority name")
    state: ProviderAccessState = Field(description="Current operational access state")
    access_mechanism: str = Field(description="Protocol/API mechanism (e.g. HTTPS Public Registry, DBIE / Macro Data, Official Exchange API)")
    credentials_required: bool = Field(default=False, description="Whether server-side credentials are required")
    has_credentials: bool = Field(default=False, description="Whether credentials are configured (no secret exposed)")
    live_supported: bool = Field(default=False, description="Whether live requests are supported by this source")
    snapshot_fallback_available: bool = Field(default=True, description="Whether official snapshot fallback exists")
    limitations: list[str] = Field(default_factory=list, description="Explicit product or access limitations")
    diagnostic_message: Optional[str] = Field(default=None, description="Human/audit diagnostic details")


class SourceHealthReport(BaseModel):
    """Overall authoritative source health and diagnostic report."""
    timestamp: str = Field(description="ISO-8601 evaluation timestamp")
    sources: dict[str, ProviderAccessConfig] = Field(default_factory=dict, description="Status keyed by source identifier")
    summary: dict[str, str] = Field(default_factory=dict, description="High-level status per source (e.g. SEBI: LIVE_AVAILABLE)")


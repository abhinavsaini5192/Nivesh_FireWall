"""Phase 15.B — Production Credential Activation & Real-Record Verification Test Suite.

Validates legitimate production access, server-side credential isolation,
and end-to-end verification against actual authoritative records:
- REAL CLAIM → CLAIM REQUIREMENT → GATEWAY → REAL DATA → NORMALIZATION → PROVENANCE → EVIDENCE VERIFICATION → IDENTITY RESOLUTION → POLICY

Tests explicitly distinguish:
- LIVE
- OFFICIAL_SNAPSHOT
- CACHE
- FIXTURE
- SOURCE_UNAVAILABLE
- CREDENTIALS_MISSING
- ACCESS_UNAUTHORIZED
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimAnalysis, ClaimAnalysisMetadata
from nivesh.schemas.normalized import (
    NormalizedContent,
    SourceInfo,
    RawContent,
    NormalizedText,
    Provenance,
    EntitiesContainer,
    EntityItem,
)
from nivesh.schemas.sources import (
    SourceQuery,
    SourceAnalysis,
    SourceAnalysisMetadata,
    ProviderAccessConfig,
    SourceHealthReport,
)
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import IdentityStatus
from nivesh.api.app import app


# ---------------------------------------------------------------------------
# Test 1 — SEBI Real Record Verification (Live & End-to-End)
# ---------------------------------------------------------------------------
def test_sebi_real_record_verification_chain():
    """Test 1: Verify real SEBI intermediary (360 ONE Investment Adviser and Trustee Services Limited)
    across the entire verification chain:
    Gateway -> SEBI Live Retrieval -> Normalization -> Evidence -> Identity ESTABLISHED -> Provenance
    """
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        sebi_live_enabled=True,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    sebi_adapter = SEBIAdapter(default_mode="LIVE")
    gw.register_adapter("SEBIAdapter", sebi_adapter, ["intermediary_registration"])

    claim_text = "360 ONE Investment Adviser and Trustee Services Limited is registered as a SEBI Investment Adviser."
    claim = CanonicalClaim(
        claim_id="CLM-SEBI-360ONE",
        source_content_id="CNT-360ONE",
        text=ClaimText(original=claim_text, normalized=claim_text.lower()),
        subject="360 ONE Investment Adviser and Trustee Services Limited",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    content = NormalizedContent(
        content_id="CNT-360ONE",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_text),
        normalized=NormalizedText(text=claim_text, language="en", language_confidence=1.0),
        entities=EntitiesContainer(
            organizations=[
                EntityItem(
                    text="360 ONE Investment Adviser and Trustee Services Limited",
                    normalized="360 ONE Investment Adviser and Trustee Services Limited",
                    type="organization"
                )
            ],
            regulators=[EntityItem(text="SEBI", normalized="SEBI", type="regulator")],
        ),
        provenance=Provenance(created_at="2026-10-02T00:00:00Z", input_type="text"),
    )

    # 1. Authoritative Gateway Retrieval
    source_res = gw.execute_claim_verification(claim, content=content, mode_override="LIVE")
    assert len(source_res.documents) >= 1
    doc = source_res.documents[0]
    assert doc.retrieval.status == "SUCCESS"
    assert doc.authoritative_provenance is not None
    # Provenance contains explicit authority, retrieval timestamp, and reference
    assert doc.authoritative_provenance.source == "SEBI"
    assert doc.authoritative_provenance.retrieved_at is not None
    assert "https://www.sebi.gov.in" in doc.authoritative_provenance.source_reference
    assert doc.metadata.get("registration_number") == "INA000000888"

    # 2. Evidence Verification Engine (Engine 5)
    evidence_engine = EvidenceVerificationEngine()
    claim_analysis = ClaimAnalysis(
        content_id="CNT-360ONE",
        claims=[claim],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    source_analysis = SourceAnalysis(
        content_id="CNT-360ONE",
        claim_sources=[source_res],
        analysis_metadata=SourceAnalysisMetadata(
            claims_processed=1,
            sources_queried=1,
            documents_retrieved=len(source_res.documents)
        ),
    )
    evidence_res = evidence_engine.verify(content=content, claims=claim_analysis, sources=source_analysis)
    assert len(evidence_res.verifications) == 1
    verification = evidence_res.verifications[0]
    assert verification.status == "SUPPORTED"
    assert verification.confidence >= 0.90

    # 3. Identity Verification Engine (Engine 9)
    identity_engine = IdentityVerificationEngine()
    identity_res = identity_engine.verify(
        content=content,
        claims=claim_analysis,
        sources=source_analysis,
        evidence=evidence_res
    )
    assert identity_res.identity_status == IdentityStatus.ESTABLISHED
    assert len(identity_res.entities) >= 1


# ---------------------------------------------------------------------------
# Test 2 — SEBI Nonexistent Record (NO_MATCH does not become FRAUD)
# ---------------------------------------------------------------------------
def test_sebi_nonexistent_record_no_match():
    """Test 2: Nonexistent registration INA999999999 returns NO_MATCH and NOT_ESTABLISHED,
    never fabricating FRAUD or IDENTITY_MISMATCH without positive conflicting evidence.
    """
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        sebi_live_enabled=True,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    sebi_adapter = SEBIAdapter(default_mode="LIVE")
    gw.register_adapter("SEBIAdapter", sebi_adapter, ["intermediary_registration"])

    claim_text = "Fictional Financial Advisers is registered as a SEBI Investment Adviser with registration INA999999999."
    claim = CanonicalClaim(
        claim_id="CLM-SEBI-NONEXISTENT",
        source_content_id="CNT-NONEXISTENT",
        text=ClaimText(original=claim_text, normalized=claim_text.lower()),
        subject="Fictional Financial Advisers",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )

    content = NormalizedContent(
        content_id="CNT-NONEXISTENT",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_text),
        normalized=NormalizedText(text=claim_text, language="en", language_confidence=1.0),
        entities=EntitiesContainer(
            organizations=[
                EntityItem(
                    text="Fictional Financial Advisers",
                    normalized="Fictional Financial Advisers",
                    type="organization"
                )
            ],
            regulators=[EntityItem(text="SEBI", normalized="SEBI", type="regulator")],
        ),
        provenance=Provenance(created_at="2026-10-02T00:00:00Z", input_type="text"),
    )

    source_res = gw.execute_claim_verification(claim, content=content, mode_override="LIVE")
    assert len(source_res.documents) >= 1
    doc = source_res.documents[0]
    assert doc.retrieval.status == "NO_MATCH"

    evidence_engine = EvidenceVerificationEngine()
    claim_analysis = ClaimAnalysis(
        content_id="CNT-NONEXISTENT",
        claims=[claim],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    source_analysis = SourceAnalysis(
        content_id="CNT-NONEXISTENT",
        claim_sources=[source_res],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=len(source_res.documents)),
    )
    evidence_res = evidence_engine.verify(content=content, claims=claim_analysis, sources=source_analysis)
    assert evidence_res.verifications[0].status == "INSUFFICIENT_EVIDENCE"

    identity_engine = IdentityVerificationEngine()
    identity_res = identity_engine.verify(
        content=content,
        claims=claim_analysis,
        sources=source_analysis,
        evidence=evidence_res
    )
    # INVARIANT: NO_MATCH results in NOT_ESTABLISHED, NEVER IDENTITY_MISMATCH
    assert identity_res.identity_status == IdentityStatus.NOT_ESTABLISHED
    assert identity_res.identity_status != IdentityStatus.IDENTITY_MISMATCH


# ---------------------------------------------------------------------------
# Test 3 — RBI Real Data Verification
# ---------------------------------------------------------------------------
def test_rbi_real_data_verification():
    """Test 3: Traces claimed RBI Monetary Policy Committee policy repo rate to actual authoritative publication."""
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    rbi_adapter = RBIAdapter(default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("RBIAdapter", rbi_adapter, ["official_data", "regulatory_publications"])

    claim_text = "The Reserve Bank of India MPC policy repo rate is 6.50%."
    claim = CanonicalClaim(
        claim_id="CLM-RBI-RATE",
        source_content_id="CNT-RBI",
        text=ClaimText(original=claim_text, normalized=claim_text.lower()),
        subject="Reserve Bank of India",
        predicate="POLICY_RATE_IS",
        object="6.50%",
        claim_type="FINANCIAL",
    )

    content = NormalizedContent(
        content_id="CNT-RBI",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_text),
        normalized=NormalizedText(text=claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-02T00:00:00Z", input_type="text"),
    )

    source_res = gw.execute_claim_verification(claim, content=content, mode_override="OFFICIAL_SNAPSHOT")
    assert len(source_res.documents) >= 1
    doc = source_res.documents[0]
    assert doc.retrieval.status == "SUCCESS"
    assert "6.50%" in doc.content
    assert doc.authoritative_provenance is not None
    assert doc.authoritative_provenance.source == "RBI"
    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert "rbi.org.in" in doc.authoritative_provenance.source_reference

    evidence_engine = EvidenceVerificationEngine()
    claim_analysis = ClaimAnalysis(
        content_id="CNT-RBI",
        claims=[claim],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    source_analysis = SourceAnalysis(
        content_id="CNT-RBI",
        claim_sources=[source_res],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=len(source_res.documents)),
    )
    evidence_res = evidence_engine.verify(content=content, claims=claim_analysis, sources=source_analysis)
    assert len(evidence_res.verifications) == 1
    assert evidence_res.verifications[0].status == "SUPPORTED"
    assert evidence_res.verifications[0].confidence >= 0.90


# ---------------------------------------------------------------------------
# Test 4 — NSE Credential Handling & Missing State
# ---------------------------------------------------------------------------
def test_nse_credentials_missing_state():
    """Test 4: When NSE credentials are absent, adapter and gateway explicitly report CREDENTIALS_MISSING."""
    # When api_key is None and default_mode is LIVE
    nse_adapter = NSEAdapter(default_mode="LIVE", api_key=None)
    hits = nse_adapter.search(SourceQuery(company_symbol="ABC", keywords=["bonus"]))
    assert len(hits) >= 1

    doc = nse_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "CREDENTIALS_MISSING"
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.response_status == "CREDENTIALS_MISSING"
    assert doc.retrieval.mode != "LIVE"

    # Gateway diagnostic report also reports CREDENTIALS_MISSING
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        nse_live_enabled=True,
        nse_api_key=None,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    gw.register_adapter("NSEAdapter", nse_adapter, ["corporate_announcements"])
    health = gw.check_provider_health("NSE")
    assert health.state == "CREDENTIALS_MISSING"
    assert health.credentials_required is True
    assert health.has_credentials is False


# ---------------------------------------------------------------------------
# Test 5 — BSE Credential Handling & Missing State
# ---------------------------------------------------------------------------
def test_bse_credentials_missing_state():
    """Test 5: When BSE credentials are absent, adapter and gateway explicitly report CREDENTIALS_MISSING."""
    bse_adapter = BSEAdapter(default_mode="LIVE", api_key=None)
    hits = bse_adapter.search(SourceQuery(company_symbol="ABC", keywords=["bonus"]))
    assert len(hits) >= 1

    doc = bse_adapter.retrieve(hits[0])
    assert doc.retrieval.status == "CREDENTIALS_MISSING"
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.response_status == "CREDENTIALS_MISSING"
    assert doc.retrieval.mode != "LIVE"

    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        bse_live_enabled=True,
        bse_api_key=None,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    gw.register_adapter("BSEAdapter", bse_adapter, ["corporate_data"])
    health = gw.check_provider_health("BSE")
    assert health.state == "CREDENTIALS_MISSING"
    assert health.credentials_required is True
    assert health.has_credentials is False


# ---------------------------------------------------------------------------
# Test 6 — Live Failure Degrades Truthfully (Never Fake LIVE)
# ---------------------------------------------------------------------------
def test_live_failure_never_becomes_supported_live():
    """Test 6: When a live network query fails, the system reports SOURCE_UNAVAILABLE
    or degrades to snapshot with OFFICIAL_SNAPSHOT mode, NEVER falsely reporting LIVE.
    """
    adapter = SEBIAdapter(default_mode="SOURCE_UNAVAILABLE")
    query = SourceQuery(name="Nonexistent Corp")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SOURCE_UNAVAILABLE"
    assert doc.retrieval.mode == "SOURCE_UNAVAILABLE"
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"
    assert doc.retrieval.mode != "LIVE"
    assert doc.authoritative_provenance.retrieval_mode != "LIVE"


# ---------------------------------------------------------------------------
# Test 7 — Official Snapshot Mode Preserved
# ---------------------------------------------------------------------------
def test_official_snapshot_mode_preserved():
    """Test 7: Pre-downloaded regulatory snapshots maintain OFFICIAL_SNAPSHOT mode."""
    adapter = SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(name="360 ONE")
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.freshness == "SNAPSHOT"
    assert doc.retrieval.mode != "LIVE"


# ---------------------------------------------------------------------------
# Test 8 — Cache Preserves Original Provenance & Timestamps
# ---------------------------------------------------------------------------
def test_cache_preserves_original_source_and_timestamp():
    """Test 8: Second retrieval from cache explicitly reports CACHE mode and preserves original timestamp."""
    adapter = SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(name="360 ONE")
    hits = adapter.search(query)

    doc1 = adapter.retrieve(hits[0])
    doc2 = adapter.retrieve(hits[0])

    assert doc1.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert doc2.retrieval.mode == "CACHE"
    assert doc2.authoritative_provenance.retrieval_mode == "CACHE"
    assert doc2.retrieved_at == doc1.retrieved_at


# ---------------------------------------------------------------------------
# Test 9 — Cross-Source Corroboration (NSE + BSE)
# ---------------------------------------------------------------------------
def test_cross_source_corroboration():
    """Test 9: Where a claim concerns information published by multiple authoritative sources,
    corroboration queries both NSE and BSE.
    """
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_actions"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_actions"])

    claim = CanonicalClaim(
        claim_id="CLM-CORROBORATE-BONUS",
        source_content_id="CNT-CORROBORATE",
        text=ClaimText(original="ABC Limited announced a 1:1 bonus equity share issue.", normalized="abc limited announced 1:1 bonus equity share issue"),
        subject="ABC",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    res = gw.execute_claim_verification(claim, require_cross_source=True, mode_override="OFFICIAL_SNAPSHOT")
    orgs = [d.organization for d in res.documents]
    assert "NSE" in orgs
    assert "BSE" in orgs
    assert len(res.documents) >= 2


# ---------------------------------------------------------------------------
# Test 10 — Frontend / API Provenance Health Contract
# ---------------------------------------------------------------------------
def test_frontend_provenance_health_contract():
    """Test 10: Ensures GET /api/v1/sources/health returns full diagnostics without secret leakage,
    matching the schema required by frontend ProvenanceAuditPanel and ClaimEvidenceDetailCard.
    """
    client = TestClient(app)
    resp = client.get("/api/v1/sources/health")
    assert resp.status_code == 200

    data = resp.json()
    assert "timestamp" in data
    assert "summary" in data
    assert "sources" in data

    # Verify all four authoritative providers are represented
    for provider in ("SEBI", "RBI", "NSE", "BSE"):
        assert provider in data["summary"]
        assert provider in data["sources"]
        src_info = data["sources"][provider]
        assert "state" in src_info
        assert "access_mechanism" in src_info
        assert "credentials_required" in src_info
        assert "has_credentials" in src_info
        assert "limitations" in src_info
        # CRITICAL SECURITY INVARIANT: No raw secrets or API keys in response
        assert "api_key" not in src_info
        assert "api_secret" not in src_info

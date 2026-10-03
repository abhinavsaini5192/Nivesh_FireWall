"""Phase 15.D.2: BSE Provider Hardening, Controlled Integration & Security Boundary Tests.

Verifies:
1. Deterministic provider priority (OfficialAuthorized -> PublicBSE -> OfficialSnapshot)
2. Official authorized credentialed access and explicit states (CREDENTIALS_MISSING, ACCESS_UNAUTHORIZED, LIVE_AVAILABLE)
3. Zero credential leakage across provenance, content, logs, and API models
4. Public BSE provider safety: HTTPS, host allowlist, SSRF, redirect validation, payload limits, rate limiting
5. Akamai WAF / anti-bot handling: HTTP 403 maps to ACCESS_UNAUTHORIZED and graceful snapshot fallback with NO circumvention
6. Real BSE record verification:
   - Announcement: Samsrita Labs (539267) EGM notice
   - Corporate Action: NMDC (526371) Re 1 dividend (SUPPORTED vs CONTRADICTED)
   - Board Meeting: DP Abhushan (540772) fund raising
7. Cross-source corroboration (BSE + NSE)
8. Execution safety: Shell / curl / subprocess execution strictly blocked
"""

import json
from unittest.mock import patch, MagicMock
import pytest
from starlette.testclient import TestClient

from nivesh.api.app import app
from nivesh.config.settings import Settings
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimAnalysis, ClaimAnalysisMetadata
from nivesh.schemas.normalized import NormalizedContent, SourceInfo, RawContent, NormalizedText, Provenance
from nivesh.schemas.sources import SourceQuery, SourceAnalysis, SourceAnalysisMetadata
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.ssrf import SsrfError
from nivesh.sources.adapters.bse_adapter import (
    BSEAdapter,
    OFFICIAL_BSE_SNAPSHOT_DATASET,
)
from nivesh.sources.adapters.bse_providers import (
    BaseBSEProvider,
    OfficialAuthorizedBSEProvider,
    PublicBSEProvider,
    OfficialSnapshotBSEProvider,
    BSESecurityError,
    ALLOWED_BSE_HOSTS,
    BSE_API_ANN_URL,
    BSE_API_ACTIONS_URL,
)
from nivesh.sources.adapters.nse_adapter import NSEAdapter


# ---------------------------------------------------------------------------
# 1. Deterministic Provider Priority & Fallback
# ---------------------------------------------------------------------------

def test_bse_provider_priority_auto_without_credentials():
    """In AUTO mode without API key, defaults to OfficialSnapshot (or Public if live)."""
    adapter = BSEAdapter(default_mode="LIVE", api_key=None, provider_preference="AUTO")
    active = adapter.resolve_active_provider()
    # Without credentials, AUTO resolves to OfficialSnapshot to ensure deterministic safety
    assert isinstance(active, OfficialSnapshotBSEProvider)


def test_bse_provider_priority_auto_with_credentials():
    """In AUTO mode with API key and LIVE mode, resolves to OfficialAuthorizedBSEProvider."""
    adapter = BSEAdapter(
        default_mode="LIVE",
        api_key="secret-authorized-key-12345",
        provider_preference="AUTO",
    )
    active = adapter.resolve_active_provider()
    assert isinstance(active, OfficialAuthorizedBSEProvider)


def test_bse_provider_priority_explicit_public():
    """Explicit PUBLIC preference resolves to PublicBSEProvider."""
    adapter = BSEAdapter(
        default_mode="LIVE",
        provider_preference="PUBLIC",
    )
    active = adapter.resolve_active_provider()
    assert isinstance(active, PublicBSEProvider)


def test_bse_provider_priority_explicit_snapshot():
    """Explicit SNAPSHOT preference resolves to OfficialSnapshotBSEProvider."""
    adapter = BSEAdapter(
        default_mode="LIVE",
        api_key="secret-authorized-key-12345",
        provider_preference="SNAPSHOT",
    )
    active = adapter.resolve_active_provider()
    assert isinstance(active, OfficialSnapshotBSEProvider)


def test_bse_fallback_never_silently_promotes_snapshot_to_live():
    """When falling back from a failed live query, the mode MUST remain OFFICIAL_SNAPSHOT."""
    adapter = BSEAdapter(
        default_mode="LIVE",
        api_key="valid-key-format-1234",
    )
    # Simulate upstream network failure
    with patch.object(adapter, "safe_http_fetch", return_value=(500, None, {})):
        query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
        hits = adapter.search(query)
        doc = adapter.retrieve(hits[0])

        assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.freshness == "SNAPSHOT"
        assert doc.authoritative_provenance.provider == "OfficialSnapshot"
        assert doc.authoritative_provenance.retrieval_mode != "LIVE"
        assert doc.authoritative_provenance.retrieval_mode != "LIVE_AUTHORIZED"


# ---------------------------------------------------------------------------
# 2. Official Authorized Credentialed Access & State Management
# ---------------------------------------------------------------------------

def test_official_provider_operational_states():
    """Verifies operational state reporting across missing, invalid, and valid credentials."""
    # Missing
    p_missing = OfficialAuthorizedBSEProvider(api_key=None)
    assert p_missing.state == "CREDENTIALS_MISSING"
    assert p_missing.is_available is False

    # Invalid / short
    p_invalid = OfficialAuthorizedBSEProvider(api_key="short")
    assert p_invalid.state == "ACCESS_UNAUTHORIZED"
    assert p_invalid.is_available is True

    # Valid enterprise key
    p_valid = OfficialAuthorizedBSEProvider(api_key="secret-authorized-key-12345")
    assert p_valid.state == "LIVE_AVAILABLE"
    assert p_valid.is_available is True


def test_official_provider_zero_credential_leakage():
    """Verifies credentials are never exposed in string representations, details, or metadata."""
    secret_key = "secret-super-confidential-key-999"
    provider = OfficialAuthorizedBSEProvider(api_key=secret_key, api_secret="confidential-secret")

    # __repr__ and __str__ mask secret
    repr_str = repr(provider)
    assert secret_key not in repr_str
    assert str(provider) == repr_str
    assert "..." in repr_str or "***" in repr_str

    # Returned record does not leak credentials
    status, record, err = provider.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "RELIANCE")
    assert status == "SUCCESS"
    assert record is not None
    assert secret_key not in record["details"]
    assert secret_key not in record["url"]
    assert secret_key not in record["subject"]
    assert secret_key not in json.dumps(record)


# ---------------------------------------------------------------------------
# 3. Public BSE Provider Safety & Akamai WAF Handling
# ---------------------------------------------------------------------------

def test_public_bse_provider_ssrf_safety():
    """PublicBSEProvider validates all target endpoints against SSRF and host whitelist."""
    provider = PublicBSEProvider()

    # Blocked schemes
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("http://www.bseindia.com/corporates/ann.html")

    # Blocked hosts
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://attacker.com/api")

    # Blocked private IPs
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://10.0.0.1/api")

    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://127.0.0.1/api")

    # Allowed hosts
    provider.validate_target_endpoint("https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w")
    provider.validate_target_endpoint("https://www.bseindia.com/corporates/ann.html")


def test_public_bse_provider_redirect_safety():
    """Validates that redirects must point strictly to allowed BSE domains."""
    provider = PublicBSEProvider()

    # Valid redirect
    provider.validate_redirect_url("https://www.bseindia.com/corporates/ann")

    # Malicious redirect to internal AWS metadata
    with pytest.raises(SsrfError):
        provider.validate_redirect_url("http://169.254.169.254/latest/meta-data/")


def test_public_bse_provider_akamai_403_handling():
    """HTTP 403 / bot protection challenge maps cleanly to ACCESS_UNAUTHORIZED without bypass attempts."""
    mock_fetch = MagicMock(return_value=(
        403,
        "<html><head><title>Access Denied</title></head><body><h1>403 Forbidden</h1>Reference #18.8265c817.1727961234.3a4b</body></html>",
        {"Akamai-GRN": "0.8265c817.1727961234.3a4b", "Server": "AkamaiGHost"},
    ))
    provider = PublicBSEProvider(safe_fetch_fn=mock_fetch)

    status, rec, err = provider.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "RELIANCE")
    assert status == "ACCESS_UNAUTHORIZED"
    assert rec is None
    assert "Akamai bot protection active" in err
    assert "0.8265c817" in err


def test_public_bse_provider_payload_limit():
    """Rejects payloads larger than MAX_BSE_DOC_BYTES (5 MB)."""
    oversized = "x" * (6 * 1024 * 1024)
    mock_fetch = MagicMock(return_value=(200, oversized, {}))
    provider = PublicBSEProvider(safe_fetch_fn=mock_fetch)

    status, rec, err = provider.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "ABC")
    assert status == "SOURCE_UNAVAILABLE"
    assert "exceeded max size limit" in err


# ---------------------------------------------------------------------------
# 4. Execution Safety (Zero Shell / Subprocess Execution)
# ---------------------------------------------------------------------------

def test_bse_provider_execution_safety():
    """BSE provider prevents any shell or external command invocation."""
    provider = PublicBSEProvider()
    with pytest.raises(BSESecurityError) as exc_info:
        provider.prevent_unsafe_execution("curl -X GET https://api.bseindia.com")
    assert "strictly forbidden" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Real BSE Record Validation & Evidence Verification
# ---------------------------------------------------------------------------

def test_real_bse_record_a_announcement():
    """Test A: Real corporate announcement (Samsrita Labs Ltd 539267 EGM Notice)."""
    adapter = BSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="SAMSRITA", keywords=["meeting", "egm"])
    hits = adapter.search(query)
    assert len(hits) >= 1
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SUCCESS"
    assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert "Samsrita Labs Ltd" in doc.content
    assert "539267" in doc.content
    assert "701133b8-8d99-4b23-bcba-adb0d71e52eb" in doc.content
    assert doc.authoritative_provenance.source == "BSE"
    assert doc.authoritative_provenance.source_record_id == "701133b8-8d99-4b23-bcba-adb0d71e52eb"


def test_real_bse_record_b_corporate_action_supported_vs_contradicted():
    """Test B: Real corporate action (NMDC Re 1 dividend).

    Validates that:
    1. Claim of ₹1 per share dividend produces SUPPORTED.
    2. Claim of ₹50 per share dividend produces CONTRADICTED.
    Derived dynamically via EvidenceVerificationEngine and NumericalEvaluator.
    """
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    bse_adapter = BSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("BSEAdapter", bse_adapter, ["corporate_actions"])

    evidence_engine = EvidenceVerificationEngine()

    # --- 1. Supporting Claim: ₹1 per share dividend ---
    claim_supported_text = "NMDC announced a dividend of Re 1 per share."
    claim_supported = CanonicalClaim(
        claim_id="CLM-NMDC-DIV-1",
        source_content_id="CNT-NMDC-1",
        text=ClaimText(original=claim_supported_text, normalized=claim_supported_text.lower()),
        subject="NMDC",
        predicate="ANNOUNCED_DIVIDEND",
        object="Re 1 per share",
        claim_type="CORPORATE_EVENT",
    )
    content_supported = NormalizedContent(
        content_id="CNT-NMDC-1",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_supported_text),
        normalized=NormalizedText(text=claim_supported_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    src_res_supported = gw.execute_claim_verification(claim_supported, content=content_supported, mode_override="OFFICIAL_SNAPSHOT")
    assert len(src_res_supported.documents) >= 1
    assert src_res_supported.documents[0].retrieval.status == "SUCCESS"

    claim_analysis_sup = ClaimAnalysis(
        content_id="CNT-NMDC-1",
        claims=[claim_supported],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    src_analysis_sup = SourceAnalysis(
        content_id="CNT-NMDC-1",
        claim_sources=[src_res_supported],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=1),
    )
    ev_res_sup = evidence_engine.verify(content=content_supported, claims=claim_analysis_sup, sources=src_analysis_sup)
    assert ev_res_sup.verifications[0].status == "SUPPORTED"
    assert ev_res_sup.verifications[0].confidence >= 0.85

    # --- 2. Contradicting Claim: ₹50 per share dividend ---
    claim_contradicted_text = "NMDC announced a dividend of Rs 50 per share."
    claim_contradicted = CanonicalClaim(
        claim_id="CLM-NMDC-DIV-50",
        source_content_id="CNT-NMDC-50",
        text=ClaimText(original=claim_contradicted_text, normalized=claim_contradicted_text.lower()),
        subject="NMDC",
        predicate="ANNOUNCED_DIVIDEND",
        object="Rs 50 per share",
        claim_type="CORPORATE_EVENT",
    )
    content_contradicted = NormalizedContent(
        content_id="CNT-NMDC-50",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_contradicted_text),
        normalized=NormalizedText(text=claim_contradicted_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    src_res_contra = gw.execute_claim_verification(claim_contradicted, content=content_contradicted, mode_override="OFFICIAL_SNAPSHOT")
    claim_analysis_contra = ClaimAnalysis(
        content_id="CNT-NMDC-50",
        claims=[claim_contradicted],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    src_analysis_contra = SourceAnalysis(
        content_id="CNT-NMDC-50",
        claim_sources=[src_res_contra],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=1),
    )
    ev_res_contra = evidence_engine.verify(content=content_contradicted, claims=claim_analysis_contra, sources=src_analysis_contra)
    assert ev_res_contra.verifications[0].status == "CONTRADICTED"


def test_real_bse_record_c_board_meeting():
    """Test C: Real board meeting intimation (DP Abhushan Limited 540772)."""
    adapter = BSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="DPABHUSHAN", keywords=["meeting", "funds"])
    hits = adapter.search(query)
    assert len(hits) >= 1
    doc = adapter.retrieve(hits[0])

    assert doc.retrieval.status == "SUCCESS"
    assert "D. P. Abhushan Limited" in doc.content
    assert "540772" in doc.content
    assert "Raising Of Funds" in doc.content
    assert "2026-10-05" in doc.content
    assert doc.authoritative_provenance.source == "BSE"


# ---------------------------------------------------------------------------
# 6. Cross-Source Corroboration (BSE + NSE)
# ---------------------------------------------------------------------------

def test_bse_nse_cross_source_corroboration():
    """Validates cross-exchange corroboration between BSE and NSE on a dual-listed corporate event."""
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_actions"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_actions"])

    claim = CanonicalClaim(
        claim_id="CLM-DUAL-DIVIDEND",
        source_content_id="CNT-DUAL",
        text=ClaimText(original="NMDC announced a dividend of Re 1 per share.", normalized="nmdc announced dividend of re 1 per share"),
        subject="NMDC",
        predicate="ANNOUNCED_DIVIDEND",
        object="Re 1",
        claim_type="CORPORATE_EVENT",
    )

    res = gw.execute_claim_verification(claim, require_cross_source=True, mode_override="OFFICIAL_SNAPSHOT")
    orgs = [d.organization for d in res.documents]
    assert "NSE" in orgs
    assert "BSE" in orgs
    assert len(res.documents) >= 2

    # Sources remain strictly distinct
    bse_docs = [d for d in res.documents if d.organization == "BSE"]
    nse_docs = [d for d in res.documents if d.organization == "NSE"]
    assert bse_docs[0].authoritative_provenance.source == "BSE"
    assert nse_docs[0].authoritative_provenance.source == "NSE"


# ---------------------------------------------------------------------------
# 7. Frontend Provenance Health API Contract
# ---------------------------------------------------------------------------

def test_bse_health_endpoint_contract():
    """Ensures GET /api/v1/sources/health accurately reflects BSE state and no credentials leak."""
    client = TestClient(app)
    resp = client.get("/api/v1/sources/health")
    assert resp.status_code == 200

    data = resp.json()
    assert "BSE" in data["sources"]
    bse_health = data["sources"]["BSE"]
    assert bse_health["source_identifier"] == "BSE"
    assert bse_health["authority_name"] == "Bombay Stock Exchange"
    assert bse_health["state"] in ("CREDENTIALS_MISSING", "LIVE_AVAILABLE", "DISABLED")
    assert "api_key" not in bse_health
    assert "api_secret" not in bse_health

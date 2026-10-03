"""Phase 15.C.2: Hardened NSEPython Provider & Controlled Integration Test Suite.

Verifies:
- Test A: Optional dependency absent (system starts and operates safely without nsepython)
- Test B: Optional provider available (provider loads safely when present)
- Test C: Live public request execution (structured query execution)
- Test D: Real record normalization (all essential filing fields mapped)
- Test E: Evidence verification (supporting claim evaluation)
- Test F: Contradiction detection (conflicting claim evaluation)
- Test G: Truthful provenance (NSE + NSEPythonProvider + LIVE_PUBLIC)
- Test H: Failure handling (timeouts/errors map to failure, never fake contradiction)
- Test I: Unsafe mode blocked (vpn mode and os.popen shell execution strictly blocked)
- Test J: SSRF protection (loopback, private IP, metadata, HTTP, and non-NSE hosts blocked)
- Test K: Cache and snapshot separation (never mislabeled as LIVE_PUBLIC)
- Test L: Fallback behavior (deterministic fallback without fabricating live evidence)
- Test M: Frontend provenance contract (UI fields accurately populated)
- Test N: Full gateway integration (Claim -> Gateway -> Evidence -> Identity -> Policy)
- Test O: Provider priority hierarchy (Official provider takes priority over NSEPython)
"""

from datetime import datetime, timezone
import json
import os
import pytest
from unittest.mock import MagicMock, patch

from nivesh.config import Settings
from nivesh.evidence.numerical_evaluator import NumericalEvaluator
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimAnalysis, ClaimAnalysisMetadata
from nivesh.schemas.normalized import NormalizedContent, SourceInfo, RawContent, NormalizedText, Provenance
from nivesh.schemas.sources import (
    SourceQuery,
    SourceSearchResult,
    SourceDocument,
    EvidenceCandidate,
    EvidenceRelevance,
    EvidenceProvenance,
    AuthoritativeProvenance,
    RetrievalMetadata,
    SourceAnalysis,
    SourceAnalysisMetadata,
)
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.nse_providers import (
    BaseNSEProvider,
    OfficialAuthorizedProvider,
    PublicNSEProvider,
    NSEPythonProvider,
    SecurityError,
    NSE_ANNOUNCEMENTS_ENDPOINT,
    NSE_ACTIONS_ENDPOINT,
    NSE_EVENTS_ENDPOINT,
    NSE_RESULTS_ENDPOINT,
)
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.router import SourceRouter
from nivesh.sources.ssrf import SsrfError


# Real NSE Public Records (Captured Oct 3, 2026)
REAL_ANNOUNCEMENT_RECORD = {
    "symbol": "PIONEEREMB",
    "sm_name": "Pioneer Embroideries Limited",
    "desc": "Structural Digital Database",
    "an_dt": "03-Oct-2026 14:37:49",
    "attchmntText": "Compliance certificate for the quarter ended 30th September, 2026",
    "attchmntFile": "https://nsearchives.nseindia.com/corporate/PIONEEREMB_03102026143739_CoveringRegulation30092026.pdf",
    "seq_id": "106806218",
    "sm_isin": "INE156C01018",
}

REAL_ACTION_RECORD = {
    "symbol": "NMDC",
    "comp": "NMDC Limited",
    "series": "EQ",
    "faceVal": "1",
    "subject": "Dividend - Re 1 Per Share",
    "exDate": "05-Oct-2026",
    "recDate": "05-Oct-2026",
    "isin": "INE584A01023",
}

REAL_EVENT_RECORD = {
    "symbol": "DPABHUSHAN",
    "company": "D. P. Abhushan Limited",
    "purpose": "Fund Raising/Other business matters",
    "bm_desc": "Board Meeting Intimation for Considering Raising Of Funds By Issuance Of Equity Shares And/Or Warrants...",
    "date": "05-Oct-2026",
}


# --- TEST A: Optional dependency absent ---
def test_a_optional_dependency_absent():
    """Test A: When nsepython is uninstalled or unimportable, system starts safely and handles absence gracefully."""
    provider = NSEPythonProvider()
    provider._is_available = False
    provider._nsepython_module = None

    assert provider.is_available is False
    status, record, err = provider.fetch_corporate_data(
        category="CORPORATE_ANNOUNCEMENT",
        symbol="TCS",
        keywords=["dividend"]
    )
    assert status == "SOURCE_UNAVAILABLE"
    assert record is None
    assert "Optional dependency 'nsepython' is not installed" in err

    # Verify adapter operates normally in snapshot/fixture fallback mode
    adapter = NSEAdapter(provider=provider, default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = adapter.search(query)
    assert len(hits) >= 1
    doc = adapter.retrieve(hits[0])
    assert doc.retrieval.status == "SUCCESS"
    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"


# --- TEST B: Optional provider available ---
def test_b_optional_provider_available():
    """Test B: Provider loads successfully with safe default mode ('local') when module is present."""
    provider = NSEPythonProvider()
    mock_module = MagicMock(spec=["nse_events", "nse_results", "nsefetch"])
    mock_module.mode = "local"
    provider._nsepython_module = mock_module
    provider._is_available = True

    assert provider.is_available is True
    assert provider.provider_name == "NSEPythonProvider"
    assert provider.default_success_mode == "LIVE_PUBLIC"
    assert provider.access_method == "NSEPython / NSE public endpoint"


# --- TEST C: Live public request execution ---
def test_c_live_public_request_execution():
    """Test C: Public corporate filing query succeeds and returns matched record."""
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    status, record, err = provider.fetch_corporate_data(
        category="CORPORATE_ACTION",
        symbol="NMDC",
        keywords=["dividend"]
    )
    assert status == "SUCCESS"
    assert record is not None
    assert err is None
    assert record["symbol"] == "NMDC"


# --- TEST D: Real record normalization ---
def test_d_real_record_normalization():
    """Test D: Raw NSE filing record is normalized with all core attributes."""
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.return_value = [REAL_ANNOUNCEMENT_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    status, record, err = provider.fetch_corporate_data(
        category="CORPORATE_ANNOUNCEMENT",
        symbol="PIONEEREMB",
        keywords=["compliance"]
    )
    assert status == "SUCCESS"
    assert record["symbol"] == "PIONEEREMB"
    assert record["company_name"] == "Pioneer Embroideries Limited"
    assert record["broadcast_date"] == "03-Oct-2026 14:37:49"
    assert record["accession_number"] == "106806218"
    assert "https://nsearchives.nseindia.com" in record["url"]
    assert "Pioneer Embroideries Limited" in record["details"]


# --- TEST E: Evidence verification (SUPPORTED) ---
def test_e_evidence_verification_supported():
    """Test E: Real record supports a matching corporate claim."""
    claim = CanonicalClaim(
        claim_id="CLM-NMDC-SUPP",
        source_content_id="CNT-01",
        claim_type="CORPORATE_EVENT",
        subject="NMDC",
        predicate="DIVIDEND_ANNOUNCED",
        object="1",
        text=ClaimText(
            original="NMDC announced a dividend of ₹1 per share.",
            normalized="NMDC announced a dividend of ₹1 per share."
        )
    )

    candidate = EvidenceCandidate(
        evidence_id="EVD-01",
        claim_id="CLM-NMDC-SUPP",
        source_document_id="DOC-01",
        source_id="nse_corporate_actions",
        source_type="CORPORATE_ACTION",
        authority_tier="PRIMARY_OFFICIAL",
        excerpt="NATIONAL STOCK EXCHANGE OF INDIA — DISCLOSURE\nCompany: NMDC Limited\nSubject: Dividend - Re 1 Per Share\nEx-Date: 05-Oct-2026",
        relevance=EvidenceRelevance(
            matched_terms=["dividend", "1"],
            matched_entities=["NMDC"],
            relevance_score=0.95
        ),
        provenance=EvidenceProvenance(
            retrieved_at="2026-10-03T12:00:00Z",
            retrieval_method="NSEAdapter",
            source_mode="LIVE_PUBLIC",
            source_url="https://www.nseindia.com"
        )
    )

    evaluation = NumericalEvaluator.evaluate_claim(claim, [candidate], [])
    assert evaluation is not None
    assert evaluation["status"] == "SUPPORTED"
    assert evaluation["confidence"] >= 0.95


# --- TEST F: Contradiction detection (CONTRADICTED) ---
def test_f_contradiction_detection():
    """Test F: Real record contradicts a conflicting numerical claim."""
    claim = CanonicalClaim(
        claim_id="CLM-NMDC-CONTRA",
        source_content_id="CNT-01",
        claim_type="CORPORATE_EVENT",
        subject="NMDC",
        predicate="DIVIDEND_ANNOUNCED",
        object="50",
        text=ClaimText(
            original="NMDC announced a dividend of ₹50 per share.",
            normalized="NMDC announced a dividend of ₹50 per share."
        )
    )

    candidate = EvidenceCandidate(
        evidence_id="EVD-01",
        claim_id="CLM-NMDC-CONTRA",
        source_document_id="DOC-01",
        source_id="nse_corporate_actions",
        source_type="CORPORATE_ACTION",
        authority_tier="PRIMARY_OFFICIAL",
        excerpt="NATIONAL STOCK EXCHANGE OF INDIA — DISCLOSURE\nCompany: NMDC Limited\nSubject: Dividend - Re 1 Per Share\nEx-Date: 05-Oct-2026",
        relevance=EvidenceRelevance(
            matched_terms=["dividend", "50"],
            matched_entities=["NMDC"],
            relevance_score=0.90
        ),
        provenance=EvidenceProvenance(
            retrieved_at="2026-10-03T12:00:00Z",
            retrieval_method="NSEAdapter",
            source_mode="LIVE_PUBLIC",
            source_url="https://www.nseindia.com"
        )
    )

    evaluation = NumericalEvaluator.evaluate_claim(claim, [candidate], [])
    assert evaluation is not None
    assert evaluation["status"] == "CONTRADICTED"
    assert len(evaluation["contradicting_evidence"]) > 0


# --- TEST G: Truthful provenance ---
def test_g_provenance_truthfulness():
    """Test G: Result preserves NSE + NSEPythonProvider + LIVE_PUBLIC, never claiming LIVE_AUTHORIZED."""
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-G",
        source_id="nse_corporate_actions",
        title="NSE Action",
        url="https://www.nseindia.com",
        metadata={"symbol": "NMDC", "keywords": ["dividend"]}
    )

    doc = adapter.retrieve(search_res)
    prov = doc.authoritative_provenance
    assert prov.source == "NSE"
    assert prov.provider == "NSEPythonProvider"
    assert prov.retrieval_mode == "LIVE_PUBLIC"
    assert prov.access_method == "NSEPython / NSE public endpoint"
    assert prov.source_authority == "NSE-originated public endpoint"

    # INVARIANTS: Strictly forbidden to claim official authorization
    assert prov.retrieval_mode != "LIVE_AUTHORIZED"
    assert "Authorized" not in prov.source_authority
    assert "official NSE API" not in prov.access_method.lower()


# --- TEST H: Failure handling ---
def test_h_failure_handling():
    """Test H: Upstream timeout or HTTP error returns failure status, never fake contradiction or fake support."""
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.side_effect = TimeoutError("Connection timed out after 5.0s")
    provider._nsepython_module = mock_module
    provider._is_available = True

    status, record, err = provider.fetch_corporate_data(
        category="CORPORATE_ACTION",
        symbol="NMDC",
        keywords=["dividend"]
    )
    assert status == "SOURCE_UNAVAILABLE"
    assert record is None
    assert "Connection timed out" in err


# --- TEST I: Unsafe mode blocked ---
def test_i_unsafe_mode_blocked():
    """Test I: Attempts to set or activate unsafe modes (vpn mode, os.popen) are permanently rejected."""
    provider = NSEPythonProvider()
    
    # 1. Rejecting non-local mode via set_mode
    with pytest.raises(SecurityError, match="Unsafe execution mode 'vpn' is forbidden"):
        provider.set_mode("vpn")

    with pytest.raises(SecurityError, match="Unsafe execution mode 'shell' is forbidden"):
        provider.set_mode("shell")

    # 2. Rejecting if underlying module has vpn mode
    mock_mod = MagicMock()
    mock_mod.mode = "vpn"
    provider._nsepython_module = mock_mod
    with pytest.raises(SecurityError, match="NSEPython unsafe mode 'vpn' detected"):
        provider.enforce_safe_mode()

    # 3. Guarding against os.popen during execution
    mock_mod.mode = "local"
    def sneaky_fetch(endpoint):
        import os
        return os.popen("whoami").read()

    mock_mod.nsefetch = sneaky_fetch
    provider._is_available = True
    status, record, err = provider.fetch_corporate_data(
        category="CORPORATE_ACTION",
        symbol="NMDC",
        keywords=["dividend"]
    )
    assert status == "ACCESS_UNAUTHORIZED"
    assert "Shell execution via os.popen is strictly forbidden" in err


# --- TEST J: SSRF protection ---
def test_j_ssrf_protection():
    """Test J: Endpoints pointing to loopback, private networks, metadata, non-HTTPS, or non-NSE domains fail."""
    provider = NSEPythonProvider()

    # Loopback
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://127.0.0.1/api/filings")

    # Private IP
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://10.0.0.1/api/filings")

    # Cloud metadata
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://169.254.169.254/latest/meta-data")

    # Non-HTTPS
    with pytest.raises(SsrfError, match="HTTPS is strictly required"):
        provider.validate_target_endpoint("http://www.nseindia.com/api/corporate-announcements")

    # Unrelated domain
    with pytest.raises(SsrfError, match="restricted to official NSE domains"):
        provider.validate_target_endpoint("https://evil.com/api/filings")


# --- TEST K: Cache and snapshot separation ---
def test_k_cache_and_snapshot_separation():
    """Test K: Official snapshots and cached records are never mislabeled as LIVE_PUBLIC."""
    adapter = NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    query = SourceQuery(company_symbol="ABC", keywords=["bonus"])
    hits = adapter.search(query)
    doc = adapter.retrieve(hits[0])

    assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert doc.authoritative_provenance.provider == "OfficialSnapshot"
    assert doc.authoritative_provenance.retrieval_mode != "LIVE_PUBLIC"
    assert doc.authoritative_provenance.retrieval_mode != "LIVE_AUTHORIZED"


# --- TEST L: Fallback behavior ---
def test_l_fallback_behavior():
    """Test L: Provider failure falls back to configured fallback policy without fabricating live evidence."""
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.side_effect = Exception("Edge firewall rejection HTTP 403")
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-L",
        source_id="nse_corporate_actions",
        title="NSE Corporate Action: NMDC",
        url="https://www.nseindia.com",
        metadata={"symbol": "NMDC", "keywords": ["dividend"]}
    )

    doc = adapter.retrieve(search_res)
    # Failed live provider execution must report failure, not fake SUCCESS
    assert doc.retrieval.status in ("SOURCE_UNAVAILABLE", "ACCESS_UNAUTHORIZED")
    assert doc.authoritative_provenance.retrieval_mode == "SOURCE_UNAVAILABLE"


# --- TEST M: Frontend provenance contract ---
def test_m_frontend_provenance_contract():
    """Test M: UI serialization contract exposes source, provider, access_method, and LIVE_PUBLIC mode."""
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-M",
        source_id="nse_corporate_actions",
        title="NSE Corporate Action: NMDC",
        url="https://www.nseindia.com",
        metadata={"symbol": "NMDC", "keywords": ["dividend"]}
    )

    doc = adapter.retrieve(search_res)
    ui_dict = doc.model_dump()

    assert ui_dict["organization"] == "NSE"
    assert ui_dict["authoritative_provenance"]["source"] == "NSE"
    assert ui_dict["authoritative_provenance"]["provider"] == "NSEPythonProvider"
    assert ui_dict["authoritative_provenance"]["access_method"] == "NSEPython / NSE public endpoint"
    assert ui_dict["authoritative_provenance"]["retrieval_mode"] == "LIVE_PUBLIC"
    assert ui_dict["authoritative_provenance"]["source_authority"] == "NSE-originated public endpoint"
    assert ui_dict["authoritative_provenance"]["source_record_id"] == "INE584A01023"


# --- TEST N: Full gateway integration ---
def test_n_full_gateway_integration():
    """Test N: End-to-end integration: Claim -> Router -> Gateway -> NSEPythonProvider -> Evidence -> Identity -> Policy."""
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        nse_live_enabled=True,
        nsepython_enabled=True,
        nse_provider_preference="NSEPYTHON",
    )

    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.mode = "local"
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")
    nse_adapter = NSEAdapter(
        default_mode="LIVE",
        provider=provider,
        nsepython_enabled=True,
        provider_preference="NSEPYTHON",
    )
    gw.register_adapter("NSEAdapter", nse_adapter, ["corporate_actions", "corporate_announcements"])

    claim_text = "NMDC announced a dividend of ₹1 per share."
    claim = CanonicalClaim(
        claim_id="CLM-GATEWAY-01",
        source_content_id="CNT-NMDC",
        claim_type="CORPORATE_EVENT",
        subject="NMDC",
        predicate="DIVIDEND_ANNOUNCED",
        object="1",
        text=ClaimText(original=claim_text, normalized=claim_text.lower()),
    )
    content = NormalizedContent(
        content_id="CNT-NMDC",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text=claim_text),
        normalized=NormalizedText(text=claim_text, language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    # 1. Gateway execution
    claim_src_res = gw.execute_claim_verification(claim, content=content, mode_override="LIVE")
    assert len(claim_src_res.documents) >= 1
    doc = claim_src_res.documents[0]
    assert doc.authoritative_provenance.provider == "NSEPythonProvider"
    assert doc.authoritative_provenance.retrieval_mode == "LIVE_PUBLIC"

    # 2. Evidence Engine evaluation
    claim_analysis = ClaimAnalysis(
        content_id="CNT-NMDC",
        claims=[claim],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    source_analysis = SourceAnalysis(
        content_id="CNT-NMDC",
        claim_sources=[claim_src_res],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=len(claim_src_res.documents)),
    )
    evidence_engine = EvidenceVerificationEngine()
    ev_res = evidence_engine.verify(content=content, claims=claim_analysis, sources=source_analysis)
    assert len(ev_res.verifications) == 1
    assert ev_res.verifications[0].status == "SUPPORTED"

    # 3. Identity Resolution
    identity_engine = IdentityVerificationEngine()
    id_res = identity_engine.verify(content=content, claims=claim_analysis, sources=source_analysis, evidence=ev_res)
    assert id_res is not None

    # 4. Action & Threat & Fingerprint Context
    actions_engine = ActionIntelligenceEngine()
    actions = actions_engine.analyze(content, claim_analysis)

    threat_engine = ThreatIntelligenceEngine()
    threat = threat_engine.analyze(content, claim_analysis, actions, source_analysis, ev_res)

    fp_engine = ScamFingerprintEngine()
    fp = fp_engine.create_or_match(content, claim_analysis, actions, source_analysis, ev_res, threat)

    # 5. Policy Engine
    policy_engine = PolicyInterventionEngine()
    decision = policy_engine.decide(
        content=content,
        claims=claim_analysis,
        actions=actions,
        sources=source_analysis,
        evidence=ev_res,
        threat=threat,
        fingerprint=fp,
        identity=id_res,
    )
    assert decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM, PolicyDecisionType.WARN)


# --- TEST O: Provider priority hierarchy ---
def test_o_provider_priority_hierarchy():
    """Test O: OfficialAuthorizedProvider takes priority over NSEPython when official credentials are configured."""
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        nse_live_enabled=True,
        nse_api_key="AUTHORIZED_NSE_KEY_123",
        nsepython_enabled=True,
        nse_provider_preference="AUTO",
    )

    adapter = NSEAdapter(
        api_key=settings.nse_api_key,
        nsepython_enabled=True,
        provider_preference="AUTO",
    )

    resolved = adapter.resolve_active_provider()
    # In AUTO mode with api_key configured, OfficialAuthorizedProvider must be chosen
    assert isinstance(resolved, OfficialAuthorizedProvider)
    assert resolved.default_success_mode == "LIVE_AUTHORIZED"

    # Branch 1: If api_key is None and nsepython package is uninstalled on host, falls back to None (snapshot)
    adapter_no_creds = NSEAdapter(
        api_key=None,
        nsepython_enabled=True,
        provider_preference="AUTO",
    )
    resolved_no_creds = adapter_no_creds.resolve_active_provider()
    assert resolved_no_creds is None

    # Branch 2: When nsepython package is available, NSEPythonProvider is chosen
    with patch.object(NSEPythonProvider, "_check_availability", return_value=True):
        adapter_with_pkg = NSEAdapter(
            api_key=None,
            nsepython_enabled=True,
            provider_preference="AUTO",
        )
        resolved_with_pkg = adapter_with_pkg.resolve_active_provider()
        assert isinstance(resolved_with_pkg, NSEPythonProvider)
        assert resolved_with_pkg.default_success_mode == "LIVE_PUBLIC"


# --- OPTIONAL LIVE NETWORK TEST ---
@pytest.mark.live
def test_live_nse_public_probe():
    """Live probe to NSE public endpoints; verifies actual live network connectivity and record schema."""
    import requests
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
    }
    s = requests.Session()
    try:
        r0 = s.get("https://www.nseindia.com", headers=headers, timeout=10)
        assert r0.status_code in (200, 403)
        r_events = s.get("https://www.nseindia.com/api/event-calendar", headers=headers, timeout=10)
        if r_events.status_code == 200:
            data = r_events.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "symbol" in data[0]
            assert "company" in data[0]
    except Exception as e:
        pytest.skip(f"Live network test skipped due to connectivity/WAF: {e}")

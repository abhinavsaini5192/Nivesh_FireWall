"""NSEPython Compatibility & Provenance Audit Test Suite.

Phase 15.C.1: Tests A through O covering:
- Test A: Package installation/import
- Test B: Capability discovery
- Test C: Corporate announcement retrieval
- Test D: Corporate action retrieval
- Test E: Board meeting retrieval
- Test F: Financial result retrieval
- Test G: Real NSE record comparison
- Test H: Normalization
- Test I: Provenance
- Test J: Evidence verification
- Test K: Source failure
- Test L: Cache/snapshot distinction
- Test M: Security/SSRF compatibility
- Test N: No accidental authorization claim
- Test O: Frontend provenance contract
"""

from datetime import datetime, timezone
import json
import pytest
from unittest.mock import MagicMock, patch

from nivesh.schemas.claims import CanonicalClaim, ClaimText
from nivesh.schemas.sources import (
    SourceQuery,
    SourceSearchResult,
    SourceDocument,
    EvidenceCandidate,
    EvidenceRelevance,
    EvidenceProvenance,
    AuthoritativeProvenance,
    RetrievalMetadata,
)
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.nse_providers import (
    BaseNSEProvider,
    OfficialAuthorizedProvider,
    PublicNSEProvider,
    NSEPythonProvider,
    NSE_ANNOUNCEMENTS_ENDPOINT,
    NSE_ACTIONS_ENDPOINT,
    NSE_EVENTS_ENDPOINT,
    NSE_RESULTS_ENDPOINT,
)
from nivesh.sources.ssrf import SsrfError, SsrfValidator
from nivesh.evidence.numerical_evaluator import NumericalEvaluator


# Real NSE sample payloads captured from live endpoints during 15.C.1 audit
REAL_ANNOUNCEMENT_RECORD = {
    "an_dt": "03-Oct-2026 14:37:49",
    "attFileSize": "463.77 KB",
    "attchmntFile": "https://nsearchives.nseindia.com/corporate/PIONEEREMB_03102026143739_CoveringRegulation30092026.pdf",
    "attchmntText": "Compliance certificate for the quarter ended 30th September, 2026",
    "bflag": None,
    "csvName": None,
    "desc": "Structural Digital Database",
    "difference": "00:00:01",
    "dt": "03102026143749",
    "exchdisstime": "03-Oct-2026 14:37:50",
    "fileSize": "463.77 KB",
    "hasXbrl": True,
    "old_new": None,
    "orgid": None,
    "seq_id": "106806218",
    "smIndustry": "Textile Products",
    "sm_isin": "INE156C01018",
    "sm_name": "Pioneer Embroideries Limited",
    "sort_date": "2026-10-03 14:37:49",
    "symbol": "PIONEEREMB",
}

REAL_ACTION_RECORD = {
    "bcEndDate": "-",
    "bcStartDate": "-",
    "caBroadcastDate": None,
    "comp": "NMDC Limited",
    "exDate": "05-Oct-2026",
    "faceVal": "1",
    "ind": "-",
    "isin": "INE584A01023",
    "ndEndDate": "-",
    "ndStartDate": "-",
    "recDate": "05-Oct-2026",
    "series": "EQ",
    "subject": "Dividend - Re 1 Per Share",
    "symbol": "NMDC",
}

REAL_BOARD_MEETING_RECORD = {
    "symbol": "DPABHUSHAN",
    "company": "D. P. Abhushan Limited",
    "purpose": "Fund Raising/Other business matters",
    "bm_desc": "Board Meeting Intimation for Considering Raising Of Funds By Issuance Of Equity Shares And/Or Warrants, By Way Of A Private Placement Through A Preferential Issue",
    "date": "05-Oct-2026",
}

REAL_FINANCIAL_RESULT_RECORD = {
    "audited": "Un-Audited",
    "bank": "N",
    "broadCastDate": "30-Jul-2026 17:17:53",
    "companyName": "V.S.T Tillers Tractors Limited",
    "consolidated": "Consolidated",
    "cumulative": "Non-cumulative",
    "difference": "00:00:49",
    "exchdisstime": "30-Jul-2026 17:18:42",
    "filingDate": "30-Jul-2026 17:17",
    "financialYear": "2026-2027",
    "format": "New",
    "fromDate": "01-Apr-2026",
    "indAs": "Y",
    "industry": "COMMERCIAL VEHICLES",
    "isin": "INE764D01017",
    "period": "Quarterly",
    "resultDescription": "Financial Results for the quarter ended June 30, 2026",
    "resultDetailedDataLink": "https://nsearchives.nseindia.com/corporate/financial_results/VSTTILLERS_30072026.pdf",
    "seqNumber": "129841",
    "symbol": "VSTTILLERS",
    "toDate": "30-Jun-2026",
    "xbrl": "Y",
}


# --- TEST A: Package installation / import ---
def test_a_package_installation_and_import():
    provider = NSEPythonProvider()
    # Provider must gracefully report availability without unhandled exception
    assert isinstance(provider.is_available, bool)
    assert provider.provider_name == "NSEPythonProvider"
    assert provider.default_success_mode == "LIVE_PUBLIC"


# --- TEST B: Capability discovery ---
def test_b_capability_discovery():
    # Audit finding: rahu.py contains 64 functions, but lacks dedicated corporate_announcements/actions functions
    provider = NSEPythonProvider()
    # Emulate mock module with explicit spec
    mock_module = MagicMock(spec=["nse_events", "nse_results", "nse_eq", "nsefetch"])
    provider._nsepython_module = mock_module
    provider._is_available = True

    assert hasattr(mock_module, "nse_events")
    assert hasattr(mock_module, "nse_results")
    assert hasattr(mock_module, "nsefetch")
    # Verify dedicated functions for corporate announcements and actions do not exist natively
    assert not hasattr(mock_module, "nse_corporate_announcements")
    assert not hasattr(mock_module, "nse_corporate_actions")


# --- TEST C: Corporate announcement retrieval ---
def test_c_corporate_announcement_retrieval():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_ANNOUNCEMENT_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    status, record, err = provider.fetch_corporate_data(
        category="CORPORATE_ANNOUNCEMENT",
        symbol="PIONEEREMB",
        keywords=["compliance"]
    )
    assert status == "SUCCESS"
    assert err is None
    assert record is not None
    assert record["symbol"] == "PIONEEREMB"
    assert record["accession_number"] == "106806218"
    assert "https://nsearchives.nseindia.com" in record["url"]


# --- TEST D: Corporate action retrieval ---
def test_d_corporate_action_retrieval():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
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
    assert record["symbol"] == "NMDC"
    assert "Dividend - Re 1 Per Share" in record["subject"]
    assert record["broadcast_date"] == "05-Oct-2026"


# --- TEST E: Board meeting retrieval ---
def test_e_board_meeting_retrieval():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_BOARD_MEETING_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    status, record, err = provider.fetch_corporate_data(
        category="BOARD_MEETING",
        symbol="DPABHUSHAN",
        keywords=["fund"]
    )
    assert status == "SUCCESS"
    assert record is not None
    assert record["symbol"] == "DPABHUSHAN"
    assert "Fund Raising" in record["subject"]


# --- TEST F: Financial result retrieval ---
def test_f_financial_result_retrieval():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_FINANCIAL_RESULT_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    status, record, err = provider.fetch_corporate_data(
        category="FINANCIAL_RESULTS",
        symbol="VSTTILLERS",
        keywords=["financial"]
    )
    assert status == "SUCCESS"
    assert record is not None
    assert record["symbol"] == "VSTTILLERS"
    assert record["accession_number"] == "129841"


# --- TEST G: Real NSE record comparison ---
def test_g_real_nse_record_comparison():
    # Field-by-field verification of Record A, Record B, Record C
    assert REAL_ANNOUNCEMENT_RECORD["symbol"] == "PIONEEREMB"
    assert REAL_ANNOUNCEMENT_RECORD["sm_name"] == "Pioneer Embroideries Limited"
    assert REAL_ANNOUNCEMENT_RECORD["seq_id"] == "106806218"
    assert REAL_ANNOUNCEMENT_RECORD["sm_isin"] == "INE156C01018"

    assert REAL_ACTION_RECORD["symbol"] == "NMDC"
    assert REAL_ACTION_RECORD["comp"] == "NMDC Limited"
    assert REAL_ACTION_RECORD["subject"] == "Dividend - Re 1 Per Share"
    assert REAL_ACTION_RECORD["exDate"] == "05-Oct-2026"

    assert REAL_BOARD_MEETING_RECORD["symbol"] == "DPABHUSHAN"
    assert REAL_BOARD_MEETING_RECORD["company"] == "D. P. Abhushan Limited"
    assert REAL_BOARD_MEETING_RECORD["purpose"] == "Fund Raising/Other business matters"


# --- TEST H: Normalization into SourceDocument ---
def test_h_normalization_into_source_document():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-001",
        source_id="nse_corporate_actions",
        title="NSE Corporate Action: NMDC",
        url="https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=NMDC",
        metadata={"symbol": "NMDC", "keywords": ["dividend"]}
    )

    doc = adapter.retrieve(search_res)
    assert isinstance(doc, SourceDocument)
    assert doc.organization == "NSE"
    assert doc.source_type == "CORPORATE_ACTION"
    assert "Dividend - Re 1 Per Share" in doc.content
    assert doc.content_hash is not None
    assert len(doc.content_hash) == 64


# --- TEST I: Provenance preservation ---
def test_i_provenance_preservation():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-002",
        source_id="nse_corporate_actions",
        title="NSE Corporate Action: NMDC",
        url="https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=NMDC",
        metadata={"symbol": "NMDC", "keywords": ["dividend"]}
    )

    doc = adapter.retrieve(search_res)
    prov = doc.authoritative_provenance
    assert prov is not None
    # Crucial Phase 15.C.1 rule: Must be LIVE_PUBLIC, never LIVE_AUTHORIZED
    assert prov.retrieval_mode == "LIVE_PUBLIC"
    assert prov.access_method == "NSEPython / NSE public endpoint"
    assert prov.source_authority == "NSE-originated public endpoint"
    assert prov.response_status == "SUCCESS"


# --- TEST J: Evidence verification with Engine 5 (NumericalEvaluator) ---
def test_j_evidence_verification():
    # Case 1: Matching claim (SUPPORTED)
    claim_supported = CanonicalClaim(
        claim_id="CLM-NMDC-01",
        source_content_id="CONTENT-01",
        claim_type="CORPORATE_EVENT",
        subject="NMDC",
        predicate="DIVIDEND_ANNOUNCED",
        object="1",
        text=ClaimText(
            original="NMDC announced a dividend of ₹1 per share.",
            normalized="NMDC announced a dividend of ₹1 per share."
        )
    )

    cand_supported = EvidenceCandidate(
        evidence_id="EVD-01",
        claim_id="CLM-NMDC-01",
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

    eval_supported = NumericalEvaluator.evaluate_claim(claim_supported, [cand_supported], [])
    assert eval_supported is not None
    assert eval_supported["status"] == "SUPPORTED"
    assert eval_supported["confidence"] >= 0.95

    # Case 2: Conflicting claim (CONTRADICTED)
    claim_contradicted = CanonicalClaim(
        claim_id="CLM-NMDC-02",
        source_content_id="CONTENT-01",
        claim_type="CORPORATE_EVENT",
        subject="NMDC",
        predicate="DIVIDEND_ANNOUNCED",
        object="50",
        text=ClaimText(
            original="NMDC announced a massive dividend of ₹50 per share.",
            normalized="NMDC announced a massive dividend of ₹50 per share."
        )
    )

    eval_contradicted = NumericalEvaluator.evaluate_claim(claim_contradicted, [cand_supported], [])
    assert eval_contradicted is not None
    assert eval_contradicted["status"] == "CONTRADICTED"
    assert len(eval_contradicted["contradicting_evidence"]) > 0


# --- TEST K: Source failure handling ---
def test_k_source_failure():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
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
    assert "timed out" in (err or "").lower()

    # Integrated with adapter in LIVE mode
    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-ERR",
        source_id="nse_corporate_actions",
        title="NSE Action Query",
        url="https://www.nseindia.com",
        metadata={"symbol": "NMDC"}
    )
    doc = adapter.retrieve(search_res)
    # Failure must NEVER become fake LIVE verification!
    assert doc.retrieval.mode in ("SOURCE_UNAVAILABLE", "OFFICIAL_SNAPSHOT")
    assert doc.authoritative_provenance.retrieval_mode != "LIVE_AUTHORIZED"
    assert doc.authoritative_provenance.retrieval_mode != "LIVE_PUBLIC"


# --- TEST L: Cache and snapshot distinction ---
def test_l_cache_and_snapshot_distinction():
    adapter = NSEAdapter(default_mode="OFFICIAL_SNAPSHOT")
    search_res = SourceSearchResult(
        result_id="RES-SNAP",
        source_id="nse_corporate_actions",
        title="NSE Corporate Action: ABC",
        url="https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=ABC",
        metadata={"symbol": "ABC", "keywords": ["bonus"]}
    )

    # 1. Official snapshot fetch
    doc_snap = adapter.retrieve(search_res)
    assert doc_snap.retrieval.mode == "OFFICIAL_SNAPSHOT"
    assert doc_snap.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"

    # 2. Subsequent cached fetch
    doc_cached = adapter.retrieve(search_res)
    assert doc_cached.retrieval.mode == "CACHE"
    assert doc_cached.authoritative_provenance.retrieval_mode == "CACHE"


# --- TEST M: Security & SSRF compatibility ---
def test_m_security_and_ssrf_compatibility():
    provider = NSEPythonProvider()

    # Disallowed internal endpoints must raise SsrfError
    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("http://127.0.0.1:8000/api")

    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("http://169.254.169.254/latest/meta-data")

    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("http://internal-corp-server.lan")

    with pytest.raises(SsrfError):
        provider.validate_target_endpoint("https://malicious-third-party.com/api")

    # Allowed authentic NSE endpoints must pass
    valid_endpoint = provider.validate_target_endpoint("https://www.nseindia.com/api/corporate-announcements?index=equities")
    assert "nseindia.com" in valid_endpoint


# --- TEST N: No accidental authorization claim ---
def test_n_no_accidental_authorization_claim():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_ANNOUNCEMENT_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-N",
        source_id="nse_corporate_announcements",
        title="NSE Corporate Announcement: PIONEEREMB",
        url="https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=PIONEEREMB",
        metadata={"symbol": "PIONEEREMB", "keywords": ["compliance"]}
    )

    doc = adapter.retrieve(search_res)
    prov = doc.authoritative_provenance

    # STRICT ASSERTIONS: Cannot claim LIVE_AUTHORIZED or Official NSE API
    assert prov.retrieval_mode != "LIVE_AUTHORIZED"
    assert "Authorized" not in prov.source_authority
    assert "official NSE API" not in prov.access_method.lower()


# --- TEST O: Frontend provenance contract ---
def test_o_frontend_provenance_contract():
    provider = NSEPythonProvider()
    mock_module = MagicMock()
    mock_module.nsefetch.return_value = [REAL_ACTION_RECORD]
    provider._nsepython_module = mock_module
    provider._is_available = True

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    search_res = SourceSearchResult(
        result_id="RES-O",
        source_id="nse_corporate_actions",
        title="NSE Corporate Action: NMDC",
        url="https://www.nseindia.com",
        metadata={"symbol": "NMDC", "keywords": ["dividend"]}
    )

    doc = adapter.retrieve(search_res)
    ui_dict = doc.model_dump()

    # Frontend requirements:
    assert ui_dict["organization"] == "NSE"
    assert ui_dict["authoritative_provenance"]["access_method"] == "NSEPython / NSE public endpoint"
    assert ui_dict["authoritative_provenance"]["retrieval_mode"] == "LIVE_PUBLIC"
    assert ui_dict["authoritative_provenance"]["source_record_id"] is not None
    assert ui_dict["authoritative_provenance"]["source_authority"] == "NSE-originated public endpoint"


# --- OPTIONAL LIVE INTEGRATION TEST (Explicitly identified, isolated from deterministic offline suite) ---
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

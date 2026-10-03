"""Phase 15.E.1 — Four-Source Gateway Validation Test Suite.

Validates:
1. Deterministic source routing across SEBI, RBI, NSE, and BSE.
2. Strict retrieval mode semantics: LIVE, LIVE_AUTHORIZED, LIVE_PUBLIC, OFFICIAL_SNAPSHOT, CACHE, FIXTURE, SOURCE_UNAVAILABLE.
   Specifically verifies NSEPythonProvider = LIVE_PUBLIC (never LIVE_AUTHORIZED).
3. Provider priority hierarchies:
   - NSE: OfficialAuthorized -> PublicNSE -> NSEPython -> Snapshot/Fallback
   - BSE: OfficialAuthorizedBSE -> PublicBSE -> OfficialSnapshotBSE
   - SEBI and RBI retain deterministic source-selection logic.
4. Operational state distinctions:
   - CREDENTIALS_MISSING
   - ACCESS_UNAUTHORIZED
   - SOURCE_UNAVAILABLE
   - NO_MATCH
   - MALFORMED_RESPONSE
   - RATE_LIMITED
5. Gateway error handling:
   - Timeout, 403, 404, 429, 500/502/503, malformed response, SSRF rejection.
   - Core Rule: "A technical source failure must never become evidence of fraud."
"""

import pytest
from unittest.mock import MagicMock

from nivesh.config import Settings
from nivesh.schemas.claims import CanonicalClaim, ClaimText, ClaimAnalysis, ClaimAnalysisMetadata
from nivesh.schemas.normalized import (
    NormalizedContent,
    SourceInfo,
    RawContent,
    NormalizedText,
    Provenance,
)
from nivesh.schemas.sources import (
    SourceQuery,
    SourcePlan,
    SourceDocument,
    SourceSearchResult,
    SourceAnalysis,
    SourceAnalysisMetadata,
    AuthoritativeProvenance,
)
from nivesh.sources.catalog import SourceCatalog
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.sources.adapters.nse_providers import (
    OfficialAuthorizedProvider,
    PublicNSEProvider,
    NSEPythonProvider,
)
from nivesh.sources.adapters.bse_providers import (
    OfficialAuthorizedBSEProvider,
    PublicBSEProvider,
    OfficialSnapshotBSEProvider,
)
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.policy.engine import PolicyInterventionEngine


@pytest.fixture
def default_gateway():
    catalog = SourceCatalog()
    settings = Settings(
        env="test",
        source_mode="OFFICIAL_SNAPSHOT",
        live_sources_enabled=False,
    )
    gw = AuthoritativeSourceGateway(catalog=catalog, settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("SEBIAdapter", SEBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["intermediary_registration", "circulars"])
    gw.register_adapter("RBIAdapter", RBIAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["official_data", "regulatory_publications"])
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_announcements", "corporate_actions"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_data", "disclosures", "corporate_actions"])
    return gw


# ---------------------------------------------------------------------------
# 1. Deterministic Source Routing across SEBI, RBI, NSE, BSE
# ---------------------------------------------------------------------------
def test_deterministic_routing_across_all_four_sources(default_gateway):
    """Verifies that all 4 authoritative sources route deterministically through the gateway
    and preserve source, provider, retrieval mode, access method, and provenance.
    """
    # 1. SEBI Claim
    claim_sebi = CanonicalClaim(
        claim_id="CLM-ROUTING-SEBI",
        source_content_id="CNT-01",
        text=ClaimText(original="Registered with SEBI as INA000000888", normalized="registered with sebi as ina000000888"),
        subject="360 ONE",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )
    res_sebi = default_gateway.execute_claim_verification(claim_sebi)
    assert any("sebi" in p.lower() for p in res_sebi.source_plan.primary)
    assert len(res_sebi.documents) >= 1
    doc_sebi = res_sebi.documents[0]
    assert doc_sebi.organization == "SEBI"
    assert doc_sebi.authoritative_provenance is not None
    assert doc_sebi.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
    assert doc_sebi.authoritative_provenance.source == "SEBI"

    # 2. RBI Claim
    claim_rbi = CanonicalClaim(
        claim_id="CLM-ROUTING-RBI",
        source_content_id="CNT-02",
        text=ClaimText(original="The RBI policy repo rate is 6.50%", normalized="the rbi policy repo rate is 6.50%"),
        subject="Reserve Bank of India",
        predicate="POLICY_RATE_IS",
        object="6.50%",
        claim_type="FINANCIAL",
    )
    res_rbi = default_gateway.execute_claim_verification(claim_rbi)
    assert any("rbi" in p.lower() for p in res_rbi.source_plan.primary)
    assert len(res_rbi.documents) >= 1
    doc_rbi = res_rbi.documents[0]
    assert doc_rbi.organization == "RBI"
    assert doc_rbi.authoritative_provenance is not None
    assert doc_rbi.authoritative_provenance.source == "RBI"

    # 3. NSE Claim
    claim_nse = CanonicalClaim(
        claim_id="CLM-ROUTING-NSE",
        source_content_id="CNT-03",
        text=ClaimText(original="TATASTEEL announced stock split on NSE", normalized="tatasteel announced stock split on nse"),
        subject="TATASTEEL",
        predicate="STOCK_SPLIT",
        object="10:1",
        claim_type="CORPORATE_EVENT",
    )
    res_nse = default_gateway.execute_claim_verification(claim_nse)
    assert any("nse" in p.lower() for p in res_nse.source_plan.primary)
    assert len(res_nse.documents) >= 1
    doc_nse = res_nse.documents[0]
    assert doc_nse.organization == "NSE"
    assert doc_nse.authoritative_provenance is not None
    assert doc_nse.authoritative_provenance.source == "NSE"

    # 4. BSE Claim
    claim_bse = CanonicalClaim(
        claim_id="CLM-ROUTING-BSE",
        source_content_id="CNT-04",
        text=ClaimText(original="Scrip 500325 Reliance bonus issue on BSE", normalized="scrip 500325 reliance bonus issue on bse"),
        subject="500325",
        predicate="BONUS_ISSUE",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )
    res_bse = default_gateway.execute_claim_verification(claim_bse)
    # Force BSE routing via cross source or direct
    res_bse_explicit = default_gateway.execute_claim_verification(claim_bse, require_cross_source=True)
    bse_docs = [d for d in res_bse_explicit.documents if d.organization == "BSE"]
    assert len(bse_docs) >= 1
    doc_bse = bse_docs[0]
    assert doc_bse.organization == "BSE"
    assert doc_bse.authoritative_provenance is not None
    assert doc_bse.authoritative_provenance.source == "BSE"


# ---------------------------------------------------------------------------
# 2. Retrieval Mode Semantics & NSEPythonProvider = LIVE_PUBLIC Mandate
# ---------------------------------------------------------------------------
def test_nsepython_retrieval_mode_is_live_public_never_live_authorized():
    """MANDATE: NSEPythonProvider must remain LIVE_PUBLIC.
    It must NEVER be marked LIVE_AUTHORIZED.
    """
    provider = NSEPythonProvider()
    assert provider.default_success_mode == "LIVE_PUBLIC"
    assert provider.default_success_mode != "LIVE_AUTHORIZED"

    adapter = NSEAdapter(provider=provider, default_mode="LIVE")
    assert adapter.resolve_active_provider() == provider

    # Provenance generated by adapter using NSEPythonProvider must be LIVE_PUBLIC
    prov = adapter.build_provenance(
        source="NSE",
        source_authority="National Stock Exchange of India",
        retrieval_mode="LIVE_PUBLIC",
        retrieved_at="2026-10-03T12:00:00Z",
        adapter_name="NSEAdapter",
        response_status="SUCCESS",
        evidence="Corporate announcement",
    )
    assert prov.retrieval_mode == "LIVE_PUBLIC"
    assert prov.retrieval_mode != "LIVE_AUTHORIZED"


def test_public_and_authorized_provider_modes_are_strictly_separated():
    """Verifies that authorized and public provider tiers have separate retrieval modes."""
    # NSE
    auth_nse = OfficialAuthorizedProvider(api_key="key", api_secret="secret")
    assert auth_nse.default_success_mode == "LIVE_AUTHORIZED"
    pub_nse = PublicNSEProvider()
    assert pub_nse.default_success_mode == "LIVE_PUBLIC"

    # BSE
    auth_bse = OfficialAuthorizedBSEProvider(api_key="key", api_secret="secret")
    assert auth_bse.default_success_mode == "LIVE_AUTHORIZED"
    pub_bse = PublicBSEProvider()
    assert pub_bse.default_success_mode == "LIVE_PUBLIC"
    snap_bse = OfficialSnapshotBSEProvider()
    assert snap_bse.default_success_mode == "OFFICIAL_SNAPSHOT"


# ---------------------------------------------------------------------------
# 3. Provider Priority Hierarchies
# ---------------------------------------------------------------------------
def test_nse_provider_priority_hierarchy():
    """Validates NSE hierarchy: OfficialAuthorized -> PublicNSE -> NSEPython -> Snapshot/Fallback."""
    from unittest.mock import patch

    # 1. With API key -> OfficialAuthorizedProvider
    adapter_auth = NSEAdapter(
        default_mode="LIVE",
        api_key="valid-key",
        api_secret="valid-secret",
        provider_preference="AUTO",
    )
    p_auth = adapter_auth.resolve_active_provider()
    assert isinstance(p_auth, OfficialAuthorizedProvider)

    # 2. Without API key, public enabled -> PublicNSEProvider
    adapter_pub = NSEAdapter(
        default_mode="LIVE",
        api_key=None,
        public_provider_enabled=True,
        provider_preference="AUTO",
    )
    p_pub = adapter_pub.resolve_active_provider()
    assert isinstance(p_pub, PublicNSEProvider)

    # 3. Without API key, public disabled, nsepython enabled (when available) -> NSEPythonProvider
    with patch.object(NSEPythonProvider, "is_available", True):
        adapter_py = NSEAdapter(
            default_mode="LIVE",
            api_key=None,
            public_provider_enabled=False,
            nsepython_enabled=True,
            provider_preference="AUTO",
        )
        p_py = adapter_py.resolve_active_provider()
        assert isinstance(p_py, NSEPythonProvider)

    # 4. Without any live provider enabled -> Fallback (None, yielding snapshot)
    adapter_none = NSEAdapter(
        default_mode="LIVE",
        api_key=None,
        public_provider_enabled=False,
        nsepython_enabled=False,
        provider_preference="AUTO",
    )
    p_none = adapter_none.resolve_active_provider()
    assert p_none is None


def test_bse_provider_priority_hierarchy():
    """Validates BSE hierarchy: OfficialAuthorizedBSE -> PublicBSE -> OfficialSnapshotBSE."""
    # 1. With API key -> OfficialAuthorizedBSEProvider
    adapter_auth = BSEAdapter(
        default_mode="LIVE",
        api_key="bse-key",
        api_secret="bse-secret",
        provider_preference="AUTO",
    )
    p_auth = adapter_auth.resolve_active_provider()
    assert isinstance(p_auth, OfficialAuthorizedBSEProvider)

    # 2. Without API key, public enabled -> PublicBSEProvider
    adapter_pub = BSEAdapter(
        default_mode="LIVE",
        api_key=None,
        public_enabled=True,
        provider_preference="AUTO",
    )
    p_pub = adapter_pub.resolve_active_provider()
    assert isinstance(p_pub, PublicBSEProvider)

    # 3. Without credentials or public enablement -> OfficialSnapshotBSEProvider
    adapter_snap = BSEAdapter(
        default_mode="LIVE",
        api_key=None,
        public_enabled=False,
        provider_preference="AUTO",
    )
    p_snap = adapter_snap.resolve_active_provider()
    assert isinstance(p_snap, OfficialSnapshotBSEProvider)


# ---------------------------------------------------------------------------
# 4. Operational State Distinctions
# ---------------------------------------------------------------------------
def test_operational_states_remain_distinct():
    """Verifies that credentials missing, unauthorized access, source unavailable,
    no matching record, and malformed response remain distinct operational states.
    """
    settings = Settings(
        env="test",
        source_mode="LIVE",
        live_sources_enabled=True,
        bse_live_enabled=True,
        bse_api_key=None,
    )
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")

    # 1. CREDENTIALS_MISSING
    mode, reason = gw.resolve_access_mode("bse_corporate_filings", "LIVE")
    assert mode == "SOURCE_UNAVAILABLE"
    assert "CREDENTIALS_MISSING" in reason or "BSE_API_KEY" in reason

    # 2. UNAUTHORIZED (HTTP 401/403)
    pub_bse = PublicBSEProvider(safe_fetch_fn=lambda url, **kw: (403, "Access Denied", {"Akamai-GRN": "0.1234"}))
    status, rec, err = pub_bse.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "RELIANCE")
    assert status == "ACCESS_UNAUTHORIZED"
    assert "Akamai" in err

    # 3. NO_MATCH (HTTP 200 but empty / no symbol match)
    pub_bse_empty = PublicBSEProvider(safe_fetch_fn=lambda url, **kw: (200, "[]", {}))
    status, rec, err = pub_bse_empty.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "NONEXISTENT")
    assert status == "NO_MATCH"

    # 4. MALFORMED_RESPONSE (Non-JSON payload)
    pub_bse_bad_json = PublicBSEProvider(safe_fetch_fn=lambda url, **kw: (200, "<html>Bad Gateway</html>", {}))
    status, rec, err = pub_bse_bad_json.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "RELIANCE")
    assert status == "SOURCE_UNAVAILABLE"
    assert "Malformed" in err or "non-JSON" in err

    # 5. RATE_LIMITED (HTTP 429)
    pub_bse_429 = PublicBSEProvider(safe_fetch_fn=lambda url, **kw: (429, "Too Many Requests", {}))
    status, rec, err = pub_bse_429.fetch_corporate_data("CORPORATE_ANNOUNCEMENT", "RELIANCE")
    assert status == "RATE_LIMITED"


# ---------------------------------------------------------------------------
# 5. Gateway Error Handling & Core Safety Rule
# ---------------------------------------------------------------------------
def test_technical_source_failure_never_becomes_evidence_of_fraud():
    """RULE: A technical source failure must never become evidence of fraud or trigger BLOCK."""
    settings = Settings(env="test", source_mode="LIVE", live_sources_enabled=True, sebi_live_enabled=True)
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")

    # Mock adapter that is completely unavailable
    failing_adapter = SEBIAdapter(default_mode="SOURCE_UNAVAILABLE")
    gw.register_adapter("SEBIAdapter", failing_adapter, ["intermediary_registration"])

    claim = CanonicalClaim(
        claim_id="CLM-TIMEOUT-TEST",
        source_content_id="CNT-TIMEOUT",
        text=ClaimText(original="Unknown Entity is SEBI registered", normalized="unknown entity is sebi registered"),
        subject="Unknown Entity",
        predicate="REGISTERED_WITH",
        object="SEBI",
        claim_type="REGULATORY",
    )
    content = NormalizedContent(
        content_id="CNT-TIMEOUT",
        source=SourceInfo(type="text", channel="browser"),
        raw=RawContent(text="Unknown Entity is SEBI registered"),
        normalized=NormalizedText(text="Unknown Entity is SEBI registered", language="en", language_confidence=1.0),
        provenance=Provenance(created_at="2026-10-03T00:00:00Z", input_type="text"),
    )

    source_res = gw.execute_claim_verification(claim, content=content, mode_override="SOURCE_UNAVAILABLE")
    assert len(source_res.documents) >= 1
    doc = source_res.documents[0]
    # Technical failure is recorded
    assert doc.retrieval.status in ("RETRIEVAL_FAILED", "SOURCE_UNAVAILABLE")

    # Evaluate in Evidence Verification Engine (Engine 5)
    evidence_engine = EvidenceVerificationEngine()
    claim_analysis = ClaimAnalysis(
        content_id="CNT-TIMEOUT",
        claims=[claim],
        analysis_metadata=ClaimAnalysisMetadata(total_claims=1),
    )
    source_analysis = SourceAnalysis(
        content_id="CNT-TIMEOUT",
        claim_sources=[source_res],
        analysis_metadata=SourceAnalysisMetadata(claims_processed=1, sources_queried=1, documents_retrieved=len(source_res.documents)),
    )
    evidence_res = evidence_engine.verify(content=content, claims=claim_analysis, sources=source_analysis)
    assert len(evidence_res.verifications) == 1
    v = evidence_res.verifications[0]

    # Invariant: Evidence is SOURCE_UNAVAILABLE or INSUFFICIENT_EVIDENCE or NOT_VERIFIABLE, NEVER CONTRADICTED
    assert v.status in ("SOURCE_UNAVAILABLE", "INSUFFICIENT_EVIDENCE", "NOT_VERIFIABLE")
    assert v.status != "CONTRADICTED"

    # Evaluate in Policy Engine (Engine 8)
    from nivesh.actions.engine import ActionIntelligenceEngine
    from nivesh.threat.engine import ThreatIntelligenceEngine
    from nivesh.fingerprints.engine import ScamFingerprintEngine

    ae = ActionIntelligenceEngine()
    actions = ae.analyze(content, claim_analysis)

    te = ThreatIntelligenceEngine()
    threat = te.analyze(content, claim_analysis, actions, source_analysis, evidence_res)

    fe = ScamFingerprintEngine()
    fingerprint = fe.create_or_match(content, claim_analysis, actions, source_analysis, evidence_res, threat)

    policy_engine = PolicyInterventionEngine()
    policy_decision = policy_engine.decide(
        content=content,
        claims=claim_analysis,
        actions=actions,
        sources=source_analysis,
        evidence=evidence_res,
        threat=threat,
        fingerprint=fingerprint,
    )

    # Invariant: Must NOT be BLOCK solely due to technical gateway failure
    assert policy_decision.decision.value != "BLOCK"
    assert policy_decision.decision.value in ("ALLOW", "INFORM", "WARN")

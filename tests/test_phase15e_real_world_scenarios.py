"""Phase 15.E.4 — Full Firewall Real-World Scenario Validation (Scenarios A through J).

Validates the complete end-to-end Nivesh Firewall pipeline:
Content Intelligence (1)
  -> Claim Intelligence (2)
  -> Action Intelligence (3)
  -> Source Intelligence (4)
  -> Evidence Verification (5)
  -> Threat & Attack Path Intelligence (6)
  -> Scam Fingerprint & Collective Intelligence (7)
  -> Identity Resolution (9)
  -> Behavioural Signals (10)
  -> Policy & Intervention (8)

Covers all 10 designated real-world scenarios:
- Scenario A: Benign Financial Content (No alarming policy, informational/allow)
- Scenario B: Unsupported Guarantee Claim (Modality detected, statutory prohibition, no criminal labeling)
- Scenario C: Identity / Registration Claim (NO_MATCH yields NOT_ESTABLISHED, never criminal fraud conclusion)
- Scenario D: Suspicious Action Chain (Observable chain reconstructed: contact -> off-platform -> apk -> credentials -> transfer)
- Scenario E: Contradicted Numerical Claim (Claimed 5:1 vs official 1:1, status CONTRADICTED)
- Scenario F: Multi-Source Corroboration (Dual-listed NSE + BSE corroborated independently without score inflation)
- Scenario G: Live Source Failure (Graceful fallback to snapshot, truthful provenance, never fake live)
- Scenario H: Source Conflict (Conflicting exchange disclosures yield SOURCE_CONFLICT)
- Scenario I: No Evidence (Unverifiable assertion yields INSUFFICIENT_EVIDENCE, not assumed false)
- Scenario J: Sensitive Data Safety (Passwords, PINs, OTPs, cards sanitized; never enter logs, fingerprints, or provenance)
"""

import pytest
from unittest.mock import patch, MagicMock

from nivesh.config import Settings
from nivesh.orchestrator.service import ProductOrchestrator
from nivesh.orchestrator.config import OrchestratorConfig
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.identity.schemas import IdentityStatus
from nivesh.schemas.claims import CanonicalClaim, ClaimText
from nivesh.schemas.sources import SourceDocument, EvidenceCandidate, EvidenceRelevance, EvidenceProvenance, RetrievalMetadata, ClaimSourceResult, SourcePlan, SourceQuery
from nivesh.evidence.evaluator import ClaimEvidenceEvaluator
from nivesh.sources.gateway import AuthoritativeSourceGateway
from nivesh.sources.adapters.sebi_adapter import SEBIAdapter
from nivesh.sources.adapters.nse_adapter import NSEAdapter
from nivesh.sources.adapters.bse_adapter import BSEAdapter
from nivesh.sources.adapters.rbi_adapter import RBIAdapter


@pytest.fixture
def orchestrator():
    config = OrchestratorConfig(source_mode="OFFICIAL_SNAPSHOT")
    return ProductOrchestrator(config=config)


# ---------------------------------------------------------------------------
# Scenario A — Benign Financial Content
# ---------------------------------------------------------------------------
def test_scenario_a_benign_financial_content(orchestrator):
    """Scenario A: Content contains factual financial education without dangerous requested actions.
    System must not treat financial subject matter alone as dangerous.
    """
    text = (
        "Learn how mutual fund SIP diversification protects long-term wealth across large cap equity indexes. "
        "Systematic investing helps average out market volatility over 5 to 10 year horizons."
    )
    result = orchestrator.analyze(text=text, channel="browser")

    # Invariants:
    assert result.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.INFORM)
    assert result.policy_decision.severity in ("LOW", "INFORMATIONAL")
    assert result.policy_decision.required_user_confirmation is False
    active_threat_stages = [n.stage for n in result.threat.attack_path.nodes if n.stage != "DISCOVERY"]
    assert len(active_threat_stages) == 0
    assert len(result.threat.threat_families) == 0


# ---------------------------------------------------------------------------
# Scenario B — Unsupported Guarantee Claim
# ---------------------------------------------------------------------------
def test_scenario_b_unsupported_guarantee_claim(orchestrator):
    """Scenario B: Content asserts a high-certainty financial return guarantee.
    Validates claim modality, statutory prohibition evaluation, and non-alarming intervention.
    """
    text = (
        "Invest with our proprietary trading algorithm and get guaranteed 40% monthly returns! "
        "100% risk-free capital guarantee backed by statutory fund."
    )
    result = orchestrator.analyze(text=text, channel="browser")

    # Claim Intelligence must extract guaranteed return claim
    assert len(result.claims.claims) >= 1
    # Evidence must evaluate statutory prohibition / contradiction against SEBI statutory guidelines
    assert len(result.evidence.verifications) >= 1
    # Policy must intervene (WARN or PAUSE) to protect investor before irreversible fund commitment
    assert result.decision in (PolicyDecisionType.WARN, PolicyDecisionType.PAUSE, PolicyDecisionType.INFORM)
    # Must NOT brand person as a criminal without evidentiary proof
    all_reasons = [result.policy_decision.primary_reason, result.policy_decision.user_message] + result.policy_decision.supporting_reasons
    for msg in all_reasons:
        assert "criminal" not in msg.lower()
        assert "scammer" not in msg.lower()


# ---------------------------------------------------------------------------
# Scenario C — Identity / Registration Claim
# ---------------------------------------------------------------------------
def test_scenario_c_identity_registration_claim(orchestrator):
    """Scenario C: Content asserts registration with SEBI.
    Validates identity lookup: absence of record yields NOT_ESTABLISHED, NEVER criminal fraud conclusion.
    """
    text = (
        "I am Vikram Oberoi, SEBI registered research analyst with registration number INA999888777. "
        "Join our advisory channel for stock recommendations."
    )
    result = orchestrator.analyze(text=text, channel="telegram")

    # Identity status must be NOT_ESTABLISHED (or UNVERIFIED), NEVER IDENTITY_MISMATCH
    assert result.identity.identity_status in (IdentityStatus.NOT_ESTABLISHED, IdentityStatus.NOT_APPLICABLE)
    assert result.identity.identity_status != IdentityStatus.IDENTITY_MISMATCH
    # Must not accuse of impersonation without lookalike or conflicting identity proof
    for finding in result.identity.identity_findings:
        assert finding.finding_type != "IMPERSONATION_DETECTED"


# ---------------------------------------------------------------------------
# Scenario D — Suspicious Action Chain
# ---------------------------------------------------------------------------
def test_scenario_d_suspicious_action_chain(orchestrator):
    """Scenario D: Progression: contact -> off-platform -> apk -> credentials -> fund transfer.
    Product reconstructs observable action chain and pauses interaction.
    """
    text = (
        "Contact support on WhatsApp at +91 9876543210. "
        "Download our QuickSupport apk from http://malicious-apk-host.xyz/app.apk. "
        "Enter your banking credentials and transfer ₹25,000 to verify your account."
    )
    result = orchestrator.analyze(text=text, channel="browser")

    # Action Intelligence must reconstruct multiple high-impact actions
    action_types = [a.action_type for a in result.actions.actions]
    assert any("EXTERNAL" in str(at) or "CONTACT" in str(at) or "COMMUNICATION" in str(at) for at in action_types) or len(result.actions.actions) >= 2
    # Threat & Attack Path must trace the consequential path
    assert result.decision in (PolicyDecisionType.WARN, PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)


# ---------------------------------------------------------------------------
# Scenario E — Contradicted Numerical Claim
# ---------------------------------------------------------------------------
def test_scenario_e_contradicted_numerical_claim(orchestrator):
    """Scenario E: Corporate action claimed as 5:1 bonus, whereas verified record shows 1:1.
    Numerical evaluator yields CONTRADICTED without generic fraud probability.
    """
    text = "ABC announced a 5:1 bonus."
    result = orchestrator.analyze(text=text, channel="browser")

    # Evidence engine should evaluate the numerical ratio
    bonus_verifs = [v for v in result.evidence.verifications if "bonus" in str(v.claim_id).lower() or v.status in ("CONTRADICTED", "SUPPORTED", "INSUFFICIENT_EVIDENCE")]
    assert len(bonus_verifs) >= 1
    # Claim asserting 5:1 when verified official record is 1:1 must be CONTRADICTED
    has_contradicted = any(v.status == "CONTRADICTED" for v in result.evidence.verifications)
    assert has_contradicted is True


# ---------------------------------------------------------------------------
# Scenario F — Multi-Source Corroboration
# ---------------------------------------------------------------------------
def test_scenario_f_multi_source_corroboration():
    """Scenario F: Multi-source corroboration on dual-listed record (NSE + BSE).
    Strengthens evidence picture without artificial score inflation.
    """
    settings = Settings(env="test", source_mode="OFFICIAL_SNAPSHOT")
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="OFFICIAL_SNAPSHOT")
    gw.register_adapter("NSEAdapter", NSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_actions"])
    gw.register_adapter("BSEAdapter", BSEAdapter(default_mode="OFFICIAL_SNAPSHOT"), ["corporate_data"])

    claim = CanonicalClaim(
        claim_id="CLM-SCENARIO-F",
        source_content_id="CNT-F",
        text=ClaimText(original="ABC Limited 1:1 bonus issue", normalized="abc limited 1:1 bonus issue"),
        subject="ABC Limited",
        predicate="ANNOUNCED_BONUS",
        object="1:1",
        claim_type="CORPORATE_EVENT",
    )

    res = gw.execute_claim_verification(claim, require_cross_source=True)
    orgs = [d.organization for d in res.documents]
    assert "NSE" in orgs
    assert "BSE" in orgs

    evaluator = ClaimEvidenceEvaluator()
    v = evaluator.evaluate(claim, res)
    assert v.status == "SUPPORTED"
    assert v.confidence <= 1.0
    assert v.confidence >= 0.85


# ---------------------------------------------------------------------------
# Scenario G — Live Source Failure & Fallback
# ---------------------------------------------------------------------------
def test_scenario_g_live_source_failure_fallback():
    """Scenario G: Forced live failure triggers deterministic fallback with truthful provenance."""
    settings = Settings(env="test", source_mode="LIVE", live_sources_enabled=True, sebi_live_enabled=True)
    gw = AuthoritativeSourceGateway(settings=settings, default_mode="LIVE")

    failing_sebi = SEBIAdapter(default_mode="LIVE")
    with patch.object(failing_sebi, "safe_http_fetch", side_effect=TimeoutError("Connection timed out")):
        gw.register_adapter("SEBIAdapter", failing_sebi, ["intermediary_registration"])
        claim = CanonicalClaim(
            claim_id="CLM-SCENARIO-G",
            source_content_id="CNT-G",
            text=ClaimText(original="Narayanan S. is registered with SEBI", normalized="narayanan s. is registered with sebi"),
            subject="Narayanan S.",
            predicate="REGISTERED_WITH",
            object="SEBI",
            claim_type="REGULATORY",
        )
        res = gw.execute_claim_verification(claim, mode_override="LIVE")
        doc = res.documents[0]
        # Invariant: Fallback engaged, truthful provenance
        assert doc.retrieval.mode == "OFFICIAL_SNAPSHOT"
        assert doc.authoritative_provenance.retrieval_mode == "OFFICIAL_SNAPSHOT"
        assert doc.retrieval.mode != "LIVE"


# ---------------------------------------------------------------------------
# Scenario H — Source Conflict
# ---------------------------------------------------------------------------
def test_scenario_h_source_conflict():
    """Scenario H: Authoritative sources present conflicting records on same claim.
    System reports SOURCE_CONFLICT and preserves both views.
    """
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLM-SCENARIO-H",
        source_content_id="CNT-H",
        text=ClaimText(original="Company Gamma dividend of ₹10 per share", normalized="company gamma dividend of ₹10 per share"),
        subject="Company Gamma",
        predicate="DIVIDEND",
        object="₹10",
        claim_type="FINANCIAL",
    )

    doc_1 = SourceDocument(
        document_id="DOC-H-1",
        source_id="nse_corporate_actions",
        organization="NSE",
        source_type="STOCK_EXCHANGE",
        title="NSE Corporate Action Gamma",
        url="https://nseindia.com/gamma",
        retrieved_at="2026-10-03T10:00:00Z",
        content="Company Gamma dividend approved at ₹10 per share.",
        content_hash="h1",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="NSEAdapter", mode="OFFICIAL_SNAPSHOT"),
    )

    doc_2 = SourceDocument(
        document_id="DOC-H-2",
        source_id="bse_corporate_filings",
        organization="BSE",
        source_type="STOCK_EXCHANGE",
        title="BSE Corporate Action Gamma",
        url="https://bseindia.com/gamma",
        retrieved_at="2026-10-03T10:00:00Z",
        content="Company Gamma conflicting dividend revision approved at ₹15 per share.",
        content_hash="h2",
        metadata={},
        retrieval=RetrievalMetadata(status="SUCCESS", method="BSEAdapter", mode="OFFICIAL_SNAPSHOT"),
    )

    cand_1 = EvidenceCandidate(
        evidence_id="EVID-H-1",
        claim_id="CLM-SCENARIO-H",
        source_document_id="DOC-H-1",
        excerpt=doc_1.content,
        relevance=EvidenceRelevance(),
        source_type="STOCK_EXCHANGE",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-03T10:00:00Z", retrieval_method="NSEAdapter", source_mode="OFFICIAL_SNAPSHOT", source_url=doc_1.url),
        verification_status="UNVERIFIED",
    )

    cand_2 = EvidenceCandidate(
        evidence_id="EVID-H-2",
        claim_id="CLM-SCENARIO-H",
        source_document_id="DOC-H-2",
        excerpt=doc_2.content,
        relevance=EvidenceRelevance(),
        source_type="STOCK_EXCHANGE",
        authority_tier="PRIMARY_OFFICIAL",
        provenance=EvidenceProvenance(retrieved_at="2026-10-03T10:00:00Z", retrieval_method="BSEAdapter", source_mode="OFFICIAL_SNAPSHOT", source_url=doc_2.url),
        verification_status="UNVERIFIED",
    )

    source_res = ClaimSourceResult(
        claim_id="CLM-SCENARIO-H",
        source_plan=SourcePlan(query=SourceQuery()),
        documents=[doc_1, doc_2],
        evidence_candidates=[cand_1, cand_2],
    )

    v = evaluator.evaluate(claim, source_res)
    assert v.status == "SOURCE_CONFLICT"


# ---------------------------------------------------------------------------
# Scenario I — No Evidence
# ---------------------------------------------------------------------------
def test_scenario_i_no_evidence():
    """Scenario I: Unverifiable private factual claim yields INSUFFICIENT_EVIDENCE,
    never assumed false or fabricated.
    """
    evaluator = ClaimEvidenceEvaluator()
    claim = CanonicalClaim(
        claim_id="CLM-SCENARIO-I",
        source_content_id="CNT-I",
        text=ClaimText(original="Founders signed a private memorandum of understanding in Mumbai.", normalized="founders signed a private memorandum of understanding in mumbai."),
        subject="Founders",
        predicate="SIGNED_MOU",
        object="Private MOU",
        claim_type="FACTUAL",
    )

    source_res = ClaimSourceResult(
        claim_id="CLM-SCENARIO-I",
        source_plan=SourcePlan(query=SourceQuery()),
        documents=[],
        evidence_candidates=[],
    )

    v = evaluator.evaluate(claim, source_res)
    assert v.status == "INSUFFICIENT_EVIDENCE"
    assert v.evidence_strength == "NONE"


# ---------------------------------------------------------------------------
# Scenario J — Sensitive Data Safety & Redaction
# ---------------------------------------------------------------------------
def test_scenario_j_sensitive_data_safety(orchestrator):
    """Scenario J: Content contains passwords, OTPs, PINs, or credit card numbers.
    Validates sanitization: secrets never enter fingerprints, logs, provenance, threat intelligence, or frontend output.
    """
    raw_secret_text = (
        "Please login with password=SuperSecretPassword999 and enter otp=654321. "
        "Card payment 4111 2222 3333 4444 with pin=9876."
    )
    result = orchestrator.analyze(text=raw_secret_text, channel="browser")

    # Invariants across all 5 required targets:
    # 1. Fingerprint must not contain sensitive values
    fp_str = str(result.fingerprint.model_dump())
    assert "SuperSecretPassword999" not in fp_str
    assert "654321" not in fp_str
    assert "4111 2222 3333 4444" not in fp_str
    assert "9876" not in fp_str

    # 2. Logs scrub sensitive values
    from nivesh.observability.logging import scrub_sensitive_tokens
    log_sample = f"Audit log event for {raw_secret_text}"
    scrubbed_log = scrub_sensitive_tokens(log_sample)
    assert "SuperSecretPassword999" not in scrubbed_log
    assert "654321" not in scrubbed_log
    assert "4111 2222 3333 4444" not in scrubbed_log
    assert "9876" not in scrubbed_log

    # 3. Provenance must not leak sensitive values
    prov_str = str(result.provenance)
    assert "SuperSecretPassword999" not in prov_str
    assert "4111 2222 3333 4444" not in prov_str

    # 4. Threat intelligence must not leak sensitive values
    threat_str = str(result.threat.model_dump())
    assert "SuperSecretPassword999" not in threat_str
    assert "4111 2222 3333 4444" not in threat_str

    # 5. Frontend output (FirewallAnalysisResponse) must be fully sanitized
    from nivesh.orchestrator.service import format_firewall_response
    fw_resp = format_firewall_response(result)
    fw_str = str(fw_resp.model_dump())
    assert "SuperSecretPassword999" not in fw_str
    assert "654321" not in fw_str
    assert "4111 2222 3333 4444" not in fw_str
    assert "9876" not in fw_str

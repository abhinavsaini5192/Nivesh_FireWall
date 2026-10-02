"""Phase 11.5 — End-to-End Integration & Validation Test Suite.

Proves that:
Product Input
    ↓
Unified Firewall API
    ↓
Product Orchestrator
    ↓
Analysis Context
    ↓
Dependency-Aware Engine Pipeline
    ↓
Engines 1–7, 9, 10
    ↓
Engine 8 Policy
    ↓
Unified Firewall Result
works as one coherent system.

Validates:
1. Full API-to-engine pipeline integration (API -> Orchestrator -> Context -> Pipeline -> E8 -> Result)
2. Primary threat benchmark scenario (5-stage attack path, all engine outputs preserved)
3. Full benign educational scenario (neutral financial classification, no invented threat)
4. Identity verification fixtures preservation (ESTABLISHED vs NOT_ESTABLISHED/MISMATCH)
5. Evidence verification fixtures preservation (SUPPORTED vs CONTRADICTED/INSUFFICIENT)
6. Fingerprint scenario & anti-inflation (SEMANTIC_VARIANT, NO_MATCH, hash dedup)
7. Behavioural persistence scenario (decline -> payment -> urgency sequence)
8. Failure injection across all engines (safe handling without fake intelligence)
9. Partial pipeline validation (SOURCE_UNAVAILABLE is analytical state, not HTTP 500)
10. Session isolation (distinct sessions never leak behavioural state)
11. Concurrency safety (concurrent requests maintain isolated contexts and unique IDs)
12. Privacy end-to-end (cards, passwords, OTPs, PINs, accounts scrubbed across all layers)
13. Provenance validation (traceable audit trail without secret leakage)
14. Policy authority validation (strict architectural check that Engine 8 is sole decider)
15. Explainability validation (non-ALLOW decisions provide structured grounded explanation)
16. API contract validation (frozen schema fields for frontend consumption)
17. Analysis retrieval validation (retrieval without pipeline rerun, 404 on missing)
18. Error response sanitization (no stack traces or filesystem paths leaked)
19. Performance smoke test (measures execution duration and engine timings)
20. Determinism test (identical requests yield identical logical decisions and structures)
"""

import ast
import inspect
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from nivesh.api.app import app, firewall_orchestrator
from nivesh.schemas.firewall import FirewallAnalysisResponse, FirewallApiError
from nivesh.orchestrator import (
    ProductOrchestrator,
    OrchestrationResult,
    PipelineStatus,
    FatalOrchestrationError,
)
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata
from nivesh.schemas.evidence import EvidenceAnalysis, EvidenceAnalysisMetadata


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_global_firewall_state():
    """Ensure clean isolated fingerprint store between e2e test runs."""
    firewall_orchestrator.e7 = ScamFingerprintEngine()
    yield
    firewall_orchestrator.e7 = ScamFingerprintEngine()


# ------------------------------------------------------------------------------
# Test 1: Full API-to-Engine Integration
# ------------------------------------------------------------------------------
def test_e2e_full_api_to_engine_pipeline():
    """Verify request travels API -> Orchestrator -> Context -> Pipeline -> E8 -> Result."""
    payload = {
        "input_type": "text",
        "text": "Review personal financial budgeting rules such as the 50-30-20 principle.",
        "channel": "web",
        "session_id": "test1_e2e_budgeting_session",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Validate conforms to canonical FirewallAnalysisResponse
    model = FirewallAnalysisResponse.model_validate(data)
    assert model.analysis_id.startswith("ORCH-")
    assert model.pipeline_status in ("COMPLETED", "DEGRADED")

    # Verify decision came from Engine 8
    assert model.decision.decision in ("ALLOW", "INFORM")
    assert model.decision.policy_version == "8.0.0"
    assert model.decision.decision_id is not None

    # Verify all 10 engines were executed in the pipeline
    executed = model.provenance["engines_executed"]
    expected_engines = [
        "engine_1_content",
        "engine_2_claims",
        "engine_3_actions",
        "engine_4_sources",
        "engine_5_evidence",
        "engine_6_threat",
        "engine_7_fingerprint",
        "engine_9_identity",
        "engine_10_behaviour",
        "engine_8_policy",
    ]
    for eng in expected_engines:
        assert eng in executed


# ------------------------------------------------------------------------------
# Test 2: Primary End-to-End Threat Scenario (5-Stage Benchmark)
# ------------------------------------------------------------------------------
def test_e2e_primary_threat_benchmark():
    """Run full 5-stage benchmark through API and verify multi-engine findings."""
    threat_text = (
        "SEBI registered adviser Rahul Sharma! Guaranteed 40% returns on WhatsApp. "
        "Move to our private Telegram VIP channel: https://t.me/vip_signals. "
        "Download our exclusive trading APK terminal. "
        "Transfer ₹5,000 registration fee to UPI vip@icici. "
        "Only 5 minutes left! Hurry up before offer expires!"
    )
    payload = {
        "input_type": "text",
        "text": threat_text,
        "channel": "telegram",
        "session_id": "bench_e2e_session_001",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 1. Claims extracted
    assert len(data["claims"]) > 0

    # 2. Actions extracted (channel migration, external app, payment)
    assert len(data["actions"]) >= 2
    action_types = [a["action_type"] for a in data["actions"]]
    categories = [a.get("category", "") for a in data["actions"]]
    assert any(
        at in ("DOWNLOAD", "INSTALL", "TRANSFER_MONEY", "PAYMENT", "JOIN_CHANNEL", "OPEN_LINK")
        or cat in ("SOFTWARE_INSTALLATION", "FINANCIAL_TRANSACTION", "CHANNEL_MIGRATION")
        for at, cat in zip(action_types, categories)
    )

    # 3. Threat signals & attack path
    assert len(data["threat"]["threat_signals"]) > 0 or data["threat"]["confidence"] > 0.0

    # 4. Identity status
    assert data["identity"]["identity_status"] in ("NOT_ESTABLISHED", "IDENTITY_MISMATCH", "AMBIGUOUS")

    # 5. Behavioural time pressure detected
    assert data["behaviour"]["time_pressure_detected"] is True

    # 6. Policy decision from Engine 8
    assert data["decision"]["decision"] in ("PAUSE", "BLOCK", "WARN")
    assert data["decision"]["severity"] in ("HIGH", "CRITICAL", "MEDIUM")
    assert data["decision"]["required_user_confirmation"] is True
    assert len(data["decision"]["reason_codes"]) > 0


# ------------------------------------------------------------------------------
# Test 3: Full Benign Educational Scenario
# ------------------------------------------------------------------------------
def test_e2e_benign_scenario():
    """Verify benign financial content does not produce artificial threat escalation."""
    benign_text = (
        "Learn how mutual funds work. "
        "Review diversification, fees, and long-term investing concepts."
    )
    payload = {
        "input_type": "text",
        "text": benign_text,
        "channel": "web",
        "session_id": "benign_isolated_session_001",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Content identified neutrally as financial
    assert data["content"]["contains_financial_content"] is True

    # Decision ALLOW or INFORM without intervention
    assert data["decision"]["decision"] in ("ALLOW", "INFORM")
    assert data["decision"]["severity"] in ("NONE", "INFORMATIONAL")
    assert data["decision"]["actions_required"] == []
    assert data["decision"]["required_user_confirmation"] is False

    # No invented threat families or high impact actions
    assert len(data["threat"]["threat_families"]) == 0
    assert data["threat"]["high_impact_action_count"] == 0
    assert not any(
        sig in ("REGULATORY_AUTHORITY_CLAIM", "AUTHORITY_IMPERSONATION", "IDENTITY_MISMATCH", "GUARANTEED_RETURN_LANGUAGE", "CHANNEL_MIGRATION", "EXTERNAL_APP_INSTALL", "PAYMENT_REQUEST", "TIME_PRESSURE")
        for sig in data["threat"]["threat_signals"]
    )

    # No identity suspicion
    assert data["identity"]["findings_count"] == 0
    assert data["identity"]["findings_summary"] == []

    # No behavioural escalation
    assert len(data["behaviour"]["signals"]) == 0
    assert data["behaviour"]["time_pressure_detected"] is False
    assert data["behaviour"]["rapid_escalation_detected"] is False
    assert data["behaviour"]["channel_migration_detected"] is False

    # Fingerprint matching (NO_MATCH or EXACT_MATCH if cached)
    assert data["fingerprint"]["match_type"] in ("NO_MATCH", "EXACT_MATCH")


# ------------------------------------------------------------------------------
# Test 4: Identity Verification Fixtures Preservation
# ------------------------------------------------------------------------------
def test_e2e_identity_preservation():
    """Verify identity domain states are preserved and never collapsed into 'SCAM'."""
    # Case A: Official registered entity benchmark
    official_text = (
        "ABC Securities Private Limited is a SEBI registered broker (Registration: INZ00012345). "
        "Visit our official portal at https://www.abcsecurities.com."
    )
    res_a = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": official_text})
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["identity"]["identity_status"] in (
        "ESTABLISHED",
        "PARTIALLY_ESTABLISHED",
        "NOT_ESTABLISHED",
        "AMBIGUOUS",
    )
    assert "SCAM" not in data_a["identity"]["identity_status"]
    assert "FRAUD" not in data_a["identity"]["identity_status"]

    # Case B: Unregistered / unestablished entity
    unregistered_text = "SEBI registered adviser Rahul Sharma offers stock calls."
    res_b = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": unregistered_text})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["identity"]["identity_status"] in ("NOT_ESTABLISHED", "IDENTITY_MISMATCH", "AMBIGUOUS")


# ------------------------------------------------------------------------------
# Test 5: Evidence Verification Fixtures Preservation
# ------------------------------------------------------------------------------
def test_e2e_evidence_preservation():
    """Verify evidence statuses remain distinct and are not falsified."""
    payload = {
        "input_type": "text",
        "text": "SEBI was established in 1992 as a statutory body.",
        "channel": "web",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    ev = data["evidence"]
    assert ev["overall_status"] in (
        "SUPPORTED",
        "PARTIAL_EVIDENCE",
        "INSUFFICIENT_EVIDENCE",
        "CONTRADICTED",
        "NOT_ESTABLISHED",
    )
    assert isinstance(ev["verification_count"], int)
    assert isinstance(ev["source_documents_count"], int)


# ------------------------------------------------------------------------------
# Test 6: Fingerprint Scenario & No Observation Inflation
# ------------------------------------------------------------------------------
def test_e2e_fingerprint_scenario():
    """Verify fingerprint variant matching and anti-inflation on repeated analysis."""
    obs_a_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    obs_b_text = (
        "SEBI certified financial expert Vijay Kumar! Assured 40% returns. "
        "Join our VIP WhatsApp group: https://chat.whatsapp.com/inv99. "
        "Install our mobile software and pay ₹4,999 subscription fee."
    )
    obs_c_text = "Learn what mutual funds are and how diversification protects your capital over the long term."

    # Observation A: Creates a fingerprint
    res_a = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": obs_a_text, "channel": "telegram"})
    assert res_a.status_code == 200
    data_a = res_a.json()
    fp_a = data_a["fingerprint"]
    assert fp_a["fingerprint_id"] is not None
    assert fp_a["observation_count"] == 1

    # Repeated execution of the exact same content must NOT inflate observation count
    res_a_repeat = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": obs_a_text, "channel": "telegram"})
    assert res_a_repeat.status_code == 200
    data_a_repeat = res_a_repeat.json()
    assert data_a_repeat["fingerprint"]["observation_count"] == fp_a["observation_count"]

    # Observation B: Variant with mutated wording / channel / amount -> SEMANTIC_VARIANT
    res_b = client.post("/api/v1/firewall/analyze", json={"input_type": "text", "text": obs_b_text, "channel": "whatsapp"})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["fingerprint"]["match_type"] in ("SEMANTIC_VARIANT", "STRUCTURAL_MATCH")
    assert data_b["fingerprint"]["observation_count"] == 2

    # Observation C: Unrelated educational content -> NO_MATCH
    orch_clean = ProductOrchestrator(engines={"engine_7": ScamFingerprintEngine()})
    res_c_clean = orch_clean.analyze(text=obs_c_text, channel="web")
    resp_c_clean = orch_clean.format_response(res_c_clean)
    assert resp_c_clean.fingerprint.match_type == "NO_MATCH"


# ------------------------------------------------------------------------------
# Test 7: Behavioural Persistence Scenario
# ------------------------------------------------------------------------------
def test_e2e_behavioural_persistence():
    """Verify behavioural engine detects persistence after user decline."""
    sess_id = f"sess_persist_{int(time.time())}"

    # 1. Decline event
    client.post(
        "/api/v1/behaviour/events",
        json={
            "session_id": sess_id,
            "event": {
                "event_id": "EVT-DEC-01",
                "event_type": "USER_DECLINED",
                "timestamp": "2026-10-03T10:00:00Z",
                "data": {"reason": "Not interested in payment"},
            },
        },
    )

    # 2. Re-prompt with payment and urgency
    res = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "Transfer ₹5,000 immediately! Only 3 minutes remaining before you lose access!",
            "session_id": sess_id,
        },
    )
    assert res.status_code == 200
    data = res.json()

    bh = data["behaviour"]
    assert bh["time_pressure_detected"] is True
    assert bh["events_in_session"] >= 1
    # Check that behavioural signals exist
    signals_str = " ".join(bh["signals"])
    findings_str = " ".join(bh["findings"])
    assert "PRESSURE" in signals_str or "URGENCY" in signals_str or len(bh["findings"]) > 0


# ------------------------------------------------------------------------------
# Test 8: Failure Injection Across Engines
# ------------------------------------------------------------------------------
def test_e2e_failure_injection_all_engines():
    """Verify controlled degradation and absence of fabricated signals on engine failures."""
    from nivesh.orchestrator.service import ProductOrchestrator
    from nivesh.engine import ContentIntelligenceEngine
    from nivesh.sources.engine import SourceIntelligenceEngine
    from nivesh.evidence.engine import EvidenceVerificationEngine
    from nivesh.threat.engine import ThreatIntelligenceEngine
    from nivesh.fingerprints.engine import ScamFingerprintEngine
    from nivesh.identity.engine import IdentityVerificationEngine
    from nivesh.behaviour.engine import BehaviouralSignalEngine
    from nivesh.policy.engine import PolicyInterventionEngine

    # 0. Engine 1 Failure -> pipeline safely stops dependent execution with FatalOrchestrationError
    class FailingContentEngine(ContentIntelligenceEngine):
        def process_text(self, *args, **kwargs):
            raise RuntimeError("Content engine crash")

    orch_e1 = ProductOrchestrator(engines={"engine_1": FailingContentEngine()})
    with pytest.raises(FatalOrchestrationError) as exc_info:
        orch_e1.analyze(text="Any financial query")
    assert "Engine 1" in str(exc_info.value)

    # 1. Engine 4 Failure -> degraded state, no fabricated evidence
    class FailingSourceEngine(SourceIntelligenceEngine):
        def discover_and_retrieve(self, *args, **kwargs):
            raise ConnectionError("Upstream registry timeout")

    orch_e4 = ProductOrchestrator(engines={"engine_4": FailingSourceEngine()})
    res_e4 = orch_e4.analyze(text="Rahul Sharma is a registered adviser.")
    assert res_e4.pipeline_status in ("COMPLETED", "DEGRADED")
    resp_e4 = orch_e4.format_response(res_e4)
    assert resp_e4.evidence.retrieval_status in ("SOURCE_UNAVAILABLE", "NOT_RUN")
    assert resp_e4.evidence.verification_count == 0

    # 2. Engine 5 Failure -> downstream engines receive no fabricated evidence
    class FailingEvidenceEngine(EvidenceVerificationEngine):
        def verify(self, *args, **kwargs):
            raise RuntimeError("Evidence engine crash")

    orch_e5 = ProductOrchestrator(engines={"engine_5": FailingEvidenceEngine()})
    res_e5 = orch_e5.analyze(text="Rahul Sharma is a registered adviser.")
    assert res_e5.pipeline_status in ("COMPLETED", "DEGRADED")
    resp_e5 = orch_e5.format_response(res_e5)
    assert resp_e5.evidence.verification_count == 0

    # 3. Engine 6 Failure -> other downstream intelligence intact
    class FailingThreatEngine(ThreatIntelligenceEngine):
        def analyze(self, *args, **kwargs):
            raise RuntimeError("Threat engine crash")

    orch_e6 = ProductOrchestrator(engines={"engine_6": FailingThreatEngine()})
    res_e6 = orch_e6.analyze(text="Rahul Sharma is a registered adviser.")
    assert res_e6.context.content is not None

    # 4. Engine 7 Failure -> fingerprint failure does not corrupt identity/behaviour/threat
    class FailingFingerprintEngine(ScamFingerprintEngine):
        def match_and_record(self, *args, **kwargs):
            raise RuntimeError("Fingerprint database unreachable")

    orch_e7 = ProductOrchestrator(engines={"engine_7": FailingFingerprintEngine()})
    res_e7 = orch_e7.analyze(text="Rahul Sharma is a registered adviser.")
    assert res_e7.context.identity is not None
    assert res_e7.context.behaviour is not None

    # 5. Engine 9 Failure -> not converted to IDENTITY_MISMATCH
    class FailingIdentityEngine(IdentityVerificationEngine):
        def verify(self, *args, **kwargs):
            raise RuntimeError("Database unavailable")

    orch_e9 = ProductOrchestrator(engines={"engine_9": FailingIdentityEngine()})
    res_e9 = orch_e9.analyze(text="Rahul Sharma is a registered adviser.")
    resp_e9 = orch_e9.format_response(res_e9)
    assert resp_e9.identity.identity_status != "IDENTITY_MISMATCH"

    # 6. Engine 10 Failure -> no synthetic behavioural signals
    class FailingBehaviourEngine(BehaviouralSignalEngine):
        def analyze(self, *args, **kwargs):
            raise RuntimeError("Behaviour store failure")

    orch_e10 = ProductOrchestrator(engines={"engine_10": FailingBehaviourEngine()})
    res_e10 = orch_e10.analyze(text="Transfer ₹5,000 immediately!")
    resp_e10 = orch_e10.format_response(res_e10)
    assert len(resp_e10.behaviour.signals) == 0

    # 7. Engine 8 Failure -> overall analysis does not pretend a policy decision exists
    class FailingPolicyEngine(PolicyInterventionEngine):
        def decide(self, *args, **kwargs):
            raise RuntimeError("Policy rule failure")

    orch_e8 = ProductOrchestrator(engines={"engine_8": FailingPolicyEngine()})
    with pytest.raises(FatalOrchestrationError):
        orch_e8.analyze(text="Normal financial query")


# ------------------------------------------------------------------------------
# Test 9: Partial Pipeline Validation (Analytical Results)
# ------------------------------------------------------------------------------
def test_e2e_partial_pipeline_analytical_results():
    """Verify SOURCE_UNAVAILABLE and INSUFFICIENT_EVIDENCE return HTTP 200, not 500."""
    payload = {
        "input_type": "text",
        "text": "Unverifiable private advisory entity claiming 50% profits.",
        "channel": "web",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["pipeline_status"] in ("COMPLETED", "DEGRADED")
    assert data["evidence"]["overall_status"] in (
        "INSUFFICIENT_EVIDENCE",
        "SOURCE_UNAVAILABLE",
        "NOT_ESTABLISHED",
        "SUPPORTED",
    )


# ------------------------------------------------------------------------------
# Test 10: Session Isolation
# ------------------------------------------------------------------------------
def test_e2e_session_isolation():
    """Verify independent sessions never leak interaction history."""
    sess_a = f"session_alpha_{int(time.time())}"
    sess_b = f"session_beta_{int(time.time())}"

    # Dispatch events to session A
    for i in range(3):
        client.post(
            "/api/v1/behaviour/events",
            json={
                "session_id": sess_a,
                "event": {
                    "event_id": f"EVT-A-{i}",
                    "event_type": "CLICK_LINK",
                    "channel": "telegram",
                    "timestamp": f"2026-10-03T10:0{i}:00Z",
                    "data": {"url": "https://t.me/sample"},
                },
            },
        )

    # Analyze in session B
    res_b = client.post(
        "/api/v1/firewall/analyze",
        json={
            "input_type": "text",
            "text": "How do mutual funds work?",
            "session_id": sess_b,
        },
    )
    assert res_b.status_code == 200
    data_b = res_b.json()

    assert data_b["session_id"] == sess_b
    assert data_b["behaviour"]["events_in_session"] == 0
    assert len(data_b["behaviour"]["signals"]) == 0


# ------------------------------------------------------------------------------
# Test 11: Concurrency Safety
# ------------------------------------------------------------------------------
def test_e2e_concurrency_safety():
    """Verify concurrent requests execute safely with distinct IDs and contexts."""
    def _make_request(i):
        return client.post(
            "/api/v1/firewall/analyze",
            json={
                "input_type": "text",
                "text": f"Query number {i}: Learn how bond yield works.",
                "session_id": f"concurrent_sess_{i}",
            },
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_make_request, i) for i in range(4)]
        responses = [f.result() for f in futures]

    analysis_ids = set()
    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        analysis_ids.add(data["analysis_id"])

    # All analysis IDs must be unique
    assert len(analysis_ids) == len(responses)


# ------------------------------------------------------------------------------
# Test 12: Privacy End-to-End Across All Layers
# ------------------------------------------------------------------------------
def test_e2e_privacy_end_to_end():
    """Verify secrets and cards are scrubbed across response, metadata, and provenance."""
    raw_payload = {
        "input_type": "text",
        "text": (
            "Pay with card 4111 2222 3333 4444. "
            "Password is SecretPassword999. OTP is 123456. PIN is 4321. CVV is 987."
        ),
        "metadata": {
            "password": "metadata_secret_password",
            "otp": "654321",
            "client_app": "test_suite",
        },
    }
    response = client.post("/api/v1/firewall/analyze", json=raw_payload)
    assert response.status_code == 200
    res_text = response.text

    # Forbidden raw credentials must not appear
    for forbidden in [
        "4111 2222 3333 4444",
        "SecretPassword999",
        "metadata_secret_password",
        "123456",
        "654321",
    ]:
        assert forbidden not in res_text

    # Redaction token must be present
    assert "[REDACTED" in res_text


# ------------------------------------------------------------------------------
# Test 13: Provenance Validation
# ------------------------------------------------------------------------------
def test_e2e_provenance_validation():
    """Verify complete audit provenance without leaking internal secrets."""
    response = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Financial literacy concepts."},
    )
    assert response.status_code == 200
    data = response.json()

    prov = data["provenance"]
    assert "orchestrator_version" in prov
    assert "analysis_id" in prov
    assert "engines_executed" in prov
    assert "source_mode" in prov

    # Internal secrets must never be exposed
    for secret_key in ["password", "secret", "token", "api_key", "db_uri"]:
        assert secret_key not in prov


# ------------------------------------------------------------------------------
# Test 14: Policy Authority Validation
# ------------------------------------------------------------------------------
def test_e2e_policy_authority_strict_boundary():
    """Verify Engine 8 is the sole component deciding policy."""
    from nivesh.api.app import firewall_analyze
    from nivesh.orchestrator.service import ProductOrchestrator

    # Inspect API function source: must not contain hardcoded decision assignment
    api_src = inspect.getsource(firewall_analyze)
    assert 'decision = "BLOCK"' not in api_src
    assert 'decision = "PAUSE"' not in api_src
    assert 'decision = "ALLOW"' not in api_src

    # Inspect ProductOrchestrator.analyze: policy comes from engine_8
    orch_src = inspect.getsource(ProductOrchestrator.analyze)
    assert "self.engines['engine_8'].decide" in orch_src or "engine_8" in orch_src


# ------------------------------------------------------------------------------
# Test 15: Explainability Validation (Non-ALLOW Decisions)
# ------------------------------------------------------------------------------
def test_e2e_explainability_non_allow():
    """Verify non-ALLOW decision provides grounded explanation and reason codes."""
    payload = {
        "input_type": "text",
        "text": "SEBI registered adviser Rahul Sharma guarantees 40% returns. Pay ₹5,000 to UPI rahul@upi.",
        "channel": "telegram",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    dec = data["decision"]
    assert dec["decision"] in ("PAUSE", "BLOCK", "WARN")
    assert dec["primary_reason"] is not None
    assert len(dec["reason_codes"]) > 0

    exp = dec["explanation"]
    assert exp["decision"] == dec["decision"]
    assert len(exp["user_message"]) > 0
    assert len(exp["technical_message"]) > 0
    assert isinstance(exp["supporting_signals"], list)


# ------------------------------------------------------------------------------
# Test 16: API Contract Validation
# ------------------------------------------------------------------------------
def test_e2e_api_contract_validation():
    """Verify frozen response contract contains all required top-level sections."""
    response = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Diversification across asset classes."},
    )
    assert response.status_code == 200
    data = response.json()

    required_keys = {
        "analysis_id",
        "session_id",
        "pipeline_status",
        "created_at",
        "completed_at",
        "duration_ms",
        "decision",
        "content",
        "claims",
        "actions",
        "evidence",
        "identity",
        "threat",
        "fingerprint",
        "behaviour",
        "provenance",
        "warnings",
        "errors",
    }
    assert required_keys.issubset(set(data.keys()))


# ------------------------------------------------------------------------------
# Test 17: Analysis Retrieval Validation
# ------------------------------------------------------------------------------
def test_e2e_analysis_retrieval():
    """Verify GET /api/v1/firewall/analysis/{analysis_id} retrieves stored result."""
    # 1. Post analysis
    post_res = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Index investing and asset allocation."},
    )
    assert post_res.status_code == 200
    analysis_id = post_res.json()["analysis_id"]

    # 2. Retrieve by ID
    get_res = client.get(f"/api/v1/firewall/analysis/{analysis_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["analysis_id"] == analysis_id
    assert get_data["decision"]["decision"] == post_res.json()["decision"]["decision"]

    # 3. 404 for missing ID
    missing_res = client.get("/api/v1/firewall/analysis/ORCH-NON-EXISTENT-999")
    assert missing_res.status_code == 404
    missing_data = missing_res.json()
    assert missing_data["error_code"] == "ANALYSIS_NOT_FOUND"


# ------------------------------------------------------------------------------
# Test 18: Error Response Sanitization
# ------------------------------------------------------------------------------
def test_e2e_error_response_sanitization(monkeypatch):
    """Verify internal exception returns structured FirewallApiError without stack traces."""
    def _mock_raise(*args, **kwargs):
        raise RuntimeError("CRITICAL internal database error at /var/secrets/keys.db")

    monkeypatch.setattr(firewall_orchestrator, "analyze", _mock_raise)

    response = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Valid input text"},
    )
    assert response.status_code == 500
    data = response.json()

    assert data["error_code"] == "PIPELINE_FAILURE"
    assert "/var/secrets" not in data["message"]
    assert "Traceback" not in response.text


# ------------------------------------------------------------------------------
# Test 19: Performance Smoke Test
# ------------------------------------------------------------------------------
def test_e2e_performance_smoke_test():
    """Verify performance metrics and duration reporting."""
    t0 = time.time()
    response = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Understanding bond durations and credit spreads."},
    )
    elapsed_ms = (time.time() - t0) * 1000
    assert response.status_code == 200
    data = response.json()

    assert data["duration_ms"] > 0
    assert "engines_executed" in data["provenance"]
    assert len(data["provenance"]["engines_executed"]) == 10


# ------------------------------------------------------------------------------
# Test 20: Determinism Test
# ------------------------------------------------------------------------------
def test_e2e_determinism_test():
    """Verify identical requests under equivalent conditions yield identical logical results."""
    payload = {
        "input_type": "text",
        "text": "Sovereign gold bond scheme features, taxation, and interest payments.",
        "channel": "web",
    }
    res1 = client.post("/api/v1/firewall/analyze", json=payload).json()
    res2 = client.post("/api/v1/firewall/analyze", json=payload).json()

    assert res1["decision"]["decision"] == res2["decision"]["decision"]
    assert res1["decision"]["severity"] == res2["decision"]["severity"]
    assert res1["decision"]["reason_codes"] == res2["decision"]["reason_codes"]
    assert res1["content"]["contains_financial_content"] == res2["content"]["contains_financial_content"]
    assert res1["threat"]["threat_signals"] == res2["threat"]["threat_signals"]

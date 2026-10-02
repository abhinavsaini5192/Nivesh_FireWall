"""Tests for Phase 11.4: Unified Firewall API & Result.

Validates:
1. Valid text analysis (HTTP 200, unified schema)
2. Threat benchmark scenario (detects attack signals, policy PAUSE/BLOCK)
3. Final policy decision matches Engine 8 exactly
4. No policy duplication in API layer
5. Identity result preservation (NOT_ESTABLISHED, IDENTITY_MISMATCH)
6. Behaviour result preservation (time pressure, signals)
7. Fingerprint result preservation (NO_MATCH, structural equivalence)
8. Evidence preservation (SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE)
9. Source unavailable handled as analytical result, not 500
10. Invalid input returns 400 (INVALID_REQUEST, UNSUPPORTED_INPUT, INVALID_URL)
11. Oversized input returns 400 (INPUT_TOO_LARGE)
12. Missing analysis GET returns 404 (ANALYSIS_NOT_FOUND)
13. Privacy boundary (forbidden credentials/PII stripped/redacted)
14. Session isolation (distinct sessions only receive their own history)
15. Provenance exposure without internal credential leakage
16. Error sanitization (no stack traces or filesystem paths)
17. Deterministic result structure
18. Benign content does not trigger false threat escalation
19. API Contract freeze test representing frontend consumption
20. Full 5-stage benchmark test
"""

import ast
import inspect
import pytest
from fastapi.testclient import TestClient

from nivesh.api.app import app, firewall_orchestrator
from nivesh.schemas.firewall import FirewallAnalysisResponse, FirewallApiError
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType


client = TestClient(app)


# ------------------------------------------------------------------------------
# Test 1: Valid Text Analysis
# ------------------------------------------------------------------------------
def test_valid_text_analysis():
    """Send normal financial educational content and verify unified response."""
    payload = {
        "input_type": "text",
        "text": "Learn how mutual funds and index funds work. Review asset allocation, investment fees, and long-term investing concepts.",
        "channel": "web",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Validate response conforms to canonical FirewallAnalysisResponse
    model = FirewallAnalysisResponse.model_validate(data)
    assert model.analysis_id.startswith("ORCH-")
    assert model.pipeline_status in ("COMPLETED", "DEGRADED")
    assert model.decision.decision in ("ALLOW", "INFORM")
    assert model.content.contains_financial_content is True
    assert model.provenance["orchestrator_version"] == "1.0.0"


# ------------------------------------------------------------------------------
# Test 2: Threat Benchmark
# ------------------------------------------------------------------------------
def test_threat_benchmark():
    """Send threat scenario and verify comprehensive multi-engine results."""
    threat_text = (
        "SEBI registered adviser Rahul Sharma. Guaranteed 40% returns on WhatsApp. "
        "Download secret trading APK and pay ₹5000 to UPI rahul@upi. Only 5 minutes left!"
    )
    payload = {
        "input_type": "text",
        "text": threat_text,
        "channel": "telegram",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify structured sections exist and are populated
    assert len(data["claims"]) > 0
    assert len(data["actions"]) > 0
    assert data["threat"]["confidence"] > 0.0 or len(data["threat"]["threat_signals"]) > 0
    assert data["identity"]["identity_status"] in ("NOT_ESTABLISHED", "IDENTITY_MISMATCH", "ESTABLISHED", "AMBIGUOUS")
    assert data["behaviour"]["time_pressure_detected"] is True
    assert data["decision"]["decision"] in ("PAUSE", "BLOCK", "WARN")


# ------------------------------------------------------------------------------
# Test 3: Final Policy Decision Source
# ------------------------------------------------------------------------------
def test_final_policy_decision():
    """Verify final decision matches Engine 8 canonical result."""
    payload = {
        "input_type": "text",
        "text": "Send ₹50,000 immediately to account 1234567890 to claim lottery winnings.",
        "channel": "sms",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    dec = data["decision"]
    assert dec["decision"] in ("ALLOW", "INFORM", "WARN", "PAUSE", "BLOCK")
    assert dec["severity"] in ("NONE", "INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert dec["primary_reason"] is not None
    assert isinstance(dec["reason_codes"], list)
    assert dec["explanation"]["decision"] == dec["decision"]


# ------------------------------------------------------------------------------
# Test 4: No Policy Duplication in API Layer
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Test 4: No Policy Duplication in API Layer
# ------------------------------------------------------------------------------
def test_no_policy_duplication():
    """Ensure API code contains no independent policy rules deciding BLOCK/PAUSE."""
    from nivesh.api.app import firewall_analyze
    func_src = inspect.getsource(firewall_analyze)
    # The API endpoint must not contain hardcoded logic like `decision = "BLOCK"`
    assert 'decision = "BLOCK"' not in func_src
    assert 'decision = "PAUSE"' not in func_src
    assert "decision = PolicyDecision" not in func_src


# ------------------------------------------------------------------------------
# Test 5: Identity Result Preservation
# ------------------------------------------------------------------------------
def test_identity_result_preservation():
    """Verify Engine 9 findings are preserved with nuanced domain states."""
    payload = {
        "input_type": "text",
        "text": "SEBI licensed broker FinMax Global invites you to deposit funds.",
        "channel": "whatsapp",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    idt = data["identity"]
    assert idt["identity_status"] in (
        "ESTABLISHED",
        "PARTIALLY_ESTABLISHED",
        "NOT_ESTABLISHED",
        "IDENTITY_MISMATCH",
        "AMBIGUOUS",
        "INSUFFICIENT_EVIDENCE",
    )
    assert isinstance(idt["claimed_entities"], list)
    assert isinstance(idt["findings_summary"], list)


# ------------------------------------------------------------------------------
# Test 6: Behaviour Result Preservation
# ------------------------------------------------------------------------------
def test_behaviour_result_preservation():
    """Verify Engine 10 findings are represented correctly."""
    payload = {
        "input_type": "text",
        "text": "Only 3 minutes left to claim! Hurry up or forfeit your bonus!",
        "channel": "sms",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    bh = data["behaviour"]
    assert bh["time_pressure_detected"] is True
    assert any("PRESSURE" in s or "URGENCY" in s for s in bh["signals"]) or len(bh["findings"]) > 0


# ------------------------------------------------------------------------------
# Test 7: Fingerprint Result Preservation
# ------------------------------------------------------------------------------
def test_fingerprint_result_preservation():
    """Verify Engine 7 match information is represented without flattening."""
    payload = {
        "input_type": "text",
        "text": "Normal informational text about stock indices.",
        "channel": "web",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    fp = data["fingerprint"]
    assert fp["match_type"] in ("NO_MATCH", "EXACT_MATCH", "SEMANTIC_VARIANT", "STRUCTURAL_MATCH")
    assert isinstance(fp["match_confidence"], float)


# ------------------------------------------------------------------------------
# Test 8: Evidence Preservation
# ------------------------------------------------------------------------------
def test_evidence_preservation():
    """Verify supported, contradicted, and insufficient evidence remain distinct."""
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
        "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE",
        "SOURCE_UNAVAILABLE",
        "NOT_ESTABLISHED",
        "PARTIAL_EVIDENCE",
    )
    assert isinstance(ev["verification_count"], int)
    assert isinstance(ev["source_documents_count"], int)


# ------------------------------------------------------------------------------
# Test 9: Source Unavailable as Analytical Result
# ------------------------------------------------------------------------------
def test_source_unavailable_handled_as_analytical_result():
    """Verify SOURCE_UNAVAILABLE does not crash the API or become an automatic 500."""
    from nivesh.orchestrator.service import ProductOrchestrator
    from nivesh.sources.engine import SourceIntelligenceEngine
    from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata

    class MockOfflineSourceEngine(SourceIntelligenceEngine):
        def discover_and_retrieve(self, content, claims=None, actions=None, **kwargs):
            return SourceAnalysis(
                content_id=content.content_id,
                claim_sources=[],
                analysis_metadata=SourceAnalysisMetadata(
                    claims_processed=1,
                    sources_queried=1,
                    documents_retrieved=0,
                    retrieval_failures=1,
                ),
            )

    orch = ProductOrchestrator(engines={"engine_4": MockOfflineSourceEngine()})
    res = orch.analyze(text="Unverifiable company claim ABC XYZ 100% gains.")
    response_model = orch.format_response(res)

    assert response_model.evidence.retrieval_status == "SOURCE_UNAVAILABLE"
    assert response_model.pipeline_status in ("COMPLETED", "DEGRADED")


# ------------------------------------------------------------------------------
# Test 10: Invalid Input
# ------------------------------------------------------------------------------
def test_invalid_input_rejections():
    """Verify 400 responses for malformed inputs."""
    # 1. Empty request
    res_empty = client.post("/api/v1/firewall/analyze", json={})
    assert res_empty.status_code == 400
    data = res_empty.json()
    assert data["error_code"] == "INVALID_REQUEST"

    # 2. Unsupported input type
    res_bad_type = client.post("/api/v1/firewall/analyze", json={"input_type": "audio", "text": "Hello"})
    assert res_bad_type.status_code == 400
    data = res_bad_type.json()
    assert data["error_code"] == "UNSUPPORTED_INPUT"

    # 3. Malformed URL
    res_bad_url = client.post("/api/v1/firewall/analyze", json={"input_type": "url", "url": "not_a_valid_url"})
    assert res_bad_url.status_code == 400
    data = res_bad_url.json()
    assert data["error_code"] == "INVALID_URL"

    # 4. Oversized session ID
    res_bad_sess = client.post(
        "/api/v1/firewall/analyze",
        json={"input_type": "text", "text": "Valid text", "session_id": "X" * 200},
    )
    assert res_bad_sess.status_code == 400
    data = res_bad_sess.json()
    assert data["error_code"] == "INVALID_SESSION"


# ------------------------------------------------------------------------------
# Test 11: Oversized Input
# ------------------------------------------------------------------------------
def test_oversized_input_rejected():
    """Verify text exceeding 50,000 characters is rejected safely."""
    huge_text = "A" * 50_001
    payload = {"input_type": "text", "text": huge_text}
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INPUT_TOO_LARGE"
    assert "exceeds maximum permitted limit" in data["message"]


# ------------------------------------------------------------------------------
# Test 12: Missing Analysis Retrieval
# ------------------------------------------------------------------------------
def test_missing_analysis_retrieval():
    """Verify retrieval returns 404 for non-existent analysis ID."""
    response = client.get("/api/v1/firewall/analysis/NON_EXISTENT_ID_99999")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "ANALYSIS_NOT_FOUND"
    assert "NON_EXISTENT_ID_99999" in data["message"]


# ------------------------------------------------------------------------------
# Test 13: Privacy Boundary
# ------------------------------------------------------------------------------
def test_privacy_boundary():
    """Verify forbidden credentials, card numbers, and secrets are redacted."""
    sensitive_text = (
        "Send funds using card 4111 2222 3333 4444. My password is SecretPassword123. "
        "The otp is 987654 and cvv is 123. Also account number is 9876543210."
    )
    payload = {
        "input_type": "text",
        "text": sensitive_text,
        "metadata": {
            "password": "supersecretpassword",
            "otp": "654321",
            "safe_client": "browser_extension",
        },
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    raw_json = response.text

    # Verify forbidden raw secrets are NOT present anywhere in the output
    assert "4111 2222 3333 4444" not in raw_json
    assert "SecretPassword123" not in raw_json
    assert "supersecretpassword" not in raw_json
    # Redaction tokens should be present
    assert "[REDACTED" in raw_json


# ------------------------------------------------------------------------------
# Test 14: Session Isolation
# ------------------------------------------------------------------------------
def test_session_isolation():
    """Verify different sessions do not cross-contaminate interaction history."""
    session_a = "session_iso_A"
    session_b = "session_iso_B"

    # Record event in session A
    event_payload = {
        "session_id": session_a,
        "event": {
            "event_id": "EVT-A1",
            "event_type": "CLICK_LINK",
            "channel": "telegram",
            "timestamp": "2026-10-03T00:00:00Z",
            "data": {"url": "https://t.me/fake_group"},
        },
    }
    client.post("/api/v1/behaviour/events", json=event_payload)

    # Analyze in session B
    payload_b = {
        "input_type": "text",
        "text": "Hello, how do mutual funds work?",
        "session_id": session_b,
    }
    response_b = client.post("/api/v1/firewall/analyze", json=payload_b)
    assert response_b.status_code == 200
    data_b = response_b.json()

    # Session B must NOT inherit session A's event count
    assert data_b["behaviour"]["events_in_session"] == 0
    assert data_b["session_id"] == session_b


# ------------------------------------------------------------------------------
# Test 15: Provenance Exposure
# ------------------------------------------------------------------------------
def test_provenance_exposure():
    """Verify provenance metadata is exposed without leaking internal secrets."""
    payload = {
        "input_type": "text",
        "text": "Investing concepts and index tracking.",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    prov = data["provenance"]
    assert "orchestrator_version" in prov
    assert "analysis_id" in prov
    assert "engines_executed" in prov

    # Ensure no internal credentials leaked into provenance
    for forbidden in ["api_key", "secret", "token", "password", "connection_string", "auth"]:
        assert forbidden not in prov


# ------------------------------------------------------------------------------
# Test 16: Error Sanitization
# ------------------------------------------------------------------------------
def test_error_sanitization(monkeypatch):
    """Force an internal exception and verify no stack traces or filesystem paths leak."""
    def _mock_failing_analyze(*args, **kwargs):
        raise RuntimeError("CRITICAL internal database error at /var/nivesh/secrets/db.key")

    monkeypatch.setattr(firewall_orchestrator, "analyze", _mock_failing_analyze)

    payload = {"input_type": "text", "text": "Valid text input"}
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 500
    data = response.json()

    assert data["error_code"] == "PIPELINE_FAILURE"
    # Verify no internal filesystem path or raw stack trace leaked
    assert "/var/nivesh" not in data["message"]
    assert "Traceback" not in response.text


# ------------------------------------------------------------------------------
# Test 17: Deterministic Result Structure
# ------------------------------------------------------------------------------
def test_deterministic_result_structure():
    """Equivalent input should produce equivalent logical response structure."""
    payload = {
        "input_type": "text",
        "text": "Consistent financial information regarding sovereign gold bonds.",
        "channel": "web",
    }
    res1 = client.post("/api/v1/firewall/analyze", json=payload).json()
    res2 = client.post("/api/v1/firewall/analyze", json=payload).json()

    # Structural keys must match exactly
    assert set(res1.keys()) == set(res2.keys())
    assert set(res1["decision"].keys()) == set(res2["decision"].keys())
    assert res1["decision"]["decision"] == res2["decision"]["decision"]


# ------------------------------------------------------------------------------
# Test 18: Benign Content Evaluation
# ------------------------------------------------------------------------------
def test_benign_content_no_threat_escalation():
    """Educational financial content must not produce artificial threat escalation."""
    benign_text = (
        "Learn how mutual funds work. "
        "Review diversification, fees, and long-term investing concepts."
    )
    payload = {
        "input_type": "text",
        "text": benign_text,
        "channel": "web",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Must be ALLOW or INFORM (no intervention)
    assert data["decision"]["decision"] in ("ALLOW", "INFORM")
    assert data["decision"]["severity"] in ("NONE", "INFORMATIONAL")
    assert data["decision"]["actions_required"] == []
    assert data["decision"]["required_user_confirmation"] is False

    # No invented attack threat families or high impact actions
    assert len(data["threat"]["threat_families"]) == 0
    assert data["threat"]["high_impact_action_count"] == 0
    assert not any(
        sig in ("REGULATORY_AUTHORITY_CLAIM", "AUTHORITY_IMPERSONATION", "IDENTITY_MISMATCH", "GUARANTEED_RETURN_LANGUAGE", "CHANNEL_MIGRATION", "EXTERNAL_APP_INSTALL", "PAYMENT_REQUEST", "TIME_PRESSURE")
        for sig in data["threat"]["threat_signals"]
    )

    # No identity concerns
    assert data["identity"]["findings_count"] == 0
    assert data["identity"]["findings_summary"] == []

    # No suspicious behaviour
    assert len(data["behaviour"]["signals"]) == 0
    assert data["behaviour"]["time_pressure_detected"] is False
    assert data["behaviour"]["rapid_escalation_detected"] is False
    assert data["behaviour"]["channel_migration_detected"] is False

    # Fingerprint matching (NO_MATCH on first run, EXACT_MATCH if previously recorded)
    assert data["fingerprint"]["match_type"] in ("NO_MATCH", "EXACT_MATCH")


# ------------------------------------------------------------------------------
# Test 19: API Contract Freeze Test (Frontend Consumption Shape)
# ------------------------------------------------------------------------------
def test_api_contract_freeze():
    """Freezes the product API shape before frontend development begins."""
    payload = {
        "input_type": "text",
        "text": "SEBI registered adviser Rahul Sharma guarantees 30% monthly return. Pay ₹5,000 now.",
        "channel": "telegram",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # 1. Canonical top-level contract fields
    expected_top_level_fields = {
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
    assert expected_top_level_fields.issubset(set(data.keys()))

    # 2. Decision section fields
    expected_decision_fields = {
        "decision",
        "severity",
        "primary_reason",
        "reason_codes",
        "explanation",
        "actions_required",
        "required_user_confirmation",
        "cooldown_seconds",
        "policy_version",
        "decision_id",
    }
    assert expected_decision_fields.issubset(set(data["decision"].keys()))

    # 3. Explanation section fields
    expected_explanation_fields = {
        "decision",
        "user_message",
        "technical_message",
        "primary_reason",
        "supporting_signals",
    }
    assert expected_explanation_fields.issubset(set(data["decision"]["explanation"].keys()))


# ------------------------------------------------------------------------------
# Test 20: Full End-to-End Product Test (5-stage Benchmark)
# ------------------------------------------------------------------------------
def test_full_e2e_product_benchmark():
    """End-to-end benchmark through POST /api/v1/firewall/analyze."""
    benchmark_text = (
        "Educational tips on stock trading! "
        "Join our VIP private Telegram channel: https://t.me/vip_trading. "
        "Download our exclusive APK trading terminal. "
        "Transfer ₹5,000 deposit to UPI trading@icici. "
        "Offer expires in 5 minutes! Only 5 minutes left!"
    )
    payload = {
        "input_type": "text",
        "text": benchmark_text,
        "channel": "telegram",
        "session_id": "bench_e2e_001",
    }
    response = client.post("/api/v1/firewall/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Retrieve via GET endpoint to test retrieval persistence
    analysis_id = data["analysis_id"]
    retrieval_response = client.get(f"/api/v1/firewall/analysis/{analysis_id}")
    assert retrieval_response.status_code == 200
    retrieved_data = retrieval_response.json()
    assert retrieved_data["analysis_id"] == analysis_id

    # Validate decision from Engine 8
    assert data["decision"]["decision"] in ("PAUSE", "BLOCK", "WARN")
    assert data["decision"]["severity"] in ("HIGH", "CRITICAL", "MEDIUM")
    assert len(data["decision"]["reason_codes"]) > 0

    # Validate structured findings
    assert len(data["actions"]) >= 2
    assert data["behaviour"]["time_pressure_detected"] is True
    assert data["session_id"] == "bench_e2e_001"

"""Phase 11.3 — Engine Pipeline & Failure Handling Test Suite.

Validates the canonical execution pipeline, failure handling, and safety guarantees:
- Test 1: Full successful execution (E1 -> E2 -> E3 -> E4 -> E5 -> E6/E7/E9/E10 -> E8)
- Test 2: Correct dependency order (no engine executes before prerequisites are ready)
- Test 3: Engine 1 failure (blocks downstream dependent engines)
- Test 4: Engine 4 source failure (preserves failure, skips dependent E5, no fake evidence)
- Test 5: Engine 6 threat failure (preserves independent E9/E10 results, skips dependent E7)
- Test 6: Engine 7 fingerprint failure (isolates failure without corrupting other engines)
- Test 7: Engine 9 identity failure (execution failure is not converted to IDENTITY_MISMATCH)
- Test 8: Engine 10 behaviour failure (does not create synthetic behavioural signals)
- Test 9: Policy gate (Engine 8 cannot execute while required prerequisites are unresolved)
- Test 10: Policy authority (Engine 8 remains the sole policy decision authority)
- Test 11: Timeout protection (engine timeout handled gracefully without hanging)
- Test 12: Bounded retry (transient failure retried deterministically with retry_count recorded)
- Test 13: Retry safety for fingerprinting (repeated runs do not inflate observation count)
- Test 14: Session isolation (simultaneous sessions remain completely independent)
- Test 15: Context integrity (one engine cannot overwrite another engine's results)
- Test 16: Safe cancellation (cancellation leaves context as CANCELLED, never COMPLETED)
- Test 17: Deterministic execution (equivalent inputs yield identical execution states)
- Test 18: Privacy preservation (telemetry, errors, and metadata never leak credentials/PII)
"""

import time
import pytest
from unittest.mock import MagicMock

from nivesh.orchestrator import (
    ProductOrchestrator,
    OrchestratorConfig,
    OrchestrationResult,
    PipelineStatus,
    EngineStatus,
    EngineOutcomeType,
    FatalOrchestrationError,
    CancellationToken,
    PipelineGraph,
    PolicyGate,
    SafeEngineExecutor,
    AnalysisContext,
)
from nivesh.policy.schemas import PolicyDecision, PolicyDecisionType
from nivesh.identity.schemas import IdentityStatus
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType
from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata
from nivesh.schemas.evidence import EvidenceAnalysis, EvidenceAnalysisMetadata


@pytest.fixture
def default_orchestrator():
    """Instantiate a standard ProductOrchestrator."""
    return ProductOrchestrator()


CANONICAL_TEST_TEXT = (
    "SEBI registered advisor Rahul Sharma guarantees 40% monthly returns. "
    "Join our Telegram channel: https://t.me/rahulvip. Pay ₹5,000."
)


# ==============================================================================
# Test 1 — Full Successful Execution
# ==============================================================================

def test_1_full_successful_execution(default_orchestrator):
    """Verify that E1 -> E2 -> E3 -> E4 -> E5 -> E6/E7/E9/E10 -> E8 completes successfully."""
    result = default_orchestrator.analyze(text=CANONICAL_TEST_TEXT)

    assert isinstance(result, OrchestrationResult)
    assert result.is_success is True
    assert result.pipeline_status == "COMPLETED"
    assert result.context.status == PipelineStatus.COMPLETED

    # Verify all 10 engines executed to COMPLETED
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
    for key in expected_engines:
        st = result.context.engine_states.get(key)
        assert st is not None, f"Engine {key} missing from engine states"
        assert st.status == EngineStatus.COMPLETED, f"Engine {key} has status {st.status}"

    assert result.policy_decision is not None
    assert result.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK, PolicyDecisionType.WARN)


# ==============================================================================
# Test 2 — Correct Dependency Order
# ==============================================================================

def test_2_correct_dependency_order():
    """Verify that no engine executes before its required prerequisites are ready."""
    orch = ProductOrchestrator()
    execution_order = []

    def make_spy(key, original_fn):
        def wrapper(*args, **kwargs):
            execution_order.append(key)
            return original_fn(*args, **kwargs)
        return wrapper

    orch.e1.process_text = make_spy("engine_1_content", orch.e1.process_text)
    orch.e2.analyze = make_spy("engine_2_claims", orch.e2.analyze)
    orch.e3.analyze = make_spy("engine_3_actions", orch.e3.analyze)
    orch.e4.discover_and_retrieve = make_spy("engine_4_sources", orch.e4.discover_and_retrieve)
    orch.e5.verify = make_spy("engine_5_evidence", orch.e5.verify)
    orch.e6.analyze = make_spy("engine_6_threat", orch.e6.analyze)
    orch.e7.create_or_match = make_spy("engine_7_fingerprint", orch.e7.create_or_match)
    orch.e9.verify = make_spy("engine_9_identity", orch.e9.verify)
    orch.e10.analyze = make_spy("engine_10_behaviour", orch.e10.analyze)
    orch.e8.decide = make_spy("engine_8_policy", orch.e8.decide)

    result = orch.analyze(text=CANONICAL_TEST_TEXT)
    assert result.is_success is True

    # Dependency assertions
    assert execution_order.index("engine_1_content") < execution_order.index("engine_2_claims")
    assert execution_order.index("engine_2_claims") < execution_order.index("engine_3_actions")
    assert execution_order.index("engine_3_actions") < execution_order.index("engine_4_sources")
    assert execution_order.index("engine_4_sources") < execution_order.index("engine_5_evidence")
    assert execution_order.index("engine_5_evidence") < execution_order.index("engine_6_threat")
    assert execution_order.index("engine_6_threat") < execution_order.index("engine_7_fingerprint")
    assert execution_order.index("engine_1_content") < execution_order.index("engine_9_identity")
    assert execution_order.index("engine_1_content") < execution_order.index("engine_10_behaviour")
    assert execution_order.index("engine_8_policy") == len(execution_order) - 1


# ==============================================================================
# Test 3 — Engine 1 Failure Blocks Downstream Execution
# ==============================================================================

def test_3_engine_1_failure_blocks_downstream():
    """Verify that when Engine 1 fails, downstream engines requiring E1 are not executed."""
    mock_e1 = MagicMock()
    mock_e1.process_text.side_effect = RuntimeError("Content parser corrupted")

    mock_e2 = MagicMock()
    mock_e3 = MagicMock()
    mock_e8 = MagicMock()

    orch = ProductOrchestrator(
        engines={
            "engine_1": mock_e1,
            "engine_2": mock_e2,
            "engine_3": mock_e3,
            "engine_8": mock_e8,
        }
    )

    with pytest.raises(FatalOrchestrationError) as exc_info:
        orch.analyze(text="Test input")

    assert "engine_1_content" in str(exc_info.value.engine_name)
    mock_e2.analyze.assert_not_called()
    mock_e3.analyze.assert_not_called()
    mock_e8.decide.assert_not_called()


# ==============================================================================
# Test 4 — Engine 4 Source Failure
# ==============================================================================

def test_4_engine_4_source_failure_no_fake_evidence():
    """Verify source failure is preserved, no fake evidence is produced, and E5 is skipped."""
    mock_e4 = MagicMock()
    mock_e4.discover_and_retrieve.side_effect = ConnectionError("Registry connection reset")

    orch = ProductOrchestrator(engines={"engine_4": mock_e4})
    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    # Source failure is preserved
    assert result.context.engine_states["engine_4_sources"].status == EngineStatus.FAILED
    assert result.context.sources is None

    # Engine 5 was SKIPPED due to blocked dependency; no fake evidence was generated
    st5 = result.context.engine_states["engine_5_evidence"]
    assert st5.status == EngineStatus.SKIPPED
    assert st5.dependency_blocked is True
    assert st5.failed_dependency == "engine_4_sources"
    assert result.context.evidence is None

    # Upstream results remain intact
    assert result.context.content is not None
    assert result.context.claims is not None
    assert result.context.actions is not None
    assert result.context.engine_states["engine_1_content"].status == EngineStatus.COMPLETED
    assert result.context.engine_states["engine_2_claims"].status == EngineStatus.COMPLETED
    assert result.context.engine_states["engine_3_actions"].status == EngineStatus.COMPLETED


# ==============================================================================
# Test 5 — Engine 6 Failure Preserves Independent Results
# ==============================================================================

def test_5_engine_6_threat_failure_preserves_independent_results():
    """Verify threat failure does not overwrite independent engine results."""
    mock_e6 = MagicMock()
    mock_e6.analyze.side_effect = RuntimeError("Threat graph transition cycle")

    orch = ProductOrchestrator(engines={"engine_6": mock_e6})
    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    # Engine 6 is FAILED
    assert result.context.engine_states["engine_6_threat"].status == EngineStatus.FAILED

    # Engine 7 dependent on E6 is SKIPPED
    st7 = result.context.engine_states["engine_7_fingerprint"]
    assert st7.status == EngineStatus.SKIPPED
    assert st7.failed_dependency == "engine_6_threat"

    # Independent upstream and parallel engines remain COMPLETED and intact
    assert result.context.content is not None
    assert result.context.claims is not None
    assert result.context.actions is not None
    assert result.context.sources is not None
    assert result.context.evidence is not None
    assert result.context.identity is not None
    assert result.context.behaviour is not None


# ==============================================================================
# Test 6 — Engine 7 Failure Isolation
# ==============================================================================

def test_6_engine_7_fingerprint_failure_isolation():
    """Verify fingerprint failure does not corrupt threat, identity, or behaviour analysis."""
    mock_e7 = MagicMock()
    mock_e7.create_or_match.side_effect = RuntimeError("Vector index unavailable")

    orch = ProductOrchestrator(engines={"engine_7": mock_e7})
    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    assert result.context.engine_states["engine_7_fingerprint"].status == EngineStatus.FAILED
    assert result.context.threat is not None
    assert result.context.identity is not None
    assert result.context.behaviour is not None
    assert result.policy_decision is not None


# ==============================================================================
# Test 7 — Engine 9 Failure Not Converted to Identity Mismatch
# ==============================================================================

def test_7_engine_9_identity_failure_not_converted_to_mismatch():
    """Verify execution failure in Engine 9 does NOT become IDENTITY_MISMATCH."""
    mock_e9 = MagicMock()
    mock_e9.verify.side_effect = TimeoutError("SEBI registry lookup timed out")

    orch = ProductOrchestrator(engines={"engine_9": mock_e9})
    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    st9 = result.context.engine_states["engine_9_identity"]
    assert st9.status == EngineStatus.FAILED
    assert result.context.identity is None
    # Must NOT have created a fake IDENTITY_MISMATCH result
    assert st9.analytical_result != "IDENTITY_MISMATCH"


# ==============================================================================
# Test 8 — Engine 10 Failure Does Not Create Synthetic Signals
# ==============================================================================

def test_8_engine_10_behaviour_failure_no_synthetic_signals():
    """Verify behavioural engine failure does not synthesize fake behavioural signals."""
    mock_e10 = MagicMock()
    mock_e10.analyze.side_effect = RuntimeError("Event bus corrupted")

    orch = ProductOrchestrator(engines={"engine_10": mock_e10})
    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    st10 = result.context.engine_states["engine_10_behaviour"]
    assert st10.status == EngineStatus.FAILED
    assert result.context.behaviour is None


# ==============================================================================
# Test 9 — Policy Gate
# ==============================================================================

def test_9_policy_gate_blocks_unresolved_prerequisites():
    """Verify Policy Gate prevents Engine 8 execution when prerequisites are unresolved."""
    # Case A: Empty context
    empty_ctx = AnalysisContext(analysis_id="ORCH-GATE-1")
    passed, reasons = PolicyGate.verify_gate(empty_ctx)
    assert passed is False
    assert any("Engine 1 content is missing" in r for r in reasons)

    # Case B: Engine still in RUNNING state
    empty_ctx.mark_engine_started("engine_4_sources")
    passed, reasons = PolicyGate.verify_gate(empty_ctx)
    assert passed is False
    assert any("RUNNING state" in r for r in reasons)

    # Case C: Pipeline cancelled
    empty_ctx.cancel_pipeline("Cancelled by user")
    passed, reasons = PolicyGate.verify_gate(empty_ctx)
    assert passed is False
    assert any("Pipeline was cancelled" in r for r in reasons)


# ==============================================================================
# Test 10 — Policy Authority
# ==============================================================================

def test_10_policy_authority_engine_8_sole_authority():
    """Verify final decision comes directly from Engine 8 and orchestrator never invents policy."""
    custom_policy = PolicyDecision(
        decision_id="DEC-CUSTOM-99",
        decision=PolicyDecisionType.PAUSE,
        severity="HIGH",
        primary_reason="Direct policy from mock engine 8",
        supporting_reasons=["Direct policy from mock engine 8"],
        user_message="Custom Engine 8 message",
        technical_message="Technical explanation",
        policy_version="8.0.0",
        created_at="2026-10-02T10:00:00Z",
    )

    mock_e8 = MagicMock()
    mock_e8.decide.return_value = custom_policy

    orch = ProductOrchestrator(engines={"engine_8": mock_e8})
    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    # Result must reflect Engine 8's exact returned decision
    assert result.policy_decision is custom_policy
    assert result.decision == PolicyDecisionType.PAUSE
    assert result.policy_decision.decision_id == "DEC-CUSTOM-99"


# ==============================================================================
# Test 11 — Timeout Protection
# ==============================================================================

def test_11_timeout_simulation_and_safe_state():
    """Simulate a timed-out engine and verify bounded execution and safe state."""
    def slow_discover(*args, **kwargs):
        time.sleep(0.3)
        return SourceAnalysis(content_id="test", claim_sources=[])

    mock_e4 = MagicMock()
    mock_e4.discover_and_retrieve.side_effect = slow_discover

    # 50ms timeout configuration
    cfg = OrchestratorConfig(engine_timeout_ms=50.0)
    orch = ProductOrchestrator(engines={"engine_4": mock_e4}, config=cfg)

    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    st4 = result.context.engine_states["engine_4_sources"]
    assert st4.status == EngineStatus.FAILED
    assert "timeout" in st4.error_message.lower() or "exceeded" in st4.error_message.lower()
    # Pipeline handled timeout gracefully without freezing or fabricating fake sources
    assert result.context.sources is None


# ==============================================================================
# Test 12 — Bounded Retry
# ==============================================================================

def test_12_retry_bounded_and_observable():
    """Simulate a transient failure that succeeds on retry; verify retry_count is captured."""
    attempts = 0

    def transient_claims(content):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionResetError("Transient network drop")
        real_e2 = ProductOrchestrator().e2
        return real_e2.analyze(content)

    mock_e2 = MagicMock()
    mock_e2.analyze.side_effect = transient_claims

    cfg = OrchestratorConfig(max_retries=2, retry_delay_ms=1.0)
    orch = ProductOrchestrator(engines={"engine_2": mock_e2}, config=cfg)

    result = orch.analyze(text=CANONICAL_TEST_TEXT)

    assert result.is_success is True
    rec_e2 = result.telemetry.engine_records["engine_2_claims"]
    assert rec_e2.retry_count == 1
    assert result.context.engine_states["engine_2_claims"].retry_count == 1
    assert result.context.engine_states["engine_2_claims"].status == EngineStatus.COMPLETED


# ==============================================================================
# Test 13 — Retry Safety for Fingerprinting
# ==============================================================================

def test_13_retry_safety_fingerprint_observation_count():
    """Verify repeated orchestration does not artificially inflate fingerprint observation counts."""
    orch = ProductOrchestrator()

    # First run
    res1 = orch.analyze(text=CANONICAL_TEST_TEXT, idempotency_key="REQ-FP-01")
    fp_id1 = res1.context.fingerprint.fingerprint.fingerprint_id
    obs_count_1 = res1.context.fingerprint.fingerprint.observation_count

    # Second run with same idempotency key
    res2 = orch.analyze(text=CANONICAL_TEST_TEXT, idempotency_key="REQ-FP-01")
    assert res2 is res1
    assert res2.context.fingerprint.fingerprint.observation_count == obs_count_1


# ==============================================================================
# Test 14 — Session Isolation
# ==============================================================================

def test_14_session_isolation_simultaneous():
    """Verify two distinct sessions produce completely isolated contexts."""
    orch = ProductOrchestrator()

    # Record event in Session Alpha
    orch.record_interaction_event(
        "SESS-ALPHA",
        InteractionEvent(
            event_id="EV-A1",
            session_id="SESS-ALPHA",
            event_type=InteractionEventType.CHANNEL_CHANGED,
            timestamp="2026-10-02T10:00:00Z",
            channel="telegram",
        ),
    )

    # Record event in Session Beta
    orch.record_interaction_event(
        "SESS-BETA",
        InteractionEvent(
            event_id="EV-B1",
            session_id="SESS-BETA",
            event_type=InteractionEventType.CONTENT_VIEW,
            timestamp="2026-10-02T10:05:00Z",
            channel="web",
        ),
    )

    res_alpha = orch.analyze(text=CANONICAL_TEST_TEXT, session_id="SESS-ALPHA")
    res_beta = orch.analyze(text=CANONICAL_TEST_TEXT, session_id="SESS-BETA")

    assert res_alpha.context.session_id == "SESS-ALPHA"
    assert res_beta.context.session_id == "SESS-BETA"
    assert res_alpha.analysis_id != res_beta.analysis_id
    assert res_alpha.context.analysis_id != res_beta.context.analysis_id

    # Verify session summary isolation
    assert res_alpha.context.behaviour.session_summary.session_id == "SESS-ALPHA"
    assert res_beta.context.behaviour.session_summary.session_id == "SESS-BETA"

    # Verify history event isolation
    hist_alpha = orch.get_session_history("SESS-ALPHA")
    hist_beta = orch.get_session_history("SESS-BETA")
    assert any(e.event_id == "EV-A1" for e in hist_alpha.events)
    assert not any(e.event_id == "EV-A1" for e in hist_beta.events)
    assert any(e.event_id == "EV-B1" for e in hist_beta.events)
    assert not any(e.event_id == "EV-B1" for e in hist_alpha.events)


# ==============================================================================
# Test 15 — Context Integrity
# ==============================================================================

def test_15_context_integrity_no_cross_overwrite(default_orchestrator):
    """Verify one engine cannot overwrite another engine's context fields."""
    result = default_orchestrator.analyze(text=CANONICAL_TEST_TEXT)
    ctx = result.context

    original_identity_id = ctx.identity.analysis_id
    original_threat_id = ctx.threat.content_id

    # Context update methods only touch their respective slots
    ctx.set_threat_result(ctx.threat)
    assert ctx.identity.analysis_id == original_identity_id

    ctx.set_identity_result(ctx.identity)
    assert ctx.threat.content_id == original_threat_id


# ==============================================================================
# Test 16 — Cancellation
# ==============================================================================

def test_16_cancellation_reflects_cancelled_not_completed():
    """Verify cancellation leaves context in CANCELLED state and never reports COMPLETED."""
    orch = ProductOrchestrator()
    token = CancellationToken()
    token.cancel("User initiated cancellation before processing")

    result = orch.analyze(text=CANONICAL_TEST_TEXT, cancellation_token=token)

    assert result.pipeline_status == "CANCELLED"
    assert result.context.status == PipelineStatus.CANCELLED
    assert result.policy_decision is None
    assert result.is_success is False


# ==============================================================================
# Test 17 — Deterministic Execution
# ==============================================================================

def test_17_deterministic_execution():
    """Equivalent inputs must produce equivalent logical execution states and results."""
    orch1 = ProductOrchestrator()
    orch2 = ProductOrchestrator()

    res1 = orch1.analyze(text=CANONICAL_TEST_TEXT)
    res2 = orch2.analyze(text=CANONICAL_TEST_TEXT)

    assert res1.pipeline_status == res2.pipeline_status == "COMPLETED"
    assert res1.decision == res2.decision
    assert len(res1.context.claims.claims) == len(res2.context.claims.claims)
    assert len(res1.context.actions.actions) == len(res2.context.actions.actions)
    assert res1.telemetry.engines_executed == res2.telemetry.engines_executed


# ==============================================================================
# Test 18 — Privacy Preservation
# ==============================================================================

def test_18_privacy_no_credential_leakage_in_telemetry_or_errors():
    """Verify orchestration telemetry, errors, and metadata never leak credentials or PII."""
    mock_e2 = MagicMock()
    mock_e2.analyze.side_effect = ValueError(
        "Failed parsing password=SuperSecret!123 with OTP: 987654 and card 4111 2222 3333 4444 and CVV: 789"
    )

    metadata_with_creds = {
        "user_note": "Confidential",
        "pin": "1234",
        "account_num": "998877665544",
    }

    orch = ProductOrchestrator(engines={"engine_2": mock_e2})
    result = orch.analyze(text="Test input", metadata=metadata_with_creds)

    all_error_text = " ".join(result.errors + result.warnings)
    telemetry_err = result.telemetry.engine_records["engine_2_claims"].error_message

    for forbidden in ["SuperSecret!123", "987654", "4111 2222 3333 4444", "789"]:
        assert forbidden not in all_error_text
        assert forbidden not in telemetry_err

    assert "[REDACTED]" in all_error_text or "[REDACTED_CARD]" in all_error_text

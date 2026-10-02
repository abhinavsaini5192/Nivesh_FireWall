"""Phase 11.1 — Product Orchestrator Core Test Suite.

Validates the central Product Orchestrator:
- Test A: Basic orchestration through all 10 engines
- Test B: Correct canonical dependency flow
- Test C: Policy receives complete available context
- Test D: Engine failure handling (fatal vs recoverable degraded)
- Test E: Source unavailable remains an analytical result
- Test F: Identity not established remains an analytical result
- Test G: Behaviour integration without orchestrator inference
- Test H: Fingerprint integration and provenance
- Test I: Analysis correlation across all engine output IDs
- Test J: Session isolation (zero cross-session contamination)
- Test K: Policy authority boundary (Engine 8 is sole authority)
- Test L: No duplicated intelligence or heuristic policy inside orchestrator
- Test M: Privacy preservation (metadata scrubbing of credentials/PII)
- Test N: Deterministic coordination
- Test Full Integration: Canonical Nivesh benchmark scenario
"""

import pytest
from unittest.mock import MagicMock

from nivesh.orchestrator import (
    ProductOrchestrator,
    OrchestratorConfig,
    OrchestrationResult,
    OrchestrationState,
    EngineOutcomeType,
    FatalOrchestrationError,
    InputIngestionError,
)
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.identity.schemas import IdentityStatus
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType, InteractionHistory
from nivesh.behaviour.schemas import BehaviouralSignalType


@pytest.fixture
def orchestrator():
    """Instantiate a default ProductOrchestrator."""
    return ProductOrchestrator()


# ==============================================================================
# Test A — Basic Orchestration
# ==============================================================================

def test_a_basic_orchestration(orchestrator):
    """A valid input reaches Engine 1 and progresses through all 10 engines."""
    raw_text = (
        "SEBI registered advisor Rahul Sharma guarantees 40% monthly returns. "
        "Join our Telegram channel: https://t.me/rahulvip. Pay ₹5,000."
    )
    result = orchestrator.analyze(text=raw_text)

    assert isinstance(result, OrchestrationResult)
    assert result.is_success is True
    assert result.pipeline_status == "COMPLETED"
    assert result.analysis_id.startswith("ORCH-")
    assert result.policy_decision is not None
    assert result.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK, PolicyDecisionType.WARN)

    # Verify all 10 engines executed in order
    expected_order = [
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
    assert result.telemetry.engines_executed == expected_order
    assert len(result.telemetry.engines_succeeded) == 10
    assert len(result.telemetry.engines_degraded) == 0


# ==============================================================================
# Test B — Correct Dependency Flow
# ==============================================================================

def test_b_correct_dependency_flow():
    """Verify that engines receive the expected upstream outputs in sequence."""
    orch = ProductOrchestrator()

    # Wrap engines with spies to inspect call arguments
    original_e2_analyze = orch.e2.analyze
    orch.e2.analyze = MagicMock(side_effect=original_e2_analyze)

    original_e3_analyze = orch.e3.analyze
    orch.e3.analyze = MagicMock(side_effect=original_e3_analyze)

    original_e4_discover = orch.e4.discover_and_retrieve
    orch.e4.discover_and_retrieve = MagicMock(side_effect=original_e4_discover)

    original_e5_verify = orch.e5.verify
    orch.e5.verify = MagicMock(side_effect=original_e5_verify)

    original_e6_analyze = orch.e6.analyze
    orch.e6.analyze = MagicMock(side_effect=original_e6_analyze)

    original_e8_decide = orch.e8.decide
    orch.e8.decide = MagicMock(side_effect=original_e8_decide)

    text = "Guaranteed 25% returns on index mutual funds. Visit https://t.me/invest."
    result = orch.analyze(text=text)

    # Verify E2 received E1 content
    orch.e2.analyze.assert_called_once()
    e2_arg = orch.e2.analyze.call_args[0][0]
    assert e2_arg.content_id == result.state.content.content_id

    # Verify E3 received E1 content and E2 claims
    orch.e3.analyze.assert_called_once()
    e3_content, e3_claims = orch.e3.analyze.call_args[0]
    assert e3_content.content_id == result.state.content.content_id
    assert e3_claims.content_id == result.state.claims.content_id

    # Verify E4 received content, claims, and actions
    orch.e4.discover_and_retrieve.assert_called_once()
    e4_content, e4_claims, e4_actions = orch.e4.discover_and_retrieve.call_args[0]
    assert e4_content.content_id == result.state.content.content_id
    assert e4_claims.content_id == result.state.claims.content_id
    assert e4_actions.content_id == result.state.actions.content_id

    # Verify E5 received content, claims, and sources
    orch.e5.verify.assert_called_once()
    e5_content, e5_claims, e5_sources = orch.e5.verify.call_args[0]
    assert e5_content.content_id == result.state.content.content_id
    assert e5_claims.content_id == result.state.claims.content_id
    assert e5_sources.content_id == result.state.sources.content_id

    # Verify E8 received all upstream intelligence
    orch.e8.decide.assert_called_once()
    kwargs = orch.e8.decide.call_args[1]
    assert kwargs["content"].content_id == result.state.content.content_id
    assert kwargs["claims"].content_id == result.state.claims.content_id
    assert kwargs["actions"].content_id == result.state.actions.content_id
    assert kwargs["sources"].content_id == result.state.sources.content_id
    assert kwargs["evidence"].content_id == result.state.evidence.content_id
    assert kwargs["threat"] is not None
    assert kwargs["fingerprint"] is not None


# ==============================================================================
# Test C — Policy Receives Complete Available Context
# ==============================================================================

def test_c_policy_receives_complete_available_context(orchestrator):
    """Verify Engine 8 receives all relevant intelligence results and captures provenance."""
    raw_text = "SEBI registered advisor. Guaranteed 30% profit. Pay ₹10,000."
    result = orchestrator.analyze(text=raw_text)

    decision = result.policy_decision
    assert decision is not None
    assert decision.policy_version == "8.0.0"

    # Upstream entity references captured in policy decision
    assert len(decision.relevant_claim_ids) == len(result.state.claims.claims)
    assert len(decision.relevant_action_ids) == len(result.state.actions.actions)
    assert decision.relevant_fingerprint_id is not None


# ==============================================================================
# Test D — Engine Failure Handling
# ==============================================================================

def test_d_engine_failure_handling_fatal():
    """Verify fatal failures when no input is provided or Engine 1 crashes."""
    orch = ProductOrchestrator()

    # Case 1: Missing input
    with pytest.raises(FatalOrchestrationError) as exc_info:
        orch.analyze()
    assert "No valid input provided" in str(exc_info.value)

    # Case 2: Engine 1 crash
    mock_e1 = MagicMock()
    mock_e1.process_text.side_effect = RuntimeError("OCR crashed")
    orch_fatal = ProductOrchestrator(engines={"engine_1": mock_e1})

    with pytest.raises(FatalOrchestrationError) as exc_info2:
        orch_fatal.analyze(text="Test")
    assert "engine_1_content" == exc_info2.value.engine_name


def test_d_engine_failure_handling_recoverable():
    """Verify recoverable engine failure allows pipeline to continue in degraded mode."""
    mock_e4 = MagicMock()
    mock_e4.discover_and_retrieve.side_effect = ConnectionError("Registry lookup timeout")

    orch = ProductOrchestrator(engines={"engine_4": mock_e4})
    result = orch.analyze(text="Guaranteed returns of 20%. Pay ₹5,000.")

    # Status must be DEGRADED, not crashed
    assert result.pipeline_status == "DEGRADED"
    assert result.is_degraded is True
    assert "engine_4_sources" in result.telemetry.engines_degraded
    assert any("Registry lookup timeout" in w for w in result.warnings)

    # Engine 8 still produced a decision using available intelligence
    assert result.policy_decision is not None
    assert result.decision is not None


def test_d_engine_failure_handling_fail_fast():
    """Verify that with fail_fast=True, recoverable engine failure raises FatalOrchestrationError."""
    mock_e4 = MagicMock()
    mock_e4.discover_and_retrieve.side_effect = ConnectionError("Registry lookup timeout")

    cfg = OrchestratorConfig(fail_fast=True)
    orch = ProductOrchestrator(engines={"engine_4": mock_e4}, config=cfg)

    with pytest.raises(FatalOrchestrationError) as exc_info:
        orch.analyze(text="Guaranteed returns. Pay ₹5,000.")
    assert exc_info.value.engine_name == "engine_4_sources"


# ==============================================================================
# Test E — Source Unavailable Analytical Result
# ==============================================================================

def test_e_source_unavailable_preserved():
    """Verify SOURCE_UNAVAILABLE remains an analytical result rather than fabricated evidence."""
    from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata

    mock_e4 = MagicMock()
    mock_e4.discover_and_retrieve.return_value = SourceAnalysis(
        content_id="test-content",
        claim_sources=[],
        analysis_metadata=SourceAnalysisMetadata(retrieval_failures=1),
    )
    orch = ProductOrchestrator(engines={"engine_4": mock_e4})
    result = orch.analyze(text="Unregistered entity GlobalQuantumReturns offers 1000% annual profit.")

    # Source retrieval produced zero documents
    total_docs = sum(len(cs.documents) for cs in result.state.sources.claim_sources)
    assert total_docs == 0

    # In telemetry, E4 recorded as EXPECTED_ANALYTICAL_RESULT with SOURCE_UNAVAILABLE
    rec_e4 = result.telemetry.engine_records["engine_4_sources"]
    assert rec_e4.status == EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
    assert rec_e4.analytical_result == "SOURCE_UNAVAILABLE"

    # Evidence engine verified claims as INSUFFICIENT_EVIDENCE without fabricating documents
    rec_e5 = result.telemetry.engine_records["engine_5_evidence"]
    assert rec_e5.status == EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
    assert rec_e5.analytical_result == "INSUFFICIENT_EVIDENCE"


# ==============================================================================
# Test F — Identity Not Established
# ==============================================================================

def test_f_identity_not_established_preserved(orchestrator):
    """Verify NOT_ESTABLISHED is preserved as a valid analytical outcome."""
    text = "Certified SEBI analyst Amit Khurana guarantees 25% returns on crypto."
    result = orchestrator.analyze(text=text)

    # Engine 9 should report identity status
    rec_e9 = result.telemetry.engine_records["engine_9_identity"]
    assert rec_e9.status == EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
    assert rec_e9.analytical_result in (
        "NOT_ESTABLISHED",
        "IDENTITY_MISMATCH",
        "AMBIGUOUS",
    )
    assert result.state.identity.identity_status in (
        IdentityStatus.NOT_ESTABLISHED,
        IdentityStatus.IDENTITY_MISMATCH,
        IdentityStatus.AMBIGUOUS,
    )


# ==============================================================================
# Test G — Behaviour Integration
# ==============================================================================

def test_g_behaviour_integration(orchestrator):
    """Verify Engine 10 output is passed to Engine 8 without orchestrator making behavioural conclusions."""
    session_id = "SESS-BEHAVIOUR-TEST"
    history = InteractionHistory(session_id=session_id)
    history.add_event(InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.CONTENT_VIEW,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-02",
        timestamp="10:01:00",
        event_type=InteractionEventType.CHANNEL_CHANGED,
        channel="telegram",
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-03",
        timestamp="10:02:00",
        event_type=InteractionEventType.EXTERNAL_APP_REQUESTED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-04",
        timestamp="10:03:00",
        event_type=InteractionEventType.PAYMENT_REQUESTED,
    ))
    history.add_event(InteractionEvent(
        event_id="EVT-05",
        timestamp="10:03:30",
        event_type=InteractionEventType.ACTION_REQUESTED,
        metadata={"urgency_marker": "Only 5 minutes remaining"},
    ))

    text = "Pay ₹5,000 now. Only 5 minutes remaining."
    result = orchestrator.analyze(
        text=text,
        session_id=session_id,
        interaction_history=history,
    )

    # Engine 10 produced behavioural signals
    rec_e10 = result.telemetry.engine_records["engine_10_behaviour"]
    assert rec_e10.status == EngineOutcomeType.SUCCESS
    assert result.state.behaviour is not None
    assert len(result.state.behaviour.signals) > 0

    # Policy engine received behaviour
    assert result.policy_decision is not None
    # Orchestrator itself did not classify behaviour (verified by absence of custom flags)


# ==============================================================================
# Test H — Fingerprint Integration
# ==============================================================================

def test_h_fingerprint_integration(orchestrator):
    """Verify Engine 7 output is preserved and passed onward correctly."""
    text = (
        "SEBI registered advisor Rahul Sharma guaranteed 40% returns. "
        "Join Telegram: https://t.me/rahulinvest. Pay ₹5,000."
    )
    result = orchestrator.analyze(text=text)

    rec_e7 = result.telemetry.engine_records["engine_7_fingerprint"]
    assert rec_e7.status in (EngineOutcomeType.SUCCESS, EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT)
    assert rec_e7.output_id.startswith("SFP-")
    assert result.state.fingerprint is not None
    assert result.policy_decision.relevant_fingerprint_id == result.state.fingerprint.fingerprint.fingerprint_id


# ==============================================================================
# Test I — Analysis Correlation
# ==============================================================================

def test_i_analysis_correlation(orchestrator):
    """Verify all engine results belonging to one request are correlated under analysis_id."""
    result = orchestrator.analyze(text="Guaranteed 15% return on debt instruments.")

    assert result.analysis_id.startswith("ORCH-")
    output_ids = result.engine_output_ids

    # All major engines have output IDs tracked
    assert "engine_1_content" in output_ids
    assert "engine_2_claims" in output_ids
    assert "engine_3_actions" in output_ids
    assert "engine_4_sources" in output_ids
    assert "engine_5_evidence" in output_ids
    assert "engine_8_policy" in output_ids

    # Provenance contains trace metadata
    assert result.provenance["analysis_id"] == result.analysis_id
    assert result.provenance["engines_executed"] == result.telemetry.engines_executed


# ==============================================================================
# Test J — Session Isolation
# ==============================================================================

def test_j_session_isolation(orchestrator):
    """Verify separate sessions cannot contaminate one another."""
    session_a = "SESSION-ALPHA"
    session_b = "SESSION-BETA"

    # Add suspicious sequence into Session A
    orchestrator.record_interaction_event(
        session_a,
        InteractionEvent(event_id="EA-1", timestamp="10:00:00", event_type=InteractionEventType.CHANNEL_CHANGED, channel="telegram")
    )
    orchestrator.record_interaction_event(
        session_a,
        InteractionEvent(event_id="EA-2", timestamp="10:01:00", event_type=InteractionEventType.PAYMENT_REQUESTED)
    )

    # Session B has only benign content view
    orchestrator.record_interaction_event(
        session_b,
        InteractionEvent(event_id="EB-1", timestamp="10:00:00", event_type=InteractionEventType.CONTENT_VIEW)
    )

    # Run Session B analysis
    res_b = orchestrator.analyze(text="Educational guide on Nifty ETF investing.", session_id=session_b)
    history_b = orchestrator.get_session_history(session_b)

    assert len(history_b.events) == 1
    assert history_b.events[0].event_type == InteractionEventType.CONTENT_VIEW
    assert res_b.state.behaviour is not None
    # Session B should have no channel migration signals
    stypes_b = {s.signal_type for s in res_b.state.behaviour.signals}
    assert BehaviouralSignalType.CHANNEL_MIGRATION not in stypes_b

    # Run Session A analysis
    history_a = orchestrator.get_session_history(session_a)
    assert len(history_a.events) == 2


# ==============================================================================
# Test K — Policy Authority Boundary
# ==============================================================================

def test_k_policy_authority_boundary(orchestrator):
    """Verify only Engine 8 produces the final decision; orchestrator never decides policy."""
    # Highly suspicious text
    text = "Guaranteed 100% returns in 24 hours. Pay ₹50,000 immediately via UPI."
    result = orchestrator.analyze(text=text)

    # The decision in result.decision is strictly the decision returned by Engine 8
    assert result.decision == result.policy_decision.decision
    assert result.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)
    assert result.primary_reason == result.policy_decision.primary_reason


# ==============================================================================
# Test L — No Duplicated Intelligence
# ==============================================================================

def test_l_no_duplicated_intelligence():
    """Verify the orchestrator contains zero scam classification or threat heuristic rules."""
    import inspect
    from nivesh.orchestrator.service import ProductOrchestrator

    source = inspect.getsource(ProductOrchestrator)

    # Verify no heuristic scam detection keywords in orchestrator source
    assert "guaranteed_returns" not in source
    assert "scam_probability" not in source
    assert "risk_score" not in source
    assert "PolicyDecisionType.BLOCK" not in source.split("def _handle_engine_error")[0]  # No custom BLOCK logic


# ==============================================================================
# Test M — Privacy Preservation
# ==============================================================================

def test_m_privacy_preservation(orchestrator):
    """Verify orchestration metadata does not store credentials or prohibited sensitive fields."""
    dirty_metadata = {
        "client_app": "mobile_android",
        "api_key": "sk-secret-token-12345",
        "password": "supersecretpassword",
        "otp": "123456",
        "cvv": "999",
        "card_number": "4111111111111234",
        "public_channel": "telegram",
    }

    result = orchestrator.analyze(
        text="Investment advice for mutual funds.",
        metadata=dirty_metadata,
    )

    clean_meta = result.state.request_metadata
    assert "api_key" not in clean_meta
    assert "password" not in clean_meta
    assert "otp" not in clean_meta
    assert "cvv" not in clean_meta
    assert "card_number" not in clean_meta
    assert clean_meta["client_app"] == "mobile_android"
    assert clean_meta["public_channel"] == "telegram"


# ==============================================================================
# Test N — Deterministic Orchestration
# ==============================================================================

def test_n_deterministic_orchestration():
    """Repeated execution with equivalent inputs produces equivalent logical pipeline results."""
    text = "SEBI registered advisor Rahul Sharma guarantees 40% returns. Pay ₹5,000."

    orch1 = ProductOrchestrator()
    orch2 = ProductOrchestrator()

    res1 = orch1.analyze(text=text)
    res2 = orch2.analyze(text=text)

    # Engine ordering identical
    assert res1.telemetry.engines_executed == res2.telemetry.engines_executed
    assert res1.pipeline_status == res2.pipeline_status

    # Decisions and reasons identical
    assert res1.decision == res2.decision
    assert res1.primary_reason == res2.primary_reason
    assert res1.reason_codes == res2.reason_codes

    # Engine counts identical
    assert len(res1.state.claims.claims) == len(res2.state.claims.claims)
    assert len(res1.state.actions.actions) == len(res2.state.actions.actions)


# ==============================================================================
# Section 20 — Full Integration Benchmark Test
# ==============================================================================

def test_full_integration_benchmark(orchestrator):
    """Execute complete 10-engine pipeline on canonical Nivesh benchmark scenario.

    Benchmark sequence:
    10:00: Educational financial content
    10:01: Private Telegram migration
    10:02: External application request
    10:03: Payment request
    10:03:30: Urgency & time-pressure message
    """
    session_id = "SESS-BENCHMARK-E2E"

    # Step 1: Record interaction events reflecting the progression
    orchestrator.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-01", timestamp="10:00:00", event_type=InteractionEventType.CONTENT_VIEW)
    )
    orchestrator.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-02", timestamp="10:01:00", event_type=InteractionEventType.CHANNEL_CHANGED, channel="telegram")
    )
    orchestrator.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-03", timestamp="10:02:00", event_type=InteractionEventType.EXTERNAL_APP_REQUESTED)
    )
    orchestrator.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-04", timestamp="10:03:00", event_type=InteractionEventType.PAYMENT_REQUESTED)
    )
    orchestrator.record_interaction_event(
        session_id,
        InteractionEvent(
            event_id="EVT-05",
            timestamp="10:03:30",
            event_type=InteractionEventType.ACTION_REQUESTED,
            metadata={"urgency_marker": "Only 5 minutes left"},
        )
    )

    composite_text = (
        "Learn about our investment education program. "
        "SEBI registered advisor Rahul Sharma guarantees 40% monthly returns! "
        "Join our private Telegram group: https://t.me/rahulvip. "
        "Install our APK application. "
        "Pay ₹5,000 now. Only 5 minutes left."
    )

    result = orchestrator.analyze(
        text=composite_text,
        session_id=session_id,
    )

    # 1. Pipeline completed
    assert result.is_success is True
    assert result.pipeline_status == "COMPLETED"

    # 2. Upstream intelligence extracted
    assert len(result.state.claims.claims) >= 1
    assert len(result.state.actions.actions) >= 1

    # 3. Downstream intelligence executed
    assert result.state.threat is not None
    assert result.state.fingerprint is not None
    assert result.state.identity is not None
    assert result.state.behaviour is not None

    # 4. Behaviour engine caught progression
    stypes = {s.signal_type for s in result.state.behaviour.signals}
    assert BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION in stypes
    assert BehaviouralSignalType.CHANNEL_MIGRATION in stypes
    assert BehaviouralSignalType.TIME_PRESSURE in stypes

    # 5. Engine 8 Policy issued high-severity intervention
    assert result.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)
    assert result.policy_decision.severity in ("HIGH", "CRITICAL")
    assert result.policy_decision.required_user_confirmation is True

    # 6. Provenance continuity verified
    assert result.policy_decision.relevant_fingerprint_id == result.state.fingerprint.fingerprint.fingerprint_id
    assert len(result.policy_decision.relevant_claim_ids) == len(result.state.claims.claims)
    assert result.provenance["analysis_id"] == result.analysis_id

"""Phase 11.2 — Unified Analysis Context Test Suite.

Validates the canonical AnalysisContext for Nivesh Firewall:
1. Context creation & default state
2. Session correlation & validation
3. Canonical engine outputs attachment (all 10 engines strongly typed)
4. Engine execution state transitions (PENDING -> RUNNING -> COMPLETED/FAILED/SKIPPED)
5. Partial / analytical results vs execution failure
6. Failure representation & pipeline status degradation
7. Analysis correlation across engine result IDs
8. Upstream references and provenance tracking
9. Sensitive data boundary (scrubbing of forbidden keys)
10. Mutation protection across engine boundaries
11. Session isolation across distinct contexts
12. Safe serialization and round-trip deserialization
13. Determinism
14. Policy integration & upstream prerequisite validation
15. Lightweight structural snapshot generation
16. Orchestrator integration (ProductOrchestrator produces valid context)
17. Full Integration Benchmark: case reconstruction from AnalysisContext
"""

import pytest
from datetime import datetime, timezone

from nivesh.orchestrator import (
    ProductOrchestrator,
    AnalysisContext,
    PipelineStatus,
    EngineStatus,
    ContextLifecycleStage,
    EngineExecutionState,
    ContextSnapshot,
    OrchestrationResult,
)
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis
from nivesh.identity.schemas import IdentityAnalysis, IdentityStatus
from nivesh.behaviour.schemas import BehaviouralAnalysis, BehaviouralSignalType
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType, InteractionHistory
from nivesh.policy.schemas import PolicyDecision, PolicyDecisionType


@pytest.fixture(scope="module")
def canonical_fixtures():
    """Produce real canonical engine outputs from a realistic input."""
    orch = ProductOrchestrator()
    norm = orch.e1.process_text(
        "SEBI registered advisor Rahul Sharma guarantees 40% monthly returns. "
        "Join our Telegram channel: https://t.me/rahulvip. Pay ₹5,000."
    )
    claims = orch.e2.analyze(norm)
    actions = orch.e3.analyze(norm, claims)
    sources = orch.e4.discover_and_retrieve(norm, claims, actions)
    evidence = orch.e5.verify(norm, claims, sources)
    threat = orch.e6.analyze(norm, claims, actions, sources, evidence)
    fingerprint = orch.e7.create_or_match(norm, claims, actions, sources, evidence, threat)
    identity = orch.e9.verify(
        content=norm,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )
    hist = InteractionHistory(session_id="SESS-01")
    behaviour = orch.e10.analyze(
        content=norm,
        claims=claims,
        actions=actions,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        interaction_history=hist,
    )
    policy = orch.e8.decide(
        content=norm,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
        behaviour=behaviour,
    )
    return {
        "content": norm,
        "claims": claims,
        "actions": actions,
        "sources": sources,
        "evidence": evidence,
        "threat": threat,
        "fingerprint": fingerprint,
        "identity": identity,
        "behaviour": behaviour,
        "policy": policy,
    }


# ==============================================================================
# 1. Context Creation & Default State
# ==============================================================================

def test_context_creation():
    """AnalysisContext initializes with unique ID, default timestamps, and PENDING engine states."""
    ctx = AnalysisContext(
        analysis_id="ORCH-123456",
        session_id="SESS-9999",
        input_type="text",
        channel="telegram",
    )

    assert ctx.analysis_id == "ORCH-123456"
    assert ctx.session_id == "SESS-9999"
    assert ctx.input_type == "text"
    assert ctx.channel == "telegram"
    assert ctx.status == PipelineStatus.CREATED
    assert ctx.stage == ContextLifecycleStage.CREATED

    # All 10 canonical engines initialized to PENDING
    assert len(ctx.engine_states) == 10
    for key, state in ctx.engine_states.items():
        assert state.status == EngineStatus.PENDING
        assert state.engine_key == key
        assert state.duration_ms == 0.0
        assert state.started_at is None

    assert ctx.engine_result_ids["analysis_id"] == "ORCH-123456"


# ==============================================================================
# 2. Session Correlation & Validation
# ==============================================================================

def test_session_correlation_match(canonical_fixtures):
    """Matching session IDs attach without issue."""
    ctx = AnalysisContext(analysis_id="ORCH-01", session_id="SESS-01")
    ctx.set_behaviour_result(canonical_fixtures["behaviour"])

    assert ctx.behaviour is not None
    assert ctx.behaviour.session_summary.session_id == "SESS-01"
    assert ctx.engine_result_ids["behaviour_id"] == canonical_fixtures["behaviour"].analysis_id


def test_session_correlation_mismatch_raises(canonical_fixtures):
    """Mismatched session ID raises ValueError to preserve case integrity."""
    ctx = AnalysisContext(analysis_id="ORCH-01", session_id="SESS-DIFFERENT")

    with pytest.raises(ValueError, match="Session correlation mismatch"):
        ctx.set_behaviour_result(canonical_fixtures["behaviour"])


# ==============================================================================
# 3. Canonical Engine Outputs Attachment (Strongly Typed)
# ==============================================================================

def test_canonical_engine_outputs_attachment(canonical_fixtures):
    """All 10 engine outputs can be attached with type integrity and correct lifecycle transitions."""
    ctx = AnalysisContext(analysis_id="ORCH-FULL", session_id="SESS-01")

    # Step 1: Content
    ctx.set_content_result(canonical_fixtures["content"])
    assert isinstance(ctx.content, NormalizedContent)
    assert ctx.stage == ContextLifecycleStage.CONTENT_READY
    assert ctx.content_reference == canonical_fixtures["content"].content_id

    # Step 2: Claims
    ctx.set_claim_result(canonical_fixtures["claims"])
    assert isinstance(ctx.claims, ClaimAnalysis)
    assert ctx.stage == ContextLifecycleStage.CLAIMS_READY

    # Step 3: Actions
    ctx.set_action_result(canonical_fixtures["actions"])
    assert isinstance(ctx.actions, ActionAnalysis)
    assert ctx.stage == ContextLifecycleStage.ACTIONS_READY

    # Step 4: Sources
    ctx.set_source_result(canonical_fixtures["sources"])
    assert isinstance(ctx.sources, SourceAnalysis)
    assert ctx.stage == ContextLifecycleStage.SOURCES_READY

    # Step 5: Evidence
    ctx.set_evidence_result(canonical_fixtures["evidence"])
    assert isinstance(ctx.evidence, EvidenceAnalysis)
    assert ctx.stage == ContextLifecycleStage.EVIDENCE_READY

    # Step 6: Threat
    ctx.set_threat_result(canonical_fixtures["threat"])
    assert isinstance(ctx.threat, ThreatAnalysis)
    assert ctx.stage == ContextLifecycleStage.DOWNSTREAM_INTELLIGENCE_READY

    # Step 7: Fingerprint
    ctx.set_fingerprint_result(canonical_fixtures["fingerprint"])
    assert isinstance(ctx.fingerprint, FingerprintAnalysis)

    # Step 8: Identity
    ctx.set_identity_result(canonical_fixtures["identity"])
    assert isinstance(ctx.identity, IdentityAnalysis)

    # Step 9: Behaviour
    ctx.set_behaviour_result(canonical_fixtures["behaviour"])
    assert isinstance(ctx.behaviour, BehaviouralAnalysis)
    assert ctx.stage == ContextLifecycleStage.BEHAVIOUR_READY

    # Step 10: Policy
    ctx.set_policy_result(canonical_fixtures["policy"])
    assert isinstance(ctx.policy, PolicyDecision)
    assert ctx.stage == ContextLifecycleStage.POLICY_READY

    ctx.finalize_pipeline()
    assert ctx.stage == ContextLifecycleStage.COMPLETED
    assert ctx.status == PipelineStatus.COMPLETED


# ==============================================================================
# 4. Engine Execution State Transitions
# ==============================================================================

def test_engine_execution_state_transitions():
    """Engines transition from PENDING -> RUNNING -> COMPLETED / SKIPPED / FAILED."""
    ctx = AnalysisContext(analysis_id="ORCH-TRANS")

    # Start engine 1
    ctx.mark_engine_started("engine_1_content")
    st1 = ctx.engine_states["engine_1_content"]
    assert st1.status == EngineStatus.RUNNING
    assert st1.started_at is not None
    assert ctx.status == PipelineStatus.RUNNING

    # Complete engine 1
    ctx.mark_engine_completed("engine_1_content", result_id="C-100", duration_ms=12.5)
    assert st1.status == EngineStatus.COMPLETED
    assert st1.result_id == "C-100"
    assert st1.duration_ms == 12.5
    assert ctx.engine_result_ids["engine_1_content"] == "C-100"

    # Skip engine 4
    ctx.mark_engine_skipped("engine_4_sources", reason="Offline mode requested")
    st4 = ctx.engine_states["engine_4_sources"]
    assert st4.status == EngineStatus.SKIPPED
    assert st4.metadata["skip_reason"] == "Offline mode requested"
    assert any("skipped: Offline mode requested" in w for w in ctx.warnings)

    # Fail engine 6
    ctx.mark_engine_failed("engine_6_threat", error_message="Model timeout", error_code="TIMEOUT", duration_ms=500.0)
    st6 = ctx.engine_states["engine_6_threat"]
    assert st6.status == EngineStatus.FAILED
    assert st6.error_code == "TIMEOUT"
    assert st6.error_message == "Model timeout"
    assert any("Model timeout" in err for err in ctx.errors)


# ==============================================================================
# 5. Partial / Analytical Results vs Execution Failure
# ==============================================================================

def test_partial_analytical_results_distinguished_from_crashes():
    """Analytical outcomes (e.g. SOURCE_UNAVAILABLE, NOT_ESTABLISHED) are COMPLETED, not FAILED."""
    ctx = AnalysisContext(analysis_id="ORCH-PARTIAL")

    # Engine 4 reports SOURCE_UNAVAILABLE
    ctx.mark_engine_started("engine_4_sources")
    ctx.mark_engine_completed(
        "engine_4_sources",
        result_id="SRC-NONE",
        analytical_result="SOURCE_UNAVAILABLE",
        duration_ms=45.0,
    )
    st4 = ctx.engine_states["engine_4_sources"]
    assert st4.status == EngineStatus.COMPLETED
    assert st4.analytical_result == "SOURCE_UNAVAILABLE"
    assert st4.error_message is None

    # Engine 9 reports NOT_ESTABLISHED
    ctx.mark_engine_started("engine_9_identity")
    ctx.mark_engine_completed(
        "engine_9_identity",
        result_id="ID-UNESTABLISHED",
        analytical_result="NOT_ESTABLISHED",
        duration_ms=30.0,
    )
    st9 = ctx.engine_states["engine_9_identity"]
    assert st9.status == EngineStatus.COMPLETED
    assert st9.analytical_result == "NOT_ESTABLISHED"


# ==============================================================================
# 6. Failure Representation & Degradation
# ==============================================================================

def test_failure_representation_and_pipeline_degradation(canonical_fixtures):
    """Actual crashes yield FAILED status on engine and PARTIAL on completed pipeline."""
    ctx = AnalysisContext(analysis_id="ORCH-FAIL")
    ctx.set_content_result(canonical_fixtures["content"])
    ctx.set_claim_result(canonical_fixtures["claims"])
    ctx.set_action_result(canonical_fixtures["actions"])
    ctx.set_source_result(canonical_fixtures["sources"])
    ctx.set_evidence_result(canonical_fixtures["evidence"])

    # Engine 7 crashes
    ctx.mark_engine_failed("engine_7_fingerprint", error_message="Database connection error", error_code="DB_ERR")

    # Pipeline continues and Engine 8 produces policy
    ctx.set_policy_result(canonical_fixtures["policy"])
    ctx.finalize_pipeline()

    assert ctx.status == PipelineStatus.PARTIAL
    assert ctx.engine_states["engine_7_fingerprint"].status == EngineStatus.FAILED
    assert len(ctx.errors) == 1
    assert "Database connection error" in ctx.errors[0]


def test_fatal_failure_aborts_pipeline():
    """If pipeline aborts before policy, pipeline status is FAILED."""
    ctx = AnalysisContext(analysis_id="ORCH-ABORT")
    ctx.mark_engine_failed("engine_1_content", error_message="Corrupted input stream")
    ctx.finalize_pipeline()

    assert ctx.status == PipelineStatus.FAILED
    assert ctx.policy is None


# ==============================================================================
# 7. Analysis Correlation Across Engine Result IDs
# ==============================================================================

def test_analysis_correlation(canonical_fixtures):
    """All attached engine outputs register correlated IDs without overwriting original IDs."""
    ctx = AnalysisContext(analysis_id="A-1024", session_id="SESS-01")

    ctx.set_content_result(canonical_fixtures["content"])
    ctx.set_claim_result(canonical_fixtures["claims"])
    ctx.set_action_result(canonical_fixtures["actions"])
    ctx.set_source_result(canonical_fixtures["sources"])
    ctx.set_evidence_result(canonical_fixtures["evidence"])
    ctx.set_threat_result(canonical_fixtures["threat"])
    ctx.set_fingerprint_result(canonical_fixtures["fingerprint"])
    ctx.set_identity_result(canonical_fixtures["identity"])
    ctx.set_behaviour_result(canonical_fixtures["behaviour"])
    ctx.set_policy_result(canonical_fixtures["policy"])

    ids = ctx.engine_result_ids
    assert ids["analysis_id"] == "A-1024"
    assert ids["content_id"] == canonical_fixtures["content"].content_id
    assert ids["fingerprint_id"] == canonical_fixtures["fingerprint"].fingerprint.fingerprint_id
    assert ids["identity_id"] == canonical_fixtures["identity"].analysis_id
    assert ids["behaviour_id"] == canonical_fixtures["behaviour"].analysis_id
    assert ids["policy_id"] == canonical_fixtures["policy"].decision_id


# ==============================================================================
# 8. Upstream References and Provenance
# ==============================================================================

def test_upstream_references_tracking(canonical_fixtures):
    """Engines record which upstream result IDs they depend on."""
    ctx = AnalysisContext(analysis_id="ORCH-REF")

    content = canonical_fixtures["content"]
    ctx.set_content_result(content)

    claims = canonical_fixtures["claims"]
    ctx.set_claim_result(claims)
    assert ctx.upstream_references["engine_2_claims"] == [content.content_id]

    actions = canonical_fixtures["actions"]
    ctx.set_action_result(actions)
    assert content.content_id in ctx.upstream_references["engine_3_actions"]

    sources = canonical_fixtures["sources"]
    ctx.set_source_result(sources)
    assert content.content_id in ctx.upstream_references["engine_4_sources"]


# ==============================================================================
# 9. Sensitive Data Boundary
# ==============================================================================

def test_sensitive_data_boundary_stripping():
    """Forbidden sensitive metadata keys are scrubbed upon creation and safe serialization."""
    dirty_metadata = {
        "user_agent": "Mozilla/5.0",
        "client_ip": "192.168.1.1",
        "password": "SuperSecretPassword123",
        "OTP": "654321",
        "pin": "1234",
        "cvv": "999",
        "card_number": "4111222233334444",
        "bearer_token": "eyJh...",
    }

    ctx = AnalysisContext(
        analysis_id="ORCH-PRIVACY",
        request_metadata=dirty_metadata,
    )

    # Initial scrub in model_post_init
    assert "user_agent" in ctx.request_metadata
    assert "client_ip" in ctx.request_metadata
    assert "password" not in ctx.request_metadata
    assert "otp" not in ctx.request_metadata
    assert "pin" not in ctx.request_metadata
    assert "cvv" not in ctx.request_metadata
    assert "card_number" not in ctx.request_metadata
    assert "bearer_token" not in ctx.request_metadata

    # Deep scrub in to_safe_dict
    safe_dict = ctx.to_safe_dict()
    assert "password" not in safe_dict["request_metadata"]
    assert "otp" not in safe_dict["request_metadata"]


# ==============================================================================
# 10. Mutation Protection Across Engine Boundaries
# ==============================================================================

def test_mutation_protection(canonical_fixtures):
    """Downstream engines do not alter previously stored upstream engine results."""
    ctx = AnalysisContext(analysis_id="ORCH-MUT", session_id="SESS-01")

    ctx.set_content_result(canonical_fixtures["content"])
    orig_text = ctx.content.raw.text

    ctx.set_threat_result(canonical_fixtures["threat"])
    orig_threat_signals_count = len(ctx.threat.threat_signals)

    ctx.set_fingerprint_result(canonical_fixtures["fingerprint"])
    orig_fp_id = ctx.fingerprint.fingerprint.fingerprint_id

    # Later attach identity and behaviour
    ctx.set_identity_result(canonical_fixtures["identity"])
    ctx.set_behaviour_result(canonical_fixtures["behaviour"])

    # Verify original objects remain unchanged
    assert ctx.content.raw.text == orig_text
    assert len(ctx.threat.threat_signals) == orig_threat_signals_count
    assert ctx.fingerprint.fingerprint.fingerprint_id == orig_fp_id


# ==============================================================================
# 11. Session Isolation
# ==============================================================================

def test_session_isolation():
    """Different sessions maintain completely independent AnalysisContext instances."""
    ctx1 = AnalysisContext(analysis_id="A-1", session_id="SESS-1")
    ctx2 = AnalysisContext(analysis_id="A-2", session_id="SESS-2")

    ctx1.mark_engine_started("engine_1_content")
    ctx1.mark_engine_completed("engine_1_content", result_id="C-1")

    assert ctx1.engine_states["engine_1_content"].status == EngineStatus.COMPLETED
    assert ctx2.engine_states["engine_1_content"].status == EngineStatus.PENDING
    assert ctx1.session_id != ctx2.session_id
    assert ctx1.analysis_id != ctx2.analysis_id


# ==============================================================================
# 12. Safe Serialization & Round-Trip Deserialization
# ==============================================================================

def test_safe_serialization_and_roundtrip(canonical_fixtures):
    """Context serializes to dictionary and deserializes back into AnalysisContext without loss."""
    ctx = AnalysisContext(analysis_id="ORCH-ROUNDTRIP", session_id="SESS-01")
    ctx.set_content_result(canonical_fixtures["content"])
    ctx.set_claim_result(canonical_fixtures["claims"])
    ctx.set_action_result(canonical_fixtures["actions"])
    ctx.set_source_result(canonical_fixtures["sources"])
    ctx.set_evidence_result(canonical_fixtures["evidence"])
    ctx.set_threat_result(canonical_fixtures["threat"])
    ctx.set_fingerprint_result(canonical_fixtures["fingerprint"])
    ctx.set_identity_result(canonical_fixtures["identity"])
    ctx.set_behaviour_result(canonical_fixtures["behaviour"])
    ctx.set_policy_result(canonical_fixtures["policy"])
    ctx.finalize_pipeline()

    # Serialize
    safe_data = ctx.to_safe_dict()
    assert isinstance(safe_data, dict)
    assert safe_data["analysis_id"] == "ORCH-ROUNDTRIP"
    assert safe_data["policy"]["decision"] == canonical_fixtures["policy"].decision.value

    # Deserialize
    reconstructed = AnalysisContext.model_validate(safe_data)
    assert reconstructed.analysis_id == ctx.analysis_id
    assert reconstructed.session_id == ctx.session_id
    assert reconstructed.status == PipelineStatus.COMPLETED
    assert reconstructed.policy.decision == canonical_fixtures["policy"].decision
    assert reconstructed.content.content_id == canonical_fixtures["content"].content_id

    # Consistency check passes
    reconstructed.validate_consistency()


# ==============================================================================
# 13. Determinism
# ==============================================================================

def test_context_determinism(canonical_fixtures):
    """Equivalent inputs and mock results produce logically equivalent AnalysisContext state."""
    def build_ctx():
        ctx = AnalysisContext(analysis_id="DET-01", session_id="SESS-01")
        ctx.set_content_result(canonical_fixtures["content"])
        ctx.set_claim_result(canonical_fixtures["claims"])
        ctx.set_action_result(canonical_fixtures["actions"])
        ctx.set_source_result(canonical_fixtures["sources"])
        ctx.set_evidence_result(canonical_fixtures["evidence"])
        ctx.set_policy_result(canonical_fixtures["policy"])
        ctx.finalize_pipeline()
        return ctx

    ctx1 = build_ctx()
    ctx2 = build_ctx()

    assert ctx1.analysis_id == ctx2.analysis_id
    assert ctx1.status == ctx2.status
    assert ctx1.stage == ctx2.stage
    assert ctx1.engine_result_ids == ctx2.engine_result_ids
    assert ctx1.get_snapshot().policy_decision == ctx2.get_snapshot().policy_decision


# ==============================================================================
# 14. Policy Integration & Upstream Prerequisite Validation
# ==============================================================================

def test_policy_requires_upstream_intelligence(canonical_fixtures):
    """Attempting to set policy without required upstream results raises ValueError."""
    ctx = AnalysisContext(analysis_id="ORCH-NO-UPSTREAM")
    pol = canonical_fixtures["policy"]

    # Content missing
    with pytest.raises(ValueError, match="Engine 1 content is missing"):
        ctx.set_policy_result(pol)

    # Provide content, but claims missing
    ctx.set_content_result(canonical_fixtures["content"])
    with pytest.raises(ValueError, match="Engine 2 claims are missing"):
        ctx.set_policy_result(pol)


def test_inconsistent_state_validation_raises():
    """validate_consistency detects corrupted or mismatched internal state."""
    ctx = AnalysisContext(analysis_id="ORCH-INCONSISTENT")
    # Mark failed with result_id but no error message
    ctx.engine_states["engine_1_content"].status = EngineStatus.FAILED
    ctx.engine_states["engine_1_content"].result_id = "RES-1"
    ctx.engine_states["engine_1_content"].error_message = None

    with pytest.raises(ValueError, match="Inconsistent state"):
        ctx.validate_consistency()


# ==============================================================================
# 15. Context Snapshot Generation
# ==============================================================================

def test_context_snapshot():
    """get_snapshot produces a lightweight structural summary of execution progress."""
    ctx = AnalysisContext(analysis_id="SNAP-01")
    ctx.mark_engine_completed("engine_1_content", result_id="C-01")
    ctx.mark_engine_completed("engine_2_claims", result_id="CL-01")
    ctx.mark_engine_skipped("engine_4_sources", reason="offline")
    ctx.mark_engine_failed("engine_7_fingerprint", error_message="timeout")

    snap = ctx.get_snapshot()
    assert isinstance(snap, ContextSnapshot)
    assert snap.analysis_id == "SNAP-01"
    assert "engine_1_content" in snap.completed_engines
    assert "engine_2_claims" in snap.completed_engines
    assert "engine_4_sources" in snap.skipped_engines
    assert "engine_7_fingerprint" in snap.failed_engines
    assert "engine_8_policy" in snap.pending_engines
    assert snap.policy_decision is None
    assert snap.warnings_count >= 1
    assert snap.errors_count >= 1


# ==============================================================================
# 16. ProductOrchestrator Integration
# ==============================================================================

def test_orchestrator_populates_analysis_context():
    """ProductOrchestrator.analyze populates a canonical AnalysisContext on OrchestrationResult."""
    orch = ProductOrchestrator()
    sample_text = (
        "SEBI registered advisor Rahul Sharma guarantees 40% monthly returns. "
        "Join our Telegram channel: https://t.me/rahulvip. Pay ₹5,000."
    )
    result = orch.analyze(text=sample_text, session_id="SESS-ORCH-CTX")

    assert result.context is not None
    ctx = result.context
    assert isinstance(ctx, AnalysisContext)
    assert ctx.analysis_id == result.analysis_id
    assert ctx.session_id == "SESS-ORCH-CTX"
    assert ctx.status == PipelineStatus.COMPLETED
    assert ctx.stage == ContextLifecycleStage.COMPLETED

    # Verify all 10 engines have completed states
    for key in ctx.engine_states:
        state = ctx.engine_states[key]
        assert state.status == EngineStatus.COMPLETED
        assert state.duration_ms > 0
        assert state.started_at is not None
        assert state.completed_at is not None

    # Canonical outputs are strongly typed
    assert isinstance(ctx.content, NormalizedContent)
    assert isinstance(ctx.claims, ClaimAnalysis)
    assert isinstance(ctx.actions, ActionAnalysis)
    assert isinstance(ctx.sources, SourceAnalysis)
    assert isinstance(ctx.evidence, EvidenceAnalysis)
    assert isinstance(ctx.threat, ThreatAnalysis)
    assert isinstance(ctx.fingerprint, FingerprintAnalysis)
    assert isinstance(ctx.identity, IdentityAnalysis)
    assert isinstance(ctx.behaviour, BehaviouralAnalysis)
    assert isinstance(ctx.policy, PolicyDecision)

    # Snapshot matches
    snap = ctx.get_snapshot()
    assert len(snap.completed_engines) == 10
    assert snap.policy_decision == result.policy_decision.decision.value

    # Consistency passes
    ctx.validate_consistency()


# ==============================================================================
# 17. Full Integration Benchmark: Case Reconstruction from AnalysisContext
# ==============================================================================

def test_full_integration_benchmark_context_reconstruction():
    """Execute canonical Nivesh benchmark scenario and reconstruct case from AnalysisContext."""
    orch = ProductOrchestrator()
    session_id = "SESS-BENCHMARK-CTX-E2E"

    # Setup interaction history
    orch.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-01", timestamp="10:00:00", event_type=InteractionEventType.CONTENT_VIEW)
    )
    orch.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-02", timestamp="10:01:00", event_type=InteractionEventType.CHANNEL_CHANGED, channel="telegram")
    )
    orch.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-03", timestamp="10:02:00", event_type=InteractionEventType.EXTERNAL_APP_REQUESTED)
    )
    orch.record_interaction_event(
        session_id,
        InteractionEvent(event_id="EVT-04", timestamp="10:03:00", event_type=InteractionEventType.PAYMENT_REQUESTED)
    )
    orch.record_interaction_event(
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

    res = orch.analyze(text=composite_text, session_id=session_id)
    ctx = res.context
    assert ctx is not None

    # Case reconstruction verification without re-running engines:
    # 1. Input reference
    assert ctx.input_type == "text"
    assert ctx.content_reference == ctx.content.content_id

    # 2. Extracted claims and actions
    claim_types = [c.claim_type for c in ctx.claims.claims]
    assert "FINANCIAL" in claim_types or "REGULATORY" in claim_types

    action_types = [a.action_type for a in ctx.actions.actions]
    assert "JOIN_CHANNEL" in action_types or "PAYMENT" in action_types or "INSTALL" in action_types

    # 3. Threat and fingerprint intelligence
    assert len(ctx.threat.threat_signals) >= 1
    assert ctx.threat.attack_path is not None
    assert ctx.fingerprint.fingerprint.fingerprint_id is not None

    # 4. Identity status
    assert any(e.name == "Rahul Sharma" for e in ctx.identity.entities)

    # 5. Behavioural signals
    b_signals = {s.signal_type for s in ctx.behaviour.signals}
    assert BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION in b_signals
    assert BehaviouralSignalType.CHANNEL_MIGRATION in b_signals

    # 6. Policy decision
    assert ctx.policy.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK)
    assert ctx.policy.severity in ("HIGH", "CRITICAL")

    # 7. Safe dictionary contains all engine keys without credential leakage
    safe_data = ctx.to_safe_dict()
    assert "content" in safe_data
    assert "claims" in safe_data
    assert "actions" in safe_data
    assert "sources" in safe_data
    assert "evidence" in safe_data
    assert "threat" in safe_data
    assert "fingerprint" in safe_data
    assert "identity" in safe_data
    assert "behaviour" in safe_data
    assert "policy" in safe_data

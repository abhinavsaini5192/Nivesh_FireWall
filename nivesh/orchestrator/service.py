"""Canonical Product Orchestrator Service for Nivesh Firewall.

Coordinates all 10 intelligence engines into a unified analysis pipeline:
1. Ingests raw multi-modal input through Engine 1.
2. Segments and canonicalizes assertions through Engine 2.
3. Structures and categorizes requested actions through Engine 3.
4. Retrieves authoritative sources and filings through Engine 4.
5. Verifies claim-evidence relationships through Engine 5.
6. Analyzes multi-stage attack paths through Engine 6.
7. Generates structural fingerprints and matches through Engine 7.
8. Resolves entity identities and authority claims through Engine 9.
9. Analyzes behavioural sequences and temporal pressure through Engine 10.
10. Evaluates all collected intelligence through Engine 8 (sole policy authority).

Does NOT duplicate engine logic. Does NOT create an Engine 11.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Literal

from nivesh.engine import ContentIntelligenceEngine, ENGINE_VERSION as E1_VERSION
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import IdentityStatus
from nivesh.behaviour.engine import BehaviouralSignalEngine
from nivesh.behaviour.event_model import InteractionEvent, InteractionHistory
from nivesh.policy.engine import PolicyInterventionEngine, POLICY_VERSION as E8_VERSION
from nivesh.policy.schemas import PolicyContext

from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata
from nivesh.schemas.evidence import EvidenceAnalysis, EvidenceAnalysisMetadata
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import (
    FingerprintAnalysis,
    ScamFingerprint,
    FingerprintObservation,
    FingerprintProvenance,
)

from .config import OrchestratorConfig
from .errors import (
    EngineOutcomeType,
    FatalOrchestrationError,
    InputIngestionError,
)
from .telemetry import EngineExecutionRecord, PipelineTelemetry
from .state import OrchestrationState
from .result import OrchestrationResult
from .context import (
    AnalysisContext,
    PipelineStatus,
    EngineStatus,
    ContextLifecycleStage,
)


class ProductOrchestrator:
    """Central product orchestrator coordinating Nivesh Firewall intelligence engines."""

    def __init__(
        self,
        engines: Optional[dict[str, Any]] = None,
        config: Optional[OrchestratorConfig] = None,
    ):
        """Initialize the product orchestrator with optional dependency injection.

        Args:
            engines: Optional mapping of engine overrides for testing or custom adapters.
            config: Optional orchestration configuration (timeouts, modes, fail-fast).
        """
        self.config = config or OrchestratorConfig()
        injected = engines or {}

        # Initialize or inject canonical engines
        self.e1: ContentIntelligenceEngine = injected.get("engine_1") or ContentIntelligenceEngine()
        self.e2: ClaimIntelligenceEngine = injected.get("engine_2") or ClaimIntelligenceEngine()
        self.e3: ActionIntelligenceEngine = injected.get("engine_3") or ActionIntelligenceEngine()
        self.e4: SourceIntelligenceEngine = injected.get("engine_4") or SourceIntelligenceEngine(
            default_mode=self.config.source_mode
        )
        self.e5: EvidenceVerificationEngine = injected.get("engine_5") or EvidenceVerificationEngine()
        self.e6: ThreatIntelligenceEngine = injected.get("engine_6") or ThreatIntelligenceEngine()
        self.e7: ScamFingerprintEngine = injected.get("engine_7") or ScamFingerprintEngine()
        self.e9: IdentityVerificationEngine = injected.get("engine_9") or IdentityVerificationEngine()
        self.e10: BehaviouralSignalEngine = injected.get("engine_10") or BehaviouralSignalEngine()
        self.e8: PolicyInterventionEngine = injected.get("engine_8") or PolicyInterventionEngine()

    def record_interaction_event(
        self, session_id: str, event: InteractionEvent
    ) -> InteractionHistory:
        """Record an observable interaction event into Engine 10's session tracker."""
        return self.e10.record_event(session_id, event)

    def get_session_history(self, session_id: str) -> Optional[InteractionHistory]:
        """Retrieve recorded session interaction history by session ID."""
        return self.e10.get_session(session_id)

    def analyze(
        self,
        text: Optional[str] = None,
        url: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
        session_id: Optional[str] = None,
        interaction_history: Optional[InteractionHistory] = None,
        metadata: Optional[dict[str, Any]] = None,
        channel: str = "unknown",
        policy_context: Optional[PolicyContext] = None,
    ) -> OrchestrationResult:
        """Execute a complete end-to-end Nivesh Firewall analysis.

        Coordinates Engines 1 through 10 in canonical dependency order,
        records telemetry, isolates failures, and returns a unified OrchestrationResult.
        """
        pipe_start_perf = time.perf_counter()
        started_at_iso = datetime.now(timezone.utc).isoformat()
        analysis_id = f"ORCH-{uuid.uuid4().hex[:12].upper()}"

        # Initialize shared execution state & unified analysis context
        input_type = "text" if text is not None else "url" if url is not None else "image"
        context = AnalysisContext(
            analysis_id=analysis_id,
            session_id=session_id,
            input_type=input_type,
            channel=channel,
            request_metadata=metadata or {},
            created_at=started_at_iso,
            updated_at=started_at_iso,
            status=PipelineStatus.RUNNING,
        )

        state = OrchestrationState(
            analysis_id=analysis_id,
            session_id=session_id,
            request_metadata=metadata or {},
            started_at=started_at_iso,
            status="RUNNING",
        )
        telemetry = state.telemetry
        telemetry.started_at = started_at_iso

        # ----------------------------------------------------------------------
        # Step 1: Engine 1 — Content Intelligence
        # ----------------------------------------------------------------------
        context.mark_engine_started("engine_1_content")
        t0 = time.perf_counter()
        rec_e1 = EngineExecutionRecord(
            engine_name="Engine 1: Content Intelligence Engine",
            engine_key="engine_1_content",
            engine_version=E1_VERSION,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            if text is not None:
                content = self.e1.process_text(text, channel=channel)
            elif url is not None:
                content = self.e1.process_url(url, channel=channel)
            elif image_bytes is not None or image_path is not None:
                content = self.e1.process_image(
                    image_bytes=image_bytes, image_path=image_path, channel=channel
                )
            else:
                raise InputIngestionError("No valid input provided. Specify text, url, or image.")

            if content.status == "error":
                raise InputIngestionError(f"Engine 1 failed to process content: {content.error_message}")

            # Attach session_id to content metadata if provided
            if session_id and hasattr(content, "metadata") and content.metadata is not None:
                content.metadata["session_id"] = session_id

            state.content = content
            rec_e1.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e1.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e1.status = EngineOutcomeType.SUCCESS
            rec_e1.output_id = content.content_id
            telemetry.record_engine(rec_e1)

            context.set_content_result(content)
            context.mark_engine_completed(
                "engine_1_content",
                result_id=content.content_id,
                duration_ms=rec_e1.duration_ms,
            )
        except Exception as e:
            rec_e1.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e1.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e1.status = EngineOutcomeType.FATAL_FAILURE
            rec_e1.error_type = type(e).__name__
            rec_e1.error_message = str(e)
            telemetry.record_engine(rec_e1)
            state.status = "FAILED"
            state.errors.append(f"Engine 1 Fatal Failure: {e}")
            state.completed_at = datetime.now(timezone.utc).isoformat()
            telemetry.completed_at = state.completed_at
            telemetry.total_duration_ms = round((time.perf_counter() - pipe_start_perf) * 1000, 2)
            context.mark_engine_failed("engine_1_content", str(e), duration_ms=rec_e1.duration_ms)
            context.finalize_pipeline()
            raise FatalOrchestrationError(f"Engine 1 failed: {e}", engine_name="engine_1_content") from e

        # ----------------------------------------------------------------------
        # Step 2: Engine 2 — Claim Intelligence
        # ----------------------------------------------------------------------
        context.mark_engine_started("engine_2_claims")
        t0 = time.perf_counter()
        rec_e2 = EngineExecutionRecord(
            engine_name="Engine 2: Claim Intelligence Engine",
            engine_key="engine_2_claims",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            claims = self.e2.analyze(state.content)
            state.claims = claims
            rec_e2.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e2.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e2.status = EngineOutcomeType.SUCCESS
            rec_e2.output_id = getattr(claims, "analysis_id", getattr(claims, "content_id", None))
            rec_e2.metadata["claim_count"] = len(claims.claims)
            telemetry.record_engine(rec_e2)

            context.set_claim_result(claims)
            context.mark_engine_completed(
                "engine_2_claims",
                result_id=rec_e2.output_id,
                duration_ms=rec_e2.duration_ms,
                metadata=rec_e2.metadata,
            )
        except Exception as e:
            self._handle_engine_error("engine_2_claims", rec_e2, t0, e, state)
            if state.claims is None and state.content is not None:
                state.claims = ClaimAnalysis(content_id=state.content.content_id, claims=[])
            context.mark_engine_failed("engine_2_claims", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
            if state.claims:
                context.set_claim_result(state.claims)

        # ----------------------------------------------------------------------
        # Step 3: Engine 3 — Action Intelligence
        # ----------------------------------------------------------------------
        context.mark_engine_started("engine_3_actions")
        t0 = time.perf_counter()
        rec_e3 = EngineExecutionRecord(
            engine_name="Engine 3: Action Intelligence Engine",
            engine_key="engine_3_actions",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            actions = self.e3.analyze(state.content, state.claims)
            state.actions = actions
            rec_e3.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e3.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e3.status = EngineOutcomeType.SUCCESS
            rec_e3.output_id = getattr(actions, "analysis_id", getattr(actions, "content_id", None))
            rec_e3.metadata["action_count"] = len(actions.actions)
            telemetry.record_engine(rec_e3)

            context.set_action_result(actions)
            context.mark_engine_completed(
                "engine_3_actions",
                result_id=rec_e3.output_id,
                duration_ms=rec_e3.duration_ms,
                metadata=rec_e3.metadata,
            )
        except Exception as e:
            self._handle_engine_error("engine_3_actions", rec_e3, t0, e, state)
            if state.actions is None and state.content is not None:
                state.actions = ActionAnalysis(content_id=state.content.content_id, actions=[])
            context.mark_engine_failed("engine_3_actions", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
            if state.actions:
                context.set_action_result(state.actions)

        # ----------------------------------------------------------------------
        # Step 4: Engine 4 — Source Intelligence
        # ----------------------------------------------------------------------
        context.mark_engine_started("engine_4_sources")
        t0 = time.perf_counter()
        rec_e4 = EngineExecutionRecord(
            engine_name="Engine 4: Source Intelligence Engine",
            engine_key="engine_4_sources",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            sources = self.e4.discover_and_retrieve(state.content, state.claims, state.actions)
            state.sources = sources
            rec_e4.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e4.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e4.output_id = getattr(sources, "analysis_id", getattr(sources, "content_id", None))
            total_docs = sum(len(getattr(cs, "documents", [])) for cs in getattr(sources, "claim_sources", []))
            total_candidates = sum(len(getattr(cs, "evidence_candidates", [])) for cs in getattr(sources, "claim_sources", []))
            rec_e4.metadata["source_count"] = total_docs
            rec_e4.metadata["candidate_count"] = total_candidates

            # Classify analytical outcomes vs errors
            retrieval_failures = getattr(getattr(sources, "analysis_metadata", None), "retrieval_failures", 0)
            if total_docs == 0:
                rec_e4.status = EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
                rec_e4.analytical_result = "SOURCE_UNAVAILABLE"
            else:
                rec_e4.status = EngineOutcomeType.SUCCESS
            telemetry.record_engine(rec_e4)

            context.set_source_result(sources)
            context.mark_engine_completed(
                "engine_4_sources",
                result_id=rec_e4.output_id,
                analytical_result=rec_e4.analytical_result,
                duration_ms=rec_e4.duration_ms,
                metadata=rec_e4.metadata,
            )
        except Exception as e:
            self._handle_engine_error("engine_4_sources", rec_e4, t0, e, state)
            if state.sources is None and state.content is not None:
                state.sources = SourceAnalysis(
                    content_id=state.content.content_id,
                    claim_sources=[],
                    analysis_metadata=SourceAnalysisMetadata(retrieval_failures=1),
                )
            context.mark_engine_failed("engine_4_sources", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
            if state.sources:
                context.set_source_result(state.sources)

        # ----------------------------------------------------------------------
        # Step 5: Engine 5 — Evidence Verification
        # ----------------------------------------------------------------------
        context.mark_engine_started("engine_5_evidence")
        t0 = time.perf_counter()
        rec_e5 = EngineExecutionRecord(
            engine_name="Engine 5: Evidence Verification Engine",
            engine_key="engine_5_evidence",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            evidence = self.e5.verify(state.content, state.claims, state.sources)
            state.evidence = evidence
            rec_e5.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e5.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e5.output_id = getattr(evidence, "analysis_id", getattr(evidence, "content_id", None))
            rec_e5.metadata["verification_count"] = len(evidence.verifications)

            # Check if verifications contain analytical outcomes
            has_insufficient = any(
                getattr(v, "status", None) == "INSUFFICIENT_EVIDENCE" for v in evidence.verifications
            )
            if has_insufficient:
                rec_e5.status = EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
                rec_e5.analytical_result = "INSUFFICIENT_EVIDENCE"
            else:
                rec_e5.status = EngineOutcomeType.SUCCESS
            telemetry.record_engine(rec_e5)

            context.set_evidence_result(evidence)
            context.mark_engine_completed(
                "engine_5_evidence",
                result_id=rec_e5.output_id,
                analytical_result=rec_e5.analytical_result,
                duration_ms=rec_e5.duration_ms,
                metadata=rec_e5.metadata,
            )
        except Exception as e:
            self._handle_engine_error("engine_5_evidence", rec_e5, t0, e, state)
            if state.evidence is None and state.content is not None:
                state.evidence = EvidenceAnalysis(
                    content_id=state.content.content_id,
                    verifications=[],
                    analysis_metadata=EvidenceAnalysisMetadata(),
                )
            context.mark_engine_failed("engine_5_evidence", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
            if state.evidence:
                context.set_evidence_result(state.evidence)

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 6 — Threat Intelligence
        # ----------------------------------------------------------------------
        if self.config.enable_threat:
            context.mark_engine_started("engine_6_threat")
            t0 = time.perf_counter()
            rec_e6 = EngineExecutionRecord(
                engine_name="Engine 6: Threat & Attack-Path Intelligence",
                engine_key="engine_6_threat",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                threat = self.e6.analyze(
                    state.content, state.claims, state.actions, state.sources, state.evidence
                )
                state.threat = threat
                rec_e6.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e6.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                rec_e6.status = EngineOutcomeType.SUCCESS
                rec_e6.output_id = threat.content_id
                rec_e6.metadata["threat_signal_count"] = len(threat.threat_signals)
                telemetry.record_engine(rec_e6)

                context.set_threat_result(threat)
                context.mark_engine_completed(
                    "engine_6_threat",
                    result_id=threat.content_id,
                    duration_ms=rec_e6.duration_ms,
                    metadata=rec_e6.metadata,
                )
            except Exception as e:
                self._handle_engine_error("engine_6_threat", rec_e6, t0, e, state)
                if state.threat is None and state.content is not None:
                    state.threat = ThreatAnalysis(content_id=state.content.content_id)
                context.mark_engine_failed("engine_6_threat", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        else:
            context.mark_engine_skipped("engine_6_threat", "Disabled in orchestrator config")

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 7 — Scam Fingerprint Intelligence
        # ----------------------------------------------------------------------
        if self.config.enable_fingerprint and state.threat is not None:
            context.mark_engine_started("engine_7_fingerprint")
            t0 = time.perf_counter()
            rec_e7 = EngineExecutionRecord(
                engine_name="Engine 7: Scam Fingerprint & Collective Intelligence",
                engine_key="engine_7_fingerprint",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                fingerprint = self.e7.create_or_match(
                    state.content, state.claims, state.actions, state.sources, state.evidence, state.threat
                )
                state.fingerprint = fingerprint
                rec_e7.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e7.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                rec_e7.output_id = fingerprint.fingerprint.fingerprint_id
                rec_e7.metadata["match_type"] = str(fingerprint.match_type)

                if fingerprint.match_type == "NO_MATCH":
                    rec_e7.status = EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
                    rec_e7.analytical_result = "NO_MATCH"
                else:
                    rec_e7.status = EngineOutcomeType.SUCCESS
                telemetry.record_engine(rec_e7)

                context.set_fingerprint_result(fingerprint)
                context.mark_engine_completed(
                    "engine_7_fingerprint",
                    result_id=fingerprint.fingerprint.fingerprint_id,
                    analytical_result=rec_e7.analytical_result,
                    duration_ms=rec_e7.duration_ms,
                    metadata=rec_e7.metadata,
                )
            except Exception as e:
                self._handle_engine_error("engine_7_fingerprint", rec_e7, t0, e, state)
                context.mark_engine_failed("engine_7_fingerprint", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        else:
            context.mark_engine_skipped("engine_7_fingerprint", "Skipped or threat analysis unavailable")

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 9 — Identity Verification
        # ----------------------------------------------------------------------
        if self.config.enable_identity:
            context.mark_engine_started("engine_9_identity")
            t0 = time.perf_counter()
            rec_e9 = EngineExecutionRecord(
                engine_name="Engine 9: Identity Verification & Entity Resolution",
                engine_key="engine_9_identity",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                identity = self.e9.verify(
                    content=state.content,
                    claims=state.claims,
                    sources=state.sources,
                    evidence=state.evidence,
                    threat=state.threat,
                )
                state.identity = identity
                rec_e9.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e9.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                rec_e9.output_id = identity.analysis_id
                rec_e9.metadata["identity_status"] = str(identity.identity_status)

                id_status_val = getattr(identity.identity_status, "value", str(identity.identity_status))
                if identity.identity_status in (
                    IdentityStatus.NOT_ESTABLISHED,
                    IdentityStatus.IDENTITY_MISMATCH,
                    IdentityStatus.AMBIGUOUS,
                ):
                    rec_e9.status = EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT
                    rec_e9.analytical_result = id_status_val
                else:
                    rec_e9.status = EngineOutcomeType.SUCCESS
                telemetry.record_engine(rec_e9)

                context.set_identity_result(identity)
                context.mark_engine_completed(
                    "engine_9_identity",
                    result_id=identity.analysis_id,
                    analytical_result=rec_e9.analytical_result,
                    duration_ms=rec_e9.duration_ms,
                    metadata=rec_e9.metadata,
                )
            except Exception as e:
                self._handle_engine_error("engine_9_identity", rec_e9, t0, e, state)
                context.mark_engine_failed("engine_9_identity", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        else:
            context.mark_engine_skipped("engine_9_identity", "Disabled in orchestrator config")

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 10 — Behavioural Signal Intelligence
        # ----------------------------------------------------------------------
        if self.config.enable_behaviour:
            context.mark_engine_started("engine_10_behaviour")
            t0 = time.perf_counter()
            rec_e10 = EngineExecutionRecord(
                engine_name="Engine 10: Behavioural Signal Intelligence",
                engine_key="engine_10_behaviour",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            try:
                # Resolve session history without cross-session contamination
                resolved_history = interaction_history
                if not resolved_history and session_id:
                    resolved_history = self.e10.get_session(session_id)

                behaviour = self.e10.analyze(
                    content=state.content,
                    claims=state.claims,
                    actions=state.actions,
                    threat=state.threat,
                    fingerprint=state.fingerprint,
                    identity=state.identity,
                    interaction_history=resolved_history,
                )
                state.behaviour = behaviour
                rec_e10.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e10.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                rec_e10.status = EngineOutcomeType.SUCCESS
                rec_e10.output_id = behaviour.analysis_id
                rec_e10.metadata["behaviour_signal_count"] = len(behaviour.signals)
                telemetry.record_engine(rec_e10)

                context.set_behaviour_result(behaviour)
                context.mark_engine_completed(
                    "engine_10_behaviour",
                    result_id=behaviour.analysis_id,
                    duration_ms=rec_e10.duration_ms,
                    metadata=rec_e10.metadata,
                )
            except Exception as e:
                self._handle_engine_error("engine_10_behaviour", rec_e10, t0, e, state)
                context.mark_engine_failed("engine_10_behaviour", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
        else:
            context.mark_engine_skipped("engine_10_behaviour", "Disabled in orchestrator config")

        # ----------------------------------------------------------------------
        # Step 10: Engine 8 — Policy & Intervention Engine (SOLE FINAL AUTHORITY)
        # ----------------------------------------------------------------------
        context.mark_engine_started("engine_8_policy")
        t0 = time.perf_counter()
        rec_e8 = EngineExecutionRecord(
            engine_name="Engine 8: Policy & Intervention Engine",
            engine_key="engine_8_policy",
            engine_version=E8_VERSION,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            fallback_threat = state.threat
            if fallback_threat is None and state.content is not None:
                fallback_threat = ThreatAnalysis(content_id=state.content.content_id)

            fallback_fp = state.fingerprint
            if fallback_fp is None and state.content is not None:
                fp_obj = ScamFingerprint(
                    fingerprint_id="SFP-NONE",
                    exact_signature="",
                    semantic_signature="",
                    created_at="",
                    updated_at="",
                    first_seen="",
                    last_seen="",
                )
                obs_obj = FingerprintObservation(
                    observation_id="OBS-NONE",
                    fingerprint_id="SFP-NONE",
                    content_id=state.content.content_id,
                    observed_at="",
                    channel="unknown",
                    match_type="NO_MATCH",
                    match_confidence=0.0,
                )
                prov_obj = FingerprintProvenance(analyzed_at="")
                fallback_fp = FingerprintAnalysis(
                    content_id=state.content.content_id,
                    fingerprint=fp_obj,
                    observation=obs_obj,
                    provenance=prov_obj,
                    match_type="NO_MATCH",
                )

            policy = self.e8.decide(
                content=state.content,
                claims=state.claims,
                actions=state.actions,
                sources=state.sources,
                evidence=state.evidence,
                threat=fallback_threat,
                fingerprint=fallback_fp,
                identity=state.identity,
                behaviour=state.behaviour,
                context=policy_context,
            )
            state.policy = policy
            rec_e8.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e8.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e8.status = EngineOutcomeType.SUCCESS
            rec_e8.output_id = policy.decision_id
            rec_e8.metadata["decision"] = policy.decision.value
            telemetry.record_engine(rec_e8)

            context.set_policy_result(policy)
            context.mark_engine_completed(
                "engine_8_policy",
                result_id=policy.decision_id,
                duration_ms=rec_e8.duration_ms,
                metadata=rec_e8.metadata,
            )
            context.finalize_pipeline()
        except Exception as e:
            rec_e8.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e8.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            rec_e8.status = EngineOutcomeType.FATAL_FAILURE
            rec_e8.error_type = type(e).__name__
            rec_e8.error_message = str(e)
            telemetry.record_engine(rec_e8)
            state.status = "FAILED"
            state.errors.append(f"Engine 8 Policy Failure: {e}")
            context.mark_engine_failed("engine_8_policy", str(e), duration_ms=round((time.perf_counter() - t0) * 1000, 2))
            context.finalize_pipeline()
            raise FatalOrchestrationError(f"Engine 8 policy failed: {e}", engine_name="engine_8_policy") from e

        # Finalize pipeline execution state
        completed_at_iso = datetime.now(timezone.utc).isoformat()
        state.completed_at = completed_at_iso
        telemetry.completed_at = completed_at_iso
        telemetry.total_duration_ms = round((time.perf_counter() - pipe_start_perf) * 1000, 2)

        if state.errors and state.status != "FAILED":
            state.status = "DEGRADED"
        elif not state.errors:
            state.status = "COMPLETED"

        provenance = {
            "orchestrator_version": "1.0.0",
            "analysis_id": analysis_id,
            "session_id": session_id,
            "source_mode": self.config.source_mode,
            "engines_executed": telemetry.engines_executed,
            "engines_succeeded": telemetry.engines_succeeded,
            "engines_degraded": telemetry.engines_degraded,
            "total_duration_ms": telemetry.total_duration_ms,
            "started_at": started_at_iso,
            "completed_at": completed_at_iso,
        }

        context.provenance = provenance
        context.warnings = list(state.warnings)
        context.errors = list(state.errors)
        context.execution_metadata["total_duration_ms"] = telemetry.total_duration_ms
        context.finalize_pipeline()

        return OrchestrationResult(
            analysis_id=analysis_id,
            session_id=session_id,
            pipeline_status=state.status,
            policy_decision=state.policy,
            state=state,
            context=context,
            engine_output_ids=state.get_output_ids(),
            telemetry=telemetry,
            provenance=provenance,
            warnings=state.warnings,
            errors=state.errors,
        )

    def _handle_engine_error(
        self,
        engine_key: str,
        record: EngineExecutionRecord,
        t0: float,
        exception: Exception,
        state: OrchestrationState,
    ) -> None:
        """Handle non-fatal or fatal engine errors with graceful degradation."""
        record.completed_at = datetime.now(timezone.utc).isoformat()
        record.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        record.error_type = type(exception).__name__
        record.error_message = str(exception)

        if self.config.fail_fast:
            record.status = EngineOutcomeType.FATAL_FAILURE
            state.telemetry.record_engine(record)
            state.status = "FAILED"
            state.errors.append(f"{record.engine_name} failed: {exception}")
            raise FatalOrchestrationError(
                f"{record.engine_name} failed: {exception}", engine_name=engine_key
            ) from exception

        # Graceful degradation: Record recoverable failure and allow downstream engines to continue
        record.status = EngineOutcomeType.RECOVERABLE_FAILURE
        state.telemetry.record_engine(record)
        state.warnings.append(f"{record.engine_name} failed recoverably: {exception}")
        state.errors.append(f"{record.engine_name}: {exception}")

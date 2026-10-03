"""Canonical Product Orchestrator Service for Nivesh Firewall.

Coordinates all 10 intelligence engines into a unified, dependency-aware pipeline:
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

import re
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
from nivesh.schemas.threat import (
    ThreatAnalysis,
    AttackPath,
    ThreatExplanation,
    ThreatProvenance,
    ThreatAnalysisMetadata,
)
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
from .pipeline import (
    CancellationToken,
    PipelineGraph,
    PolicyGate,
    SafeEngineExecutor,
)
from nivesh.schemas.firewall import (
    FirewallAnalysisResponse,
    FirewallDecisionSummary,
    FirewallExplanation,
    FirewallContentSummary,
    FirewallClaimSummary,
    FirewallActionSummary,
    FirewallEvidenceSummary,
    FirewallIdentitySummary,
    FirewallThreatSummary,
    FirewallFingerprintSummary,
    FirewallBehaviourSummary,
    FirewallApiError,
)

SENSITIVE_PATTERNS = [
    # Card numbers (13 to 19 digits)
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_CARD]"),
    # OTP / PIN / CVV / CVC
    (re.compile(r"(?i)\b(otp|pin|cvv|cvc)\s*[:=]\s*\d+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(otp|pin|cvv|cvc)\s+is\s+\d+"), r"\1 is [REDACTED]"),
    (re.compile(r"(?i)\b(otp|pin|cvv|cvc)\s+(\d{3,8})\b"), r"\1 [REDACTED]"),
    # Passwords and secrets
    (re.compile(r"(?i)\b(password|passwd|pwd|secret|token)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(password|passwd|pwd)\s+is\s+\S+"), r"\1 is [REDACTED]"),
    # Bank accounts
    (re.compile(r"(?i)\b(account|acct|acc)\s*(?:number|num|no)?\s*[:=]\s*\d+"), r"\1=[REDACTED]"),
    # Keystrokes & raw credentials
    (re.compile(r"(?i)\b(keystroke[s]?|raw_credential[s]?)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
]

FORBIDDEN_FIELD_NAMES = {
    "password", "passwd", "pwd", "otp", "pin", "cvv", "cvc",
    "card_number", "card_no", "account_number", "bank_account",
    "raw_credentials", "raw_credential", "keystrokes", "secret",
    "private_key", "access_token", "refresh_token", "api_key",
    "bearer", "authorization", "auth_token", "jwt", "session_token",
    "secret_key",
}


def sanitize_sensitive_data(val: Any) -> Any:
    """Sanitize passwords, OTPs, PINs, CVVs, card numbers, accounts, and credentials."""
    if isinstance(val, str):
        cleaned = val
        for pat, repl in SENSITIVE_PATTERNS:
            cleaned = pat.sub(repl, cleaned)
        return cleaned
    elif isinstance(val, dict):
        res = {}
        for k, v in val.items():
            if str(k).lower() in FORBIDDEN_FIELD_NAMES:
                res[k] = "[REDACTED]"
            else:
                res[k] = sanitize_sensitive_data(v)
        return res
    elif isinstance(val, list):
        return [sanitize_sensitive_data(v) for v in val]
    return val


def normalize_channel(ch: Optional[str]) -> str:
    """Normalize user-friendly channel names (e.g. 'web', 'sms') to valid Engine 1 ChannelType."""
    if not ch:
        return "unknown"
    c = str(ch).lower().strip()
    if c in ("browser", "web", "chrome", "firefox", "safari", "edge"):
        return "browser"
    elif c in ("telegram", "tg"):
        return "telegram"
    elif c in ("whatsapp", "wa"):
        return "whatsapp"
    elif c in ("instagram", "ig"):
        return "instagram"
    elif c in ("youtube", "yt"):
        return "youtube"
    elif c in ("email", "mail"):
        return "email"
    elif c in ("browser", "telegram", "whatsapp", "instagram", "youtube", "email"):
        return c
    return "unknown"


def create_empty_threat_analysis(content_id: str) -> ThreatAnalysis:
    """Construct an empty, non-fabricated ThreatAnalysis container for degraded evaluation."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return ThreatAnalysis(
        content_id=content_id,
        attack_path=AttackPath(),
        explanation=ThreatExplanation(summary="No threat analysis executed or degraded"),
        confidence=0.0,
        provenance=ThreatProvenance(
            engine_version="1.0.0",
            engine_name="Threat & Attack-Path Intelligence Engine",
            analysis_method="rule",
            analyzed_at=now_iso,
        ),
        analysis_metadata=ThreatAnalysisMetadata(),
    )


class ProductOrchestrator:
    """Central product orchestrator coordinating Nivesh Firewall intelligence engines."""

    def __init__(
        self,
        engines: Optional[dict[str, Any]] = None,
        config: Optional[OrchestratorConfig] = None,
        analysis_repository: Optional[Any] = None,
        session_repository: Optional[Any] = None,
    ):
        """Initialize the product orchestrator with optional dependency injection.

        Args:
            engines: Optional mapping of engine overrides for testing or custom adapters.
            config: Optional orchestration configuration (timeouts, modes, fail-fast).
            analysis_repository: Optional persistent AnalysisRepository.
            session_repository: Optional persistent SessionRepository.
        """
        self.config = config or OrchestratorConfig()
        self.analysis_repo = analysis_repository
        self.session_repo = session_repository
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

        # Phase 11.3 Pipeline Components
        self.pipeline_graph = PipelineGraph()
        self.executor = SafeEngineExecutor()
        self._idempotency_cache: dict[str, OrchestrationResult] = {}
        self._analysis_store: dict[str, OrchestrationResult] = {}

    def record_interaction_event(
        self, session_id: str, event: InteractionEvent
    ) -> InteractionHistory:
        """Record an observable interaction event into Engine 10 and persistent storage."""
        if self.session_repo is not None:
            try:
                self.session_repo.record_event(session_id, event)
            except Exception:
                pass
        return self.e10.record_event(session_id, event)

    def get_session_history(self, session_id: str) -> Optional[InteractionHistory]:
        """Retrieve recorded session interaction history by session ID."""
        history = self.e10.get_session(session_id)
        if not history and self.session_repo is not None:
            try:
                return self.session_repo.get_session(session_id)
            except Exception:
                pass
        return history

    def get_analysis(self, analysis_id: str) -> Optional[Any]:
        """Retrieve a previously executed analysis by analysis ID without re-running engines."""
        in_memory = self._analysis_store.get(analysis_id)
        if in_memory is not None:
            return in_memory
        if self.analysis_repo is not None:
            try:
                return self.analysis_repo.get_analysis(analysis_id)
            except Exception:
                pass
        return None

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
        cancellation_token: Optional[CancellationToken] = None,
        idempotency_key: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> OrchestrationResult:
        """Execute a complete end-to-end Nivesh Firewall analysis.

        Coordinates Engines 1 through 10 in canonical dependency order,
        records telemetry, isolates failures, and returns a unified OrchestrationResult.
        """
        # Idempotency cache check
        if idempotency_key and idempotency_key in self._idempotency_cache:
            return self._idempotency_cache[idempotency_key]

        pipe_start_perf = time.perf_counter()
        started_at_iso = datetime.now(timezone.utc).isoformat()
        analysis_id = f"ORCH-{uuid.uuid4().hex[:12].upper()}"

        channel = normalize_channel(channel)
        clean_metadata = sanitize_sensitive_data(metadata or {})
        if user_id:
            clean_metadata["user_id"] = user_id
        if organization_id:
            clean_metadata["organization_id"] = organization_id
        input_type = "text" if text is not None else "url" if url is not None else "image"

        context = AnalysisContext(
            analysis_id=analysis_id,
            session_id=session_id,
            input_type=input_type,
            channel=channel,
            request_metadata=clean_metadata,
            created_at=started_at_iso,
            updated_at=started_at_iso,
            status=PipelineStatus.RUNNING,
        )

        state = OrchestrationState(
            analysis_id=analysis_id,
            session_id=session_id,
            request_metadata=clean_metadata,
            started_at=started_at_iso,
            status="RUNNING",
        )
        telemetry = state.telemetry
        telemetry.started_at = started_at_iso

        # Immediate cancellation check before any engine execution
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Cancelled before start")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        def _handle_blocked_engine(node_key: str, dep_key: Optional[str], reason: Optional[str]) -> None:
            context.mark_engine_blocked(node_key, failed_dependency=dep_key or "upstream", reason=reason or "Dependency blocked")
            rec = EngineExecutionRecord(
                engine_name=self.pipeline_graph.nodes[node_key].engine_name,
                engine_key=node_key,
                started_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration_ms=0.0,
                status=EngineOutcomeType.SKIPPED,
                error_message=sanitize_sensitive_data(f"Blocked by {dep_key}: {reason}"),
            )
            telemetry.record_engine(rec)
            state.warnings.append(f"{self.pipeline_graph.nodes[node_key].engine_name} skipped: blocked by {dep_key}")

        # ----------------------------------------------------------------------
        # Step 1: Engine 1 — Content Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        context.mark_engine_started("engine_1_content")
        rec_e1 = EngineExecutionRecord(
            engine_name="Engine 1: Content Intelligence Engine",
            engine_key="engine_1_content",
            engine_version=E1_VERSION,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        def _run_e1():
            if text is not None:
                return self.e1.process_text(text, channel=channel)
            elif url is not None:
                return self.e1.process_url(url, channel=channel)
            elif image_bytes is not None or image_path is not None:
                return self.e1.process_image(
                    image_bytes=image_bytes, image_path=image_path, channel=channel
                )
            else:
                raise InputIngestionError("No valid input provided. Specify text, url, or image.")

        content, dur_e1, retries_e1, err_e1 = self.executor.execute(
            _run_e1,
            engine_key="engine_1_content",
            engine_name="Engine 1: Content Intelligence Engine",
            timeout_ms=self.config.engine_timeout_ms,
            max_retries=self.config.max_retries,
            retry_delay_ms=self.config.retry_delay_ms,
            cancellation_token=cancellation_token,
        )
        rec_e1.retry_count = retries_e1

        if err_e1 is not None or (content is not None and getattr(content, "status", None) == "error"):
            e = err_e1 or InputIngestionError(f"Engine 1 failed to process content: {content.error_message}")
            clean_err = sanitize_sensitive_data(str(e))
            rec_e1.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e1.duration_ms = dur_e1
            rec_e1.status = EngineOutcomeType.FATAL_FAILURE
            rec_e1.error_type = type(e).__name__
            rec_e1.error_message = clean_err
            telemetry.record_engine(rec_e1)
            state.status = "FAILED"
            state.errors.append(f"Engine 1 Fatal Failure: {clean_err}")
            state.completed_at = datetime.now(timezone.utc).isoformat()
            telemetry.completed_at = state.completed_at
            telemetry.total_duration_ms = round((time.perf_counter() - pipe_start_perf) * 1000, 2)
            context.mark_engine_failed("engine_1_content", clean_err, duration_ms=dur_e1)
            context.engine_states["engine_1_content"].retry_count = retries_e1
            context.finalize_pipeline()
            raise FatalOrchestrationError(f"Engine 1 failed: {clean_err}", engine_name="engine_1_content") from e

        # Attach session_id to content metadata if provided
        if session_id and hasattr(content, "metadata") and content.metadata is not None:
            content.metadata["session_id"] = session_id

        state.content = content
        rec_e1.completed_at = datetime.now(timezone.utc).isoformat()
        rec_e1.duration_ms = dur_e1
        rec_e1.status = EngineOutcomeType.SUCCESS
        rec_e1.output_id = content.content_id
        telemetry.record_engine(rec_e1)

        context.set_content_result(content)
        context.mark_engine_completed(
            "engine_1_content",
            result_id=content.content_id,
            duration_ms=dur_e1,
        )
        context.engine_states["engine_1_content"].retry_count = retries_e1

        # ----------------------------------------------------------------------
        # Step 2: Engine 2 — Claim Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_2_claims", context)
        if not can_run:
            _handle_blocked_engine("engine_2_claims", dep_key, block_reason)
        else:
            context.mark_engine_started("engine_2_claims")
            rec_e2 = EngineExecutionRecord(
                engine_name="Engine 2: Claim Intelligence Engine",
                engine_key="engine_2_claims",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            claims, dur_e2, retries_e2, err_e2 = self.executor.execute(
                self.e2.analyze,
                state.content,
                engine_key="engine_2_claims",
                engine_name="Engine 2: Claim Intelligence Engine",
                timeout_ms=self.config.engine_timeout_ms,
                max_retries=self.config.max_retries,
                retry_delay_ms=self.config.retry_delay_ms,
                cancellation_token=cancellation_token,
            )
            rec_e2.retry_count = retries_e2

            if err_e2 is not None:
                self._handle_engine_error("engine_2_claims", rec_e2, dur_e2, err_e2, state)
                context.mark_engine_failed("engine_2_claims", sanitize_sensitive_data(str(err_e2)), duration_ms=dur_e2)
                context.engine_states["engine_2_claims"].retry_count = retries_e2
                if not self.config.fail_fast and state.content is not None:
                    state.claims = ClaimAnalysis(content_id=state.content.content_id, claims=[])
            else:
                state.claims = claims
                rec_e2.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e2.duration_ms = dur_e2
                rec_e2.status = EngineOutcomeType.SUCCESS
                rec_e2.output_id = getattr(claims, "analysis_id", getattr(claims, "content_id", None))
                rec_e2.metadata["claim_count"] = len(claims.claims)
                telemetry.record_engine(rec_e2)

                context.set_claim_result(claims)
                context.mark_engine_completed(
                    "engine_2_claims",
                    result_id=rec_e2.output_id,
                    duration_ms=dur_e2,
                    metadata=rec_e2.metadata,
                )
                context.engine_states["engine_2_claims"].retry_count = retries_e2

        # ----------------------------------------------------------------------
        # Step 3: Engine 3 — Action Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_3_actions", context)
        if not can_run:
            _handle_blocked_engine("engine_3_actions", dep_key, block_reason)
        else:
            context.mark_engine_started("engine_3_actions")
            rec_e3 = EngineExecutionRecord(
                engine_name="Engine 3: Action Intelligence Engine",
                engine_key="engine_3_actions",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            actions, dur_e3, retries_e3, err_e3 = self.executor.execute(
                self.e3.analyze,
                state.content,
                state.claims,
                engine_key="engine_3_actions",
                engine_name="Engine 3: Action Intelligence Engine",
                timeout_ms=self.config.engine_timeout_ms,
                max_retries=self.config.max_retries,
                retry_delay_ms=self.config.retry_delay_ms,
                cancellation_token=cancellation_token,
            )
            rec_e3.retry_count = retries_e3

            if err_e3 is not None:
                self._handle_engine_error("engine_3_actions", rec_e3, dur_e3, err_e3, state)
                context.mark_engine_failed("engine_3_actions", sanitize_sensitive_data(str(err_e3)), duration_ms=dur_e3)
                context.engine_states["engine_3_actions"].retry_count = retries_e3
                if not self.config.fail_fast and state.content is not None:
                    state.actions = ActionAnalysis(content_id=state.content.content_id, actions=[])
            else:
                state.actions = actions
                rec_e3.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e3.duration_ms = dur_e3
                rec_e3.status = EngineOutcomeType.SUCCESS
                rec_e3.output_id = getattr(actions, "analysis_id", getattr(actions, "content_id", None))
                rec_e3.metadata["action_count"] = len(actions.actions)
                telemetry.record_engine(rec_e3)

                context.set_action_result(actions)
                context.mark_engine_completed(
                    "engine_3_actions",
                    result_id=rec_e3.output_id,
                    duration_ms=dur_e3,
                    metadata=rec_e3.metadata,
                )
                context.engine_states["engine_3_actions"].retry_count = retries_e3

        # ----------------------------------------------------------------------
        # Step 4: Engine 4 — Source Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_4_sources", context)
        if not can_run:
            _handle_blocked_engine("engine_4_sources", dep_key, block_reason)
        else:
            context.mark_engine_started("engine_4_sources")
            rec_e4 = EngineExecutionRecord(
                engine_name="Engine 4: Source Intelligence Engine",
                engine_key="engine_4_sources",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            sources, dur_e4, retries_e4, err_e4 = self.executor.execute(
                self.e4.discover_and_retrieve,
                state.content,
                state.claims,
                state.actions,
                engine_key="engine_4_sources",
                engine_name="Engine 4: Source Intelligence Engine",
                timeout_ms=self.config.engine_timeout_ms,
                max_retries=self.config.max_retries,
                retry_delay_ms=self.config.retry_delay_ms,
                cancellation_token=cancellation_token,
            )
            rec_e4.retry_count = retries_e4

            if err_e4 is not None:
                self._handle_engine_error("engine_4_sources", rec_e4, dur_e4, err_e4, state)
                context.mark_engine_failed("engine_4_sources", sanitize_sensitive_data(str(err_e4)), duration_ms=dur_e4)
                context.engine_states["engine_4_sources"].retry_count = retries_e4
                if not self.config.fail_fast and state.content is not None:
                    # Provide degraded fallback container for downstream non-null expectations
                    state.sources = SourceAnalysis(
                        content_id=state.content.content_id,
                        claim_sources=[],
                        analysis_metadata=SourceAnalysisMetadata(retrieval_failures=1),
                    )
            else:
                state.sources = sources
                rec_e4.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e4.duration_ms = dur_e4
                rec_e4.output_id = getattr(sources, "analysis_id", getattr(sources, "content_id", None))
                total_docs = sum(len(getattr(cs, "documents", [])) for cs in getattr(sources, "claim_sources", []))
                total_candidates = sum(len(getattr(cs, "evidence_candidates", [])) for cs in getattr(sources, "claim_sources", []))
                rec_e4.metadata["source_count"] = total_docs
                rec_e4.metadata["candidate_count"] = total_candidates

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
                    duration_ms=dur_e4,
                    metadata=rec_e4.metadata,
                )
                context.engine_states["engine_4_sources"].retry_count = retries_e4

        # ----------------------------------------------------------------------
        # Step 5: Engine 5 — Evidence Verification
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_5_evidence", context)
        if not can_run:
            _handle_blocked_engine("engine_5_evidence", dep_key, block_reason)
        else:
            context.mark_engine_started("engine_5_evidence")
            rec_e5 = EngineExecutionRecord(
                engine_name="Engine 5: Evidence Verification Engine",
                engine_key="engine_5_evidence",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            evidence, dur_e5, retries_e5, err_e5 = self.executor.execute(
                self.e5.verify,
                state.content,
                state.claims,
                state.sources,
                engine_key="engine_5_evidence",
                engine_name="Engine 5: Evidence Verification Engine",
                timeout_ms=self.config.engine_timeout_ms,
                max_retries=self.config.max_retries,
                retry_delay_ms=self.config.retry_delay_ms,
                cancellation_token=cancellation_token,
            )
            rec_e5.retry_count = retries_e5

            if err_e5 is not None:
                self._handle_engine_error("engine_5_evidence", rec_e5, dur_e5, err_e5, state)
                context.mark_engine_failed("engine_5_evidence", sanitize_sensitive_data(str(err_e5)), duration_ms=dur_e5)
                context.engine_states["engine_5_evidence"].retry_count = retries_e5
                if not self.config.fail_fast and state.content is not None:
                    state.evidence = EvidenceAnalysis(
                        content_id=state.content.content_id,
                        verifications=[],
                        analysis_metadata=EvidenceAnalysisMetadata(),
                    )
            else:
                state.evidence = evidence
                rec_e5.completed_at = datetime.now(timezone.utc).isoformat()
                rec_e5.duration_ms = dur_e5
                rec_e5.output_id = getattr(evidence, "analysis_id", getattr(evidence, "content_id", None))
                rec_e5.metadata["verification_count"] = len(evidence.verifications)

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
                    duration_ms=dur_e5,
                    metadata=rec_e5.metadata,
                )
                context.engine_states["engine_5_evidence"].retry_count = retries_e5

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 6 — Threat Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        if not self.config.enable_threat:
            context.mark_engine_skipped("engine_6_threat", "Disabled in orchestrator config")
        else:
            can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_6_threat", context)
            if not can_run:
                _handle_blocked_engine("engine_6_threat", dep_key, block_reason)
            else:
                context.mark_engine_started("engine_6_threat")
                rec_e6 = EngineExecutionRecord(
                    engine_name="Engine 6: Threat & Attack-Path Intelligence",
                    engine_key="engine_6_threat",
                    started_at=datetime.now(timezone.utc).isoformat(),
                )
                threat, dur_e6, retries_e6, err_e6 = self.executor.execute(
                    self.e6.analyze,
                    state.content,
                    state.claims,
                    state.actions,
                    state.sources,
                    state.evidence,
                    engine_key="engine_6_threat",
                    engine_name="Engine 6: Threat & Attack-Path Intelligence",
                    timeout_ms=self.config.engine_timeout_ms,
                    max_retries=self.config.max_retries,
                    retry_delay_ms=self.config.retry_delay_ms,
                    cancellation_token=cancellation_token,
                )
                rec_e6.retry_count = retries_e6

                if err_e6 is not None:
                    self._handle_engine_error("engine_6_threat", rec_e6, dur_e6, err_e6, state)
                    context.mark_engine_failed("engine_6_threat", sanitize_sensitive_data(str(err_e6)), duration_ms=dur_e6)
                    context.engine_states["engine_6_threat"].retry_count = retries_e6
                    if not self.config.fail_fast and state.content is not None:
                        state.threat = create_empty_threat_analysis(state.content.content_id)
                else:
                    state.threat = threat
                    rec_e6.completed_at = datetime.now(timezone.utc).isoformat()
                    rec_e6.duration_ms = dur_e6
                    rec_e6.status = EngineOutcomeType.SUCCESS
                    rec_e6.output_id = threat.content_id
                    rec_e6.metadata["threat_signal_count"] = len(threat.threat_signals)
                    telemetry.record_engine(rec_e6)

                    context.set_threat_result(threat)
                    context.mark_engine_completed(
                        "engine_6_threat",
                        result_id=threat.content_id,
                        duration_ms=dur_e6,
                        metadata=rec_e6.metadata,
                    )
                    context.engine_states["engine_6_threat"].retry_count = retries_e6

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 7 — Scam Fingerprint Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        if not self.config.enable_fingerprint:
            context.mark_engine_skipped("engine_7_fingerprint", "Disabled in orchestrator config")
        else:
            can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_7_fingerprint", context)
            if not can_run:
                _handle_blocked_engine("engine_7_fingerprint", dep_key, block_reason)
            else:
                context.mark_engine_started("engine_7_fingerprint")
                rec_e7 = EngineExecutionRecord(
                    engine_name="Engine 7: Scam Fingerprint & Collective Intelligence",
                    engine_key="engine_7_fingerprint",
                    started_at=datetime.now(timezone.utc).isoformat(),
                )
                fingerprint, dur_e7, retries_e7, err_e7 = self.executor.execute(
                    self.e7.create_or_match,
                    state.content,
                    state.claims,
                    state.actions,
                    state.sources,
                    state.evidence,
                    state.threat,
                    engine_key="engine_7_fingerprint",
                    engine_name="Engine 7: Scam Fingerprint & Collective Intelligence",
                    timeout_ms=self.config.engine_timeout_ms,
                    max_retries=self.config.max_retries,
                    retry_delay_ms=self.config.retry_delay_ms,
                    cancellation_token=cancellation_token,
                )
                rec_e7.retry_count = retries_e7

                if err_e7 is not None:
                    self._handle_engine_error("engine_7_fingerprint", rec_e7, dur_e7, err_e7, state)
                    context.mark_engine_failed("engine_7_fingerprint", sanitize_sensitive_data(str(err_e7)), duration_ms=dur_e7)
                    context.engine_states["engine_7_fingerprint"].retry_count = retries_e7
                else:
                    state.fingerprint = fingerprint
                    rec_e7.completed_at = datetime.now(timezone.utc).isoformat()
                    rec_e7.duration_ms = dur_e7
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
                        duration_ms=dur_e7,
                        metadata=rec_e7.metadata,
                    )
                    context.engine_states["engine_7_fingerprint"].retry_count = retries_e7

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 9 — Identity Verification
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        if not self.config.enable_identity:
            context.mark_engine_skipped("engine_9_identity", "Disabled in orchestrator config")
        else:
            can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_9_identity", context)
            if not can_run:
                _handle_blocked_engine("engine_9_identity", dep_key, block_reason)
            else:
                context.mark_engine_started("engine_9_identity")
                rec_e9 = EngineExecutionRecord(
                    engine_name="Engine 9: Identity Verification & Entity Resolution",
                    engine_key="engine_9_identity",
                    started_at=datetime.now(timezone.utc).isoformat(),
                )
                identity, dur_e9, retries_e9, err_e9 = self.executor.execute(
                    self.e9.verify,
                    content=state.content,
                    claims=state.claims,
                    sources=state.sources,
                    evidence=state.evidence,
                    threat=state.threat,
                    engine_key="engine_9_identity",
                    engine_name="Engine 9: Identity Verification & Entity Resolution",
                    timeout_ms=self.config.engine_timeout_ms,
                    max_retries=self.config.max_retries,
                    retry_delay_ms=self.config.retry_delay_ms,
                    cancellation_token=cancellation_token,
                )
                rec_e9.retry_count = retries_e9

                if err_e9 is not None:
                    # Record execution failure without converting to fake analytical IDENTITY_MISMATCH
                    self._handle_engine_error("engine_9_identity", rec_e9, dur_e9, err_e9, state)
                    context.mark_engine_failed("engine_9_identity", sanitize_sensitive_data(str(err_e9)), duration_ms=dur_e9)
                    context.engine_states["engine_9_identity"].retry_count = retries_e9
                else:
                    state.identity = identity
                    rec_e9.completed_at = datetime.now(timezone.utc).isoformat()
                    rec_e9.duration_ms = dur_e9
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
                        duration_ms=dur_e9,
                        metadata=rec_e9.metadata,
                    )
                    context.engine_states["engine_9_identity"].retry_count = retries_e9

        # ----------------------------------------------------------------------
        # Downstream Intelligence: Engine 10 — Behavioural Signal Intelligence
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        if not self.config.enable_behaviour:
            context.mark_engine_skipped("engine_10_behaviour", "Disabled in orchestrator config")
        else:
            can_run, dep_key, block_reason = self.pipeline_graph.can_execute("engine_10_behaviour", context)
            if not can_run:
                _handle_blocked_engine("engine_10_behaviour", dep_key, block_reason)
            else:
                context.mark_engine_started("engine_10_behaviour")
                rec_e10 = EngineExecutionRecord(
                    engine_name="Engine 10: Behavioural Signal Intelligence",
                    engine_key="engine_10_behaviour",
                    started_at=datetime.now(timezone.utc).isoformat(),
                )

                resolved_history = interaction_history
                if not resolved_history and session_id:
                    resolved_history = self.e10.get_session(session_id)

                behaviour, dur_e10, retries_e10, err_e10 = self.executor.execute(
                    self.e10.analyze,
                    content=state.content,
                    claims=state.claims,
                    actions=state.actions,
                    threat=state.threat,
                    fingerprint=state.fingerprint,
                    identity=state.identity,
                    interaction_history=resolved_history,
                    engine_key="engine_10_behaviour",
                    engine_name="Engine 10: Behavioural Signal Intelligence",
                    timeout_ms=self.config.engine_timeout_ms,
                    max_retries=self.config.max_retries,
                    retry_delay_ms=self.config.retry_delay_ms,
                    cancellation_token=cancellation_token,
                )
                rec_e10.retry_count = retries_e10

                if err_e10 is not None:
                    # Record execution failure without creating synthetic signals
                    self._handle_engine_error("engine_10_behaviour", rec_e10, dur_e10, err_e10, state)
                    context.mark_engine_failed("engine_10_behaviour", sanitize_sensitive_data(str(err_e10)), duration_ms=dur_e10)
                    context.engine_states["engine_10_behaviour"].retry_count = retries_e10
                else:
                    state.behaviour = behaviour
                    rec_e10.completed_at = datetime.now(timezone.utc).isoformat()
                    rec_e10.duration_ms = dur_e10
                    rec_e10.status = EngineOutcomeType.SUCCESS
                    rec_e10.output_id = behaviour.analysis_id
                    rec_e10.metadata["behaviour_signal_count"] = len(behaviour.signals)
                    telemetry.record_engine(rec_e10)

                    context.set_behaviour_result(behaviour)
                    context.mark_engine_completed(
                        "engine_10_behaviour",
                        result_id=behaviour.analysis_id,
                        duration_ms=dur_e10,
                        metadata=rec_e10.metadata,
                    )
                    context.engine_states["engine_10_behaviour"].retry_count = retries_e10

        # ----------------------------------------------------------------------
        # Step 10: Policy Gate & Engine 8 (SOLE FINAL POLICY AUTHORITY)
        # ----------------------------------------------------------------------
        if cancellation_token and cancellation_token.is_cancelled:
            context.cancel_pipeline(cancellation_token.reason or "Pipeline cancelled")
            state.status = "CANCELLED"
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        # Policy Gate: Verify all required prerequisites before invoking Engine 8
        gate_passed, gate_reasons = PolicyGate.verify_gate(
            context, allow_degraded=(not self.config.fail_fast)
        )
        if not gate_passed:
            # Policy Gate blocked! Orchestrator does NOT make policy decisions; does NOT invent fallback decision.
            context.mark_engine_blocked("engine_8_policy", failed_dependency="prerequisites", reason="; ".join(gate_reasons))
            rec_e8 = EngineExecutionRecord(
                engine_name="Engine 8: Policy & Intervention Engine",
                engine_key="engine_8_policy",
                started_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration_ms=0.0,
                status=EngineOutcomeType.SKIPPED,
                error_message=sanitize_sensitive_data("; ".join(gate_reasons)),
            )
            telemetry.record_engine(rec_e8)
            state.warnings.append(f"Engine 8 Policy Gate blocked: {'; '.join(gate_reasons)}")
            state.errors.extend(gate_reasons)
            if state.status != "CANCELLED":
                state.status = "PARTIAL" if context.content else "FAILED"
            context.finalize_pipeline()
            return self._build_result(
                analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
            )

        context.mark_engine_started("engine_8_policy")
        rec_e8 = EngineExecutionRecord(
            engine_name="Engine 8: Policy & Intervention Engine",
            engine_key="engine_8_policy",
            engine_version=E8_VERSION,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Resolve degraded fallback containers where required for Engine 8 rule evaluation
        fallback_threat = state.threat
        if fallback_threat is None and state.content is not None:
            fallback_threat = create_empty_threat_analysis(state.content.content_id)

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

        fallback_sources = state.sources
        if fallback_sources is None and state.content is not None:
            fallback_sources = SourceAnalysis(
                content_id=state.content.content_id,
                claim_sources=[],
                analysis_metadata=SourceAnalysisMetadata(retrieval_failures=1),
            )

        fallback_evidence = state.evidence
        if fallback_evidence is None and state.content is not None:
            fallback_evidence = EvidenceAnalysis(
                content_id=state.content.content_id,
                verifications=[],
                analysis_metadata=EvidenceAnalysisMetadata(),
            )

        def _run_e8():
            return self.e8.decide(
                content=state.content,
                claims=state.claims,
                actions=state.actions,
                sources=fallback_sources,
                evidence=fallback_evidence,
                threat=fallback_threat,
                fingerprint=fallback_fp,
                identity=state.identity,
                behaviour=state.behaviour,
                context=policy_context,
            )

        policy, dur_e8, retries_e8, err_e8 = self.executor.execute(
            _run_e8,
            engine_key="engine_8_policy",
            engine_name="Engine 8: Policy & Intervention Engine",
            timeout_ms=self.config.engine_timeout_ms,
            max_retries=self.config.max_retries,
            retry_delay_ms=self.config.retry_delay_ms,
            cancellation_token=cancellation_token,
        )
        rec_e8.retry_count = retries_e8

        if err_e8 is not None:
            rec_e8.completed_at = datetime.now(timezone.utc).isoformat()
            rec_e8.duration_ms = dur_e8
            rec_e8.status = EngineOutcomeType.FATAL_FAILURE
            rec_e8.error_type = type(err_e8).__name__
            clean_err = sanitize_sensitive_data(str(err_e8))
            rec_e8.error_message = clean_err
            telemetry.record_engine(rec_e8)
            state.status = "FAILED"
            state.errors.append(f"Engine 8 Policy Failure: {clean_err}")
            context.mark_engine_failed("engine_8_policy", clean_err, duration_ms=dur_e8)
            context.engine_states["engine_8_policy"].retry_count = retries_e8
            context.finalize_pipeline()
            raise FatalOrchestrationError(f"Engine 8 policy failed: {clean_err}", engine_name="engine_8_policy") from err_e8

        state.policy = policy
        rec_e8.completed_at = datetime.now(timezone.utc).isoformat()
        rec_e8.duration_ms = dur_e8
        rec_e8.status = EngineOutcomeType.SUCCESS
        rec_e8.output_id = policy.decision_id
        rec_e8.metadata["decision"] = policy.decision.value
        telemetry.record_engine(rec_e8)

        context.set_policy_result(policy, allow_degraded=(not self.config.fail_fast))
        context.mark_engine_completed(
            "engine_8_policy",
            result_id=policy.decision_id,
            duration_ms=dur_e8,
            metadata=rec_e8.metadata,
        )
        context.engine_states["engine_8_policy"].retry_count = retries_e8
        context.finalize_pipeline()

        return self._build_result(
            analysis_id, session_id, state, context, telemetry, pipe_start_perf, started_at_iso, idempotency_key
        )

    def _build_result(
        self,
        analysis_id: str,
        session_id: Optional[str],
        state: OrchestrationState,
        context: AnalysisContext,
        telemetry: PipelineTelemetry,
        pipe_start_perf: float,
        started_at_iso: str,
        idempotency_key: Optional[str] = None,
    ) -> OrchestrationResult:
        """Construct the final OrchestrationResult and cache for idempotency if applicable."""
        completed_at_iso = datetime.now(timezone.utc).isoformat()
        state.completed_at = completed_at_iso
        telemetry.completed_at = completed_at_iso
        telemetry.total_duration_ms = round((time.perf_counter() - pipe_start_perf) * 1000, 2)

        if context.status == PipelineStatus.CANCELLED or state.status == "CANCELLED":
            state.status = "CANCELLED"
        elif state.errors and state.status != "FAILED":
            state.status = "DEGRADED"
        elif not state.errors and state.status not in ("FAILED", "CANCELLED", "PARTIAL"):
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

        res = OrchestrationResult(
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

        self._analysis_store[analysis_id] = res

        if idempotency_key:
            self._idempotency_cache[idempotency_key] = res

        if self.analysis_repo is not None:
            try:
                self.analysis_repo.save_analysis(
                    res,
                    idempotency_key=idempotency_key,
                    user_id=state.request_metadata.get("user_id"),
                    organization_id=state.request_metadata.get("organization_id"),
                )
            except Exception as e:
                import logging
                logging.getLogger("nivesh.orchestrator").warning(
                    "Failed to persist analysis %s: %s", analysis_id, e
                )

        return res

    def format_response(self, result: OrchestrationResult) -> FirewallAnalysisResponse:
        """Format an OrchestrationResult into the canonical FirewallAnalysisResponse."""
        return format_firewall_response(result)

    def _handle_engine_error(
        self,
        engine_key: str,
        record: EngineExecutionRecord,
        dur_ms: float,
        exception: Exception,
        state: OrchestrationState,
    ) -> None:
        """Handle non-fatal or fatal engine errors with graceful degradation."""
        record.completed_at = datetime.now(timezone.utc).isoformat()
        record.duration_ms = dur_ms
        record.error_type = type(exception).__name__
        clean_msg = sanitize_sensitive_data(str(exception))
        record.error_message = clean_msg

        if self.config.fail_fast:
            record.status = EngineOutcomeType.FATAL_FAILURE
            state.telemetry.record_engine(record)
            state.status = "FAILED"
            state.errors.append(f"{record.engine_name} failed: {clean_msg}")
            raise FatalOrchestrationError(
                f"{record.engine_name} failed: {clean_msg}", engine_name=engine_key
            ) from exception

        # Graceful degradation: Record recoverable failure and allow downstream engines to continue
        record.status = EngineOutcomeType.RECOVERABLE_FAILURE
        state.telemetry.record_engine(record)
        state.warnings.append(f"{record.engine_name} failed recoverably: {clean_msg}")
        state.errors.append(f"{record.engine_name}: {clean_msg}")


def format_firewall_response(result: OrchestrationResult) -> FirewallAnalysisResponse:
    """Transform a product OrchestrationResult into the canonical FirewallAnalysisResponse."""
    state = result.state
    context = result.context

    # 1. Final Decision Summary (sole authority: Engine 8)
    if result.policy_decision is not None:
        pd = result.policy_decision
        exp = FirewallExplanation(
            decision=str(getattr(pd.decision, "value", pd.decision)),
            user_message=pd.user_message,
            technical_message=pd.technical_message,
            primary_reason=pd.primary_reason,
            supporting_signals=list(pd.triggered_signals),
        )
        actions_req = list(pd.actions_required) if hasattr(pd, "actions_required") else []
        if pd.required_user_confirmation and "USER_CONFIRMATION_REQUIRED" not in actions_req:
            actions_req.append("USER_CONFIRMATION_REQUIRED")

        decision_summary = FirewallDecisionSummary(
            decision=str(getattr(pd.decision, "value", pd.decision)),
            severity=str(getattr(pd.severity, "value", pd.severity)),
            primary_reason=pd.primary_reason,
            reason_codes=list(pd.reason_codes),
            explanation=exp,
            actions_required=actions_req,
            required_user_confirmation=pd.required_user_confirmation,
            cooldown_seconds=pd.cooldown_seconds,
            policy_version=pd.policy_version,
            decision_id=pd.decision_id,
        )
    else:
        fallback_decision = "PAUSE" if state.status == "FAILED" else "INFORM"
        exp = FirewallExplanation(
            decision=fallback_decision,
            user_message="Analysis could not be fully completed due to an internal execution event.",
            technical_message="Pipeline execution halted or degraded before Engine 8 policy evaluation.",
            primary_reason="Pipeline incomplete before policy evaluation",
            supporting_signals=["PIPELINE_INCOMPLETE"],
        )
        decision_summary = FirewallDecisionSummary(
            decision=fallback_decision,
            severity="MEDIUM" if state.status == "FAILED" else "NONE",
            primary_reason="Pipeline incomplete before policy evaluation",
            reason_codes=["PIPELINE_INCOMPLETE"],
            explanation=exp,
            actions_required=["RETRY_ANALYSIS"],
            required_user_confirmation=False,
            cooldown_seconds=None,
            policy_version="8.0.0",
            decision_id=None,
        )

    # 2. Content Summary
    if state.content is not None:
        c = state.content
        summary_text = c.normalized.text[:200] if c.normalized and c.normalized.text else ""
        entities_dict = {
            "people": [p.text for p in c.entities.people],
            "organizations": [o.text for o in c.entities.organizations],
            "regulators": [r.text for r in c.entities.regulators],
            "financial_instruments": [f.text for f in c.entities.financial_instruments],
        }
        content_summary = FirewallContentSummary(
            content_id=c.content_id,
            input_type=c.source.type,
            channel=c.source.channel,
            summary=summary_text,
            contains_financial_content=c.content_features.contains_financial_content,
            language=c.normalized.language,
            language_confidence=c.normalized.language_confidence,
            entities=entities_dict,
        )
    else:
        content_summary = FirewallContentSummary(
            content_id="UNKNOWN",
            input_type=context.input_type or "text",
            channel=context.channel or "unknown",
            summary="",
            contains_financial_content=False,
            language=None,
            language_confidence=None,
            entities={},
        )

    # 3. Claims
    claim_verif_lookup: dict[str, str] = {}
    if state.evidence is not None:
        for v in state.evidence.verifications:
            claim_verif_lookup[v.claim_id] = str(getattr(v.status, "value", v.status))

    claim_summaries: list[FirewallClaimSummary] = []
    if state.claims is not None:
        for cl in state.claims.claims:
            verif_st = claim_verif_lookup.get(cl.claim_id)
            claim_text = cl.text.original if hasattr(cl, "text") and hasattr(cl.text, "original") else str(getattr(cl, "text", ""))
            raw_topic = getattr(cl, "claim_type", getattr(cl, "topic", "CLAIM"))
            topic_str = str(getattr(raw_topic, "value", raw_topic))
            pred_str = str(getattr(cl.predicate, "value", cl.predicate)) if hasattr(cl, "predicate") else "ASSERTION"
            mod_str = str(getattr(cl.modality.type, "value", cl.modality.type)) if hasattr(cl, "modality") and hasattr(cl.modality, "type") else "statement"
            claim_summaries.append(
                FirewallClaimSummary(
                    claim_id=cl.claim_id,
                    text=claim_text,
                    topic=topic_str,
                    predicate=pred_str,
                    modality=mod_str,
                    verification_status=verif_st,
                )
            )

    # 4. Actions
    action_summaries: list[FirewallActionSummary] = []
    if state.actions is not None:
        for act in state.actions.actions:
            target_val = act.target.value if act.target and act.target.value else (act.target.type if act.target else None)
            is_urg = bool(act.parameters.get("deadline") or (hasattr(act, "modality") and getattr(act.modality, "type", None) in ("warning", "instruction") and "immediate" in str(act.text.original).lower()))
            cat = str(getattr(act.category, "value", act.category))
            rev = "IRREVERSIBLE" if cat in ("FINANCIAL_TRANSACTION", "CREDENTIAL_ACCESS") else "REVERSIBLE"
            action_summaries.append(
                FirewallActionSummary(
                    action_id=act.action_id,
                    action_type=str(getattr(act.action_type, "value", act.action_type)),
                    target=target_val,
                    impact_category=cat,
                    reversibility=rev,
                    urgency_detected=is_urg,
                )
            )

    # 5. Evidence
    if state.evidence is not None:
        ev = state.evidence
        status_counts: dict[str, int] = {}
        for v in ev.verifications:
            st = str(getattr(v.status, "value", v.status))
            status_counts[st] = status_counts.get(st, 0) + 1

        overall = "NOT_ESTABLISHED"
        if status_counts.get("CONTRADICTED", 0) > 0:
            overall = "CONTRADICTED"
        elif status_counts.get("SOURCE_UNAVAILABLE", 0) > 0 and not ev.verifications:
            overall = "SOURCE_UNAVAILABLE"
        elif status_counts.get("SUPPORTED", 0) > 0 and status_counts.get("CONTRADICTED", 0) == 0:
            overall = "SUPPORTED"
        elif status_counts.get("INSUFFICIENT_EVIDENCE", 0) > 0:
            overall = "INSUFFICIENT_EVIDENCE"
        elif ev.verifications:
            overall = "PARTIAL_EVIDENCE"

        src_count = 0
        if state.sources is not None:
            if hasattr(state.sources, "analysis_metadata") and hasattr(state.sources.analysis_metadata, "documents_retrieved"):
                src_count = state.sources.analysis_metadata.documents_retrieved
            elif hasattr(state.sources, "claim_sources"):
                src_count = sum(len(getattr(cs, "documents", [])) for cs in state.sources.claim_sources)

        retrieval_st = "COMPLETED"
        e4_record = context.engine_states.get("engine_4_sources") if hasattr(context, "engine_states") else None
        if (
            (e4_record and getattr(e4_record, "analytical_result", None) == "SOURCE_UNAVAILABLE")
            or getattr(state.sources, "retrieval_status", None) == "SOURCE_UNAVAILABLE"
            or (state.sources and getattr(state.sources, "analysis_metadata", None) and getattr(state.sources.analysis_metadata, "retrieval_failures", 0) > 0 and src_count == 0)
        ):
            retrieval_st = "SOURCE_UNAVAILABLE"

        evidence_summary = FirewallEvidenceSummary(
            overall_status=overall,
            verification_count=len(ev.verifications),
            supported_claims_count=ev.analysis_metadata.claims_supported + ev.analysis_metadata.claims_partially_supported,
            contradicted_claims_count=ev.analysis_metadata.claims_contradicted,
            insufficient_claims_count=ev.analysis_metadata.claims_insufficient,
            source_documents_count=src_count,
            retrieval_status=retrieval_st,
        )
    else:
        src_status = "SOURCE_UNAVAILABLE" if (state.sources and getattr(state.sources, "retrieval_status", None) == "SOURCE_UNAVAILABLE") else "NOT_RUN"
        overall_ev = "SOURCE_UNAVAILABLE" if src_status == "SOURCE_UNAVAILABLE" else "NOT_ESTABLISHED"
        src_count = 0
        if state.sources is not None:
            if hasattr(state.sources, "analysis_metadata") and hasattr(state.sources.analysis_metadata, "documents_retrieved"):
                src_count = state.sources.analysis_metadata.documents_retrieved
            elif hasattr(state.sources, "claim_sources"):
                src_count = sum(len(getattr(cs, "documents", [])) for cs in state.sources.claim_sources)

        evidence_summary = FirewallEvidenceSummary(
            overall_status=overall_ev,
            verification_count=0,
            supported_claims_count=0,
            contradicted_claims_count=0,
            insufficient_claims_count=0,
            source_documents_count=src_count,
            retrieval_status=src_status,
        )

    # 6. Identity
    if state.identity is not None:
        idt = state.identity
        id_status = str(getattr(idt.identity_status, "value", idt.identity_status))
        entities_list = [getattr(e, "name", getattr(e, "normalized_name", str(e))) for e in idt.entities] if hasattr(idt, "entities") else []
        findings_desc = [f.description for f in idt.identity_findings[:5]] if hasattr(idt, "identity_findings") else []
        identity_summary = FirewallIdentitySummary(
            identity_status=id_status,
            claimed_entities=entities_list,
            findings_count=len(idt.identity_findings) if hasattr(idt, "identity_findings") else 0,
            findings_summary=findings_desc,
            confidence=idt.confidence,
        )
    else:
        identity_summary = FirewallIdentitySummary(
            identity_status="NOT_ESTABLISHED",
            claimed_entities=[],
            findings_count=0,
            findings_summary=[],
            confidence=0.0,
        )

    # 7. Threat
    if state.threat is not None:
        th = state.threat
        threat_signals = []
        if hasattr(th, "threat_signals") and th.threat_signals:
            for s in th.threat_signals:
                sig_type = getattr(s, "type", getattr(s, "signal_type", str(s)))
                threat_signals.append(str(getattr(sig_type, "value", sig_type)))

        th_fams: list[str] = []
        if hasattr(th, "threat_families") and th.threat_families:
            th_fams = [str(getattr(f, "value", f)) for f in th.threat_families]

        init_st = None
        term_st = None
        if hasattr(th, "attack_path") and th.attack_path:
            raw_entry = getattr(th.attack_path, "entry_stage", getattr(th.attack_path, "initial_stage", None))
            init_st = str(getattr(raw_entry, "value", raw_entry)) if raw_entry else None
            raw_term = getattr(th.attack_path, "terminal_stage", None)
            term_st = str(getattr(raw_term, "value", raw_term)) if raw_term else None

        hi_count = len(th.high_impact_actions) if hasattr(th, "high_impact_actions") and th.high_impact_actions else len([a for a in action_summaries if a.impact_category in ("FINANCIAL_TRANSACTION", "CREDENTIAL_ACCESS")])

        threat_summary = FirewallThreatSummary(
            threat_signals=threat_signals,
            attack_stage=init_st,
            terminal_stage=term_st,
            threat_families=th_fams,
            high_impact_action_count=hi_count,
            confidence=th.confidence,
        )
    else:
        threat_summary = FirewallThreatSummary(
            threat_signals=[],
            attack_stage=None,
            terminal_stage=None,
            threat_families=[],
            high_impact_action_count=0,
            confidence=0.0,
        )

    # 8. Fingerprint
    if state.fingerprint is not None:
        fp = state.fingerprint
        m_type = str(getattr(fp.match_type, "value", fp.match_type))
        fp_id = fp.fingerprint.fingerprint_id if fp.fingerprint else None
        obs_count = fp.fingerprint.observation_count if fp.fingerprint else 0
        channels_count = len(fp.fingerprint.distinct_channels) if (fp.fingerprint and hasattr(fp.fingerprint, "distinct_channels")) else 0
        sig = fp.fingerprint.attack_path_signature if (fp.fingerprint and hasattr(fp.fingerprint, "attack_path_signature")) else None
        fingerprint_summary = FirewallFingerprintSummary(
            match_type=m_type,
            fingerprint_id=fp_id,
            match_confidence=fp.match_confidence,
            observation_count=obs_count,
            distinct_channels_count=channels_count,
            attack_path_signature=sig,
        )
    else:
        fingerprint_summary = FirewallFingerprintSummary(
            match_type="NO_MATCH",
            fingerprint_id=None,
            match_confidence=0.0,
            observation_count=0,
            distinct_channels_count=0,
            attack_path_signature=None,
        )

    # 9. Behaviour
    if state.behaviour is not None:
        bh = state.behaviour
        bh_signals = [str(getattr(s.signal_type, "value", s.signal_type)) for s in bh.signals]
        bh_findings = [f.description for f in bh.findings]
        time_press = bh.policy_hints.pressure_present or any("PRESSURE" in s or "URGENCY" in s for s in bh_signals)
        rapid_esc = bh.policy_hints.rapid_escalation_present or any("RAPID" in s for s in bh_signals)
        chan_mig = any("CHANNEL" in s for s in bh_signals)
        behaviour_summary = FirewallBehaviourSummary(
            signals=bh_signals,
            findings=bh_findings,
            session_id=result.session_id,
            events_in_session=bh.session_summary.event_count if bh.session_summary else 0,
            time_pressure_detected=time_press,
            rapid_escalation_detected=rapid_esc,
            channel_migration_detected=chan_mig,
        )
    else:
        behaviour_summary = FirewallBehaviourSummary(
            signals=[],
            findings=[],
            session_id=result.session_id,
            events_in_session=0,
            time_pressure_detected=False,
            rapid_escalation_detected=False,
            channel_migration_detected=False,
        )

    # Provenance sanitized
    safe_provenance = sanitize_sensitive_data(dict(result.provenance or {}))
    for forbidden in ["api_key", "secret", "token", "password", "connection_string", "auth"]:
        safe_provenance.pop(forbidden, None)

    c_at = getattr(context, "created_at", None) or getattr(state, "started_at", None) or datetime.now(timezone.utc).isoformat()
    d_at = getattr(state, "completed_at", None) or getattr(context, "updated_at", None) or datetime.now(timezone.utc).isoformat()

    raw_response = FirewallAnalysisResponse(
        analysis_id=result.analysis_id,
        session_id=result.session_id,
        pipeline_status=result.pipeline_status,
        created_at=c_at,
        completed_at=d_at,
        duration_ms=result.telemetry.total_duration_ms if result.telemetry else 0.0,
        decision=decision_summary,
        content=content_summary,
        claims=claim_summaries,
        actions=action_summaries,
        evidence=evidence_summary,
        identity=identity_summary,
        threat=threat_summary,
        fingerprint=fingerprint_summary,
        behaviour=behaviour_summary,
        provenance=safe_provenance,
        warnings=list(result.warnings),
        errors=list(result.errors),
    )

    sanitized_dict = sanitize_sensitive_data(raw_response.model_dump())
    return FirewallAnalysisResponse.model_validate(sanitized_dict)

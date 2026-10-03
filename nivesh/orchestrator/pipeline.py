"""Production-style Engine Pipeline & Dependency Graph for Nivesh Firewall (Phase 11.3).

Coordinates the execution of Engines 1 through 10 in canonical dependency-aware order:
- Explicit DAG and dependency rules
- Dependency-aware blocking (skipping dependent engines when prerequisites fail)
- Bounded retry for transient errors with side-effect protection
- Bounded timeout protection per engine invocation
- Safe cancellation handling (RUNNING -> CANCELLED)
- Policy Gate enforcement before Engine 8 policy finalization
- Idempotency protection against duplicate side effects
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from pydantic import BaseModel, Field

from .context import AnalysisContext, EngineStatus, PipelineStatus
from .errors import OrchestrationError
from nivesh.observability import metrics, tracer, engine_key_ctx


class CancellationToken:
    """Thread-safe cooperative cancellation token for in-flight pipeline analyses."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancelled = False
        self._reason = ""
        self._timestamp: Optional[str] = None

    def cancel(self, reason: str = "Execution cancelled by caller") -> None:
        """Signal cancellation for this token."""
        with self._lock:
            self._cancelled = True
            self._reason = reason
            self._timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        with self._lock:
            return self._cancelled

    @property
    def reason(self) -> str:
        """Retrieve reason for cancellation."""
        with self._lock:
            return self._reason

    @property
    def cancelled_at(self) -> Optional[str]:
        """Timestamp of cancellation."""
        with self._lock:
            return self._timestamp


class PipelineNode(BaseModel):
    """Represents a discrete engine execution node within the orchestration DAG."""
    engine_key: str = Field(description="Unique engine key (e.g. engine_1_content)")
    engine_name: str = Field(description="Human-readable engine title")
    dependencies: list[str] = Field(default_factory=list, description="Direct prerequisite engine keys")
    optional: bool = Field(default=False, description="Whether failure permits degraded downstream execution")


class PipelineGraph:
    """Canonical Dependency-Aware Execution Graph for Nivesh Firewall.

    Dependency Graph:
                        ENGINE 1
                           │
                           ▼
                        ENGINE 2
                           │
                           ▼
                        ENGINE 3
                           │
                           ▼
                        ENGINE 4
                           │
                           ▼
                        ENGINE 5
                           │
                 ┌─────────┼─────────┐
                 ▼         ▼         ▼
              ENGINE 6  ENGINE 7  ENGINE 9
                 │         │         │
                 └─────────┼─────────┘
                           ▼
                       ENGINE 10
                           │
                           ▼
                       ENGINE 8
                           │
                           ▼
                   FINAL POLICY
    """

    def __init__(self) -> None:
        self.nodes: dict[str, PipelineNode] = {
            "engine_1_content": PipelineNode(
                engine_key="engine_1_content",
                engine_name="Engine 1: Content Intelligence Engine",
                dependencies=[],
                optional=False,
            ),
            "engine_2_claims": PipelineNode(
                engine_key="engine_2_claims",
                engine_name="Engine 2: Claim Intelligence Engine",
                dependencies=["engine_1_content"],
                optional=False,
            ),
            "engine_3_actions": PipelineNode(
                engine_key="engine_3_actions",
                engine_name="Engine 3: Action Intelligence Engine",
                dependencies=["engine_1_content", "engine_2_claims"],
                optional=False,
            ),
            "engine_4_sources": PipelineNode(
                engine_key="engine_4_sources",
                engine_name="Engine 4: Source Intelligence Engine",
                dependencies=["engine_1_content", "engine_2_claims", "engine_3_actions"],
                optional=True,
            ),
            "engine_5_evidence": PipelineNode(
                engine_key="engine_5_evidence",
                engine_name="Engine 5: Evidence Verification Engine",
                dependencies=["engine_1_content", "engine_2_claims", "engine_4_sources"],
                optional=True,
            ),
            "engine_6_threat": PipelineNode(
                engine_key="engine_6_threat",
                engine_name="Engine 6: Threat & Attack-Path Intelligence",
                dependencies=["engine_1_content", "engine_2_claims", "engine_3_actions", "engine_5_evidence"],
                optional=True,
            ),
            "engine_7_fingerprint": PipelineNode(
                engine_key="engine_7_fingerprint",
                engine_name="Engine 7: Scam Fingerprint & Collective Intelligence",
                dependencies=["engine_1_content", "engine_2_claims", "engine_3_actions", "engine_6_threat"],
                optional=True,
            ),
            "engine_9_identity": PipelineNode(
                engine_key="engine_9_identity",
                engine_name="Engine 9: Identity Verification & Entity Resolution",
                dependencies=["engine_1_content", "engine_2_claims"],
                optional=True,
            ),
            "engine_10_behaviour": PipelineNode(
                engine_key="engine_10_behaviour",
                engine_name="Engine 10: Behavioural Signal Intelligence",
                dependencies=["engine_1_content", "engine_2_claims", "engine_3_actions"],
                optional=True,
            ),
            "engine_8_policy": PipelineNode(
                engine_key="engine_8_policy",
                engine_name="Engine 8: Policy & Intervention Engine",
                dependencies=["engine_1_content", "engine_2_claims", "engine_3_actions"],
                optional=False,
            ),
        }

    def can_execute(
        self,
        engine_key: str,
        context: AnalysisContext,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Verify whether an engine's required dependencies are satisfied.

        Returns:
            (can_execute, failed_dependency_key, failure_reason)
        """
        node = self.nodes.get(engine_key)
        if not node:
            return True, None, None

        for dep_key in node.dependencies:
            dep_state = context.engine_states.get(dep_key)
            if not dep_state:
                return False, dep_key, f"Prerequisite {dep_key} is not registered in context"

            # Check if dependency failed
            if dep_state.status == EngineStatus.FAILED:
                return False, dep_key, f"Prerequisite {dep_key} failed; execution blocked"

            # Check if dependency was skipped or blocked
            if dep_state.status == EngineStatus.SKIPPED:
                return False, dep_key, f"Prerequisite {dep_key} was skipped; execution blocked"

            # Check if dependency was cancelled
            if dep_state.status == EngineStatus.CANCELLED:
                return False, dep_key, f"Prerequisite {dep_key} was cancelled; execution blocked"

            # Check if dependency is still pending or running
            if dep_state.status in (EngineStatus.PENDING, EngineStatus.RUNNING):
                return False, dep_key, f"Prerequisite {dep_key} is unresolved ({dep_state.status.value})"

        return True, None, None


class PolicyGate:
    """Enforces strict prerequisite verification before Engine 8 policy invocation.

    Engine 8 is the final policy decision authority.
    The orchestrator does NOT make policy decisions; it verifies that available
    intelligence context is coherent before passing it to Engine 8.
    """

    @classmethod
    def verify_gate(
        cls,
        context: AnalysisContext,
        allow_degraded: bool = True,
    ) -> tuple[bool, list[str]]:
        """Verify whether Engine 8 is permitted to execute.

        Checks (Section 11.3.4):
        1. Required content exists
        2. Required claims and actions state is valid
        3. Relevant source and evidence results are represented where required
        4. Threat result is represented where required
        5. Fingerprint result is represented where required
        6. Identity result is represented where required
        7. Behavioural result is represented where required
        8. No prerequisite is in an unresolved RUNNING or PENDING state
        """
        reasons: list[str] = []

        # 1. Required content exists
        if not context.content:
            reasons.append("Policy Gate blocked: Engine 1 content is missing or failed")

        # 2. Required claims and actions state is valid
        if not context.claims:
            reasons.append("Policy Gate blocked: Engine 2 claims are missing or failed")
        if not context.actions:
            reasons.append("Policy Gate blocked: Engine 3 actions are missing or failed")

        # Cancellation check
        if context.status == PipelineStatus.CANCELLED:
            reasons.append("Policy Gate blocked: Pipeline was cancelled")

        # 8. No prerequisite is in an unresolved RUNNING or PENDING state
        for key, st in context.engine_states.items():
            if key != "engine_8_policy":
                if st.status == EngineStatus.RUNNING:
                    reasons.append(f"Policy Gate blocked: Engine {key} is still in RUNNING state")
                elif st.status == EngineStatus.PENDING and not allow_degraded:
                    reasons.append(f"Policy Gate blocked: Engine {key} is still in PENDING state")

        # 3-7. If degradation is disabled, all downstream engines must be represented
        if not allow_degraded:
            if not context.sources:
                reasons.append("Policy Gate blocked: Engine 4 sources missing and degradation disabled")
            if not context.evidence:
                reasons.append("Policy Gate blocked: Engine 5 evidence missing and degradation disabled")
            if not context.threat:
                reasons.append("Policy Gate blocked: Engine 6 threat analysis missing and degradation disabled")
            if not context.fingerprint:
                reasons.append("Policy Gate blocked: Engine 7 fingerprint missing and degradation disabled")
            if not context.identity:
                reasons.append("Policy Gate blocked: Engine 9 identity missing and degradation disabled")
            if not context.behaviour:
                reasons.append("Policy Gate blocked: Engine 10 behaviour missing and degradation disabled")

        passes = len(reasons) == 0
        return passes, reasons


class SafeEngineExecutor:
    """Executes an individual engine with bounded timeouts, retries, and side-effect protections."""

    @classmethod
    def execute(
        cls,
        func: Callable[..., Any],
        *args: Any,
        engine_key: str,
        engine_name: str,
        timeout_ms: Optional[float] = None,
        max_retries: int = 0,
        retry_delay_ms: float = 0.0,
        cancellation_token: Optional[CancellationToken] = None,
        **kwargs: Any,
    ) -> tuple[Any, float, int, Optional[Exception]]:
        """Execute callable with cancellation check, timeout enforcement, and bounded retry.

        Returns:
            (result, duration_ms, retry_count, error)
        """
        engine_token = engine_key_ctx.set(engine_key)
        span = tracer.start_span(
            name=f"engine_{engine_key}",
            attributes={"engine_key": engine_key, "engine_name": engine_name},
        )
        try:
            if cancellation_token and cancellation_token.is_cancelled:
                span.finish(status="CANCELLED")
                return None, 0.0, 0, OrchestrationError(f"Cancelled before {engine_name} execution")

            t_start = time.perf_counter()
            attempt = 0
            last_error: Optional[Exception] = None

            while attempt <= max_retries:
                if cancellation_token and cancellation_token.is_cancelled:
                    dur = round((time.perf_counter() - t_start) * 1000, 2)
                    span.finish(status="CANCELLED")
                    return None, dur, attempt, OrchestrationError(
                        f"Cancelled during retry of {engine_name}"
                    )

                t_attempt_start = time.perf_counter()
                try:
                    if timeout_ms is not None and timeout_ms > 0:
                        timeout_sec = timeout_ms / 1000.0
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(func, *args, **kwargs)
                            try:
                                result = future.result(timeout=timeout_sec)
                                dur = round((time.perf_counter() - t_start) * 1000, 2)
                                metrics.engine_executions_total.inc(engine_key=engine_key, status="SUCCESS")
                                metrics.engine_duration_seconds.observe(dur / 1000.0, engine_key=engine_key, status="SUCCESS")
                                if attempt > 0:
                                    metrics.engine_retries_total.inc(value=attempt, engine_key=engine_key)
                                span.finish(status="OK")
                                return result, dur, attempt, None
                            except FutureTimeoutError as te:
                                metrics.engine_timeouts_total.inc(engine_key=engine_key)
                                raise TimeoutError(
                                    f"{engine_name} exceeded execution timeout of {timeout_ms}ms"
                                ) from te
                    else:
                        result = func(*args, **kwargs)
                        dur = round((time.perf_counter() - t_start) * 1000, 2)
                        metrics.engine_executions_total.inc(engine_key=engine_key, status="SUCCESS")
                        metrics.engine_duration_seconds.observe(dur / 1000.0, engine_key=engine_key, status="SUCCESS")
                        if attempt > 0:
                            metrics.engine_retries_total.inc(value=attempt, engine_key=engine_key)
                        span.finish(status="OK")
                        return result, dur, attempt, None

                except Exception as e:
                    last_error = e
                    attempt += 1
                    if attempt <= max_retries:
                        if retry_delay_ms > 0:
                            time.sleep(retry_delay_ms / 1000.0)

            total_dur = round((time.perf_counter() - t_start) * 1000, 2)
            metrics.engine_executions_total.inc(engine_key=engine_key, status="FAILED")
            metrics.engine_duration_seconds.observe(total_dur / 1000.0, engine_key=engine_key, status="FAILED")
            if attempt > 1:
                metrics.engine_retries_total.inc(value=attempt - 1, engine_key=engine_key)
            if isinstance(last_error, TimeoutError):
                span.finish(status="TIMEOUT")
            else:
                span.record_exception(last_error or Exception("Unknown engine error"))
                span.finish(status="ERROR")
            return None, total_dur, attempt - 1, last_error
        finally:
            engine_key_ctx.reset(engine_token)

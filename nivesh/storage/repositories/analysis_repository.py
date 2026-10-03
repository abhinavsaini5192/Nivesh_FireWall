"""Persistent Analysis Repository for Nivesh Firewall.

Persists completed or degraded analysis results, Engine 8 policy decisions,
structured intelligence summaries, and execution telemetry into relational storage.
Allows retrieval of analyses without re-running intelligence engines.
"""

from typing import Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from nivesh.orchestrator.result import OrchestrationResult
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
)
from nivesh.storage.models import (
    AnalysisModel,
    PolicyDecisionModel,
    AnalysisResultModel,
    EngineExecutionModel,
)
from nivesh.storage.errors import (
    AnalysisNotFoundError,
    ConstraintViolationError,
    StorageError,
    ForbiddenFieldError,
)
from nivesh.storage.database import get_db_session

FORBIDDEN_KEYS = frozenset({
    "password", "passwd", "pwd", "otp", "pin", "cvv", "cvc",
    "card_number", "account_number", "bank_account", "raw_credentials",
    "keystrokes", "secret", "private_key", "access_token",
})


def _validate_safe_content(data: Any) -> None:
    """Validate that forbidden raw credential field names are not present."""
    if isinstance(data, dict):
        for k, v in data.items():
            if str(k).lower() in FORBIDDEN_KEYS:
                raise ForbiddenFieldError(f"Forbidden field '{k}' detected in persistent payload.")
            _validate_safe_content(v)
    elif isinstance(data, list):
        for item in data:
            _validate_safe_content(item)


class AnalysisRepository:
    """Repository interface for persisting and retrieving Nivesh Analyses."""

    def save_analysis(
        self,
        result: OrchestrationResult,
        idempotency_key: Optional[str] = None,
    ) -> AnalysisModel:
        """Persist analysis result, policy decision, and telemetry atomically."""
        raise NotImplementedError

    def get_analysis(self, analysis_id: str) -> Optional[FirewallAnalysisResponse]:
        """Retrieve a persisted analysis reconstructed into a FirewallAnalysisResponse."""
        raise NotImplementedError

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an individual analysis record without deleting collective fingerprints."""
        raise NotImplementedError

    def exists(self, analysis_id: str) -> bool:
        """Check if an analysis exists by ID."""
        raise NotImplementedError


class SqlAlchemyAnalysisRepository(AnalysisRepository):
    """SQLAlchemy implementation of the AnalysisRepository."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory

    def save_analysis(
        self,
        result: OrchestrationResult,
        idempotency_key: Optional[str] = None,
    ) -> AnalysisModel:
        """Atomically persist analysis, policy decision, result summaries, and engine executions."""
        state = result.state
        context = result.context
        pd = result.policy_decision

        # Validate that no raw forbidden fields leaked into state metadata
        _validate_safe_content(context.execution_metadata)

        with get_db_session(session_factory=self._session_factory) as session:
            # Idempotency check: if key already exists, return existing
            if idempotency_key:
                existing = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.idempotency_key == idempotency_key)
                    .first()
                )
                if existing:
                    return existing

            # Also check if analysis_id already exists (idempotent retry)
            existing_id = (
                session.query(AnalysisModel)
                .filter(AnalysisModel.analysis_id == result.analysis_id)
                .first()
            )
            if existing_id:
                return existing_id

            # 1. Base Analysis Entity
            input_type = "unknown"
            channel = "unknown"
            content_id = None
            content_summary_text = None
            contains_financial = True
            if state.content is not None:
                c = state.content
                input_type = c.source.type
                channel = c.source.channel
                content_id = c.content_id
                content_summary_text = (
                    c.normalized.text[:200]
                    if c.normalized and c.normalized.text
                    else ""
                )
                contains_financial = getattr(c, "contains_financial_content", True)

            analysis = AnalysisModel(
                analysis_id=result.analysis_id,
                session_id=result.session_id,
                pipeline_status=result.pipeline_status,
                created_at=getattr(context, "created_at", None) or result.telemetry.started_at,
                completed_at=result.telemetry.completed_at or getattr(context, "updated_at", None),
                duration_ms=result.telemetry.total_duration_ms,
                input_type=input_type,
                channel=channel,
                content_id=content_id,
                content_summary=content_summary_text,
                contains_financial_content=contains_financial,
                idempotency_key=idempotency_key,
            )
            session.add(analysis)

            # 2. Engine 8 Policy Decision Entity
            if pd is not None:
                actions_req = list(getattr(pd, "actions_required", []))
                policy_model = PolicyDecisionModel(
                    decision_id=pd.decision_id,
                    analysis_id=result.analysis_id,
                    decision=str(getattr(pd.decision, "value", pd.decision)),
                    severity=str(getattr(pd.severity, "value", pd.severity)),
                    primary_reason=pd.primary_reason,
                    reason_codes=list(pd.reason_codes),
                    user_message=pd.user_message,
                    technical_message=pd.technical_message,
                    actions_required=actions_req,
                    required_user_confirmation=pd.required_user_confirmation,
                    cooldown_seconds=pd.cooldown_seconds,
                    policy_version=pd.policy_version,
                    created_at=getattr(pd, "created_at", None) or getattr(pd, "timestamp", None) or analysis.created_at,
                )
            else:
                fallback_decision = "PAUSE" if result.pipeline_status == "FAILED" else "INFORM"
                policy_model = PolicyDecisionModel(
                    decision_id=None,
                    analysis_id=result.analysis_id,
                    decision=fallback_decision,
                    severity="MEDIUM" if result.pipeline_status == "FAILED" else "NONE",
                    primary_reason="Pipeline incomplete before policy evaluation",
                    reason_codes=["PIPELINE_INCOMPLETE"],
                    user_message="Analysis could not be fully completed due to an internal execution event.",
                    technical_message="Pipeline execution halted before Engine 8 policy evaluation.",
                    actions_required=["RETRY_ANALYSIS"],
                    required_user_confirmation=False,
                    cooldown_seconds=None,
                    policy_version="8.0.0",
                    created_at=analysis.created_at,
                )
            session.add(policy_model)

            # 3. Structured Analysis Result Entity (JSON summaries)
            # Reuses format_firewall_response logic to serialize clean display models
            from nivesh.orchestrator.service import format_firewall_response
            resp = format_firewall_response(result)

            result_model = AnalysisResultModel(
                analysis_id=result.analysis_id,
                content_summary_json=resp.content.model_dump(),
                claims_json=[c.model_dump() for c in resp.claims],
                actions_json=[a.model_dump() for a in resp.actions],
                evidence_json=resp.evidence.model_dump(),
                identity_json=resp.identity.model_dump(),
                threat_json=resp.threat.model_dump(),
                fingerprint_json=resp.fingerprint.model_dump(),
                behaviour_json=resp.behaviour.model_dump(),
                provenance_json=dict(resp.provenance),
                warnings_json=list(resp.warnings),
                errors_json=list(resp.errors),
            )
            session.add(result_model)

            # 4. Engine Execution Telemetry Records
            for rec in result.telemetry.engine_records.values():
                exec_model = EngineExecutionModel(
                    analysis_id=result.analysis_id,
                    engine_key=rec.engine_key,
                    engine_name=rec.engine_name,
                    status=str(getattr(rec.status, "value", rec.status)),
                    started_at=rec.started_at,
                    completed_at=rec.completed_at,
                    duration_ms=rec.duration_ms,
                    output_id=rec.output_id,
                    error_type=rec.error_type,
                    error_message=rec.error_message,
                    retry_count=rec.retry_count,
                    metadata_json=dict(rec.metadata),
                )
                session.add(exec_model)

            session.flush()
            return analysis

    def get_analysis(self, analysis_id: str) -> Optional[FirewallAnalysisResponse]:
        """Retrieve a stored analysis and reconstruct the canonical FirewallAnalysisResponse."""
        with get_db_session(session_factory=self._session_factory) as session:
            analysis = (
                session.query(AnalysisModel)
                .options(
                    joinedload(AnalysisModel.policy_decision),
                    joinedload(AnalysisModel.result),
                )
                .filter(AnalysisModel.analysis_id == analysis_id)
                .first()
            )

            if not analysis or not analysis.result:
                return None

            pd = analysis.policy_decision
            res = analysis.result

            # Reconstruct FirewallDecisionSummary
            explanation = FirewallExplanation(
                decision=pd.decision if pd else "INFORM",
                user_message=pd.user_message if pd else "",
                technical_message=pd.technical_message if pd else "",
                primary_reason=pd.primary_reason if pd else "",
                supporting_signals=[],
            )
            decision_summary = FirewallDecisionSummary(
                decision=pd.decision if pd else "INFORM",
                severity=pd.severity if pd else "NONE",
                primary_reason=pd.primary_reason if pd else "",
                reason_codes=list(pd.reason_codes or []) if pd else [],
                explanation=explanation,
                actions_required=list(pd.actions_required or []) if pd else [],
                required_user_confirmation=pd.required_user_confirmation if pd else False,
                cooldown_seconds=pd.cooldown_seconds if pd else None,
                policy_version=pd.policy_version if pd else "8.0.0",
                decision_id=pd.decision_id if pd else None,
            )

            # Reconstruct summaries
            content_summary = FirewallContentSummary.model_validate(res.content_summary_json)
            claims = [FirewallClaimSummary.model_validate(c) for c in (res.claims_json or [])]
            actions = [FirewallActionSummary.model_validate(a) for a in (res.actions_json or [])]
            evidence = FirewallEvidenceSummary.model_validate(res.evidence_json)
            identity = FirewallIdentitySummary.model_validate(res.identity_json)
            threat = FirewallThreatSummary.model_validate(res.threat_json)
            fingerprint = FirewallFingerprintSummary.model_validate(res.fingerprint_json)
            behaviour = FirewallBehaviourSummary.model_validate(res.behaviour_json)

            return FirewallAnalysisResponse(
                analysis_id=analysis.analysis_id,
                session_id=analysis.session_id,
                pipeline_status=analysis.pipeline_status,
                created_at=analysis.created_at,
                completed_at=analysis.completed_at,
                duration_ms=analysis.duration_ms,
                decision=decision_summary,
                content=content_summary,
                claims=claims,
                actions=actions,
                evidence=evidence,
                identity=identity,
                threat=threat,
                fingerprint=fingerprint,
                behaviour=behaviour,
                provenance=dict(res.provenance_json or {}),
                warnings=list(res.warnings_json or []),
                errors=list(res.errors_json or []),
            )

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an individual analysis record and its child relations."""
        with get_db_session(session_factory=self._session_factory) as session:
            analysis = (
                session.query(AnalysisModel)
                .filter(AnalysisModel.analysis_id == analysis_id)
                .first()
            )
            if not analysis:
                return False
            session.delete(analysis)
            return True

    def exists(self, analysis_id: str) -> bool:
        """Check if an analysis exists in storage."""
        with get_db_session(session_factory=self._session_factory) as session:
            count = (
                session.query(AnalysisModel)
                .filter(AnalysisModel.analysis_id == analysis_id)
                .count()
            )
            return count > 0

    def list_engine_executions(self, analysis_id: str) -> list[dict[str, Any]]:
        """Retrieve telemetry engine executions for an analysis."""
        with get_db_session(session_factory=self._session_factory) as session:
            records = (
                session.query(EngineExecutionModel)
                .filter(EngineExecutionModel.analysis_id == analysis_id)
                .order_by(EngineExecutionModel.id.asc())
                .all()
            )
            return [
                {
                    "engine_key": r.engine_key,
                    "engine_name": r.engine_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "retry_count": r.retry_count,
                    "error_message": r.error_message,
                    "metadata": r.metadata_json,
                }
                for r in records
            ]

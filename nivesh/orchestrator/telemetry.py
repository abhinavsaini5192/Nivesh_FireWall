"""Observability and execution telemetry for the Product Orchestrator.

Captures high-level execution timestamps, durations, statuses, output references,
and error summaries without storing sensitive credentials or raw message text.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field

from .errors import EngineOutcomeType


class EngineExecutionRecord(BaseModel):
    """Execution telemetry for a single intelligence engine invocation."""
    engine_name: str = Field(description="Human-readable engine name (e.g. Engine 1: Content Intelligence)")
    engine_key: str = Field(description="Internal machine identifier (e.g. engine_1_content)")
    engine_version: Optional[str] = Field(default=None, description="Engine release version if available")
    started_at: str = Field(description="ISO 8601 timestamp of invocation start")
    completed_at: Optional[str] = Field(default=None, description="ISO 8601 timestamp of invocation completion")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
    status: EngineOutcomeType = Field(default=EngineOutcomeType.SUCCESS, description="Categorical execution outcome")
    output_id: Optional[str] = Field(default=None, description="Identifier of produced output (e.g. analysis_id, content_id)")
    analytical_result: Optional[str] = Field(default=None, description="Expected analytical flag (e.g. NO_MATCH, NOT_ESTABLISHED)")
    error_type: Optional[str] = Field(default=None, description="Exception class name if an error occurred")
    error_message: Optional[str] = Field(default=None, description="Sanitized summary of error message")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe structural telemetry metadata")


class PipelineTelemetry(BaseModel):
    """Aggregate execution telemetry for an entire orchestration run."""
    total_duration_ms: float = Field(default=0.0, description="Total pipeline execution duration in milliseconds")
    started_at: Optional[str] = Field(default=None, description="ISO 8601 pipeline start timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO 8601 pipeline completion timestamp")
    engines_executed: list[str] = Field(default_factory=list, description="Ordered list of executed engine keys")
    engines_succeeded: list[str] = Field(default_factory=list, description="List of engine keys that completed successfully")
    engines_degraded: list[str] = Field(default_factory=list, description="List of engine keys that failed recoverably")
    engine_records: dict[str, EngineExecutionRecord] = Field(
        default_factory=dict, description="Detailed records indexed by engine key"
    )

    def record_engine(self, record: EngineExecutionRecord) -> None:
        """Add or update an engine execution record."""
        self.engine_records[record.engine_key] = record
        if record.engine_key not in self.engines_executed:
            self.engines_executed.append(record.engine_key)
        if record.status in (EngineOutcomeType.SUCCESS, EngineOutcomeType.EXPECTED_ANALYTICAL_RESULT):
            if record.engine_key not in self.engines_succeeded:
                self.engines_succeeded.append(record.engine_key)
        elif record.status == EngineOutcomeType.RECOVERABLE_FAILURE:
            if record.engine_key not in self.engines_degraded:
                self.engines_degraded.append(record.engine_key)

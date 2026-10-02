"""Product Orchestrator Core for Nivesh Firewall.

Coordinates all 10 intelligence engines into a unified analysis pipeline.
"""

from .errors import (
    EngineOutcomeType,
    OrchestrationError,
    FatalOrchestrationError,
    RecoverableEngineError,
    InputIngestionError,
)
from .telemetry import EngineExecutionRecord, PipelineTelemetry
from .config import OrchestratorConfig
from .state import OrchestrationState
from .result import OrchestrationResult
from .service import ProductOrchestrator
from .context import (
    AnalysisContext,
    PipelineStatus,
    EngineStatus,
    ContextLifecycleStage,
    EngineExecutionState,
    ContextSnapshot,
)

__all__ = [
    "ProductOrchestrator",
    "OrchestratorConfig",
    "OrchestrationResult",
    "OrchestrationState",
    "AnalysisContext",
    "PipelineStatus",
    "EngineStatus",
    "ContextLifecycleStage",
    "EngineExecutionState",
    "ContextSnapshot",
    "PipelineTelemetry",
    "EngineExecutionRecord",
    "EngineOutcomeType",
    "OrchestrationError",
    "FatalOrchestrationError",
    "RecoverableEngineError",
    "InputIngestionError",
]

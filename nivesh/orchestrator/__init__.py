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
from .service import ProductOrchestrator, format_firewall_response, sanitize_sensitive_data
from .context import (
    AnalysisContext,
    PipelineStatus,
    EngineStatus,
    ContextLifecycleStage,
    EngineExecutionState,
    ContextSnapshot,
)

from .pipeline import (
    CancellationToken,
    PipelineNode,
    PipelineGraph,
    PolicyGate,
    SafeEngineExecutor,
)
from nivesh.schemas.firewall import (
    FirewallAnalyzeRequest,
    FirewallAnalysisResponse,
    FirewallApiError,
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
    "CancellationToken",
    "PipelineNode",
    "PipelineGraph",
    "PolicyGate",
    "SafeEngineExecutor",
    "format_firewall_response",
    "sanitize_sensitive_data",
    "FirewallAnalyzeRequest",
    "FirewallAnalysisResponse",
    "FirewallApiError",
    "FirewallDecisionSummary",
    "FirewallExplanation",
    "FirewallContentSummary",
    "FirewallClaimSummary",
    "FirewallActionSummary",
    "FirewallEvidenceSummary",
    "FirewallIdentitySummary",
    "FirewallThreatSummary",
    "FirewallFingerprintSummary",
    "FirewallBehaviourSummary",
]

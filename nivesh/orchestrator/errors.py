"""Error and classification models for the Product Orchestrator.

Distinguishes:
A. Engine success
B. Expected analytical results (NO_MATCH, NOT_ESTABLISHED, INSUFFICIENT_EVIDENCE, SOURCE_UNAVAILABLE)
C. Recoverable engine failures (graceful pipeline continuation with degraded telemetry)
D. Fatal orchestration failures (pipeline cannot proceed meaningfully)
"""

from enum import Enum
from typing import Optional


class EngineOutcomeType(str, Enum):
    """Categorical classification of an engine invocation outcome."""
    SUCCESS = "SUCCESS"
    EXPECTED_ANALYTICAL_RESULT = "EXPECTED_ANALYTICAL_RESULT"
    RECOVERABLE_FAILURE = "RECOVERABLE_FAILURE"
    FATAL_FAILURE = "FATAL_FAILURE"


class OrchestrationError(Exception):
    """Base exception for all product orchestration errors."""

    def __init__(self, message: str, engine_name: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.engine_name = engine_name


class FatalOrchestrationError(OrchestrationError):
    """Unrecoverable failure preventing meaningful pipeline completion (e.g. missing raw input)."""
    pass


class RecoverableEngineError(OrchestrationError):
    """Recoverable engine failure where pipeline continues with degraded telemetry."""
    pass


class InputIngestionError(FatalOrchestrationError):
    """Raised when raw input cannot be processed by Engine 1."""
    pass

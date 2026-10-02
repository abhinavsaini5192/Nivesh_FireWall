"""Evidence Verification Engine (Engine 5 of Nivesh Firewall).

Evaluates retrieved source material against canonical claims:
- Identifies supporting, partially supporting, and contradicting evidence
- Detects context gaps, missing elements, and source conflicts
- Produces auditable reasoning traces and uncertainty indicators.
"""

from .engine import EvidenceVerificationEngine, ENGINE_VERSION
from .evaluator import ClaimEvidenceEvaluator
from .regulatory_evaluator import RegulatoryEvaluator
from .numerical_evaluator import NumericalEvaluator
from .opinion_prediction_evaluator import OpinionPredictionEvaluator
from .conflict_detector import ConflictDetector
from .llm_verifier import LlmEvidenceVerifier

__all__ = [
    "EvidenceVerificationEngine",
    "ENGINE_VERSION",
    "ClaimEvidenceEvaluator",
    "RegulatoryEvaluator",
    "NumericalEvaluator",
    "OpinionPredictionEvaluator",
    "ConflictDetector",
    "LlmEvidenceVerifier",
]

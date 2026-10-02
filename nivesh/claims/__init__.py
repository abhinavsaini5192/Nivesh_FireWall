"""Claims Intelligence Engine exports for Engine 2."""

from .engine import ClaimIntelligenceEngine, ENGINE_VERSION
from .segmenter import ClaimSegmenter, CandidateSegment
from .canonicalizer import ClaimCanonicalizer
from .modality import ModalityDetector
from .temporal import TemporalDetector
from .verification_reqs import VerificationRequirementsGenerator
from .relation_detector import RelationDetector
from .deduplicator import ClaimDeduplicator
from .llm_adapter import LlmClaimAdapter

__all__ = [
    "ClaimIntelligenceEngine",
    "ENGINE_VERSION",
    "ClaimSegmenter",
    "CandidateSegment",
    "ClaimCanonicalizer",
    "ModalityDetector",
    "TemporalDetector",
    "VerificationRequirementsGenerator",
    "RelationDetector",
    "ClaimDeduplicator",
    "LlmClaimAdapter",
]

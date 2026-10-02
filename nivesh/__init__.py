"""Nivesh Firewall — Engine 1: Content Intelligence Engine.

Converts raw user-provided financial content into clean, normalized,
structured representation for downstream security engines.
"""

from .engine import ContentIntelligenceEngine, ENGINE_VERSION
from .claims import ClaimIntelligenceEngine
from .actions import ActionIntelligenceEngine
from .sources import SourceIntelligenceEngine
from .evidence import EvidenceVerificationEngine
from .schemas import (
    ContentInput,
    NormalizedContent,
    SourceInfo,
    RawContent,
    NormalizedText,
    EntityItem,
    EntitiesContainer,
    UrlSignal,
    DomainSignal,
    SocialHandleSignal,
    RegistrationNumberSignal,
    CurrencyAmountSignal,
    PercentageSignal,
    DateSignal,
    CallToAction,
    StructuredSignals,
    ContentFeatures,
    Provenance,
    ClaimAnalysis,
    CanonicalClaim,
    ClaimRelation,
    ActionAnalysis,
    CanonicalAction,
    ActionRelation,
    SourceAnalysis,
    SourceDocument,
    EvidenceCandidate,
    ClaimSourceResult,
    ClaimVerificationStatus,
    EvidenceRelationType,
    EvidenceStrength,
    RegulatoryFinding,
    VerificationResult,
    EvidenceAnalysis,
)

__version__ = ENGINE_VERSION

__all__ = [
    "ContentIntelligenceEngine",
    "ClaimIntelligenceEngine",
    "ActionIntelligenceEngine",
    "SourceIntelligenceEngine",
    "EvidenceVerificationEngine",
    "ENGINE_VERSION",
    "ContentInput",
    "NormalizedContent",
    "SourceInfo",
    "RawContent",
    "NormalizedText",
    "EntityItem",
    "EntitiesContainer",
    "UrlSignal",
    "DomainSignal",
    "SocialHandleSignal",
    "RegistrationNumberSignal",
    "CurrencyAmountSignal",
    "PercentageSignal",
    "DateSignal",
    "CallToAction",
    "StructuredSignals",
    "ContentFeatures",
    "Provenance",
    "ClaimAnalysis",
    "CanonicalClaim",
    "ClaimRelation",
    "ActionAnalysis",
    "CanonicalAction",
    "ActionRelation",
    "SourceAnalysis",
    "SourceDocument",
    "EvidenceCandidate",
    "ClaimSourceResult",
    "ClaimVerificationStatus",
    "EvidenceRelationType",
    "EvidenceStrength",
    "RegulatoryFinding",
    "VerificationResult",
    "EvidenceAnalysis",
]



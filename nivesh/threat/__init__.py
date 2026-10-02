"""Nivesh Firewall — Engine 6: Threat & Attack-Path Intelligence Engine.

Constructs structured attack paths, identifies stage transitions, connects
claims to requested actions, surfaces evidence gaps, and evaluates threat families.
"""

from .engine import ThreatIntelligenceEngine, ENGINE_VERSION
from .signal_detector import ThreatSignalDetector
from .claim_action_linker import ClaimActionLinker
from .attack_path_builder import AttackPathBuilder
from .impact_evaluator import ImpactEvaluator
from .combination_engine import CombinationEngine
from .explainer import ThreatExplainer

__all__ = [
    "ThreatIntelligenceEngine",
    "ENGINE_VERSION",
    "ThreatSignalDetector",
    "ClaimActionLinker",
    "AttackPathBuilder",
    "ImpactEvaluator",
    "CombinationEngine",
    "ThreatExplainer",
]

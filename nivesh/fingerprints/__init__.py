"""Nivesh Firewall — Engine 7: Scam Fingerprint & Collective Threat Intelligence Engine.

Builds privacy-preserving scam fingerprints, matches structural variants,
maintains collective memory across observations, and protects against content amplification.
"""

from .engine import ScamFingerprintEngine, ENGINE_VERSION
from .feature_extractor import NormalizedFeatureExtractor
from .matcher import FingerprintMatcher
from .repository import FingerprintRepository

__all__ = [
    "ScamFingerprintEngine",
    "ENGINE_VERSION",
    "NormalizedFeatureExtractor",
    "FingerprintMatcher",
    "FingerprintRepository",
]

"""Source Intelligence Engine (Engine 4 of Nivesh Firewall).

Discovers authoritative sources, retrieves source documents, extracts structured
evidence candidates, and preserves complete provenance without making truth or scam judgments.
"""

from .engine import SourceIntelligenceEngine, ENGINE_VERSION
from .catalog import SourceCatalog
from .router import SourceRouter
from .cache import SourceCache
from .rate_limiter import RateLimiter
from .normalizer import SourceNormalizer
from .ssrf import SsrfValidator, SsrfError
from .adapters import (
    BaseSourceAdapter,
    SEBIAdapter,
    NSEAdapter,
    BSEAdapter,
    RBIAdapter,
    CompanySourceAdapter,
)

__all__ = [
    "SourceIntelligenceEngine",
    "ENGINE_VERSION",
    "SourceCatalog",
    "SourceRouter",
    "SourceCache",
    "RateLimiter",
    "SourceNormalizer",
    "SsrfValidator",
    "SsrfError",
    "BaseSourceAdapter",
    "SEBIAdapter",
    "NSEAdapter",
    "BSEAdapter",
    "RBIAdapter",
    "CompanySourceAdapter",
]

"""Engine 9: Identity Verification & Entity Resolution Engine for Nivesh Firewall.

Exports canonical engine, typed schemas, and resolver components.
"""

from nivesh.identity.schemas import (
    IdentityEntityType,
    IdentityStatus,
    IdentityMatchStatus,
    IdentityFindingType,
    IdentityRelationshipType,
    ClaimedEntity,
    ResolvedEntity,
    IdentityMatch,
    AuthorityAlignment,
    DomainAlignment,
    IdentityFinding,
    IdentityProvenance,
    IdentityAnalysis,
    ENGINE_VERSION,
)
from nivesh.identity.normalizer import IdentityNormalizer
from nivesh.identity.entity_resolver import EntityResolver
from nivesh.identity.registration_resolver import RegistrationResolver
from nivesh.identity.domain_resolver import DomainResolver
from nivesh.identity.authority_resolver import AuthorityResolver
from nivesh.identity.social_resolver import SocialResolver
from nivesh.identity.matcher import IdentityMatcher
from nivesh.identity.findings import IdentityFindingGenerator
from nivesh.identity.provenance import ProvenanceBuilder
from nivesh.identity.engine import IdentityVerificationEngine

__all__ = [
    "IdentityVerificationEngine",
    "IdentityEntityType",
    "IdentityStatus",
    "IdentityMatchStatus",
    "IdentityFindingType",
    "IdentityRelationshipType",
    "ClaimedEntity",
    "ResolvedEntity",
    "IdentityMatch",
    "AuthorityAlignment",
    "DomainAlignment",
    "IdentityFinding",
    "IdentityProvenance",
    "IdentityAnalysis",
    "ENGINE_VERSION",
    "IdentityNormalizer",
    "EntityResolver",
    "RegistrationResolver",
    "DomainResolver",
    "AuthorityResolver",
    "SocialResolver",
    "IdentityMatcher",
    "IdentityFindingGenerator",
    "ProvenanceBuilder",
]

"""Nivesh Firewall — Engine 8: Policy & Intervention Engine.

Determines and explains the appropriate investor-protection intervention
for user interactions based on structured intelligence from Engines 1–7.
"""

from nivesh.policy.config import (
    POLICY_VERSION,
    DEFAULT_COOLDOWN_PAUSE_SECONDS,
    DEFAULT_COOLDOWN_BLOCK_SECONDS,
)
from nivesh.policy.reason_codes import ReasonCode
from nivesh.policy.schemas import (
    PolicyDecisionType,
    InterventionScope,
    PolicySeverity,
    PolicyContext,
    PolicyRuleResult,
    PolicyDecision,
)
from nivesh.policy.rules import POLICY_RULES, PolicyRule
from nivesh.policy.evaluator import PolicyEvaluator
from nivesh.policy.precedence import PolicyPrecedenceResolver
from nivesh.policy.explain import PolicyExplainer
from nivesh.policy.engine import PolicyInterventionEngine

__all__ = [
    "POLICY_VERSION",
    "DEFAULT_COOLDOWN_PAUSE_SECONDS",
    "DEFAULT_COOLDOWN_BLOCK_SECONDS",
    "ReasonCode",
    "PolicyDecisionType",
    "InterventionScope",
    "PolicySeverity",
    "PolicyContext",
    "PolicyRuleResult",
    "PolicyDecision",
    "PolicyRule",
    "POLICY_RULES",
    "PolicyEvaluator",
    "PolicyPrecedenceResolver",
    "PolicyExplainer",
    "PolicyInterventionEngine",
]

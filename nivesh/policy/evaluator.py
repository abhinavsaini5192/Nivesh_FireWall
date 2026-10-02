"""Policy Evaluator for Engine 8.

Iterates through policy rules, evaluates conditions against structured
intelligence from Engines 1–7, and collects all triggered rule results.
"""

from typing import Optional
from nivesh.policy.schemas import PolicyRuleResult, PolicyContext
from nivesh.policy.rules import POLICY_RULES, PolicyRule
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis


class PolicyEvaluator:
    """Evaluates registered policy rules against structured engine intelligence."""

    def __init__(self, rules: Optional[list[PolicyRule]] = None):
        self.rules = rules or POLICY_RULES

    def evaluate_all(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
        threat: ThreatAnalysis,
        fingerprint: FingerprintAnalysis,
        identity: Optional[Any] = None,
        context: Optional[PolicyContext] = None,
    ) -> list[PolicyRuleResult]:
        """Evaluates every rule and returns all matching results in order."""
        triggered: list[PolicyRuleResult] = []

        for rule in self.rules:
            result = rule.evaluate(
                content=content,
                claims=claims,
                actions=actions,
                sources=sources,
                evidence=evidence,
                threat=threat,
                fingerprint=fingerprint,
                identity=identity,
                context=context,
            )
            if result:
                triggered.append(result)

        return triggered

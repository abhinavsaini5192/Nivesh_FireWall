"""Deterministic precedence resolution for Engine 8.

Resolves multiple triggered policy rules according to strict hierarchical precedence:
BLOCK > PAUSE > WARN > INFORM > ALLOW

Aggregates reason codes, supporting explanations, and triggered signals.
"""

from typing import Optional
from nivesh.policy.schemas import (
    PolicyDecisionType,
    PolicySeverity,
    InterventionScope,
    PolicyRuleResult,
    PolicyContext,
)
from nivesh.policy.reason_codes import ReasonCode


class PolicyPrecedenceResolver:
    """Deterministically resolves conflicting rule evaluations."""

    DECISION_PRECEDENCE: dict[PolicyDecisionType, int] = {
        PolicyDecisionType.BLOCK: 5,
        PolicyDecisionType.PAUSE: 4,
        PolicyDecisionType.WARN: 3,
        PolicyDecisionType.INFORM: 2,
        PolicyDecisionType.ALLOW: 1,
    }

    SEVERITY_PRECEDENCE: dict[PolicySeverity, int] = {
        PolicySeverity.CRITICAL: 5,
        PolicySeverity.HIGH: 4,
        PolicySeverity.MEDIUM: 3,
        PolicySeverity.LOW: 2,
        PolicySeverity.NONE: 1,
    }

    @classmethod
    def resolve(
        cls,
        triggered_rules: list[PolicyRuleResult],
        context: Optional[PolicyContext] = None,
    ) -> PolicyRuleResult:
        """Selects primary decision and aggregates metadata across all triggered rules."""
        if not triggered_rules:
            # Fallback default: ALLOW
            return PolicyRuleResult(
                rule_id="RULE-ALLOW-DEFAULT",
                rule_name="Default Allow Baseline",
                decision=PolicyDecisionType.ALLOW,
                severity=PolicySeverity.NONE,
                scope=InterventionScope.INFORMATION_ONLY,
                reason_codes=[ReasonCode.NO_INTERVENTION_REQUIRED],
                primary_reason="No safety policy rules triggered.",
                supporting_reasons=["Baseline interaction permitted."],
                triggered_signals=[],
                required_user_confirmation=False,
            )

        # Sort triggered rules by decision precedence descending, then by rule priority order
        sorted_rules = sorted(
            triggered_rules,
            key=lambda r: cls.DECISION_PRECEDENCE.get(r.decision, 0),
            reverse=True,
        )

        primary_rule = sorted_rules[0]

        # Handle user override if present and applicable
        active_decision = primary_rule.decision
        active_severity = primary_rule.severity
        active_req_confirm = primary_rule.required_user_confirmation
        override_applied = False

        if context and context.user_override is True:
            # Overrides are permitted for PAUSE (acting as user acknowledging and continuing)
            if active_decision == PolicyDecisionType.PAUSE:
                active_decision = PolicyDecisionType.WARN
                active_severity = PolicySeverity.MEDIUM
                active_req_confirm = False
                override_applied = True
            # Overrides cannot bypass BLOCK (safety invariant)

        # Aggregate reason codes, supporting reasons, and signals across all matching rules
        aggregated_codes: list[str] = []
        aggregated_supporting: list[str] = []
        aggregated_signals: list[str] = []

        seen_codes: set[str] = set()
        seen_supporting: set[str] = set()
        seen_signals: set[str] = set()

        if override_applied:
            aggregated_codes.append(ReasonCode.USER_OVERRIDE_APPLIED)
            seen_codes.add(ReasonCode.USER_OVERRIDE_APPLIED)

        for r in sorted_rules:
            for c in r.reason_codes:
                if c not in seen_codes:
                    seen_codes.add(c)
                    aggregated_codes.append(c)

            for s in r.supporting_reasons:
                if s not in seen_supporting:
                    seen_supporting.add(s)
                    aggregated_supporting.append(s)

            for sig in r.triggered_signals:
                if sig not in seen_signals:
                    seen_signals.add(sig)
                    aggregated_signals.append(sig)

        return PolicyRuleResult(
            rule_id=primary_rule.rule_id,
            rule_name=primary_rule.rule_name,
            decision=active_decision,
            severity=active_severity,
            scope=primary_rule.scope,
            reason_codes=aggregated_codes,
            primary_reason=primary_rule.primary_reason,
            supporting_reasons=aggregated_supporting,
            triggered_signals=aggregated_signals,
            required_user_confirmation=active_req_confirm,
            cooldown_seconds=primary_rule.cooldown_seconds,
        )

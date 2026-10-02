"""Explainability generator for Engine 8.

Generates neutral, objective, non-accusatory user-facing messages
and structured technical messages for auditing and enforcement adapters.
"""

from nivesh.policy.schemas import PolicyRuleResult, PolicyDecisionType


class PolicyExplainer:
    """Generates non-accusatory, evidence-based user and technical messages."""

    @classmethod
    def generate_user_message(cls, result: PolicyRuleResult) -> str:
        """Constructs a clean, non-accusatory user-facing explanation."""
        decision = result.decision

        if decision == PolicyDecisionType.ALLOW:
            return (
                "Interaction permitted. Nivesh Firewall detected no significant threat "
                "patterns, unverified authority claims, or high-impact safety concerns."
            )

        if decision == PolicyDecisionType.INFORM:
            return (
                f"Informational notice: {result.primary_reason} "
                "Verification context is displayed for your awareness."
            )

        if decision == PolicyDecisionType.WARN:
            return (
                f"Caution advised: {result.primary_reason} "
                "Please verify regulatory credentials and source information before proceeding."
            )

        if decision == PolicyDecisionType.PAUSE:
            return (
                f"Pause before continuing: {result.primary_reason} "
                "This action involves high-impact financial operations. Please review the findings "
                "carefully before confirming if you wish to proceed."
            )

        if decision == PolicyDecisionType.BLOCK:
            return (
                f"Action blocked by safety policy: {result.primary_reason} "
                "Continuing this action is restricted under the current investor-protection policy."
            )

        return result.primary_reason

    @classmethod
    def generate_technical_message(cls, result: PolicyRuleResult) -> str:
        """Constructs a machine-readable technical audit string."""
        codes_str = ", ".join(result.reason_codes)
        signals_str = ", ".join(result.triggered_signals) if result.triggered_signals else "NONE"
        return (
            f"DECISION={result.decision.value} | "
            f"RULE={result.rule_id} | "
            f"SEVERITY={result.severity.value} | "
            f"SCOPE={result.scope.value} | "
            f"CONFIRM_REQUIRED={result.required_user_confirmation} | "
            f"REASON_CODES=[{codes_str}] | "
            f"SIGNALS=[{signals_str}]"
        )

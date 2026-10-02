"""Unit tests for policy precedence resolution and user override handling."""

import pytest
from nivesh.policy.schemas import (
    PolicyDecisionType,
    PolicySeverity,
    InterventionScope,
    PolicyRuleResult,
    PolicyContext,
)
from nivesh.policy.reason_codes import ReasonCode
from nivesh.policy.precedence import PolicyPrecedenceResolver


def _create_dummy_result(rule_id: str, decision: PolicyDecisionType, severity: PolicySeverity) -> PolicyRuleResult:
    return PolicyRuleResult(
        rule_id=rule_id,
        rule_name=f"Rule {rule_id}",
        decision=decision,
        severity=severity,
        scope=InterventionScope.CURRENT_ACTION,
        reason_codes=[f"CODE_{rule_id}"],
        primary_reason=f"Primary reason for {rule_id}",
        supporting_reasons=[f"Supporting reason for {rule_id}"],
        triggered_signals=[f"SIG_{rule_id}"],
        required_user_confirmation=(decision == PolicyDecisionType.PAUSE),
        cooldown_seconds=30 if decision == PolicyDecisionType.PAUSE else None,
    )


def test_precedence_hierarchy_block_over_pause():
    r_pause = _create_dummy_result("R_PAUSE", PolicyDecisionType.PAUSE, PolicySeverity.HIGH)
    r_block = _create_dummy_result("R_BLOCK", PolicyDecisionType.BLOCK, PolicySeverity.CRITICAL)

    resolved = PolicyPrecedenceResolver.resolve([r_pause, r_block])
    assert resolved.decision == PolicyDecisionType.BLOCK
    assert resolved.severity == PolicySeverity.CRITICAL
    assert resolved.required_user_confirmation is False


def test_precedence_hierarchy_pause_over_warn_and_inform():
    r_inform = _create_dummy_result("R_INF", PolicyDecisionType.INFORM, PolicySeverity.LOW)
    r_warn = _create_dummy_result("R_WARN", PolicyDecisionType.WARN, PolicySeverity.MEDIUM)
    r_pause = _create_dummy_result("R_PAUSE", PolicyDecisionType.PAUSE, PolicySeverity.HIGH)

    resolved = PolicyPrecedenceResolver.resolve([r_inform, r_pause, r_warn])
    assert resolved.decision == PolicyDecisionType.PAUSE
    assert resolved.severity == PolicySeverity.HIGH
    assert resolved.required_user_confirmation is True


def test_precedence_hierarchy_warn_over_allow():
    r_allow = _create_dummy_result("R_ALLOW", PolicyDecisionType.ALLOW, PolicySeverity.NONE)
    r_warn = _create_dummy_result("R_WARN", PolicyDecisionType.WARN, PolicySeverity.MEDIUM)

    resolved = PolicyPrecedenceResolver.resolve([r_allow, r_warn])
    assert resolved.decision == PolicyDecisionType.WARN
    assert resolved.severity == PolicySeverity.MEDIUM


def test_empty_rules_defaults_to_allow():
    resolved = PolicyPrecedenceResolver.resolve([])
    assert resolved.decision == PolicyDecisionType.ALLOW
    assert resolved.severity == PolicySeverity.NONE
    assert ReasonCode.NO_INTERVENTION_REQUIRED in resolved.reason_codes


def test_user_override_demotes_pause_to_warn():
    r_pause = _create_dummy_result("R_PAUSE", PolicyDecisionType.PAUSE, PolicySeverity.HIGH)
    context = PolicyContext(user_override=True)

    resolved = PolicyPrecedenceResolver.resolve([r_pause], context=context)
    assert resolved.decision == PolicyDecisionType.WARN
    assert resolved.severity == PolicySeverity.MEDIUM
    assert resolved.required_user_confirmation is False
    assert ReasonCode.USER_OVERRIDE_APPLIED in resolved.reason_codes


def test_user_override_cannot_bypass_block():
    r_block = _create_dummy_result("R_BLOCK", PolicyDecisionType.BLOCK, PolicySeverity.CRITICAL)
    context = PolicyContext(user_override=True)

    resolved = PolicyPrecedenceResolver.resolve([r_block], context=context)
    assert resolved.decision == PolicyDecisionType.BLOCK
    assert resolved.severity == PolicySeverity.CRITICAL
    assert ReasonCode.USER_OVERRIDE_APPLIED not in resolved.reason_codes


def test_reason_codes_and_signals_aggregated_and_deduplicated():
    r1 = PolicyRuleResult(
        rule_id="R1",
        rule_name="R1",
        decision=PolicyDecisionType.PAUSE,
        severity=PolicySeverity.HIGH,
        scope=InterventionScope.CURRENT_ACTION,
        reason_codes=[ReasonCode.PAYMENT_REQUEST, ReasonCode.IDENTITY_NOT_ESTABLISHED],
        primary_reason="Payment with unverified identity",
        supporting_reasons=["Reason A", "Reason B"],
        triggered_signals=["SIG_PAY", "SIG_ID"],
        required_user_confirmation=True,
    )
    r2 = PolicyRuleResult(
        rule_id="R2",
        rule_name="R2",
        decision=PolicyDecisionType.WARN,
        severity=PolicySeverity.MEDIUM,
        scope=InterventionScope.INFORMATION_ONLY,
        reason_codes=[ReasonCode.IDENTITY_NOT_ESTABLISHED, ReasonCode.REGULATORY_CONFLICT],
        primary_reason="Regulatory conflict",
        supporting_reasons=["Reason B", "Reason C"],  # Reason B is duplicate
        triggered_signals=["SIG_ID", "SIG_REG"],
        required_user_confirmation=False,
    )

    resolved = PolicyPrecedenceResolver.resolve([r1, r2])
    assert resolved.decision == PolicyDecisionType.PAUSE
    assert resolved.reason_codes == [
        ReasonCode.PAYMENT_REQUEST,
        ReasonCode.IDENTITY_NOT_ESTABLISHED,
        ReasonCode.REGULATORY_CONFLICT,
    ]
    assert resolved.supporting_reasons == ["Reason A", "Reason B", "Reason C"]
    assert resolved.triggered_signals == ["SIG_PAY", "SIG_ID", "SIG_REG"]

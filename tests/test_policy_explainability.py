"""Unit tests for Engine 8 explainability and messaging."""

import pytest
from nivesh.policy.schemas import (
    PolicyDecisionType,
    PolicySeverity,
    InterventionScope,
    PolicyRuleResult,
)
from nivesh.policy.reason_codes import ReasonCode
from nivesh.policy.explain import PolicyExplainer


def test_explainability_non_accusatory_language():
    """Verify that user-facing messages never use accusatory language."""
    result = PolicyRuleResult(
        rule_id="RULE-PAUSE-01",
        rule_name="Payment Request with Multi-Signal Threat Pattern",
        decision=PolicyDecisionType.PAUSE,
        severity=PolicySeverity.HIGH,
        scope=InterventionScope.CURRENT_ACTION,
        reason_codes=[
            ReasonCode.PAYMENT_REQUEST,
            ReasonCode.IDENTITY_NOT_ESTABLISHED,
            ReasonCode.REGULATORY_CONFLICT,
        ],
        primary_reason="Payment request is linked to an unverified identity claim and regulatory conflict.",
        supporting_reasons=[
            "Claimed regulatory registration could not be established from authoritative sources.",
            "Promised guaranteed returns conflict with regulatory provisions.",
        ],
        triggered_signals=["PAYMENT_REQUEST", "IDENTITY_NOT_ESTABLISHED"],
        required_user_confirmation=True,
    )

    user_msg = PolicyExplainer.generate_user_message(result)
    tech_msg = PolicyExplainer.generate_technical_message(result)

    # Prohibited defamatory / legal-adjudication terms
    prohibited_terms = ["scam", "scammer", "fraudster", "criminal", "thief", "guilty", "illegal person"]
    for term in prohibited_terms:
        assert term not in user_msg.lower(), f"Prohibited accusatory term '{term}' found in user message: {user_msg}"

    # Required structured format in technical message
    assert "DECISION=PAUSE" in tech_msg
    assert "RULE=RULE-PAUSE-01" in tech_msg
    assert "REASON_CODES=[PAYMENT_REQUEST, IDENTITY_NOT_ESTABLISHED, REGULATORY_CONFLICT]" in tech_msg


def test_explainability_across_all_decision_types():
    """Verify clean user message generation across all 5 decision levels."""
    for decision in PolicyDecisionType:
        res = PolicyRuleResult(
            rule_id=f"RULE-{decision.value}",
            rule_name=f"Test {decision.value}",
            decision=decision,
            severity=PolicySeverity.MEDIUM,
            scope=InterventionScope.CURRENT_ACTION,
            reason_codes=[ReasonCode.FINANCIAL_CONTENT_DETECTED],
            primary_reason="Test primary reason",
            supporting_reasons=["Test supporting reason"],
            triggered_signals=[],
            required_user_confirmation=(decision == PolicyDecisionType.PAUSE),
        )
        msg = PolicyExplainer.generate_user_message(res)
        assert isinstance(msg, str) and len(msg) > 10

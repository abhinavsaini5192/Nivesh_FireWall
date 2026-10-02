"""Unit tests for Engine 8 policy schemas."""

import json
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from nivesh.policy.config import POLICY_VERSION
from nivesh.policy.schemas import (
    PolicyDecisionType,
    InterventionScope,
    PolicySeverity,
    PolicyContext,
    PolicyRuleResult,
    PolicyDecision,
)
from nivesh.policy.reason_codes import ReasonCode


def test_policy_decision_type_enum_values():
    assert PolicyDecisionType.ALLOW == "ALLOW"
    assert PolicyDecisionType.INFORM == "INFORM"
    assert PolicyDecisionType.WARN == "WARN"
    assert PolicyDecisionType.PAUSE == "PAUSE"
    assert PolicyDecisionType.BLOCK == "BLOCK"
    assert len(PolicyDecisionType) == 5


def test_intervention_scope_enum_values():
    assert InterventionScope.INFORMATION_ONLY == "INFORMATION_ONLY"
    assert InterventionScope.CURRENT_ACTION == "CURRENT_ACTION"
    assert InterventionScope.CURRENT_FLOW == "CURRENT_FLOW"
    assert InterventionScope.CURRENT_CHANNEL == "CURRENT_CHANNEL"
    assert len(InterventionScope) == 4


def test_policy_severity_enum_values():
    assert PolicySeverity.NONE == "NONE"
    assert PolicySeverity.LOW == "LOW"
    assert PolicySeverity.MEDIUM == "MEDIUM"
    assert PolicySeverity.HIGH == "HIGH"
    assert PolicySeverity.CRITICAL == "CRITICAL"


def test_policy_decision_schema_valid_instantiation():
    now_iso = datetime.now(timezone.utc).isoformat()
    decision = PolicyDecision(
        decision_id="DEC-001",
        decision=PolicyDecisionType.PAUSE,
        severity=PolicySeverity.HIGH.value,
        reason_codes=[
            ReasonCode.PAYMENT_REQUEST,
            ReasonCode.IDENTITY_NOT_ESTABLISHED,
            ReasonCode.USER_CONFIRMATION_REQUIRED,
        ],
        primary_reason="Payment requested with unverified regulatory identity.",
        supporting_reasons=[
            "Claimed regulatory registration could not be verified in authoritative records.",
            "Financial payment requested.",
        ],
        triggered_signals=["PAYMENT_REQUEST", "IDENTITY_NOT_ESTABLISHED"],
        relevant_claim_ids=["CLM-001"],
        relevant_action_ids=["ACT-001"],
        relevant_source_ids=["SRC-001"],
        relevant_evidence_ids=["EV-001"],
        relevant_fingerprint_id="SFP-001",
        intervention_scope=InterventionScope.CURRENT_ACTION,
        required_user_confirmation=True,
        cooldown_seconds=30,
        user_message="Pause before proceeding. This payment is linked to an unverified identity.",
        technical_message="DECISION=PAUSE | REASON_CODES=[PAYMENT_REQUEST, IDENTITY_NOT_ESTABLISHED]",
        policy_version=POLICY_VERSION,
        created_at=now_iso,
        audit_metadata={"decision_id": "DEC-001", "policy_version": POLICY_VERSION},
    )

    assert decision.decision_id == "DEC-001"
    assert decision.decision == PolicyDecisionType.PAUSE
    assert decision.required_user_confirmation is True
    assert decision.cooldown_seconds == 30
    assert decision.policy_version == "8.0.0"

    # Test serialization to JSON
    json_str = decision.model_dump_json()
    data = json.loads(json_str)
    assert data["decision"] == "PAUSE"
    assert data["policy_version"] == "8.0.0"


def test_policy_decision_missing_required_fields_raises_error():
    with pytest.raises(ValidationError):
        PolicyDecision(
            decision_id="DEC-001",
            # missing decision, primary_reason, etc.
        )

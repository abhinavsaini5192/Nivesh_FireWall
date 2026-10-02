"""Unit tests for Multi-Signal Combinations and Threat Families in Engine 6."""

import pytest
from nivesh.schemas.threat import (
    ThreatSignal,
    HighImpactAction,
)
from nivesh.threat.combination_engine import CombinationEngine


def test_combination_regulatory_impersonation_and_investment_scam():
    signals = [
        ThreatSignal(
            signal_id="SIG-01",
            type="AUTHORITY_IMPERSONATION",
            source="claim",
            evidence="Asserts SEBI registered",
            confidence=0.92,
            description="Claims SEBI registration"
        ),
        ThreatSignal(
            signal_id="SIG-02",
            type="IDENTITY_NOT_ESTABLISHED",
            source="evidence_verification",
            evidence="Registry 0 matches",
            confidence=0.95,
            description="Registry lookup failed"
        ),
        ThreatSignal(
            signal_id="SIG-03",
            type="PRIVATE_CHANNEL_MIGRATION",
            source="action",
            evidence="Join Telegram VIP",
            confidence=0.90,
            description="Moves to Telegram"
        ),
        ThreatSignal(
            signal_id="SIG-04",
            type="PAYMENT_REQUEST",
            source="action",
            evidence="Pay ₹5,000",
            confidence=0.95,
            description="Payment request"
        )
    ]
    stages = ["TRUST_BUILDING", "CHANNEL_MIGRATION", "FINANCIAL_REQUEST"]
    high_impact = [
        HighImpactAction(
            action_id="ACT-P1",
            action_type="PAYMENT",
            impact_category="FINANCIAL",
            reversibility="IRREVERSIBLE",
            description="Payment of ₹5,000"
        )
    ]

    combos, families = CombinationEngine.evaluate(signals, stages, high_impact)

    assert len(combos) >= 2
    mechanisms = [c.mechanism for c in combos]
    assert "trust_migration_to_payment_transition" in mechanisms
    assert "unsubstantiated_regulatory_authority" in mechanisms

    assert "REGULATORY_IMPERSONATION" in families
    assert "INVESTMENT_PROMOTION_SCAM" in families
    assert "PAYMENT_FRAUD" in families


def test_combination_credential_harvesting():
    signals = [
        ThreatSignal(
            signal_id="SIG-01",
            type="CREDENTIAL_REQUEST",
            source="action",
            evidence="Enter password and OTP",
            confidence=0.96,
            description="Requests password and OTP"
        ),
        ThreatSignal(
            signal_id="SIG-02",
            type="PRIVATE_CHANNEL_MIGRATION",
            source="action",
            evidence="Join Telegram",
            confidence=0.90,
            description="Private channel"
        )
    ]
    stages = ["CHANNEL_MIGRATION", "CREDENTIAL_CAPTURE"]
    high_impact = [
        HighImpactAction(
            action_id="ACT-C1",
            action_type="ENTER_CREDENTIALS",
            impact_category="CREDENTIAL",
            reversibility="IRREVERSIBLE",
            description="Password entry"
        )
    ]

    combos, families = CombinationEngine.evaluate(signals, stages, high_impact)

    assert any(c.mechanism == "private_channel_credential_harvesting" for c in combos)
    assert "CREDENTIAL_HARVESTING" in families
    assert "ACCOUNT_TAKEOVER" in families

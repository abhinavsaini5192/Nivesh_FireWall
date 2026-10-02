"""Unit tests for ActionParameterExtractor and privacy guards (Engine 3)."""

import pytest
from nivesh.actions.parameter_extractor import ActionParameterExtractor


@pytest.fixture
def param_extractor():
    return ActionParameterExtractor()


def test_payment_amount_extraction(param_extractor):
    p1 = param_extractor.extract_parameters("Pay ₹5,000 to activate your account", "PAYMENT")
    assert p1.get("amount") == 5000.0
    assert p1.get("currency") == "INR"

    p2 = param_extractor.extract_parameters("Transfer ₹25,000 to this account", "TRANSFER_MONEY")
    assert p2.get("amount") == 25000.0
    assert p2.get("currency") == "INR"

    p3 = param_extractor.extract_parameters("Deposit ₹10,000", "DEPOSIT_MONEY")
    assert p3.get("amount") == 10000.0
    assert p3.get("currency") == "INR"


def test_deadline_and_urgency_parameters(param_extractor):
    p1 = param_extractor.extract_parameters("Pay before 6 PM", "PAYMENT")
    assert p1.get("deadline") == "6 PM"

    p2 = param_extractor.extract_parameters("Complete KYC within 24 hours", "UPLOAD_DOCUMENT")
    assert p2.get("timeframe") == "24 hours"

    p3 = param_extractor.extract_parameters("Transfer ₹10,000 immediately", "TRANSFER_MONEY")
    assert p3.get("urgency") == "immediate"


def test_strict_privacy_safeguards(param_extractor):
    # Even if text contains an OTP or password string, parameter extractor must NOT persist it
    p1 = param_extractor.extract_parameters("Share OTP 482910 immediately", "SHARE_OTP")
    assert "otp" not in p1
    assert "482910" not in str(p1)

    p2 = param_extractor.extract_parameters("Enter password SecretPass123", "ENTER_CREDENTIALS")
    assert "password" not in p2
    assert "SecretPass123" not in str(p2)

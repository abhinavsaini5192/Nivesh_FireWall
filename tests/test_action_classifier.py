"""Unit tests for ActionClassifier and hierarchy progression (Engine 3)."""

import pytest
from nivesh.actions.classifier import ActionClassifier, CATEGORY_HIERARCHY_RANK


@pytest.fixture
def classifier():
    return ActionClassifier()


def test_basic_actions_classification(classifier):
    # Join Telegram
    atype, cat, objs = classifier.classify("Join our Telegram group")
    assert atype == "JOIN_CHANNEL"
    assert cat == "CHANNEL_MIGRATION"

    # Join WhatsApp
    atype, cat, objs = classifier.classify("Join our WhatsApp group")
    assert atype == "JOIN_GROUP"
    assert cat == "CHANNEL_MIGRATION"

    # Click link
    atype, cat, objs = classifier.classify("Click the link below")
    assert atype == "CLICK_LINK"
    assert cat == "NAVIGATION"

    # Open website
    atype, cat, objs = classifier.classify("Visit our website https://example.com")
    assert atype == "OPEN_WEBSITE"
    assert cat == "NAVIGATION"

    # Download app
    atype, cat, objs = classifier.classify("Download our app")
    assert atype == "DOWNLOAD"
    assert cat == "SOFTWARE_INSTALLATION"

    # Install APK
    atype, cat, objs = classifier.classify("Install this APK")
    assert atype == "INSTALL"
    assert cat == "SOFTWARE_INSTALLATION"
    assert "APK" in objs

    # Contact
    atype, cat, objs = classifier.classify("Contact rahul@example.com")
    assert atype == "CONTACT"
    assert cat == "COMMUNICATION"

    # Call
    atype, cat, objs = classifier.classify("Call us at +919876543210")
    assert atype == "CALL_PERSON"
    assert cat == "COMMUNICATION"


def test_sensitive_actions_classification(classifier):
    # Upload PAN
    atype, cat, objs = classifier.classify("Upload your PAN card")
    assert atype == "UPLOAD_DOCUMENT"
    assert cat == "DATA_DISCLOSURE"
    assert "PAN" in objs

    # Upload Aadhaar
    atype, cat, objs = classifier.classify("Upload your Aadhaar")
    assert atype == "UPLOAD_IDENTITY"
    assert cat == "DATA_DISCLOSURE"
    assert "Aadhaar" in objs

    # Enter password
    atype, cat, objs = classifier.classify("Enter your trading password")
    assert atype == "ENTER_CREDENTIALS"
    assert cat == "CREDENTIAL_ACCESS"
    assert "trading password" in objs

    # Share OTP
    atype, cat, objs = classifier.classify("Share the OTP we just sent you")
    assert atype == "SHARE_OTP"
    assert cat == "CREDENTIAL_ACCESS"
    assert "OTP" in objs

    # Connect bank
    atype, cat, objs = classifier.classify("Connect your bank account")
    assert atype == "CONNECT_BANK"
    assert cat == "ACCOUNT_AUTHORIZATION"

    # Authorize account
    atype, cat, objs = classifier.classify("Authorize access to your demat")
    assert atype == "AUTHORIZE_ACCESS"
    assert cat == "ACCOUNT_AUTHORIZATION"


def test_financial_actions_classification(classifier):
    # Pay
    atype, cat, objs = classifier.classify("Pay ₹5,000 to activate")
    assert atype == "PAYMENT"
    assert cat == "FINANCIAL_TRANSACTION"

    # Transfer
    atype, cat, objs = classifier.classify("Transfer ₹25,000 to this account")
    assert atype == "TRANSFER_MONEY"
    assert cat == "FINANCIAL_TRANSACTION"

    # Deposit
    atype, cat, objs = classifier.classify("Deposit ₹10,000")
    assert atype == "DEPOSIT_MONEY"
    assert cat == "FINANCIAL_TRANSACTION"

    # Withdraw
    atype, cat, objs = classifier.classify("Withdraw money from wallet")
    assert atype == "WITHDRAW_MONEY"
    assert cat == "FINANCIAL_TRANSACTION"

    # Buy / Sell
    atype, cat, objs = classifier.classify("Buy stock immediately")
    assert atype == "BUY"
    assert cat == "FINANCIAL_TRANSACTION"

    atype, cat, objs = classifier.classify("Sell shares now")
    assert atype == "SELL"
    assert cat == "FINANCIAL_TRANSACTION"


def test_category_progression_hierarchy_rankings():
    # Verify relative ranks of the hierarchy progression
    assert CATEGORY_HIERARCHY_RANK["COMMUNICATION"] < CATEGORY_HIERARCHY_RANK["CHANNEL_MIGRATION"]
    assert CATEGORY_HIERARCHY_RANK["CHANNEL_MIGRATION"] < CATEGORY_HIERARCHY_RANK["NAVIGATION"]
    assert CATEGORY_HIERARCHY_RANK["NAVIGATION"] < CATEGORY_HIERARCHY_RANK["SOFTWARE_INSTALLATION"]
    assert CATEGORY_HIERARCHY_RANK["SOFTWARE_INSTALLATION"] < CATEGORY_HIERARCHY_RANK["DATA_DISCLOSURE"]
    assert CATEGORY_HIERARCHY_RANK["DATA_DISCLOSURE"] < CATEGORY_HIERARCHY_RANK["CREDENTIAL_ACCESS"]
    assert CATEGORY_HIERARCHY_RANK["CREDENTIAL_ACCESS"] < CATEGORY_HIERARCHY_RANK["ACCOUNT_AUTHORIZATION"]
    assert CATEGORY_HIERARCHY_RANK["ACCOUNT_AUTHORIZATION"] < CATEGORY_HIERARCHY_RANK["FINANCIAL_TRANSACTION"]

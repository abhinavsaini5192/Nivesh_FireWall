"""Unit tests for Call-To-Action (CTA) extraction."""

import pytest
from nivesh.extractors.cta_extractor import CtaExtractor


@pytest.fixture
def extractor():
    return CtaExtractor()


def test_join_channel_cta(extractor):
    text = "Join our Telegram VIP group today or join now for signals."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "join_channel" in categories


def test_download_and_install_cta(extractor):
    text = "Download our app from link and install APK immediately."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "download" in categories
    assert "install" in categories


def test_payment_and_transfer_cta(extractor):
    text = "Pay ₹5,000 via UPI and transfer funds to account."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "payment" in categories
    assert "transfer" in categories


def test_credential_request_cta(extractor):
    text = "Share OTP received on your mobile to complete KYC."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "credential_request" in categories


def test_upload_cta(extractor):
    text = "Upload PAN and submit documents to start trading."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "upload" in categories


def test_contact_cta(extractor):
    text = "Contact rahul@example.com or reach out to us."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "contact" in categories


def test_click_cta(extractor):
    text = "Click here to claim your guaranteed bonus."
    ctas = extractor.extract(text)
    categories = [c.category for c in ctas]
    assert "click" in categories

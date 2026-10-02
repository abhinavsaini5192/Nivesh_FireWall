"""Unit tests for ContactExtractor (Email and Phone)."""

import pytest
from nivesh.extractors.contact_extractor import ContactExtractor


@pytest.fixture
def extractor():
    return ContactExtractor()


def test_email_extraction_and_normalization(extractor):
    text = "Contact Rahul at RAHUL@EXAMPLE.COM or support.team@invest-fund.org. Thanks."
    emails = extractor.extract_emails(text)
    assert len(emails) == 2
    assert "rahul@example.com" in emails
    assert "support.team@invest-fund.org" in emails


def test_indian_phone_number_formats(extractor):
    text = (
        "Call us at +91 9876543210 or 09876543211 or 98765 43212. "
        "Also international +1-800-555-0199."
    )
    phones = extractor.extract_phones(text)
    assert "+919876543210" in phones
    assert "+919876543211" in phones
    assert "+919876543212" in phones
    assert any("18005550199" in p for p in phones)


def test_guard_against_non_phone_numbers(extractor):
    text = "Pay ₹5,000 or Rs. 50,000 on date 2026-10-02."
    phones = extractor.extract_phones(text)
    # 5,000 or dates should NOT be extracted as phone numbers
    assert len(phones) == 0


def test_empty_input(extractor):
    assert extractor.extract_emails("") == []
    assert extractor.extract_phones("") == []

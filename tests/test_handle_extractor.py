"""Unit tests for Social Handle extraction."""

import pytest
from nivesh.extractors.social_extractor import SocialExtractor


@pytest.fixture
def extractor():
    return SocialExtractor()


def test_telegram_handles(extractor):
    text = "Join our group https://t.me/rahulinvest or telegram.me/trading_hub"
    handles = extractor.extract(text)
    telegram_handles = [h for h in handles if h.platform == "telegram"]
    names = [h.handle.lower() for h in telegram_handles]
    assert "rahulinvest" in names
    assert "trading_hub" in names


def test_instagram_handles(extractor):
    text = "Follow us on instagram.com/investor_guru and see stories"
    handles = extractor.extract(text)
    insta = [h for h in handles if h.platform == "instagram"]
    assert len(insta) == 1
    assert insta[0].handle == "investor_guru"


def test_youtube_handles(extractor):
    text = "Watch daily tips at youtube.com/@wealthmaster"
    handles = extractor.extract(text)
    yt = [h for h in handles if h.platform == "youtube"]
    assert len(yt) == 1
    assert yt[0].handle == "wealthmaster"


def test_generic_at_mentions(extractor):
    text = "Message @RahulInvest for payment details"
    handles = extractor.extract(text)
    unknown = [h for h in handles if h.platform == "unknown"]
    assert len(unknown) == 1
    assert unknown[0].handle == "RahulInvest"


def test_email_guard_does_not_extract_domain_as_handle(extractor):
    text = "Send queries to rahul@example.com, do not call."
    handles = extractor.extract(text)
    # rahul@example.com should NOT produce @example handle
    handles_found = [h.handle.lower() for h in handles]
    assert "example" not in handles_found


def test_whatsapp_link_handles(extractor):
    text = "Chat on wa.me/919876543210 for immediate bonus"
    handles = extractor.extract(text)
    wa = [h for h in handles if h.platform == "whatsapp"]
    assert len(wa) == 1
    assert wa[0].handle == "919876543210"

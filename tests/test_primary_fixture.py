"""Integration tests verifying Engine 1 on the primary benchmark fixture and multi-modal flows."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.schemas.input import ContentInput
from nivesh.schemas.normalized import NormalizedContent


@pytest.fixture
def engine():
    return ContentIntelligenceEngine()


PRIMARY_FIXTURE_TEXT = (
    "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
    "Join our Telegram VIP group: https://t.me/rahulinvest. "
    "Download our app and pay ₹5,000. Contact rahul@example.com."
)


def test_primary_benchmark_fixture(engine):
    """Verifies all extracted fields on the primary hackathon fixture."""
    normalized: NormalizedContent = engine.process_text(PRIMARY_FIXTURE_TEXT)

    # 1. Verify Schema Completeness & Provenance
    assert normalized.content_id is not None
    assert normalized.provenance.processing_version == "1.0.0"
    assert normalized.provenance.input_type == "text"
    assert normalized.provenance.ocr_used is False
    assert normalized.source.type == "text"

    # 2. Raw vs Normalized Text separation
    assert normalized.raw.text == PRIMARY_FIXTURE_TEXT
    assert "Rahul Sharma" in normalized.normalized.text
    assert normalized.normalized.language == "en"

    # 3. People extraction: Rahul Sharma
    people_names = [p.normalized for p in normalized.entities.people]
    assert "Rahul Sharma" in people_names
    person = next(p for p in normalized.entities.people if p.normalized == "Rahul Sharma")
    assert person.type == "person"
    assert person.span is not None

    # 4. Regulators: SEBI
    regulator_names = [r.text for r in normalized.entities.regulators]
    assert "SEBI" in regulator_names
    sebi_reg = next(r for r in normalized.entities.regulators if r.text == "SEBI")
    assert sebi_reg.normalized == "Securities and Exchange Board of India"
    assert sebi_reg.type == "regulator"

    # 5. URLs: https://t.me/rahulinvest
    urls = [u.original_url for u in normalized.structured_signals.urls]
    assert any("t.me/rahulinvest" in u for u in urls)
    url_signal = next(u for u in normalized.structured_signals.urls if "t.me/rahulinvest" in u.original_url)
    assert url_signal.domain == "t.me"

    # 6. Social handles: rahulinvest / Telegram
    handles = normalized.structured_signals.social_handles
    telegram_handles = [h for h in handles if h.platform == "telegram"]
    assert any(h.handle.lower() == "rahulinvest" for h in telegram_handles)

    # 7. Email: rahul@example.com
    assert "rahul@example.com" in normalized.structured_signals.email_addresses

    # 8. Currency Amounts: ₹5,000
    amounts = normalized.structured_signals.currency_amounts
    assert any(a.value == 5000.0 and a.currency == "INR" for a in amounts)

    # 9. Percentages: 40%
    percentages = normalized.structured_signals.percentages
    assert any(p.value == 40.0 for p in percentages)

    # 10. Financial Terms: SEBI, advisor, returns, etc.
    terms = [t.lower() for t in normalized.structured_signals.financial_terms]
    assert "sebi" in terms
    assert "advisor" in terms
    assert "returns" in terms

    # 11. Actions / CTAs: join_channel, download, payment, contact
    cta_categories = [c.category for c in normalized.content_features.calls_to_action]
    assert "join_channel" in cta_categories
    assert "download" in cta_categories
    assert "payment" in cta_categories
    assert "contact" in cta_categories
    assert normalized.content_features.call_to_action_present is True

    # 12. Financial relevance: True
    assert normalized.content_features.contains_financial_content is True
    assert normalized.content_features.confidence >= 0.85

    # 13. STRICT CONSTRAINT: NO scam / risk / block labeling!
    dumped = normalized.model_dump()
    dumped_str = str(dumped).lower()
    assert "scam" not in dumped_str
    assert "high risk" not in dumped_str
    assert "block" not in dumped_str


def test_image_input_pipeline_end_to_end(engine):
    """Verifies that Image -> OCR -> NormalizedContent uses the identical extraction pipeline."""
    from nivesh.adapters.ocr_adapter import OcrAdapter, OcrResult

    mock_ocr = OcrAdapter(backend="mock")
    img_engine = ContentIntelligenceEngine(ocr_adapter=mock_ocr)

    img_input = ContentInput(
        image_bytes=b"dummy-image-bytes",
        channel="telegram"
    )
    # Configure mock text matching primary fixture without recursion
    mock_ocr.process = lambda **kwargs: OcrResult(
        text=PRIMARY_FIXTURE_TEXT,
        success=True,
        engine="mock_ocr",
        confidence=0.95,
        metadata={"mock": True}
    )

    result = img_engine.process(img_input)
    assert result.provenance.ocr_used is True
    assert result.provenance.input_type == "image"
    assert result.source.channel == "telegram"
    assert result.content_features.contains_financial_content is True
    assert any(p.normalized == "Rahul Sharma" for p in result.entities.people)
    assert any(a.value == 5000.0 for a in result.structured_signals.currency_amounts)


def test_url_input_pipeline_end_to_end(engine):
    """Verifies that URL -> Ingestion -> NormalizedContent handles URL text safely."""
    from nivesh.adapters.url_adapter import UrlAdapter, UrlIngestionResult

    mock_url_adapter = UrlAdapter()
    extracted_text = "ABC Investments Advisory. Guaranteed 25% returns on mutual funds. Pay ₹10,000 to start."
    mock_url_adapter.ingest = lambda url, **kwargs: UrlIngestionResult(
        original_url=url,
        normalized_url=url,
        text=extracted_text,
        status_code=200,
        success=True
    )

    url_engine = ContentIntelligenceEngine(url_adapter=mock_url_adapter)
    result = url_engine.process_url("https://abc-invest.com/join", channel="browser")

    assert result.provenance.input_type == "url"
    assert result.raw.url == "https://abc-invest.com/join"
    assert result.content_features.contains_financial_content is True
    assert any(a.value == 10000.0 for a in result.structured_signals.currency_amounts)
    assert any(p.value == 25.0 for p in result.structured_signals.percentages)

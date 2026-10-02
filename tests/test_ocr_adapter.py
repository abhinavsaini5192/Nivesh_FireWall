"""Unit tests for OcrAdapter."""

import io
import pytest
from PIL import Image, ImageDraw
from nivesh.adapters.ocr_adapter import OcrAdapter, OcrResult


@pytest.fixture
def adapter():
    return OcrAdapter()


def test_mock_ocr_mode():
    mock_adapter = OcrAdapter(backend="mock")
    res = mock_adapter.process(mock_text="Guaranteed 40% returns on investment")
    assert res.success is True
    assert "Guaranteed 40% returns" in res.text
    assert res.confidence >= 0.90
    assert res.engine == "mock_ocr"
    assert res.warnings == []


def test_blank_image_handling(adapter):
    # Create all-white blank image
    img = Image.new("RGB", (200, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    res = adapter.process(image_bytes=raw_bytes)
    # Shouldn't crash; text empty; warning recorded
    assert res.text == ""
    assert res.success is False
    assert any("No text detected" in w or "OCR" in w for w in res.warnings)


def test_corrupt_image_bytes(adapter):
    corrupt_bytes = b"NOT_AN_IMAGE_HEADER_1234567890_CORRUPT"
    res = adapter.process(image_bytes=corrupt_bytes)
    assert res.success is False
    assert res.text == ""
    assert any("corrupt" in w.lower() or "unsupported" in w.lower() for w in res.warnings)


def test_no_input_provided(adapter):
    res = adapter.process()
    assert res.success is False
    assert "No image input provided" in res.warnings


def test_oversized_image_rejection():
    adapter = OcrAdapter()
    oversized_bytes = b"0" * (26 * 1024 * 1024)  # 26 MB
    res = adapter.process(image_bytes=oversized_bytes)
    assert res.success is False
    assert any("exceeds maximum size" in w for w in res.warnings)


def test_native_windows_ocr_execution_if_available(adapter):
    # Generates a clear readable test image with text
    img = Image.new("RGB", (400, 100), color="white")
    d = ImageDraw.Draw(img)
    d.text((20, 30), "SEBI Advisor Rahul", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    res = adapter.process(image_bytes=buf.getvalue())
    # Should succeed or return clean OcrResult without throwing unhandled exception
    assert isinstance(res, OcrResult)
    if res.success:
        assert "Rahul" in res.text or "SEBI" in res.text
        assert res.engine in {"windows_media_ocr", "pytesseract"}

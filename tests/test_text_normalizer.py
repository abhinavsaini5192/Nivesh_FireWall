"""Unit tests for TextNormalizer."""

import pytest
from nivesh.normalizers.text_normalizer import TextNormalizer


@pytest.fixture
def normalizer():
    return TextNormalizer()


def test_whitespace_normalization(normalizer):
    raw = "   Multiple   spaces    and \t tabs   across \n\n\n\n lines.   "
    normalized = normalizer.normalize(raw)
    assert "Multiple spaces and tabs across" in normalized
    assert "    " not in normalized
    # Max consecutive newlines is 2
    assert "\n\n\n" not in normalized


def test_unicode_normalization_homoglyphs_and_math(normalizer):
    # Mathematical bold/italic chars commonly used by scammers: 𝐆𝐮𝐚𝐫𝐚𝐧𝐭𝐞𝐞𝐝
    math_bold = "𝐆𝐮𝐚𝐫𝐚𝐧𝐭𝐞𝐞𝐝 𝟒𝟎% 𝐫𝐞𝐭𝐮𝐫𝐧𝐬"
    normalized = normalizer.normalize(math_bold)
    assert normalized == "Guaranteed 40% returns"

    # Full-width numbers
    fullwidth = "Pay ５０００ rupees"
    assert normalizer.normalize(fullwidth) == "Pay 5000 rupees"


def test_zero_width_and_invisible_character_stripping(normalizer):
    # Injected zero-width space (\u200b) inside "Gua\u200branteed"
    obfuscated = "Gua\u200branteed 40%\u200d returns\ufeff"
    normalized = normalizer.normalize(obfuscated)
    assert normalized == "Guaranteed 40% returns"


def test_smart_quotes_and_dashes(normalizer):
    raw = "‘Rahul’s’ “VIP” group – guaranteed"
    normalized = normalizer.normalize(raw)
    assert normalized == "'Rahul's' \"VIP\" group - guaranteed"


def test_repeated_punctuation(normalizer):
    raw = "Hurry up!!!!! Guaranteed returns???? Really....."
    normalized = normalizer.normalize(raw)
    assert normalized == "Hurry up! Guaranteed returns? Really..."


def test_ocr_hyphenation_line_break_fix(normalizer):
    raw = "Top financial inves-\ntor in India"
    normalized = normalizer.normalize(raw)
    assert "investor in India" in normalized


def test_empty_and_none_text(normalizer):
    assert normalizer.normalize("") == ""
    assert normalizer.normalize(None) == ""
    assert normalizer.normalize("   ") == ""

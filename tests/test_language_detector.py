"""Unit tests for LanguageDetector."""

import pytest
from nivesh.classifiers.language_detector import LanguageDetector


@pytest.fixture
def detector():
    return LanguageDetector()


def test_english_detection(detector):
    text = "Guaranteed 40% returns on your investment portfolio. Contact our registered advisor."
    lang, conf = detector.detect(text)
    assert lang == "en"
    assert conf >= 0.80


def test_hindi_devanagari_detection(detector):
    text = "प्रति माह 40% रिटर्न की गारंटी। हमारे टेलीग्राम ग्रुप से अभी जुड़ें।"
    lang, conf = detector.detect(text)
    assert lang == "hi"
    assert conf >= 0.85


def test_hinglish_code_mixing_detection(detector):
    text = "Sir guaranteed return hai, abhi join karo aur paise kamao."
    lang, conf = detector.detect(text)
    assert lang == "hinglish"
    assert conf >= 0.75


def test_empty_string(detector):
    lang, conf = detector.detect("")
    assert lang == "en"
    assert conf == 1.0

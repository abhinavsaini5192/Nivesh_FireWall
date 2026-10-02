"""Unit tests for Modality and Temporal detection in Engine 2."""

import pytest
from nivesh.claims.modality import ModalityDetector
from nivesh.claims.temporal import TemporalDetector


@pytest.fixture
def modality_detector():
    return ModalityDetector()


@pytest.fixture
def temporal_detector():
    return TemporalDetector()


def test_modality_assertion(modality_detector):
    m = modality_detector.detect("Guaranteed 40% returns on your investment.")
    assert m.type == "assertion"
    assert m.certainty_language == "Guaranteed"

    m2 = modality_detector.detect("ABC is officially approved.")
    assert m2.type == "assertion"
    assert m2.certainty_language == "officially"


def test_modality_possibility(modality_detector):
    m = modality_detector.detect("ABC may become debt free.")
    assert m.type == "possibility"
    assert m.certainty_language == "may"


def test_modality_prediction(modality_detector):
    m = modality_detector.detect("ABC will reach ₹500 next month.")
    assert m.type == "prediction"
    assert "will" in (m.certainty_language or "")


def test_modality_opinion(modality_detector):
    m = modality_detector.detect("I think ABC is undervalued.")
    assert m.type == "opinion"
    assert "I think" in (m.certainty_language or "")


def test_modality_conditional(modality_detector):
    m = modality_detector.detect("If ABC receives funding, it may become profitable.")
    assert m.type == "conditional"
    assert "If" in (m.certainty_language or "")


def test_temporal_historical(temporal_detector):
    t = temporal_detector.detect("XYZ reported ₹40 crore profit in FY2025.")
    assert t.type == "historical"
    assert t.date == "FY2025" or t.raw_text == "FY2025"

    t2 = temporal_detector.detect("ABC achieved strong earnings last year.")
    assert t2.type == "historical"
    assert t2.raw_text == "last year"


def test_temporal_current(temporal_detector):
    t = temporal_detector.detect("ABC has ₹100 crore debt.")
    assert t.type == "current"

    t2 = temporal_detector.detect("Rahul Sharma is a SEBI registered advisor.")
    assert t2.type == "current"


def test_temporal_future(temporal_detector):
    t = temporal_detector.detect("ABC will launch a new fund next month.")
    assert t.type == "future"
    assert "next month" in (t.raw_text or "")

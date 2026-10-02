"""Unit tests for FinancialRelevanceClassifier."""

import pytest
from nivesh.classifiers.financial_relevance import FinancialRelevanceClassifier
from nivesh.schemas.normalized import (
    CurrencyAmountSignal,
    PercentageSignal,
    EntityItem,
    CallToAction,
)


@pytest.fixture
def classifier():
    return FinancialRelevanceClassifier()


def test_clearly_financial_content(classifier):
    text = "Guaranteed 30% returns. Send ₹5,000."
    amounts = [CurrencyAmountSignal(value=5000.0, currency="INR", raw="₹5,000")]
    percentages = [PercentageSignal(value=30.0, raw="30%")]
    terms = ["returns", "guaranteed"]
    ctas = [CallToAction(phrase="Send ₹5,000", category="payment", confidence=0.95)]

    features = classifier.classify(
        text=text,
        financial_terms=terms,
        currency_amounts=amounts,
        percentages=percentages,
        regulators=[],
        instruments=[],
        ctas=ctas,
    )

    assert features.contains_financial_content is True
    assert features.confidence >= 0.85
    assert "₹5,000" in features.financial_terms_detected
    assert "returns" in features.financial_terms_detected
    assert features.call_to_action_present is True


def test_clearly_unrelated_content(classifier):
    text = "Best pizza near Jaipur."
    features = classifier.classify(
        text=text,
        financial_terms=[],
        currency_amounts=[],
        percentages=[],
        regulators=[],
        instruments=[],
        ctas=[],
    )

    assert features.contains_financial_content is False
    assert features.financial_terms_detected == []
    assert features.call_to_action_present is False


def test_ambiguous_content(classifier):
    text = "Rahul Sharma"
    features = classifier.classify(
        text=text,
        financial_terms=[],
        currency_amounts=[],
        percentages=[],
        regulators=[],
        instruments=[],
        ctas=[],
    )

    # Ambiguous content must default to False without inventing financial relevance
    assert features.contains_financial_content is False
    assert features.financial_terms_detected == []


def test_does_not_generate_scam_or_risk_judgment(classifier):
    text = "SEBI registered guaranteed 100% returns"
    reg = [EntityItem(text="SEBI", normalized="Securities and Exchange Board of India", type="regulator")]
    features = classifier.classify(
        text=text,
        financial_terms=["sebi", "guaranteed", "returns"],
        currency_amounts=[],
        percentages=[PercentageSignal(value=100.0, raw="100%")],
        regulators=reg,
        instruments=[],
        ctas=[],
    )
    # Strictly neutral
    assert not hasattr(features, "risk_level")
    assert not hasattr(features, "is_scam")
    assert not hasattr(features, "decision")

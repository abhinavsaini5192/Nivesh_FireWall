"""Unit tests for FinancialExtractor."""

import pytest
from nivesh.extractors.financial_extractor import FinancialExtractor


@pytest.fixture
def extractor():
    return FinancialExtractor()


def test_rupee_values_extraction(extractor):
    text = "Pay ₹5,000 upfront. Additional Rs 10,000 or INR 50,000 for VIP."
    amounts = extractor.extract_currency_amounts(text)
    assert len(amounts) == 3
    vals = [a.value for a in amounts]
    assert 5000.0 in vals
    assert 10000.0 in vals
    assert 50000.0 in vals
    assert all(a.currency == "INR" for a in amounts)


def test_indian_units_lakh_and_crore(extractor):
    text = "Earn 5 lakh in 3 months or invest 1.5 crore for private wealth portfolio."
    amounts = extractor.extract_currency_amounts(text)
    vals = [a.value for a in amounts]
    assert 500000.0 in vals
    assert 15000000.0 in vals


def test_percentages_extraction(extractor):
    text = "Guaranteed 40% returns! Monthly 10 % or 15.5 percent profit."
    pcts = extractor.extract_percentages(text)
    assert len(pcts) == 3
    vals = [p.value for p in pcts]
    assert 40.0 in vals
    assert 10.0 in vals
    assert 15.5 in vals


def test_registration_numbers(extractor):
    text = (
        "SEBI Reg No: INA000012345. "
        "Company PAN: ABCDE1234F. "
        "CIN: U72200DL2020PTC123456."
    )
    regs = extractor.extract_registration_numbers(text)
    types = [r.type for r in regs]
    assert "SEBI" in types
    assert "PAN" in types
    assert "CIN" in types


def test_financial_terms_detection(extractor):
    text = (
        "SEBI registered advisor promising guaranteed returns through "
        "mutual fund, intraday trading, and demat portfolio bonus."
    )
    terms = extractor.extract_financial_terms(text)
    terms_lower = [t.lower() for t in terms]
    assert "sebi" in terms_lower
    assert "advisor" in terms_lower
    assert "guaranteed" in terms_lower
    assert "returns" in terms_lower
    assert "mutual fund" in terms_lower
    assert "trading" in terms_lower
    assert "demat" in terms_lower


def test_date_extraction(extractor):
    text = "Offer valid until 15/10/2026 or 2026-12-31."
    dates = extractor.extract_dates(text)
    vals = [d.value for d in dates]
    assert "15/10/2026" in vals
    assert "2026-12-31" in vals

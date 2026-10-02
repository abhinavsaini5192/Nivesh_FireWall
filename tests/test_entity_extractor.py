"""Unit tests for EntityExtractor."""

import pytest
from nivesh.extractors.entity_extractor import EntityExtractor


@pytest.fixture
def extractor():
    return EntityExtractor()


def test_regulator_extraction_and_canonical_normalization(extractor):
    text = "We are registered under SEBI and comply with RBI and NSE directives."
    entities = extractor.extract(text)
    regulators = entities.regulators
    assert len(regulators) >= 3

    sebi_entity = next(r for r in regulators if r.text == "SEBI")
    assert sebi_entity.normalized == "Securities and Exchange Board of India"
    assert sebi_entity.type == "regulator"
    assert sebi_entity.confidence >= 0.95
    assert sebi_entity.span is not None

    rbi_entity = next(r for r in regulators if r.text == "RBI")
    assert rbi_entity.normalized == "Reserve Bank of India"


def test_person_name_extraction(extractor):
    text = "Certified advisor Rahul Sharma will guide your investments."
    entities = extractor.extract(text)
    people = entities.people
    assert len(people) >= 1
    person = people[0]
    assert person.text == "Rahul Sharma"
    assert person.normalized == "Rahul Sharma"
    assert person.type == "person"
    assert person.confidence >= 0.85
    assert person.span is not None


def test_organization_extraction(extractor):
    text = "Investment managed by ABC Investments and XYZ Ltd."
    entities = extractor.extract(text)
    orgs = entities.organizations
    names = [o.text for o in orgs]
    assert any("ABC Investments" in n for n in names)
    assert any("XYZ Ltd" in n for n in names)


def test_financial_instruments_extraction(extractor):
    text = "Invest in mutual funds, equity shares, and options contracts."
    entities = extractor.extract(text)
    instruments = entities.financial_instruments
    assert len(instruments) >= 2
    types = [i.normalized for i in instruments]
    assert "Mutual Fund" in types
    assert any("Option" in t or "Share" in t for t in types)


def test_no_claim_of_legitimacy(extractor):
    # Tests that the extractor only tags structure, never legitimacy
    text = "SEBI registered Rahul Sharma"
    entities = extractor.extract(text)
    # Regulators and people are extracted with spans, but no 'is_legitimate' or 'is_verified' field exists
    assert not hasattr(entities.regulators[0], "is_legitimate")
    assert not hasattr(entities.people[0], "is_verified")

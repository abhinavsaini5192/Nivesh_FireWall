"""Unit tests for URL and Domain extraction."""

import pytest
from nivesh.extractors.url_extractor import UrlExtractor


@pytest.fixture
def extractor():
    return UrlExtractor()


def test_standard_url_extraction(extractor):
    text = "Visit https://www.example.com/invest for details."
    urls, domains = extractor.extract(text)
    assert len(urls) == 1
    assert urls[0].original_url == "https://www.example.com/invest"
    assert urls[0].scheme == "https"
    assert urls[0].domain == "www.example.com"
    assert urls[0].path == "/invest"

    assert len(domains) == 1
    assert domains[0].effective_domain == "example.com"


def test_multiple_urls_in_text(extractor):
    text = "Check https://t.me/rahulinvest and also http://invest-fast.xyz/bonus?code=123"
    urls, domains = extractor.extract(text)
    assert len(urls) == 2
    domains_list = [d.effective_domain for d in domains]
    assert "t.me" in domains_list
    assert "invest-fast.xyz" in domains_list


def test_bare_urls_without_scheme(extractor):
    text = "Join now at t.me/vipcalls or visit www.wealth-guru.com/signup"
    urls, domains = extractor.extract(text)
    assert len(urls) >= 2
    schemes = [u.scheme for u in urls]
    assert all(s in {"http", "https"} for s in schemes)


def test_trailing_punctuation_handling(extractor):
    text = "Find us at https://example.com/page, or https://example.com/faq."
    urls, _ = extractor.extract(text)
    assert urls[0].original_url == "https://example.com/page"
    assert urls[1].original_url == "https://example.com/faq"


def test_url_with_port_and_query_parameters(extractor):
    text = "Internal node at http://portal.sebi-verification.in:8080/check?id=99#frag"
    urls, domains = extractor.extract(text)
    assert len(urls) == 1
    url = urls[0]
    assert url.port == 8080
    assert "id=99" in (url.query or "")
    assert url.fragment == "frag"

    assert len(domains) == 1
    dom = domains[0]
    assert dom.port == 8080
    assert dom.effective_domain == "sebi-verification.in"
    assert dom.subdomain == "portal"


def test_subdomain_and_multi_part_tld(extractor):
    text = "Official broker site: https://secure.trading.broker.co.in/login"
    urls, domains = extractor.extract(text)
    assert len(domains) == 1
    dom = domains[0]
    # For .co.in, effective domain is broker.co.in
    assert dom.effective_domain == "broker.co.in"
    assert dom.subdomain == "secure.trading"


def test_malformed_urls_handled_gracefully(extractor):
    text = "Malformed: http://:invalid@ or https:///nothing or random string"
    urls, domains = extractor.extract(text)
    # Shouldn't crash
    assert isinstance(urls, list)
    assert isinstance(domains, list)


def test_empty_input(extractor):
    urls, domains = extractor.extract("")
    assert urls == []
    assert domains == []

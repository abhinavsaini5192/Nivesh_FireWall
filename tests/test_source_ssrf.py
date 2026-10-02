"""Unit tests for SSRF Protection in Engine 4."""

import pytest
from nivesh.sources.ssrf import SsrfValidator, SsrfError


@pytest.mark.parametrize("dangerous_url", [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:5000/api",
    "http://127.0.0.2",
    "http://10.0.0.1/admin",
    "http://10.254.1.1",
    "http://172.16.0.1",
    "http://172.31.255.255",
    "http://192.168.1.1",
    "http://192.168.0.100:8080",
    "http://169.254.169.254/latest/meta-data",  # Cloud metadata service
    "file:///etc/passwd",
    "file:///c:/windows/system32/cmd.exe",
    "ftp://example.com/file",
    "gopher://example.com",
    "http://service.local",
    "http://internal.corp",
    "http://db.lan",
    "http://admin.intranet",
])
def test_ssrf_blocks_dangerous_destinations(dangerous_url):
    is_safe, error = SsrfValidator.is_safe_url(dangerous_url)
    assert is_safe is False
    assert error is not None

    with pytest.raises(SsrfError):
        SsrfValidator.validate_or_raise(dangerous_url)


@pytest.mark.parametrize("safe_url", [
    "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes",
    "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
    "https://www.bseindia.com/corporates/ann.html",
    "https://www.rbi.org.in",
])
def test_ssrf_allows_public_authoritative_urls(safe_url):
    is_safe, error = SsrfValidator.is_safe_url(safe_url)
    assert is_safe is True
    assert error is None
    validated = SsrfValidator.validate_or_raise(safe_url)
    assert validated == safe_url

"""Unit tests for UrlAdapter."""

import pytest
from nivesh.adapters.url_adapter import UrlAdapter, UrlIngestionResult


@pytest.fixture
def adapter():
    return UrlAdapter(timeout=2.0)


def test_mock_html_ingestion(adapter):
    html = """
    <html>
      <head><title>Investment Portal</title></head>
      <body>
        <script>console.log('noisy script');</script>
        <header><nav>Home | Login</nav></header>
        <div class="content">
          <h1>Guaranteed 40% returns</h1>
          <p>Join our VIP group today and pay ₹5,000.</p>
        </div>
      </body>
    </html>
    """
    res = adapter.ingest("https://example.com/invest", fetch=True, mock_html=html)
    assert res.success is True
    assert "Guaranteed 40% returns" in res.text
    assert "pay ₹5,000" in res.text
    # Script and nav should be stripped
    assert "console.log" not in res.text
    assert "noisy script" not in res.text


def test_empty_url_handling(adapter):
    res = adapter.ingest("", fetch=True)
    assert res.success is False
    assert "Empty URL provided" in res.warnings


def test_inaccessible_url_graceful_handling(adapter):
    # Non-routable or invalid host should fail gracefully without crashing
    res = adapter.ingest("http://invalid-domain-that-does-not-exist-123456789.xyz/page", fetch=True)
    assert res.success is False
    assert len(res.warnings) > 0
    assert any("Inaccessible URL" in w for w in res.warnings)

"""Full integration test for Engine 1 -> Engine 2 pipeline (Section 29)."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis


@pytest.fixture
def content_engine():
    return ContentIntelligenceEngine()


@pytest.fixture
def claims_engine():
    return ClaimIntelligenceEngine()


def test_full_pipeline_text_to_claims(content_engine, claims_engine):
    """Verifies complete data flow: Raw Text -> Engine 1 -> Engine 2."""
    raw_text = (
        "SEBI registered advisor Rahul Sharma guarantees 40% returns. "
        "ABC announced a 1:1 bonus. Join our Telegram group."
    )
    # Engine 1
    normalized: NormalizedContent = content_engine.process_text(raw_text)
    assert normalized.status == "success"

    # Engine 2
    analysis: ClaimAnalysis = claims_engine.analyze(normalized)

    # Contract verifications:
    # 1. Content ID preservation
    assert analysis.content_id == normalized.content_id

    # 2. Claims generated with stable IDs
    assert len(analysis.claims) >= 3
    for idx, claim in enumerate(analysis.claims):
        assert claim.claim_id == f"CLAIM-{idx+1:03d}"
        assert claim.source_content_id == normalized.content_id
        assert claim.confidence > 0.0
        assert claim.canonical_fingerprint != ""
        assert len(claim.verification_requirements) > 0

    # 3. Actions not absorbed
    claim_texts = [c.text.original.lower() for c in analysis.claims]
    assert not any("join our telegram" == t for t in claim_texts)

    # 4. Provenance
    assert all(c.provenance.processing_version == "1.0.0" for c in analysis.claims)


def test_full_pipeline_url_to_claims(content_engine, claims_engine):
    """Verifies data flow: Ingested URL content -> Engine 1 -> Engine 2."""
    from nivesh.adapters.url_adapter import UrlAdapter, UrlIngestionResult

    mock_url_adapter = UrlAdapter()
    html_content = "XYZ is debt free and reported ₹50 crore revenue."
    mock_url_adapter.ingest = lambda url, **kwargs: UrlIngestionResult(
        original_url=url,
        normalized_url=url,
        text=html_content,
        status_code=200,
        success=True
    )

    custom_content_engine = ContentIntelligenceEngine(url_adapter=mock_url_adapter)
    normalized = custom_content_engine.process_url("https://xyz-corp.com/financials")

    analysis = claims_engine.analyze(normalized)
    assert analysis.content_id == normalized.content_id
    assert len(analysis.claims) >= 1
    assert any(c.predicate in {"HAS_DEBT", "REPORTED_REVENUE"} for c in analysis.claims)


def test_empty_normalized_content_handling(claims_engine):
    """Gracefully handles empty NormalizedContent without raising unhandled errors."""
    empty_normalized = NormalizedContent(
        content_id="empty-123",
        source={"type": "text", "channel": "unknown"},
        raw={"text": ""},
        normalized={"text": "", "language": "en", "language_confidence": 1.0},
        provenance={"created_at": "2026-10-02T00:00:00Z", "input_type": "text"}
    )
    analysis = claims_engine.analyze(empty_normalized)
    assert analysis.content_id == "empty-123"
    assert len(analysis.claims) == 0
    assert analysis.analysis_metadata.total_claims == 0

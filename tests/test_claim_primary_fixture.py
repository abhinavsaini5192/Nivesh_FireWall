"""Unit tests for Engine 2 on the primary benchmark fixture (Section 26)."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis


PRIMARY_FIXTURE_TEXT = (
    "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
    "Join our Telegram VIP group: https://t.me/rahulinvest. "
    "Download our app and pay ₹5,000. Contact rahul@example.com."
)


@pytest.fixture
def content_engine():
    return ContentIntelligenceEngine()


@pytest.fixture
def claims_engine():
    return ClaimIntelligenceEngine()


def test_primary_benchmark_claims_extraction(content_engine, claims_engine):
    """Verifies that the primary benchmark content extracts exactly the intended atomic claims."""
    # 1. Process via Engine 1
    normalized: NormalizedContent = content_engine.process_text(PRIMARY_FIXTURE_TEXT)

    # 2. Process via Engine 2
    claim_analysis: ClaimAnalysis = claims_engine.analyze(normalized)

    # 3. Verify content_id linkage
    assert claim_analysis.content_id == normalized.content_id
    assert len(claim_analysis.claims) >= 2

    # 4. Check Claim 1: Rahul Sharma is a SEBI registered advisor
    reg_claims = [c for c in claim_analysis.claims if c.claim_type in {"REGULATORY", "IDENTITY"}]
    assert len(reg_claims) >= 1
    reg_claim = reg_claims[0]
    assert "Rahul Sharma" in reg_claim.subject
    assert reg_claim.predicate == "REGISTERED_WITH"
    assert "SEBI" in (reg_claim.object or "")
    assert reg_claim.verification_requirements != []
    assert "official_regulator_registry" in reg_claim.verification_requirements

    # 5. Check Claim 2: 40% returns are guaranteed
    fin_claims = [c for c in claim_analysis.claims if c.claim_type == "FINANCIAL"]
    assert len(fin_claims) >= 1
    fin_claim = fin_claims[0]
    assert fin_claim.predicate == "GUARANTEED_RETURN"
    assert "40%" in (fin_claim.object or "")
    assert fin_claim.modality.type == "assertion"
    assert fin_claim.modality.certainty_language is not None
    assert "guaranteed" in fin_claim.modality.certainty_language.lower()

    # 6. Check that ACTIONS are NOT extracted as ordinary claims
    all_claim_texts = [c.text.original.lower() for c in claim_analysis.claims]
    for action_fragment in [
        "join our telegram",
        "download our app",
        "pay ₹5,000",
        "contact rahul@example.com",
    ]:
        # None of these action directives should be a claim text
        assert not any(action_fragment == t for t in all_claim_texts)

    # 7. Check that Actions filtered metadata is tracked
    assert claim_analysis.analysis_metadata.actions_filtered_count >= 2

    # 8. STRICT CONSTRAINT: NO scam / risk / block labeling!
    dumped = claim_analysis.model_dump()
    dumped_str = str(dumped).lower()
    assert "is_scam" not in dumped_str
    assert "risk_score" not in dumped_str
    assert "block_decision" not in dumped_str

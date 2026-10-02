"""Primary benchmark fixture test for Engine 7 (Scam Fingerprint & Collective Threat Intelligence Engine).

Demonstrates:
- Section 44: Primary Demo (Observation 1 -> SFP-001, Observation 2 -> STRUCTURAL_MATCH/SEMANTIC_VARIANT, count -> 2)
- Section 45: Secondary Demo (Observation 3 -> NO_MATCH, informational content isolated)
- Section 34: Downstream collective response for User B
"""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine


def test_primary_and_secondary_demo_benchmark():
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()
    fp_engine = ScamFingerprintEngine()

    # =========================================================================
    # Observation 1: Standard benchmark threat
    # SEBI authority claim + guaranteed return + Telegram + external app + ₹5,000 payment
    # =========================================================================
    obs1_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c1 = content_engine.process_text(obs1_text)
    cl1 = claims_engine.analyze(c1)
    a1 = actions_engine.analyze(c1, cl1)
    s1 = sources_engine.discover_and_retrieve(c1, cl1, a1)
    e1 = evidence_engine.verify(c1, cl1, s1)
    t1 = threat_engine.analyze(c1, cl1, a1, s1, e1)

    res1 = fp_engine.create_or_match(c1, cl1, a1, s1, e1, t1)

    assert res1.is_new_pattern is True
    assert res1.fingerprint.fingerprint_id == "SFP-001"
    assert res1.fingerprint.status == "NEW"
    assert res1.fingerprint.observation_count == 1
    assert "telegram" in res1.fingerprint.distinct_channels

    # =========================================================================
    # Observation 2: Mutated wording, WhatsApp, ₹4,999, lookalike domain
    # Expected: Matches SFP-001 as STRUCTURAL_MATCH or SEMANTIC_VARIANT; count -> 2
    # =========================================================================
    obs2_text = (
        "SEBI certified financial expert Vijay Kumar! Assured 40% returns. "
        "Join our VIP WhatsApp group: https://chat.whatsapp.com/inv99. "
        "Install our mobile software and pay ₹4,999 subscription fee."
    )
    c2 = content_engine.process_text(obs2_text)
    cl2 = claims_engine.analyze(c2)
    a2 = actions_engine.analyze(c2, cl2)
    s2 = sources_engine.discover_and_retrieve(c2, cl2, a2)
    e2 = evidence_engine.verify(c2, cl2, s2)
    t2 = threat_engine.analyze(c2, cl2, a2, s2, e2)

    res2 = fp_engine.create_or_match(c2, cl2, a2, s2, e2, t2)

    assert res2.is_new_pattern is False
    assert res2.primary_match is not None
    assert res2.match_type == "SEMANTIC_VARIANT"
    assert res2.structural_equivalence is True
    assert res2.match_confidence >= 0.85
    assert res2.fingerprint.observation_count == 2
    assert "whatsapp" in res2.fingerprint.distinct_channels
    assert "telegram" in res2.fingerprint.distinct_channels

    # Verify Downstream collective response (Section 34)
    ctx = res2.collective_context
    assert ctx["fingerprint_id"] == "SFP-001"
    assert ctx["recent_observation_count"] == 2
    assert "Private-channel migration solicitation" in ctx["matching_characteristics"]
    assert "Direct payment or fee solicitation" in ctx["matching_characteristics"]
    assert "Rahul Sharma" not in str(ctx)
    assert "Vijay Kumar" not in str(ctx)

    # =========================================================================
    # Observation 3 (Secondary Demo): "Learn what mutual funds are."
    # Expected: NO_MATCH. Must not pollute or match SFP-001.
    # =========================================================================
    obs3_text = "Learn what mutual funds are and how diversification protects your capital over the long term."
    c3 = content_engine.process_text(obs3_text)
    cl3 = claims_engine.analyze(c3)
    a3 = actions_engine.analyze(c3, cl3)
    s3 = sources_engine.discover_and_retrieve(c3, cl3, a3)
    e3 = evidence_engine.verify(c3, cl3, s3)
    t3 = threat_engine.analyze(c3, cl3, a3, s3, e3)

    res3 = fp_engine.create_or_match(c3, cl3, a3, s3, e3, t3)

    assert res3.match_type == "NO_MATCH"
    assert res3.match_confidence == 0.0
    assert res3.primary_match is None
    assert res3.fingerprint.fingerprint_id == "SFP-NONE"

    # Stored SFP-001 count must remain 2, completely untouched by Observation 3
    stored_sfp1 = fp_engine.get_fingerprint("SFP-001")
    assert stored_sfp1.observation_count == 2

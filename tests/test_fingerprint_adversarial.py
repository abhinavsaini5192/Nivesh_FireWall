"""Adversarial and boundary tests for Engine 7 (false-match and false-split defenses)."""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine


def test_adversarial_mutations_preserve_structural_match():
    """Observation 1 (Telegram, ₹5,000, 'Guaranteed') and Observation 2 (WhatsApp, ₹4,999, 'Assured')
    must match structurally without false-splitting into unrelated records.
    """
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()
    fp_engine = ScamFingerprintEngine()

    # Observation 1
    text1 = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c1 = content_engine.process_text(text1)
    cl1 = claims_engine.analyze(c1)
    a1 = actions_engine.analyze(c1, cl1)
    s1 = sources_engine.discover_and_retrieve(c1, cl1, a1)
    e1 = evidence_engine.verify(c1, cl1, s1)
    t1 = threat_engine.analyze(c1, cl1, a1, s1, e1)

    res1 = fp_engine.create_or_match(c1, cl1, a1, s1, e1, t1)
    assert res1.is_new_pattern is True
    assert res1.fingerprint.fingerprint_id == "SFP-001"
    assert res1.fingerprint.observation_count == 1

    # Observation 2: Mutated wording, WhatsApp, ₹4,999, lookalike domain
    text2 = (
        "SEBI recognized consultant Amit Verma! Assured 40 percent returns. "
        "Join our WhatsApp VIP group: https://chat.whatsapp.com/inv99. "
        "Install our client app and pay ₹4,999 activation fee."
    )
    c2 = content_engine.process_text(text2)
    cl2 = claims_engine.analyze(c2)
    a2 = actions_engine.analyze(c2, cl2)
    s2 = sources_engine.discover_and_retrieve(c2, cl2, a2)
    e2 = evidence_engine.verify(c2, cl2, s2)
    t2 = threat_engine.analyze(c2, cl2, a2, s2, e2)

    res2 = fp_engine.create_or_match(c2, cl2, a2, s2, e2, t2)
    # Must NOT false-split: must recognize as structural match or semantic variant of SFP-001
    assert res2.is_new_pattern is False
    assert res2.primary_match is not None
    assert res2.primary_match.fingerprint_id == "SFP-001"
    assert res2.match_type == "SEMANTIC_VARIANT"
    assert res2.structural_equivalence is True
    assert res2.match_confidence >= 0.80

    # Stored fingerprint should now have observation_count == 2
    fp1 = fp_engine.get_fingerprint("SFP-001")
    assert fp1.observation_count == 2
    assert "telegram" in fp1.distinct_channels
    assert "whatsapp" in fp1.distinct_channels


def test_critical_false_match_prevention():
    """Two messages both mentioning 'Telegram' and 'investment' but one is genuine educational content:
    must NOT false-match with the threat fingerprint.
    """
    content_engine = ContentIntelligenceEngine()
    claims_engine = ClaimIntelligenceEngine()
    actions_engine = ActionIntelligenceEngine()
    sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
    evidence_engine = EvidenceVerificationEngine()
    threat_engine = ThreatIntelligenceEngine()
    fp_engine = ScamFingerprintEngine()

    # Step 1: Ingest threat pattern
    scam_text = (
        "SEBI advisor! Guaranteed 40% returns. "
        "Join our Telegram VIP channel: https://t.me/vip. "
        "Pay ₹5,000 for VIP tips."
    )
    c_scam = content_engine.process_text(scam_text)
    cl_scam = claims_engine.analyze(c_scam)
    a_scam = actions_engine.analyze(c_scam, cl_scam)
    s_scam = sources_engine.discover_and_retrieve(c_scam, cl_scam, a_scam)
    e_scam = evidence_engine.verify(c_scam, cl_scam, s_scam)
    t_scam = threat_engine.analyze(c_scam, cl_scam, a_scam, s_scam, e_scam)
    res_scam = fp_engine.create_or_match(c_scam, cl_scam, a_scam, s_scam, e_scam, t_scam)
    assert res_scam.is_new_pattern is True

    # Step 2: Educational text sharing superficial words: 'Telegram', 'investment'
    edu_text = (
        "Join our free community Telegram group to discuss financial literacy and index fund investment. "
        "No fees, no guaranteed returns, strictly educational."
    )
    c_edu = content_engine.process_text(edu_text)
    cl_edu = claims_engine.analyze(c_edu)
    a_edu = actions_engine.analyze(c_edu, cl_edu)
    s_edu = sources_engine.discover_and_retrieve(c_edu, cl_edu, a_edu)
    e_edu = evidence_engine.verify(c_edu, cl_edu, s_edu)
    t_edu = threat_engine.analyze(c_edu, cl_edu, a_edu, s_edu, e_edu)

    res_edu = fp_engine.create_or_match(c_edu, cl_edu, a_edu, s_edu, e_edu, t_edu)

    # Must NOT false-match to SFP-001!
    if res_edu.primary_match:
        assert res_edu.primary_match.match_type not in ("EXACT_MATCH", "STRUCTURAL_MATCH", "SEMANTIC_VARIANT")
    assert res_edu.match_type in ("NO_MATCH", "RELATED_PATTERN")

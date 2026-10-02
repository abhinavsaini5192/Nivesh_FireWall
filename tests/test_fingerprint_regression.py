"""Targeted regression tests for Engine 7 corrections:
1. Deterministic single-valued match classification with structural_equivalence.
2. Copy-amplification handling (exact copy across channels & tracking links vs genuine variants vs unrelated).
3. Complete serialization-based privacy enforcement (no PII or raw text in stored/serialized fingerprint).
4. Channel diversity preservation without artificial corroboration.
5. Non-destructive dispute preservation and API verification.
6. Full 1 -> 7 pipeline integration with Observations A, B, and C.
"""

import json
import pytest
from fastapi.testclient import TestClient

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.fingerprints.matcher import FingerprintMatcher
from nivesh.api.app import app, fingerprint_engine


@pytest.fixture(autouse=True)
def reset_fp_repo():
    fingerprint_engine.reset()
    yield
    fingerprint_engine.reset()


def test_deterministic_single_valued_match_classification():
    """Verify that match_type is strictly single-valued and deterministic across repeated runs."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe_engine = ScamFingerprintEngine()

    text1 = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c1 = ce.process_text(text1)
    cl1 = cl.analyze(c1)
    a1 = ae.analyze(c1, cl1)
    s1 = se.discover_and_retrieve(c1, cl1, a1)
    e1 = ee.verify(c1, cl1, s1)
    t1 = te.analyze(c1, cl1, a1, s1, e1)
    res1 = fe_engine.create_or_match(c1, cl1, a1, s1, e1, t1)

    text2 = (
        "SEBI certified financial expert Vijay Kumar! Assured 40% returns. "
        "Join our VIP WhatsApp group: https://chat.whatsapp.com/inv99. "
        "Install our mobile software and pay ₹4,999 subscription fee."
    )
    c2 = ce.process_text(text2)
    cl2 = cl.analyze(c2)
    a2 = ae.analyze(c2, cl2)
    s2 = se.discover_and_retrieve(c2, cl2, a2)
    e2 = ee.verify(c2, cl2, s2)
    t2 = te.analyze(c2, cl2, a2, s2, e2)

    # Run matching 5 times; assert strict determinism and single-valued classification
    for _ in range(5):
        features2 = fe_engine.feature_extractor.extract_features(c2, cl2, a2, s2, e2, t2)
        match = fe_engine.matcher.compare(features2, res1.fingerprint)

        # Must have exactly ONE single-valued enum (no slashes)
        assert match.match_type == "SEMANTIC_VARIANT"
        assert match.structural_equivalence is True
        assert match.match_confidence == 0.91
        assert "attack_path" in match.matched_dimensions
        assert "action_patterns" in match.matched_dimensions


def test_copy_amplification_across_channels_and_tracking_params():
    """Verify that exact messages copied across Telegram, WhatsApp, and Web, or with tracking refs,
    do NOT increment independent observation_count.
    """
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe_engine = ScamFingerprintEngine()

    base_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    # 1. Observation on Telegram
    c1 = ce.process_text(base_text)
    cl1 = cl.analyze(c1)
    a1 = ae.analyze(c1, cl1)
    s1 = se.discover_and_retrieve(c1, cl1, a1)
    e1 = ee.verify(c1, cl1, s1)
    t1 = te.analyze(c1, cl1, a1, s1, e1)
    res1 = fe_engine.create_or_match(c1, cl1, a1, s1, e1, t1)

    fp = fe_engine.get_fingerprint(res1.fingerprint.fingerprint_id)
    assert fp.observation_count == 1
    assert res1.observation.is_duplicate_origin is False

    # 2. Exact same message copied to WhatsApp
    c2 = ce.process_text(base_text)
    cl2 = cl.analyze(c2)
    a2 = ae.analyze(c2, cl2)
    s2 = se.discover_and_retrieve(c2, cl2, a2)
    e2 = ee.verify(c2, cl2, s2)
    t2 = te.analyze(c2, cl2, a2, s2, e2)
    res2 = fe_engine.create_or_match(c2, cl2, a2, s2, e2, t2)

    assert fp.observation_count == 1  # Crucial: MUST NOT INCREMENT
    assert res2.observation.is_duplicate_origin is True

    # 3. Exact same message with tracking query parameter appended (?ref=vip_campaign)
    tracking_text = base_text.replace("https://t.me/rahulinvest", "https://t.me/rahulinvest?ref=vip_campaign")
    c3 = ce.process_text(tracking_text)
    cl3 = cl.analyze(c3)
    a3 = ae.analyze(c3, cl3)
    s3 = se.discover_and_retrieve(c3, cl3, a3)
    e3 = ee.verify(c3, cl3, s3)
    t3 = te.analyze(c3, cl3, a3, s3, e3)
    res3 = fe_engine.create_or_match(c3, cl3, a3, s3, e3, t3)

    assert fp.observation_count == 1  # Still 1
    assert res3.observation.is_duplicate_origin is True

    # 4. Genuine variant (mutated wording & amount) -> MUST increment
    variant_text = (
        "SEBI certified advisor Amit Roy! Assured 40% returns. "
        "Join our VIP group: https://chat.whatsapp.com/inv99. "
        "Download our app and pay ₹4,999."
    )
    c4 = ce.process_text(variant_text)
    cl4 = cl.analyze(c4)
    a4 = ae.analyze(c4, cl4)
    s4 = se.discover_and_retrieve(c4, cl4, a4)
    e4 = ee.verify(c4, cl4, s4)
    t4 = te.analyze(c4, cl4, a4, s4, e4)
    res4 = fe_engine.create_or_match(c4, cl4, a4, s4, e4, t4)

    assert fp.observation_count == 2
    assert res4.observation.is_duplicate_origin is False
    assert res4.match_type == "SEMANTIC_VARIANT"
    assert res4.structural_equivalence is True


def test_serialization_privacy_preservation_no_pii_or_raw_content():
    """Verify serialized ScamFingerprint, observations, and collective context contain NO PII or raw text."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe_engine = ScamFingerprintEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Phone: +91-9876543210, Email: rahul.sharma99@gmail.com. "
        "PAN: ABCDE1234F, Aadhaar: 1234 5678 9012, Bank Account: 123456789012, OTP: 482910. "
        "Guaranteed 40% returns. Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    c = ce.process_text(raw_text)
    claims = cl.analyze(c)
    actions = ae.analyze(c, claims)
    sources = se.discover_and_retrieve(c, claims, actions)
    evidence = ee.verify(c, claims, sources)
    threat = te.analyze(c, claims, actions, sources, evidence)

    analysis = fe_engine.create_or_match(c, claims, actions, sources, evidence, threat)
    fp = analysis.fingerprint

    # Serialize to JSON strings
    serialized_fp = fp.model_dump_json()
    serialized_obs = analysis.observation.model_dump_json()
    serialized_ctx = json.dumps(analysis.collective_context)

    prohibited_items = [
        "Rahul Sharma",
        "9876543210",
        "rahul.sharma99@gmail.com",
        "ABCDE1234F",
        "1234 5678 9012",
        "123456789012",
        "482910",
        "🚨 SEBI registered advisor Rahul Sharma! Phone:",
    ]

    for pii in prohibited_items:
        assert pii not in serialized_fp, f"PII '{pii}' leaked in ScamFingerprint: {serialized_fp}"
        assert pii not in serialized_obs, f"PII '{pii}' leaked in FingerprintObservation: {serialized_obs}"
        assert pii not in serialized_ctx, f"PII '{pii}' leaked in collective_context: {serialized_ctx}"

    # Verify structural threat information is preserved
    assert "CLAIM:GUARANTEED_RETURN" in serialized_fp
    assert "ACTION:CHANNEL_MIGRATION" in serialized_fp
    assert "ACTION:PAYMENT_REQUEST" in serialized_fp
    assert "IDENTITY:REGULATORY_AUTHORITY_CLAIM" in serialized_fp
    assert "TRUST_BUILDING" in serialized_fp
    assert "CHANNEL_MIGRATION" in serialized_fp


def test_api_dispute_preserves_audit_trail_and_history():
    """Verify POST /api/v1/fingerprints/{id}/dispute updates status, records audit, and preserves observations."""
    client = TestClient(app)
    ce = ContentIntelligenceEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c = ce.process_text(raw_text)

    # 1. Create fingerprint via match endpoint
    match_resp = client.post("/api/v1/fingerprints/match", json={"content": c.model_dump()})
    assert match_resp.status_code == 200
    fp_id = match_resp.json()["fingerprint"]["fingerprint_id"]

    # 2. Record dispute
    dispute_payload = {
        "reason": "Claimed individual is legitimately licensed under a sub-broker code.",
        "actor": "compliance_auditor"
    }
    disp_resp = client.post(f"/api/v1/fingerprints/{fp_id}/dispute", json=dispute_payload)
    assert disp_resp.status_code == 200
    disp_data = disp_resp.json()

    assert disp_data["status"] == "DISPUTED"
    assert disp_data["dispute_count"] == 1
    assert len(disp_data["dispute_notes"]) == 1
    assert "legitimately licensed" in disp_data["dispute_notes"][0]
    assert len(disp_data["status_change_history"]) == 1
    assert disp_data["status_change_history"][0]["to_status"] == "DISPUTED"

    # Historical observations must NOT be wiped
    repo_fp = fingerprint_engine.get_fingerprint(fp_id)
    obs_list = fingerprint_engine.repository.list_observations(fp_id)
    assert len(obs_list) == 1
    assert repo_fp.status == "DISPUTED"


def test_full_pipeline_observations_a_b_c_integration():
    """Execute complete 1 -> 7 pipeline on Observations A, B, and C."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()

    # Observation A
    text_a = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c_a = ce.process_text(text_a)
    cl_a = cl.analyze(c_a)
    a_a = ae.analyze(c_a, cl_a)
    s_a = se.discover_and_retrieve(c_a, cl_a, a_a)
    e_a = ee.verify(c_a, cl_a, s_a)
    t_a = te.analyze(c_a, cl_a, a_a, s_a, e_a)
    res_a = fe.create_or_match(c_a, cl_a, a_a, s_a, e_a, t_a)

    assert res_a.is_new_pattern is True
    assert res_a.fingerprint.fingerprint_id == "SFP-001"
    assert res_a.fingerprint.observation_count == 1
    assert res_a.fingerprint.status == "NEW"

    # Observation B
    text_b = (
        "SEBI certified financial expert Vijay Kumar! Assured 40% returns. "
        "Join our VIP WhatsApp group: https://chat.whatsapp.com/inv99. "
        "Install our mobile software and pay ₹4,999 subscription fee."
    )
    c_b = ce.process_text(text_b)
    cl_b = cl.analyze(c_b)
    a_b = ae.analyze(c_b, cl_b)
    s_b = se.discover_and_retrieve(c_b, cl_b, a_b)
    e_b = ee.verify(c_b, cl_b, s_b)
    t_b = te.analyze(c_b, cl_b, a_b, s_b, e_b)
    res_b = fe.create_or_match(c_b, cl_b, a_b, s_b, e_b, t_b)

    assert res_b.is_new_pattern is False
    assert res_b.primary_match.fingerprint_id == "SFP-001"
    assert res_b.match_type == "SEMANTIC_VARIANT"
    assert res_b.structural_equivalence is True
    assert res_b.match_confidence == 0.91
    assert res_b.fingerprint.observation_count == 2
    assert res_b.fingerprint.status == "ACTIVE"

    # Observation C
    text_c = "Learn what mutual funds are and how diversification protects capital."
    c_c = ce.process_text(text_c)
    cl_c = cl.analyze(c_c)
    a_c = ae.analyze(c_c, cl_c)
    s_c = se.discover_and_retrieve(c_c, cl_c, a_c)
    e_c = ee.verify(c_c, cl_c, s_c)
    t_c = te.analyze(c_c, cl_c, a_c, s_c, e_c)
    res_c = fe.create_or_match(c_c, cl_c, a_c, s_c, e_c, t_c)

    assert res_c.match_type == "NO_MATCH"
    assert res_c.structural_equivalence is False
    assert res_c.match_confidence == 0.0

    # Assert SFP-001 is completely unmutated
    sfp1 = fe.get_fingerprint("SFP-001")
    assert sfp1.observation_count == 2
    assert sfp1.status == "ACTIVE"

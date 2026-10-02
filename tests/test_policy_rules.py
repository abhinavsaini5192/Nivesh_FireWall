"""Unit tests for individual policy rules in Engine 8."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.evaluator import PolicyEvaluator
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.policy.reason_codes import ReasonCode


@pytest.fixture
def engines():
    return {
        "content": ContentIntelligenceEngine(),
        "claims": ClaimIntelligenceEngine(),
        "actions": ActionIntelligenceEngine(),
        "sources": SourceIntelligenceEngine(default_mode="FIXTURE"),
        "evidence": EvidenceVerificationEngine(),
        "threat": ThreatIntelligenceEngine(),
        "fingerprints": ScamFingerprintEngine(),
        "evaluator": PolicyEvaluator(),
    }


def test_rule_allow_benign_educational(engines):
    """Assert RULE-ALLOW-01 triggers for benign educational content."""
    text = "Learn what mutual funds are and how diversification protects capital."
    c = engines["content"].process_text(text)
    cl = engines["claims"].analyze(c)
    a = engines["actions"].analyze(c, cl)
    s = engines["sources"].discover_and_retrieve(c, cl, a)
    e = engines["evidence"].verify(c, cl, s)
    t = engines["threat"].analyze(c, cl, a, s, e)
    fp = engines["fingerprints"].create_or_match(c, cl, a, s, e, t)

    results = engines["evaluator"].evaluate_all(c, cl, a, s, e, t, fp)
    assert any(r.rule_id == "RULE-ALLOW-01" and r.decision == PolicyDecisionType.ALLOW for r in results)


def test_rule_inform_market_prediction(engines):
    """Assert RULE-INFORM-01 triggers for market predictions and opinions without threats."""
    text = "In my opinion, Indian equities and Nifty index may reach new highs this year due to strong economic growth."
    c = engines["content"].process_text(text)
    cl = engines["claims"].analyze(c)
    a = engines["actions"].analyze(c, cl)
    s = engines["sources"].discover_and_retrieve(c, cl, a)
    e = engines["evidence"].verify(c, cl, s)
    t = engines["threat"].analyze(c, cl, a, s, e)
    fp = engines["fingerprints"].create_or_match(c, cl, a, s, e, t)

    results = engines["evaluator"].evaluate_all(c, cl, a, s, e, t, fp)
    assert any(r.decision == PolicyDecisionType.INFORM for r in results)
    assert not any(r.decision in (PolicyDecisionType.PAUSE, PolicyDecisionType.BLOCK) for r in results)


def test_rule_warn_channel_migration_unverified(engines):
    """Assert RULE-WARN-01 triggers for private channel migration with unverified assertions."""
    text = "SEBI registered advisor! Join our private VIP Telegram community at https://t.me/superinvest for premium stock alerts."
    c = engines["content"].process_text(text)
    cl = engines["claims"].analyze(c)
    a = engines["actions"].analyze(c, cl)
    s = engines["sources"].discover_and_retrieve(c, cl, a)
    e = engines["evidence"].verify(c, cl, s)
    t = engines["threat"].analyze(c, cl, a, s, e)
    fp = engines["fingerprints"].create_or_match(c, cl, a, s, e, t)

    results = engines["evaluator"].evaluate_all(c, cl, a, s, e, t, fp)
    # Channel migration detected with unverified authority context
    assert any(r.decision == PolicyDecisionType.WARN for r in results)
    assert not any(r.decision == PolicyDecisionType.BLOCK for r in results)


def test_rule_pause_payment_request_with_threat_pattern(engines):
    """Assert RULE-PAUSE-01 triggers when payment is requested under unverified claims and matching threat pattern."""
    text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    c = engines["content"].process_text(text)
    cl = engines["claims"].analyze(c)
    a = engines["actions"].analyze(c, cl)
    s = engines["sources"].discover_and_retrieve(c, cl, a)
    e = engines["evidence"].verify(c, cl, s)
    t = engines["threat"].analyze(c, cl, a, s, e)
    fp = engines["fingerprints"].create_or_match(c, cl, a, s, e, t)

    results = engines["evaluator"].evaluate_all(c, cl, a, s, e, t, fp)
    pause_results = [r for r in results if r.decision == PolicyDecisionType.PAUSE]
    assert len(pause_results) > 0
    pause_rule = pause_results[0]
    assert pause_rule.rule_id == "RULE-PAUSE-01"
    assert pause_rule.required_user_confirmation is True
    assert pause_rule.cooldown_seconds == 30
    assert ReasonCode.PAYMENT_REQUEST in pause_rule.reason_codes
    assert ReasonCode.IDENTITY_NOT_ESTABLISHED in pause_rule.reason_codes


def test_rule_pause_software_installation_unverified(engines):
    """Assert RULE-PAUSE-02 triggers when app installation is requested under unverified authority."""
    text = "Download and install our investment app APK at https://investvip.xyz/app.apk to receive SEBI registered advice."
    c = engines["content"].process_text(text)
    cl = engines["claims"].analyze(c)
    a = engines["actions"].analyze(c, cl)
    s = engines["sources"].discover_and_retrieve(c, cl, a)
    e = engines["evidence"].verify(c, cl, s)
    t = engines["threat"].analyze(c, cl, a, s, e)
    fp = engines["fingerprints"].create_or_match(c, cl, a, s, e, t)

    results = engines["evaluator"].evaluate_all(c, cl, a, s, e, t, fp)
    assert any(r.rule_id == "RULE-PAUSE-02" and r.decision == PolicyDecisionType.PAUSE for r in results)

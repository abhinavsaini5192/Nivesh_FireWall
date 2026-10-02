"""Privacy and safety boundary verification tests for Engine 8."""

import json
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine


def test_policy_decision_privacy_preservation_no_pii_or_credentials():
    """Verify serialized PolicyDecision and audit_metadata contain NO PII or sensitive credentials."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()

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
    fingerprint = fe.create_or_match(c, claims, actions, sources, evidence, threat)

    decision = pe.decide(c, claims, actions, sources, evidence, threat, fingerprint)

    serialized_decision = decision.model_dump_json()
    serialized_audit = json.dumps(decision.audit_metadata)

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

    for item in prohibited_items:
        assert item not in serialized_decision, f"PII/credential '{item}' found in serialized PolicyDecision!"
        assert item not in serialized_audit, f"PII/credential '{item}' found in audit_metadata!"


def test_policy_boundaries_no_investment_advice():
    """Verify that Engine 8 outputs contain zero investment advice, buy/sell/hold ratings, or criminal labels."""
    pe = PolicyInterventionEngine()
    rules = pe.list_rules()

    prohibited_investment_terms = ["buy", "sell", "hold", "target price", "undervalued", "overvalued", "scammer", "criminal"]

    for r in rules:
        for term in prohibited_investment_terms:
            assert term not in r["name"].lower(), f"Prohibited term '{term}' in rule name: {r['name']}"
            assert term not in r["description"].lower(), f"Prohibited term '{term}' in rule description: {r['description']}"

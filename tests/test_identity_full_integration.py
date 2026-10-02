"""Full 9-Engine End-to-End Pipeline Integration Test.

Executes real sequential pipeline:
Raw Content
  -> Engine 1 (Content Intelligence)
  -> Engine 2 (Claim Intelligence)
  -> Engine 3 (Action Intelligence)
  -> Engine 4 (Source Intelligence)
  -> Engine 5 (Evidence Verification)
  -> Engine 6 (Threat & Attack-Path Intelligence)
  -> Engine 7 (Scam Fingerprint & Collective Threat Intelligence)
  -> Engine 8 (Policy & Intervention)
  -> Engine 9 (Identity Verification & Entity Resolution)
"""

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import (
    IdentityStatus,
    IdentityFindingType,
)


def test_full_9_engine_primary_benchmark_pipeline():
    """Execute complete 1 -> 9 pipeline on primary benchmark content."""
    # Instantiate all 9 real engines
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()
    ie = IdentityVerificationEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    # 1. Engine 1
    content = ce.process_text(raw_text)
    assert content.normalized.text is not None

    # 2. Engine 2
    claims = cl.analyze(content)
    assert len(claims.claims) >= 2

    # 3. Engine 3
    actions = ae.analyze(content, claims)
    assert len(actions.actions) >= 3

    # 4. Engine 4
    sources = se.discover_and_retrieve(content, claims, actions)
    assert len(sources.claim_sources) > 0

    # 5. Engine 5
    evidence = ee.verify(content, claims, sources)
    assert len(evidence.verifications) >= 2

    # 6. Engine 6
    threat = te.analyze(content, claims, actions, sources, evidence)
    assert len(threat.attack_path.nodes) >= 3

    # 7. Engine 7
    fingerprint = fe.create_or_match(content, claims, actions, sources, evidence, threat)
    assert fingerprint.fingerprint is not None

    # 8. Engine 8
    decision = pe.decide(content, claims, actions, sources, evidence, threat, fingerprint)
    assert decision.decision.value in ("PAUSE", "BLOCK", "WARN")

    # 9. Engine 9: Identity Verification & Entity Resolution
    identity_analysis = ie.verify(
        content=content,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )

    # Validate Engine 9 outputs
    assert identity_analysis.analysis_id.startswith("IDA-")
    assert identity_analysis.identity_status == IdentityStatus.NOT_ESTABLISHED

    # Check extracted claimed entities
    entity_names = [e.normalized_name.lower() for e in identity_analysis.entities]
    assert any("rahul" in name for name in entity_names)

    # Check regulator authority alignment
    sebi_alignment = next((a for a in identity_analysis.authority_alignments if a.authority_name == "SEBI"), None)
    assert sebi_alignment is not None
    assert sebi_alignment.alignment_status == "NOT_ESTABLISHED"

    # Check findings
    finding_types = [f.finding_type for f in identity_analysis.identity_findings]
    assert IdentityFindingType.AUTHORITY_CLAIM in finding_types
    assert (
        IdentityFindingType.AUTHORITY_IDENTITY_NOT_ESTABLISHED in finding_types
        or IdentityFindingType.REGISTRATION_IDENTIFIER_UNRESOLVED in finding_types
    )

    # Check social channel
    assert any(f.finding_type == IdentityFindingType.SOCIAL_ACCOUNT_NOT_ESTABLISHED for f in identity_analysis.identity_findings)

    # Verify complete Provenance Continuity across Engines 1-9
    assert identity_analysis.provenance.input_content_id == content.content_id
    assert identity_analysis.provenance.claim_count == len(claims.claims)
    assert identity_analysis.provenance.evidence_count == len(evidence.verifications)
    assert identity_analysis.upstream_references["content_id"] == content.content_id
    assert set(identity_analysis.upstream_references["claim_ids"]) == {c.claim_id for c in claims.claims}
    assert identity_analysis.upstream_references["threat_id"] == threat.content_id


def test_full_9_engine_informational_content():
    """Execute complete 1 -> 9 pipeline on benign educational content."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    pe = PolicyInterventionEngine()
    ie = IdentityVerificationEngine()

    raw_text = "What is rupee cost averaging? Investing a fixed amount regularly balances market volatility."

    content = ce.process_text(raw_text)
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)
    sources = se.discover_and_retrieve(content, claims, actions)
    evidence = ee.verify(content, claims, sources)
    threat = te.analyze(content, claims, actions, sources, evidence)
    fingerprint = fe.create_or_match(content, claims, actions, sources, evidence, threat)
    decision = pe.decide(content, claims, actions, sources, evidence, threat, fingerprint)

    identity_analysis = ie.verify(
        content=content,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )

    assert decision.decision.value == "ALLOW"
    assert identity_analysis.identity_status in (IdentityStatus.NOT_APPLICABLE, IdentityStatus.NOT_ESTABLISHED)
    assert identity_analysis.confidence >= 0.5

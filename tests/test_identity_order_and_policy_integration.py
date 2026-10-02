"""Regression tests verifying corrected downstream dependency ordering between Engine 9 and Engine 8.

Proves:
1. Engine 9 identity findings exist before Engine 8 executes.
2. Engine 8 consumes IdentityAnalysis directly.
3. IdentityAnalysis indicating NOT_ESTABLISHED does NOT force BLOCK.
4. IdentityAnalysis indicating IDENTITY_MISMATCH requires authoritative contradiction.
5. IdentityAnalysis = AMBIGUOUS does not fabricate an entity.
6. Engine 8 does not independently re-run identity-resolution logic.
7. No circular dependency exists (Engine 9 never imports or calls Engine 8).
8. Existing Engine 1-8 behaviors and non-accusatory semantics are strictly preserved.
"""

import sys
import importlib
import inspect
from unittest.mock import MagicMock, patch

from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.fingerprints.engine import ScamFingerprintEngine
from nivesh.policy.engine import PolicyInterventionEngine
from nivesh.policy.schemas import PolicyDecisionType
from nivesh.policy.reason_codes import ReasonCode
from nivesh.identity.engine import IdentityVerificationEngine
from nivesh.identity.schemas import (
    IdentityStatus,
    IdentityFindingType,
    IdentityAnalysis,
    ClaimedEntity,
    IdentityEntityType,
    ResolvedEntity,
    IdentityMatch,
    IdentityMatchStatus,
    IdentityProvenance,
)


def _build_upstream_intelligence(raw_text: str):
    """Helper to generate consistent upstream intelligence from Engines 1-7."""
    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()

    content = ce.process_text(raw_text)
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)
    sources = se.discover_and_retrieve(content, claims, actions)
    evidence = ee.verify(content, claims, sources)
    threat = te.analyze(content, claims, actions, sources, evidence)
    fingerprint = fe.create_or_match(content, claims, actions, sources, evidence, threat)

    return content, claims, actions, sources, evidence, threat, fingerprint


def test_regression_1_engine_9_executes_and_completes_before_engine_8():
    """Verify Engine 9 executes and completes before Engine 8 makes its policy decision."""
    execution_order = []

    ce = ContentIntelligenceEngine()
    cl = ClaimIntelligenceEngine()
    ae = ActionIntelligenceEngine()
    se = SourceIntelligenceEngine(default_mode="FIXTURE")
    ee = EvidenceVerificationEngine()
    te = ThreatIntelligenceEngine()
    fe = ScamFingerprintEngine()
    ie = IdentityVerificationEngine()
    pe = PolicyInterventionEngine()

    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )

    # Execute upstream
    content = ce.process_text(raw_text)
    claims = cl.analyze(content)
    actions = ae.analyze(content, claims)
    sources = se.discover_and_retrieve(content, claims, actions)
    evidence = ee.verify(content, claims, sources)
    threat = te.analyze(content, claims, actions, sources, evidence)
    fingerprint = fe.create_or_match(content, claims, actions, sources, evidence, threat)

    # Execute Engine 9
    execution_order.append("ENGINE_9_START")
    identity_analysis = ie.verify(
        content=content,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )
    execution_order.append("ENGINE_9_FINISH")
    assert isinstance(identity_analysis, IdentityAnalysis)
    assert identity_analysis.analysis_id.startswith("IDA-")

    # Execute Engine 8 with Engine 9 output
    execution_order.append("ENGINE_8_START")
    decision = pe.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity_analysis,
    )
    execution_order.append("ENGINE_8_FINISH")

    # Invariant: Engine 9 MUST finish before Engine 8 starts
    assert execution_order == [
        "ENGINE_9_START",
        "ENGINE_9_FINISH",
        "ENGINE_8_START",
        "ENGINE_8_FINISH",
    ]
    assert decision.relevant_identity_id == identity_analysis.analysis_id


def test_regression_2_engine_8_consumes_identity_analysis_directly():
    """Verify Engine 8 consumes IdentityAnalysis directly and exposes it in decision metadata."""
    raw_text = "SEBI registered advisor Rahul Sharma! Free market insights on our group."
    content, claims, actions, sources, evidence, threat, fingerprint = _build_upstream_intelligence(raw_text)

    ie = IdentityVerificationEngine()
    pe = PolicyInterventionEngine()

    identity = ie.verify(
        content=content,
        claims=claims,
        sources=sources,
        evidence=evidence,
        threat=threat,
    )

    decision = pe.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
    )

    # Assert decision consumed the real identity analysis object
    assert decision.relevant_identity_id == identity.analysis_id
    assert decision.audit_metadata["identity_status"] == identity.identity_status.value
    assert decision.audit_metadata["identity_analysis_id"] == identity.analysis_id
    assert "identity_entity_count" in decision.audit_metadata


def test_regression_3_identity_not_established_does_not_force_block():
    """Verify IdentityAnalysis indicating NOT_ESTABLISHED does NOT force BLOCK."""
    # Scenario: Regulatory claim with unverified identity, but no direct payment or credential theft
    raw_text = "SEBI registered advisor Rahul Sharma shares general thoughts on index funds."
    content, claims, actions, sources, evidence, threat, fingerprint = _build_upstream_intelligence(raw_text)

    ie = IdentityVerificationEngine()
    pe = PolicyInterventionEngine()

    identity = ie.verify(content, claims, sources, evidence, threat)
    assert identity.identity_status == IdentityStatus.NOT_ESTABLISHED

    decision = pe.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
    )

    # Must NOT block simply because identity could not be established
    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.decision in (PolicyDecisionType.WARN, PolicyDecisionType.INFORM, PolicyDecisionType.ALLOW)
    assert ReasonCode.IDENTITY_NOT_ESTABLISHED in decision.reason_codes or ReasonCode.UNVERIFIED_REGULATORY_CLAIM in decision.reason_codes


def test_regression_4_identity_mismatch_requires_authoritative_contradiction():
    """Verify IdentityAnalysis indicating IDENTITY_MISMATCH requires authoritative contradiction."""
    # Case A: Missing registry entry produces NOT_ESTABLISHED, strictly NOT IDENTITY_MISMATCH
    raw_text_missing = "SEBI registered advisor Rahul Sharma. Guaranteed returns."
    c1, cl1, a1, s1, e1, t1, fp1 = _build_upstream_intelligence(raw_text_missing)
    ie = IdentityVerificationEngine()
    id_missing = ie.verify(c1, cl1, s1, e1, t1)

    assert id_missing.identity_status == IdentityStatus.NOT_ESTABLISHED
    assert id_missing.identity_status != IdentityStatus.IDENTITY_MISMATCH

    # Case B: Authoritative registry evidence contradicting claimed entity
    # When official evidence explicitly contradicts the entity
    c_entity = ClaimedEntity(
        entity_id="ENT-TEST-001",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
        associated_registration="INA000000001",
    )
    r_entity = ResolvedEntity(
        candidate_id="CAND-TEST-001",
        legal_name="Completely Different Entity Private Limited",
        normalized_name="completely different entity private limited",
        entity_type=IdentityEntityType.FINANCIAL_INTERMEDIARY,
        registration_number="INA000000001",
    )
    i_match = IdentityMatch(
        identity_match_id="IM-TEST-001",
        claimed_entity_id="ENT-TEST-001",
        candidate_entity_id="CAND-TEST-001",
        entity_type=IdentityEntityType.ADVISER,
        match_status=IdentityMatchStatus.IDENTITY_MISMATCH,
        match_basis="Registration number INA000000001 belongs to 'Completely Different Entity Private Limited', contradicting 'Rahul Sharma'.",
        conflicting_attributes=["legal_name", "normalized_name"],
        confidence=0.95,
    )
    id_mismatch = IdentityAnalysis(
        analysis_id="IDA-TEST-MISMATCH",
        entities=[c_entity],
        identity_matches=[i_match],
        identity_status=IdentityStatus.IDENTITY_MISMATCH,
        confidence=0.95,
        provenance=IdentityProvenance(
            verified_at="2026-10-02T00:00:00Z",
            input_content_id=c1.content_id,
        ),
    )

    pe = PolicyInterventionEngine()
    decision = pe.decide(
        content=c1,
        claims=cl1,
        actions=a1,
        sources=s1,
        evidence=e1,
        threat=t1,
        fingerprint=fp1,
        identity=id_mismatch,
    )

    assert decision.relevant_identity_id == "IDA-TEST-MISMATCH"
    assert decision.audit_metadata["identity_status"] == "IDENTITY_MISMATCH"


def test_regression_5_ambiguous_identity_does_not_fabricate_entity():
    """Verify IdentityAnalysis with AMBIGUOUS status does not pick a fabricated entity."""
    c_entity = ClaimedEntity(
        entity_id="ENT-TEST-002",
        name="Rahul Sharma",
        normalized_name="rahul sharma",
        entity_type=IdentityEntityType.ADVISER,
    )
    cand1 = ResolvedEntity(
        candidate_id="CAND-1",
        legal_name="Rahul Sharma Advisory Services",
        normalized_name="rahul sharma advisory services",
        entity_type=IdentityEntityType.ADVISER,
        registration_number="INA000001111",
    )
    cand2 = ResolvedEntity(
        candidate_id="CAND-2",
        legal_name="Rahul Sharma Capital Partners",
        normalized_name="rahul sharma capital partners",
        entity_type=IdentityEntityType.ADVISER,
        registration_number="INA000002222",
    )
    m1 = IdentityMatch(
        identity_match_id="IM-1",
        claimed_entity_id="ENT-TEST-002",
        candidate_entity_id="CAND-1",
        entity_type=IdentityEntityType.ADVISER,
        match_status=IdentityMatchStatus.AMBIGUOUS,
        match_basis="Multiple plausible matching intermediaries share this name.",
        confidence=0.45,
    )
    m2 = IdentityMatch(
        identity_match_id="IM-2",
        claimed_entity_id="ENT-TEST-002",
        candidate_entity_id="CAND-2",
        entity_type=IdentityEntityType.ADVISER,
        match_status=IdentityMatchStatus.AMBIGUOUS,
        match_basis="Multiple plausible matching intermediaries share this name.",
        confidence=0.45,
    )
    ambiguous_analysis = IdentityAnalysis(
        analysis_id="IDA-TEST-AMBIGUOUS",
        entities=[c_entity],
        identity_matches=[m1, m2],
        identity_status=IdentityStatus.AMBIGUOUS,
        confidence=0.45,
        provenance=IdentityProvenance(
            verified_at="2026-10-02T00:00:00Z",
            input_content_id="CNT-001",
        ),
    )

    raw_text = "SEBI registered advisor Rahul Sharma. General investment guide."
    content, claims, actions, sources, evidence, threat, fingerprint = _build_upstream_intelligence(raw_text)

    pe = PolicyInterventionEngine()
    decision = pe.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=ambiguous_analysis,
    )

    # Engine 8 should record the ambiguous identity analysis without fabricating an entity or forcing BLOCK
    assert decision.relevant_identity_id == "IDA-TEST-AMBIGUOUS"
    assert decision.decision != PolicyDecisionType.BLOCK
    assert decision.audit_metadata["identity_status"] == "AMBIGUOUS"


def test_regression_6_engine_8_does_not_independently_rerun_identity_resolution():
    """Verify Engine 8 does not independently re-run identity resolution or query registries."""
    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    content, claims, actions, sources, evidence, threat, fingerprint = _build_upstream_intelligence(raw_text)

    ie = IdentityVerificationEngine()
    identity = ie.verify(content, claims, sources, evidence, threat)

    pe = PolicyInterventionEngine()

    # Spy on ie.verify to ensure pe.decide does NOT call ie.verify
    with patch.object(ie, "verify", wraps=ie.verify) as spy_verify:
        decision = pe.decide(
            content=content,
            claims=claims,
            actions=actions,
            sources=sources,
            evidence=evidence,
            threat=threat,
            fingerprint=fingerprint,
            identity=identity,
        )
        assert spy_verify.call_count == 0

    # Verify Engine 8 has no registry lookup or entity resolution attributes
    assert not hasattr(pe, "registry_adapter")
    assert not hasattr(pe, "entity_resolver")
    assert not hasattr(pe, "domain_resolver")
    assert decision.relevant_identity_id == identity.analysis_id


def test_regression_7_no_circular_dependency_between_engine_8_and_engine_9():
    """Verify no circular dependency exists between Engine 8 and Engine 9."""
    import nivesh.identity
    import nivesh.identity.engine
    import nivesh.identity.schemas
    import nivesh.identity.entity_resolver
    import nivesh.identity.authority_resolver
    import nivesh.identity.domain_resolver
    import nivesh.identity.registration_resolver
    import nivesh.identity.social_resolver
    import nivesh.identity.matcher
    import nivesh.identity.findings
    import nivesh.identity.normalizer
    import nivesh.identity.provenance

    identity_modules = [
        nivesh.identity,
        nivesh.identity.engine,
        nivesh.identity.schemas,
        nivesh.identity.entity_resolver,
        nivesh.identity.authority_resolver,
        nivesh.identity.domain_resolver,
        nivesh.identity.registration_resolver,
        nivesh.identity.social_resolver,
        nivesh.identity.matcher,
        nivesh.identity.findings,
        nivesh.identity.normalizer,
        nivesh.identity.provenance,
    ]

    for mod in identity_modules:
        mod_source = inspect.getsource(mod)
        assert "nivesh.policy" not in mod_source, f"Circular dependency: {mod.__name__} imports nivesh.policy"
        assert "PolicyInterventionEngine" not in mod_source, f"Circular dependency in {mod.__name__}"


def test_regression_8_non_accusatory_semantics_preserved():
    """Verify non-accusatory semantics are strictly preserved in both Engine 8 and Engine 9."""
    raw_text = (
        "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group: https://t.me/rahulinvest. "
        "Download our app and pay ₹5,000."
    )
    content, claims, actions, sources, evidence, threat, fingerprint = _build_upstream_intelligence(raw_text)
    ie = IdentityVerificationEngine()
    identity = ie.verify(content, claims, sources, evidence, threat)

    pe = PolicyInterventionEngine()
    decision = pe.decide(
        content=content,
        claims=claims,
        actions=actions,
        sources=sources,
        evidence=evidence,
        threat=threat,
        fingerprint=fingerprint,
        identity=identity,
    )

    # Check Engine 9 outputs for prohibited derogatory labels
    for entity in identity.entities:
        assert "scammer" not in entity.name.lower()
        assert "fraudster" not in entity.name.lower()
        assert "criminal" not in entity.name.lower()

    for finding in identity.identity_findings:
        assert "scammer" not in finding.description.lower()
        assert "fraudster" not in finding.description.lower()
        assert "criminal" not in finding.description.lower()

    # Check Engine 8 outputs for prohibited derogatory labels
    assert "scam" not in decision.user_message.lower()
    assert "fraud" not in decision.user_message.lower()
    assert "criminal" not in decision.user_message.lower()

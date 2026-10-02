"""Dedicated semantic correction tests for Engine 6.

Tests A through F as specified in Engine 6 Targeted Semantic Correction:
- Test A: Explicit rationale ("SEBI approved this platform, so join Telegram.") -> RATIONALE_FOR exists.
- Test B: Adjacent claims/actions ("SEBI approved this platform. Join Telegram.") -> no automatic RATIONALE_FOR.
- Test C: Return claim explains payment ("Guaranteed 40% returns, so pay ₹5,000.") -> GUARANTEED_RETURN -> RATIONALE_FOR -> PAYMENT.
- Test D: Benchmark ("SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join our Telegram VIP group. Download our app and pay ₹5,000.") -> no unjustified blanket links.
- Test E: Authority claim before verification ("Rahul Sharma is a SEBI registered advisor.") -> REGULATORY_AUTHORITY_CLAIM, not automatically AUTHORITY_IMPERSONATION.
- Test F: Identity mismatch when Engine 5 supplies concrete mismatch evidence -> elevates to AUTHORITY_IMPERSONATION with provenance.
"""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.claims.engine import ClaimIntelligenceEngine
from nivesh.actions.engine import ActionIntelligenceEngine
from nivesh.sources.engine import SourceIntelligenceEngine
from nivesh.evidence.engine import EvidenceVerificationEngine
from nivesh.threat.engine import ThreatIntelligenceEngine
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim, ClaimText
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction, ActionTarget, ActionText
from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata
from nivesh.schemas.evidence import (
    EvidenceAnalysis,
    EvidenceAnalysisMetadata,
    VerificationResult,
    VerificationProvenance,
    EvidenceItemEvaluation,
)
from nivesh.threat.signal_detector import ThreatSignalDetector
from nivesh.threat.claim_action_linker import ClaimActionLinker


@pytest.fixture
def engines():
    return {
        "content": ContentIntelligenceEngine(),
        "claims": ClaimIntelligenceEngine(),
        "actions": ActionIntelligenceEngine(),
        "sources": SourceIntelligenceEngine(default_mode="FIXTURE"),
        "evidence": EvidenceVerificationEngine(),
        "threat": ThreatIntelligenceEngine(),
    }


def test_a_explicit_rationale_connective(engines):
    """Test A — Explicit rationale: 'SEBI approved this platform, so join Telegram.'
    Expected: RATIONALE_FOR exists.
    """
    raw_text = "SEBI approved this platform, so join Telegram."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    assert len(threat.claim_action_links) >= 1
    rationale_links = [l for l in threat.claim_action_links if l.type == "RATIONALE_FOR"]
    assert len(rationale_links) >= 1
    # Verify link connects the SEBI approval claim to the join Telegram action
    r_link = rationale_links[0]
    claim_map = {c.claim_id: c for c in claims.claims}
    action_map = {a.action_id: a for a in actions.actions}
    assert r_link.claim_id in claim_map
    assert r_link.action_id in action_map
    assert "SEBI" in (claim_map[r_link.claim_id].object or "") or claim_map[r_link.claim_id].predicate == "APPROVED_BY"
    assert action_map[r_link.action_id].action_type in ("JOIN_CHANNEL", "JOIN_GROUP")


def test_b_adjacent_claims_actions_no_automatic_rationale(engines):
    """Test B — Adjacent claims/actions: 'SEBI approved this platform. Join Telegram.'
    Expected: no automatic RATIONALE_FOR.
    """
    raw_text = "SEBI approved this platform. Join Telegram."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    # Proximity or presence in the same text must NOT produce automatic RATIONALE_FOR
    assert len(threat.claim_action_links) == 0


def test_c_return_claim_explains_payment(engines):
    """Test C — Return claim explains payment: 'Guaranteed 40% returns, so pay ₹5,000.'
    Expected: GUARANTEED_RETURN -> RATIONALE_FOR -> PAYMENT.
    """
    raw_text = "Guaranteed 40% returns, so pay ₹5,000."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    assert len(threat.claim_action_links) >= 1
    r_link = next((l for l in threat.claim_action_links if l.type == "RATIONALE_FOR"), None)
    assert r_link is not None

    claim_map = {c.claim_id: c for c in claims.claims}
    action_map = {a.action_id: a for a in actions.actions}
    linked_claim = claim_map[r_link.claim_id]
    linked_action = action_map[r_link.action_id]

    assert linked_claim.predicate in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or "40%" in (linked_claim.object or "")
    assert linked_action.action_type in ("PAYMENT", "TRANSFER_MONEY") or "5,000" in linked_action.text.original


def test_d_benchmark_no_unjustified_blanket_links(engines):
    """Test D — Benchmark: 'SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join our Telegram VIP group. Download our app and pay ₹5,000.'
    Expected:
    SEBI claim -> no unjustified blanket action links.
    Guaranteed-return claim -> may link to payment only where context supports it.
    """
    raw_text = (
        "SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
        "Join our Telegram VIP group. Download our app and pay ₹5,000."
    )
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = engines["sources"].discover_and_retrieve(norm, claims, actions)
    evidence = engines["evidence"].verify(norm, claims, sources)

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    # 1. SEBI registration claim must NOT link to Telegram, Download app, or Payment
    sebi_claims = [c for c in claims.claims if "SEBI" in (c.object or "") or c.predicate == "REGISTERED_WITH"]
    for sc in sebi_claims:
        unjustified_links = [l for l in threat.claim_action_links if l.claim_id == sc.claim_id]
        assert len(unjustified_links) == 0, f"Unjustified links found for SEBI claim: {unjustified_links}"

    # 2. Guaranteed-return claim must NOT have blanket links to Telegram or Download app
    ret_claims = [c for c in claims.claims if c.predicate in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or "40%" in (c.object or "")]
    for rc in ret_claims:
        for link in threat.claim_action_links:
            if link.claim_id == rc.claim_id:
                target_act = next((a for a in actions.actions if a.action_id == link.action_id), None)
                if target_act:
                    assert target_act.action_type not in ("JOIN_CHANNEL", "JOIN_GROUP", "DOWNLOAD"), \
                        f"Unjustified link from return claim to {target_act.action_type}"


def test_e_authority_claim_before_verification(engines):
    """Test E — Authority claim before verification: 'Rahul Sharma is a SEBI registered advisor.'
    Expected: REGULATORY_AUTHORITY_CLAIM, not automatically AUTHORITY_IMPERSONATION.
    """
    raw_text = "Rahul Sharma is a SEBI registered advisor."
    norm = engines["content"].process_text(raw_text)
    claims = engines["claims"].analyze(norm)
    actions = engines["actions"].analyze(norm, claims)
    sources = SourceAnalysis(content_id=norm.content_id, claim_sources=[], analysis_metadata=SourceAnalysisMetadata())
    # Pre-verification: No evidence analysis completed yet
    evidence = EvidenceAnalysis(content_id=norm.content_id, verifications=[], analysis_metadata=EvidenceAnalysisMetadata())

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    sig_types = {s.type for s in threat.threat_signals}
    assert "REGULATORY_AUTHORITY_CLAIM" in sig_types
    # Must NOT automatically infer AUTHORITY_IMPERSONATION before verification
    assert "AUTHORITY_IMPERSONATION" not in sig_types
    assert "IDENTITY_MISMATCH" not in sig_types


def test_f_identity_mismatch_escalates_to_authority_impersonation(engines):
    """Test F — Identity mismatch: When Engine 5 supplies concrete identity mismatch evidence:
    CLAIM + IDENTITY_MISMATCH evidence
    Expected: AUTHORITY_IMPERSONATION with provenance.
    """
    raw_text = "Rahul Sharma is a SEBI registered advisor."
    norm = engines["content"].process_text(raw_text)
    claims = ClaimAnalysis(
        content_id=norm.content_id,
        claims=[
            CanonicalClaim(
                claim_id="CLAIM-001",
                source_content_id=norm.content_id,
                text=ClaimText(original="Rahul Sharma is a SEBI registered advisor.", normalized="Rahul Sharma is registered with SEBI."),
                claim_type="REGULATORY",
                subject="Rahul Sharma",
                predicate="REGISTERED_WITH",
                object="SEBI"
            )
        ]
    )
    actions = ActionAnalysis(content_id=norm.content_id, actions=[])
    sources = SourceAnalysis(content_id=norm.content_id, claim_sources=[], analysis_metadata=SourceAnalysisMetadata())

    # Engine 5 supplies definitive contradicting evidence establishing identity mismatch
    evidence = EvidenceAnalysis(
        content_id=norm.content_id,
        verifications=[
            VerificationResult(
                claim_id="CLAIM-001",
                status="CONTRADICTED",
                confidence=0.99,
                evidence_strength="HIGH",
                supporting_evidence=[],
                contradicting_evidence=[
                    EvidenceItemEvaluation(
                        evidence_id="EVID-001",
                        source_document_id="SRC-SEBI-REG",
                        source_url="https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes",
                        organization="SEBI",
                        relation="CONTRADICTS",
                        excerpt="SEBI registration INH000009999 belongs to Alpha Wealth Advisors Private Limited, not Rahul Sharma.",
                        reasoning="Registration belongs to a corporate entity, not the individual claimant."
                    )
                ],
                reasoning_trace=[
                    "Official SEBI registry verification reveals registration belongs to another entity (Alpha Wealth Advisors Pvt Ltd).",
                    "Identity mismatch detected for asserted individual 'Rahul Sharma'."
                ],
                provenance=VerificationProvenance(engine_version="1.0.0", verification_method="rule", verified_at="2026-10-02T12:00:00Z")
            )
        ],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    threat = engines["threat"].analyze(norm, claims, actions, sources, evidence)

    sig_types = {s.type for s in threat.threat_signals}
    assert "REGULATORY_AUTHORITY_CLAIM" in sig_types
    assert "IDENTITY_MISMATCH" in sig_types
    assert "AUTHORITY_IMPERSONATION" in sig_types

    imp_sig = next(s for s in threat.threat_signals if s.type == "AUTHORITY_IMPERSONATION")
    assert imp_sig.source == "evidence_verification"
    assert imp_sig.claim_id == "CLAIM-001"
    assert "identity mismatch" in imp_sig.evidence.lower() or "mismatch" in imp_sig.description.lower()

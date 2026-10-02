"""Unit tests for Threat Intelligence schemas in Engine 6."""

import pytest
from pydantic import ValidationError
from nivesh.schemas.threat import (
    ThreatSignal,
    AttackNode,
    AttackTransition,
    AttackPath,
    ClaimActionLink,
    EvidenceWeakness,
    HighImpactAction,
    ThreatCombination,
    ThreatExplanation,
    FingerprintPreparation,
    ThreatProvenance,
    ThreatAnalysisMetadata,
    ThreatAnalysis,
)


def test_threat_signal_schema_valid():
    sig = ThreatSignal(
        signal_id="SIG-001",
        type="AUTHORITY_IMPERSONATION",
        source="claim",
        evidence="Claim asserts SEBI registration",
        confidence=0.92,
        description="Leverages regulatory trust without verified license.",
        claim_id="CLAIM-001"
    )
    assert sig.signal_id == "SIG-001"
    assert sig.type == "AUTHORITY_IMPERSONATION"
    assert sig.source == "claim"
    assert sig.confidence == 0.92


def test_attack_path_and_transition_schema_valid():
    node1 = AttackNode(
        node_id="NODE-01",
        stage="TRUST_BUILDING",
        type="trust_building_stage",
        label="Regulatory Authority Claims",
        linked_claim_ids=["CLAIM-001"],
        linked_action_ids=[],
        evidence_ids=[]
    )
    node2 = AttackNode(
        node_id="NODE-02",
        stage="CHANNEL_MIGRATION",
        type="channel_migration_stage",
        label="Telegram Migration",
        linked_claim_ids=[],
        linked_action_ids=["ACTION-001"],
        evidence_ids=[]
    )
    trans = AttackTransition(
        from_stage="TRUST_BUILDING",
        to_stage="CHANNEL_MIGRATION",
        supporting_actions=["ACTION-001"],
        supporting_claims=["CLAIM-001"],
        confidence=0.88,
        description="Migrates from trust claim to private Telegram channel."
    )
    path = AttackPath(
        nodes=[node1, node2],
        transitions=[trans],
        entry_stage="TRUST_BUILDING",
        terminal_stage="CHANNEL_MIGRATION"
    )
    assert len(path.nodes) == 2
    assert len(path.transitions) == 1
    assert path.entry_stage == "TRUST_BUILDING"
    assert path.terminal_stage == "CHANNEL_MIGRATION"


def test_claim_action_link_schema_valid():
    link = ClaimActionLink(
        link_id="CAL-001",
        claim_id="CLAIM-001",
        action_id="ACTION-001",
        type="RATIONALE_FOR",
        confidence=0.90,
        explanation="SEBI approval assertion provides justification to join Telegram."
    )
    assert link.link_id == "CAL-001"
    assert link.type == "RATIONALE_FOR"


def test_high_impact_action_schema_valid():
    action = HighImpactAction(
        action_id="ACTION-003",
        action_type="PAYMENT",
        impact_category="FINANCIAL",
        reversibility="IRREVERSIBLE",
        description="Direct payment of ₹5,000 is irreversible once settled."
    )
    assert action.action_id == "ACTION-003"
    assert action.impact_category == "FINANCIAL"
    assert action.reversibility == "IRREVERSIBLE"


def test_threat_analysis_full_schema_valid():
    analysis = ThreatAnalysis(
        content_id="c-test-01",
        threat_signals=[],
        attack_path=AttackPath(nodes=[], transitions=[]),
        transitions=[],
        claim_action_links=[],
        evidence_weaknesses=[],
        high_impact_actions=[],
        threat_combinations=[],
        threat_families=["INVESTMENT_PROMOTION_SCAM"],
        fingerprint_prep=FingerprintPreparation(),
        explanation=ThreatExplanation(summary="Test explanation", mechanisms=[], key_factors=[]),
        uncertainty=["Test uncertainty"],
        confidence=0.85,
        provenance=ThreatProvenance(
            engine_version="1.0.0",
            analysis_method="hybrid",
            analyzed_at="2026-10-02T12:00:00Z"
        ),
        analysis_metadata=ThreatAnalysisMetadata()
    )
    assert analysis.content_id == "c-test-01"
    assert analysis.threat_families == ["INVESTMENT_PROMOTION_SCAM"]
    assert analysis.confidence == 0.85

"""Unit tests for High Impact Actions and Evidence Weaknesses in Engine 6."""

import pytest
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction, ActionTarget, ActionText
from nivesh.schemas.evidence import (
    EvidenceAnalysis,
    EvidenceAnalysisMetadata,
    VerificationResult,
    VerificationProvenance,
    RegulatoryFinding,
)
from nivesh.threat.impact_evaluator import ImpactEvaluator


def test_evaluate_high_impact_actions():
    actions = ActionAnalysis(
        content_id="c-hi-1",
        actions=[
            CanonicalAction(
                action_id="ACT-P1",
                source_content_id="c-hi-1",
                text=ActionText(original="Pay ₹5,000", normalized="Pay ₹5,000"),
                action_type="PAYMENT",
                category="FINANCIAL_TRANSACTION",
                target=ActionTarget(type="account", value="Bank")
            ),
            CanonicalAction(
                action_id="ACT-D1",
                source_content_id="c-hi-1",
                text=ActionText(original="Download app", normalized="Download app"),
                action_type="DOWNLOAD",
                category="SOFTWARE_INSTALLATION",
                target=ActionTarget(type="application", value="app.apk")
            ),
            CanonicalAction(
                action_id="ACT-O1",
                source_content_id="c-hi-1",
                text=ActionText(original="Provide OTP", normalized="Provide OTP"),
                action_type="SHARE_OTP",
                category="CREDENTIAL_ACCESS",
                target=ActionTarget(type="account", value="OTP")
            ),
            CanonicalAction(
                action_id="ACT-K1",
                source_content_id="c-hi-1",
                text=ActionText(original="Provide KYC", normalized="Provide KYC"),
                action_type="UPLOAD_IDENTITY",
                category="DATA_DISCLOSURE",
                target=ActionTarget(type="account", value="Aadhaar Card")
            )
        ]
    )

    high_impact = ImpactEvaluator.evaluate_high_impact_actions(actions)
    assert len(high_impact) == 4

    p_act = next(a for a in high_impact if a.action_id == "ACT-P1")
    assert p_act.impact_category == "FINANCIAL"
    assert p_act.reversibility == "IRREVERSIBLE"

    d_act = next(a for a in high_impact if a.action_id == "ACT-D1")
    assert d_act.impact_category == "DEVICE"
    assert d_act.reversibility == "DIFFICULT_TO_REVERSE"

    o_act = next(a for a in high_impact if a.action_id == "ACT-O1")
    assert o_act.impact_category == "CREDENTIAL"
    assert o_act.reversibility == "IRREVERSIBLE"

    k_act = next(a for a in high_impact if a.action_id == "ACT-K1")
    assert k_act.impact_category == "IDENTITY"
    assert k_act.reversibility == "IRREVERSIBLE"


def test_evaluate_evidence_weaknesses():
    evidence = EvidenceAnalysis(
        content_id="c-ew-1",
        verifications=[
            VerificationResult(
                claim_id="C-1",
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.95,
                evidence_strength="HIGH",
                supporting_evidence=[],
                contradicting_evidence=[],
                reasoning_trace=["Official registry search for 'Rahul Sharma' returned 0 matches."],
                provenance=VerificationProvenance(engine_version="1.0.0", verification_method="rule", verified_at="2026-10-02T12:00:00Z")
            ),
            VerificationResult(
                claim_id="C-2",
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.95,
                evidence_strength="HIGH",
                supporting_evidence=[],
                contradicting_evidence=[],
                regulatory_findings=[
                    RegulatoryFinding(
                        type="REGULATORY_CONFLICT",
                        source_document_id="DOC-REG-01",
                        description="Guaranteed returns prohibited by SEBI"
                    )
                ],
                reasoning_trace=["Regulatory prohibition circular consulted"],
                provenance=VerificationProvenance(engine_version="1.0.0", verification_method="rule", verified_at="2026-10-02T12:00:00Z")
            )
        ],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    weaknesses = ImpactEvaluator.evaluate_evidence_weaknesses(evidence)
    w_types = [w.weakness_type for w in weaknesses]

    assert "IDENTITY_NOT_ESTABLISHED" in w_types
    assert "REGULATORY_CONFLICT" in w_types

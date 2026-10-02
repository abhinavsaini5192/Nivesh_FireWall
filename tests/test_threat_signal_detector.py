"""Unit tests for Threat Signal Detector in Engine 6."""

import pytest
from nivesh.engine import ContentIntelligenceEngine
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim, ClaimText
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction, ActionTarget, ActionText
from nivesh.schemas.sources import SourceAnalysis, SourceAnalysisMetadata
from nivesh.schemas.evidence import (
    EvidenceAnalysis,
    EvidenceAnalysisMetadata,
    VerificationResult,
    VerificationProvenance,
    RegulatoryFinding,
)
from nivesh.threat.signal_detector import ThreatSignalDetector


@pytest.fixture
def content_engine():
    return ContentIntelligenceEngine()


def test_detect_authority_and_identity_not_established_signals(content_engine):
    content = content_engine.process_text("SEBI registered advisor Rahul Sharma.")
    claims = ClaimAnalysis(
        content_id=content.content_id,
        claims=[
            CanonicalClaim(
                claim_id="CLAIM-001",
                source_content_id=content.content_id,
                text=ClaimText(original="Rahul Sharma is registered with SEBI.", normalized="Rahul Sharma is registered with SEBI."),
                claim_type="REGULATORY",
                subject="Rahul Sharma",
                predicate="REGISTERED_WITH",
                object="SEBI"
            )
        ]
    )
    actions = ActionAnalysis(content_id=content.content_id, actions=[])
    sources = SourceAnalysis(content_id=content.content_id, claim_sources=[], analysis_metadata=SourceAnalysisMetadata())
    evidence = EvidenceAnalysis(
        content_id=content.content_id,
        verifications=[
            VerificationResult(
                claim_id="CLAIM-001",
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.95,
                evidence_strength="HIGH",
                supporting_evidence=[],
                contradicting_evidence=[],
                reasoning_trace=["Official registry search for 'Rahul Sharma' returned 0 matches."],
                provenance=VerificationProvenance(engine_version="1.0.0", verification_method="rule", verified_at="2026-10-02T12:00:00Z")
            )
        ],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    signals = ThreatSignalDetector.detect_signals(content, claims, actions, sources, evidence)
    sig_types = [s.type for s in signals]

    assert "AUTHORITY_IMPERSONATION" in sig_types
    assert "IDENTITY_NOT_ESTABLISHED" in sig_types

    id_sig = next(s for s in signals if s.type == "IDENTITY_NOT_ESTABLISHED")
    assert id_sig.source == "evidence_verification"
    assert id_sig.claim_id == "CLAIM-001"


def test_detect_guaranteed_return_and_regulatory_conflict_signals(content_engine):
    content = content_engine.process_text("Guaranteed 40% returns on your investment portfolio.")
    claims = ClaimAnalysis(
        content_id=content.content_id,
        claims=[
            CanonicalClaim(
                claim_id="CLAIM-002",
                source_content_id=content.content_id,
                text=ClaimText(original="Guaranteed 40% returns.", normalized="Guaranteed 40% returns."),
                claim_type="FINANCIAL",
                subject="unspecified_offer",
                predicate="GUARANTEED_RETURN",
                object="40% returns"
            )
        ]
    )
    actions = ActionAnalysis(content_id=content.content_id, actions=[])
    sources = SourceAnalysis(content_id=content.content_id, claim_sources=[], analysis_metadata=SourceAnalysisMetadata())
    evidence = EvidenceAnalysis(
        content_id=content.content_id,
        verifications=[
            VerificationResult(
                claim_id="CLAIM-002",
                status="INSUFFICIENT_EVIDENCE",
                confidence=0.95,
                evidence_strength="HIGH",
                supporting_evidence=[],
                contradicting_evidence=[],
                regulatory_findings=[
                    RegulatoryFinding(
                        type="REGULATORY_CONFLICT",
                        source_document_id="DOC-REG-01",
                        description="SEBI Code of Conduct prohibits guaranteed returns."
                    )
                ],
                reasoning_trace=["Prohibition on Assured Returns circular consulted."],
                provenance=VerificationProvenance(engine_version="1.0.0", verification_method="rule", verified_at="2026-10-02T12:00:00Z")
            )
        ],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    signals = ThreatSignalDetector.detect_signals(content, claims, actions, sources, evidence)
    sig_types = [s.type for s in signals]

    assert "GUARANTEED_RETURN_LANGUAGE" in sig_types
    assert "REGULATORY_CLAIM_CONFLICT" in sig_types


def test_detect_action_signals_channel_app_payment(content_engine):
    content = content_engine.process_text("Join our VIP Telegram group! Download our app and pay registration fee of ₹5,000.")
    claims = ClaimAnalysis(content_id=content.content_id, claims=[])
    actions = ActionAnalysis(
        content_id=content.content_id,
        actions=[
            CanonicalAction(
                action_id="ACT-001",
                source_content_id=content.content_id,
                text=ActionText(original="Join our VIP Telegram group", normalized="Join Telegram VIP Group"),
                action_type="JOIN_CHANNEL",
                category="CHANNEL_MIGRATION",
                target=ActionTarget(type="channel", value="Telegram VIP Group")
            ),
            CanonicalAction(
                action_id="ACT-002",
                source_content_id=content.content_id,
                text=ActionText(original="Download our app", normalized="Download app"),
                action_type="DOWNLOAD",
                category="SOFTWARE_INSTALLATION",
                target=ActionTarget(type="application", value="investment.apk")
            ),
            CanonicalAction(
                action_id="ACT-003",
                source_content_id=content.content_id,
                text=ActionText(original="Pay registration fee of ₹5,000", normalized="Pay fee ₹5,000"),
                action_type="PAYMENT",
                category="FINANCIAL_TRANSACTION",
                target=ActionTarget(type="account", value="Bank/UPI"),
                parameters={"amount": "₹5,000"}
            )
        ]
    )
    sources = SourceAnalysis(content_id=content.content_id, claim_sources=[], analysis_metadata=SourceAnalysisMetadata())
    evidence = EvidenceAnalysis(
        content_id=content.content_id,
        verifications=[],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    signals = ThreatSignalDetector.detect_signals(content, claims, actions, sources, evidence)
    sig_types = [s.type for s in signals]

    assert "PRIVATE_CHANNEL_MIGRATION" in sig_types
    assert "EXTERNAL_APP" in sig_types
    assert "PAYMENT_REQUEST" in sig_types
    assert "UPFRONT_FEE" in sig_types


def test_detect_psychological_urgency_and_fomo(content_engine):
    content = content_engine.process_text("HURRY! Act now, limited seats left for our exclusive VIP insider group. Don't miss this opportunity!")
    claims = ClaimAnalysis(content_id=content.content_id, claims=[])
    actions = ActionAnalysis(content_id=content.content_id, actions=[])
    sources = SourceAnalysis(content_id=content.content_id, claim_sources=[], analysis_metadata=SourceAnalysisMetadata())
    evidence = EvidenceAnalysis(
        content_id=content.content_id,
        verifications=[],
        analysis_metadata=EvidenceAnalysisMetadata()
    )

    signals = ThreatSignalDetector.detect_signals(content, claims, actions, sources, evidence)
    sig_types = [s.type for s in signals]

    assert "URGENCY" in sig_types
    assert "FOMO" in sig_types

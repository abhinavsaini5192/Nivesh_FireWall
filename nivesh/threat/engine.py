"""Threat and Attack-Path Intelligence Engine (Engine 6 of Nivesh Firewall).

Answers:
"How do the claims, requested actions, identity signals, and evidence relationships
combine into a potentially harmful financial interaction?"

Constructs an auditable attack path, identifies high-impact transitions, connects
claims to actions, surfaces evidence weaknesses, and classifies threat families.
Does NOT make investment recommendations, calculate scam probabilities, or make
final blocking decisions.
"""

import time
from datetime import datetime, timezone
from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import (
    ThreatAnalysis,
    ThreatProvenance,
    ThreatAnalysisMetadata,
)
from nivesh.threat.signal_detector import ThreatSignalDetector
from nivesh.threat.claim_action_linker import ClaimActionLinker
from nivesh.threat.attack_path_builder import AttackPathBuilder
from nivesh.threat.impact_evaluator import ImpactEvaluator
from nivesh.threat.combination_engine import CombinationEngine
from nivesh.threat.explainer import ThreatExplainer

ENGINE_VERSION = "1.0.0"


class ThreatIntelligenceEngine:
    """Core service for Engine 6: Threat & Attack-Path Intelligence Engine."""

    def __init__(self):
        self.signal_detector = ThreatSignalDetector()
        self.linker = ClaimActionLinker()
        self.path_builder = AttackPathBuilder()
        self.impact_evaluator = ImpactEvaluator()
        self.combination_engine = CombinationEngine()
        self.explainer = ThreatExplainer()

    def analyze(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
    ) -> ThreatAnalysis:
        """Main service interface for Engine 6.
        
        Consumes:
        - NormalizedContent (Engine 1)
        - ClaimAnalysis (Engine 2)
        - ActionAnalysis (Engine 3)
        - SourceAnalysis (Engine 4)
        - EvidenceAnalysis (Engine 5)
        
        Produces:
        - ThreatAnalysis with structured attack path, transitions, and threat families.
        """
        start_time = time.time()

        # 1. Detect Threat Signals
        signals = self.signal_detector.detect_signals(
            content=content,
            claims=claims,
            actions=actions,
            sources=sources,
            evidence=evidence
        )

        # 2. Build Attack Path & Transitions
        attack_path, transitions = self.path_builder.build_path(
            content=content,
            claims=claims,
            actions=actions,
            evidence=evidence
        )

        # 3. Link Claims to Actions
        claim_action_links = self.linker.link_claims_and_actions(
            content=content,
            claims=claims,
            actions=actions
        )

        # 4. Evaluate High-Impact Actions & Evidence Weaknesses
        high_impact_actions = self.impact_evaluator.evaluate_high_impact_actions(actions)
        evidence_weaknesses = self.impact_evaluator.evaluate_evidence_weaknesses(evidence)

        # 5. Evaluate Multi-Signal Combinations & Threat Families
        active_stages = [n.stage for n in attack_path.nodes if n.stage != "DISCOVERY"]
        combinations, threat_families = self.combination_engine.evaluate(
            signals=signals,
            stages=active_stages,
            high_impact_actions=high_impact_actions
        )

        # 6. Generate Structural Explanation & Fingerprint Data
        explanation = self.explainer.generate_explanation(
            signals=signals,
            attack_path=attack_path,
            combinations=combinations,
            threat_families=threat_families,
            weaknesses=evidence_weaknesses
        )

        fingerprint_prep = self.explainer.prepare_fingerprint_components(
            content=content,
            claims=claims,
            actions=actions,
            threat_families=threat_families,
            attack_path=attack_path,
            transitions=transitions
        )

        uncertainties = self.explainer.collect_uncertainties(
            signals=signals,
            weaknesses=evidence_weaknesses,
            evidence=evidence
        )

        # Calculate overall pattern match confidence
        # Measures confidence in the structured pattern detection (NOT probability of user being a scammer)
        if threat_families:
            confidence = min(0.95, max(0.70, sum(s.confidence for s in signals) / len(signals))) if signals else 0.85
        elif active_stages:
            confidence = 0.60
        else:
            confidence = 0.90  # Confident that no threat pattern is formed

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        upstream_versions = {
            "content_intelligence": getattr(content.provenance, "processing_version", "1.0.0") if hasattr(content, "provenance") and content.provenance else "1.0.0",
            "claim_intelligence": getattr(claims.analysis_metadata, "processing_version", "1.0.0") if hasattr(claims, "analysis_metadata") and claims.analysis_metadata else "1.0.0",
            "action_intelligence": getattr(actions.actions[0].provenance, "processing_version", "1.0.0") if actions.actions and actions.actions[0].provenance else "1.0.0",
            "source_intelligence": "1.0.0",
            "evidence_verification": getattr(evidence.verifications[0].provenance, "engine_version", "1.0.0") if evidence.verifications and evidence.verifications[0].provenance else "1.0.0",
        }

        provenance = ThreatProvenance(
            engine_version=ENGINE_VERSION,
            engine_name="Threat & Attack-Path Intelligence Engine",
            analysis_method="hybrid",
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            upstream_engine_versions=upstream_versions
        )

        metadata = ThreatAnalysisMetadata(
            total_signals=len(signals),
            stages_detected=len(active_stages),
            transitions_detected=len(transitions),
            high_impact_action_count=len(high_impact_actions),
            threat_families_count=len(threat_families),
            processing_time_ms=processing_time_ms
        )

        return ThreatAnalysis(
            content_id=content.content_id,
            threat_signals=signals,
            attack_path=attack_path,
            transitions=transitions,
            claim_action_links=claim_action_links,
            evidence_weaknesses=evidence_weaknesses,
            high_impact_actions=high_impact_actions,
            threat_combinations=combinations,
            threat_families=threat_families,
            fingerprint_prep=fingerprint_prep,
            fingerprint_preparation=fingerprint_prep,
            explanation=explanation,
            uncertainty=uncertainties,
            confidence=round(confidence, 2),
            provenance=provenance,
            analysis_metadata=metadata
        )

"""Policy & Intervention Engine — Engine 8.

Determines the appropriate investor-protection intervention for the user's
current interaction based on structured intelligence from Engines 1–7.
"""

import threading
from datetime import datetime, timezone
from typing import Optional, Any

from nivesh.policy.config import POLICY_VERSION
from nivesh.policy.schemas import (
    PolicyDecision,
    PolicyContext,
    PolicyDecisionType,
)
from nivesh.policy.rules import POLICY_RULES
from nivesh.policy.evaluator import PolicyEvaluator
from nivesh.policy.precedence import PolicyPrecedenceResolver
from nivesh.policy.explain import PolicyExplainer

from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis
from nivesh.identity.schemas import IdentityAnalysis


class PolicyInterventionEngine:
    """Core Policy & Intervention Engine (Engine 8).

    Provides deterministic, explainable, and privacy-preserving intervention decisions
    to protect investors from harmful financial interactions.
    """

    def __init__(self):
        self.evaluator = PolicyEvaluator(rules=POLICY_RULES)
        self.precedence_resolver = PolicyPrecedenceResolver()
        self.explainer = PolicyExplainer()
        self._counter: int = 1
        self._lock = threading.Lock()
        self._decisions: dict[str, PolicyDecision] = {}

    def decide(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
        threat: ThreatAnalysis,
        fingerprint: FingerprintAnalysis,
        identity: Optional[IdentityAnalysis] = None,
        behaviour: Optional[Any] = None,
        context: Optional[PolicyContext] = None,
    ) -> PolicyDecision:
        """Determines the safety intervention for the current interaction.

        Consumes the structured outputs from Engines 1–7, Engine 9, and Engine 10 without re-computing them.
        """
        # Defensive handling if context was passed positionally
        if isinstance(identity, PolicyContext) and context is None:
            context = identity
            identity = None
        elif isinstance(behaviour, PolicyContext) and context is None:
            context = behaviour
            behaviour = None

        with self._lock:
            decision_id = f"DEC-{self._counter:03d}"
            self._counter += 1

        # 1. Evaluate all registered policy rules
        triggered_rules = self.evaluator.evaluate_all(
            content=content,
            claims=claims,
            actions=actions,
            sources=sources,
            evidence=evidence,
            threat=threat,
            fingerprint=fingerprint,
            identity=identity,
            behaviour=behaviour,
            context=context,
        )

        # 2. Resolve precedence and aggregate metadata
        resolved = self.precedence_resolver.resolve(triggered_rules, context=context)

        # 3. Generate non-accusatory user and technical explanations
        user_message = self.explainer.generate_user_message(resolved)
        technical_message = self.explainer.generate_technical_message(resolved)

        # 4. Extract upstream entity references
        relevant_claim_ids = [c.claim_id for c in claims.claims]
        relevant_action_ids = [a.action_id for a in actions.actions]
        
        relevant_source_ids = []
        if sources and hasattr(sources, "claim_sources"):
            for cs in sources.claim_sources:
                for doc in getattr(cs, "documents", []):
                    relevant_source_ids.append(doc.document_id)
        elif sources and hasattr(sources, "documents"):
            relevant_source_ids = [d.document_id for d in sources.documents]

        verif_items = getattr(evidence, "verifications", getattr(evidence, "results", []))
        relevant_evidence_ids = [
            getattr(v, "result_id", getattr(v, "claim_id", f"EV-{i+1}"))
            for i, v in enumerate(verif_items)
        ]

        relevant_fp_id = None
        if fingerprint.primary_match:
            relevant_fp_id = fingerprint.primary_match.fingerprint_id
        elif fingerprint.fingerprint:
            relevant_fp_id = fingerprint.fingerprint.fingerprint_id

        relevant_identity_id = None
        if identity is not None and hasattr(identity, "analysis_id"):
            relevant_identity_id = identity.analysis_id

        relevant_behaviour_id = None
        if behaviour is not None and hasattr(behaviour, "analysis_id"):
            relevant_behaviour_id = behaviour.analysis_id

        # 5. Build privacy-safe audit record (zero PII, credentials, or raw content)
        threat_stages = []
        if threat and hasattr(threat, "attack_path") and hasattr(threat.attack_path, "nodes"):
            threat_stages = [n.stage.value if hasattr(n.stage, "value") else str(n.stage) for n in threat.attack_path.nodes]
        elif threat and hasattr(threat, "attack_stages"):
            threat_stages = list(threat.attack_stages)

        audit_metadata: dict[str, Any] = {
            "decision_id": decision_id,
            "policy_version": POLICY_VERSION,
            "primary_rule_id": resolved.rule_id,
            "decision": resolved.decision.value,
            "severity": resolved.severity.value,
            "scope": resolved.scope.value,
            "reason_codes": resolved.reason_codes,
            "rules_triggered_count": len(triggered_rules),
            "user_override_applied": bool(context and context.user_override),
            "threat_stages": threat_stages,
            "threat_families": threat.threat_families,
            "fingerprint_match_type": str(fingerprint.match_type),
        }
        if identity is not None:
            audit_metadata["identity_status"] = (
                identity.identity_status.value
                if hasattr(identity.identity_status, "value")
                else str(identity.identity_status)
            )
            audit_metadata["identity_analysis_id"] = identity.analysis_id
            audit_metadata["identity_entity_count"] = len(getattr(identity, "entities", []))

        if behaviour is not None:
            audit_metadata["behaviour_analysis_id"] = behaviour.analysis_id
            audit_metadata["behaviour_signal_count"] = len(getattr(behaviour, "signals", []))
            audit_metadata["behaviour_signals"] = [
                s.signal_type.value if hasattr(s.signal_type, "value") else str(s.signal_type)
                for s in getattr(behaviour, "signals", [])
            ]

        # 6. Instantiate canonical PolicyDecision
        decision = PolicyDecision(
            decision_id=decision_id,
            decision=resolved.decision,
            severity=resolved.severity.value,
            reason_codes=resolved.reason_codes,
            primary_reason=resolved.primary_reason,
            supporting_reasons=resolved.supporting_reasons,
            triggered_signals=resolved.triggered_signals,
            relevant_claim_ids=relevant_claim_ids,
            relevant_action_ids=relevant_action_ids,
            relevant_source_ids=relevant_source_ids,
            relevant_evidence_ids=relevant_evidence_ids,
            relevant_fingerprint_id=relevant_fp_id,
            relevant_identity_id=relevant_identity_id,
            relevant_behaviour_id=relevant_behaviour_id,
            intervention_scope=resolved.scope,
            required_user_confirmation=resolved.required_user_confirmation,
            cooldown_seconds=resolved.cooldown_seconds,
            user_message=user_message,
            technical_message=technical_message,
            policy_version=POLICY_VERSION,
            created_at=datetime.now(timezone.utc).isoformat(),
            audit_metadata=audit_metadata,
        )

        with self._lock:
            self._decisions[decision_id] = decision

        return decision

    def get_decision(self, decision_id: str) -> Optional[PolicyDecision]:
        """Retrieves a previously stored policy decision by ID."""
        with self._lock:
            return self._decisions.get(decision_id)

    def list_rules(self) -> list[dict[str, Any]]:
        """Returns metadata for all registered policy rules."""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "decision": r.decision.value,
                "severity": r.severity.value,
                "scope": r.scope.value,
                "description": r.description,
            }
            for r in self.evaluator.rules
        ]

    def reset(self) -> None:
        """Resets in-memory storage and counter (useful for unit testing)."""
        with self._lock:
            self._counter = 1
            self._decisions.clear()

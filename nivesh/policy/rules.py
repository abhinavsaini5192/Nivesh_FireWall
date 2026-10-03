"""Explicit, deterministic policy rules for Engine 8.

Rules are evaluated against the structured outputs of Engines 1–7.
Each rule defines explicit logical conditions, returning a PolicyRuleResult
with machine-readable reason codes when conditions are satisfied.
"""

from typing import Optional, Callable, Any
from nivesh.policy.schemas import (
    PolicyDecisionType,
    PolicySeverity,
    InterventionScope,
    PolicyRuleResult,
    PolicyContext,
)
from nivesh.policy.reason_codes import ReasonCode
from nivesh.policy.config import (
    DEFAULT_COOLDOWN_PAUSE_SECONDS,
    DEFAULT_COOLDOWN_BLOCK_SECONDS,
    HIGH_IMPACT_ACTION_TYPES,
    IRREVERSIBLE_ACTION_TYPES,
)
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.schemas.fingerprint import FingerprintAnalysis


class PolicyRule:
    """Encapsulates a single deterministic safety policy rule."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        decision: PolicyDecisionType,
        severity: PolicySeverity,
        scope: InterventionScope,
        condition_fn: Callable[..., Optional[PolicyRuleResult]],
        description: str = "",
    ):
        self.rule_id = rule_id
        self.name = name
        self.decision = decision
        self.severity = severity
        self.scope = scope
        self.condition_fn = condition_fn
        self.description = description

    def evaluate(
        self,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
        threat: ThreatAnalysis,
        fingerprint: FingerprintAnalysis,
        identity: Optional[Any] = None,
        behaviour: Optional[Any] = None,
        context: Optional[PolicyContext] = None,
    ) -> Optional[PolicyRuleResult]:
        return self.condition_fn(
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


# ==============================================================================
# Helper Predicates
# ==============================================================================

def _get_action_types(actions: ActionAnalysis) -> set[str]:
    return {a.action_type for a in actions.actions}


def _get_threat_signal_types(threat: ThreatAnalysis) -> set[str]:
    return {s.type for s in threat.threat_signals}


def _has_payment_action(actions: ActionAnalysis, threat: ThreatAnalysis) -> bool:
    act_types = {a.action_type for a in actions.actions}
    act_cats = {getattr(a, "category", "") for a in actions.actions}
    sig_types = {s.type for s in threat.threat_signals}
    payment_terms = {
        "PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY", "BUY",
        "FINANCIAL_TRANSACTION", "PAYMENT_REQUEST", "FINANCIAL_TRANSFER"
    }
    return bool(
        act_types.intersection(payment_terms)
        or act_cats.intersection(payment_terms)
        or sig_types.intersection({"PAYMENT_REQUEST", "FINANCIAL_TRANSFER"})
    )


def _has_software_action(actions: ActionAnalysis, threat: ThreatAnalysis) -> bool:
    act_types = {a.action_type for a in actions.actions}
    act_cats = {getattr(a, "category", "") for a in actions.actions}
    sig_types = {s.type for s in threat.threat_signals}
    soft_terms = {"DOWNLOAD", "INSTALL", "SOFTWARE_INSTALLATION", "EXTERNAL_APP"}
    return bool(
        act_types.intersection(soft_terms)
        or act_cats.intersection(soft_terms)
        or sig_types.intersection({"EXTERNAL_APP", "SOFTWARE_INSTALLATION"})
    )


def _has_channel_migration_action(actions: ActionAnalysis, threat: ThreatAnalysis) -> bool:
    act_types = {a.action_type for a in actions.actions}
    act_cats = {getattr(a, "category", "") for a in actions.actions}
    sig_types = {s.type for s in threat.threat_signals}
    channel_terms = {"JOIN_CHANNEL", "JOIN_GROUP", "CHANNEL_MIGRATION", "PRIVATE_CHANNEL_MIGRATION"}
    return bool(
        act_types.intersection(channel_terms)
        or act_cats.intersection(channel_terms)
        or sig_types.intersection({"CHANNEL_MIGRATION", "PRIVATE_CHANNEL_MIGRATION"})
    )


def _has_credential_action(actions: ActionAnalysis, threat: ThreatAnalysis) -> bool:
    act_types = {a.action_type for a in actions.actions}
    act_cats = {getattr(a, "category", "") for a in actions.actions}
    sig_types = {s.type for s in threat.threat_signals}
    cred_terms = {
        "ENTER_CREDENTIALS", "SHARE_OTP", "CONNECT_ACCOUNT", "CONNECT_BANK",
        "AUTHORIZE_ACCESS", "UPLOAD_IDENTITY", "UPLOAD_DOCUMENT",
        "CREDENTIAL_ACCESS", "ACCOUNT_AUTHORIZATION", "DATA_DISCLOSURE", "DATA_COLLECTION"
    }
    return bool(
        act_types.intersection(cred_terms)
        or act_cats.intersection(cred_terms)
        or sig_types.intersection({"CREDENTIAL_ACCESS", "CREDENTIAL_HARVESTING"})
    )


def _get_evidence_verdicts(evidence: EvidenceAnalysis) -> set[str]:
    verdicts: set[str] = set()
    verif_list = getattr(evidence, "verifications", getattr(evidence, "results", []))
    for v in verif_list:
        status_val = v.status.value if hasattr(v.status, "value") else str(v.status)
        verdicts.add(status_val)
        for rf in getattr(v, "regulatory_findings", []):
            rf_val = rf.finding_type if hasattr(rf, "finding_type") else str(rf)
            verdicts.add(rf_val)
    return verdicts


def _has_unverified_authority(
    threat: ThreatAnalysis,
    evidence: EvidenceAnalysis,
    identity: Optional[Any] = None,
) -> bool:
    sig_types = _get_threat_signal_types(threat)
    verdicts = _get_evidence_verdicts(evidence)
    verif_list = getattr(evidence, "verifications", getattr(evidence, "results", []))
    has_missing = any(
        any("not_found" in str(m).lower() or "missing" in str(m).lower() for m in getattr(v, "missing_elements", []))
        for v in verif_list
    )
    has_identity_unverified = False
    if identity is not None and hasattr(identity, "identity_status"):
        status_val = (
            identity.identity_status.value
            if hasattr(identity.identity_status, "value")
            else str(identity.identity_status)
        )
        if status_val in ("NOT_ESTABLISHED", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE", "SOURCE_UNAVAILABLE"):
            has_identity_unverified = True

    return bool(
        "IDENTITY_NOT_ESTABLISHED" in sig_types
        or "INSUFFICIENT_EVIDENCE" in verdicts
        or "NO_USABLE_EVIDENCE" in verdicts
        or "NOT_VERIFIABLE" in verdicts
        or has_missing
        or has_identity_unverified
    )


def _has_regulatory_conflict(
    threat: ThreatAnalysis,
    evidence: EvidenceAnalysis,
    identity: Optional[Any] = None,
) -> bool:
    sig_types = _get_threat_signal_types(threat)
    verdicts = _get_evidence_verdicts(evidence)
    has_id_conflict = False
    if identity is not None and hasattr(identity, "authority_alignments"):
        for a in identity.authority_alignments:
            status = getattr(a, "alignment_status", "")
            if status in ("MISMATCH", "CONFLICT"):
                has_id_conflict = True
    return "REGULATORY_CLAIM_CONFLICT" in sig_types or "REGULATORY_CONFLICT" in verdicts or has_id_conflict


def _has_factual_contradiction(
    evidence: EvidenceAnalysis,
    identity: Optional[Any] = None,
) -> bool:
    has_evidence_contradiction = "CONTRADICTED" in _get_evidence_verdicts(evidence)
    has_identity_contradiction = False
    if identity is not None and hasattr(identity, "identity_status"):
        status_val = (
            identity.identity_status.value
            if hasattr(identity.identity_status, "value")
            else str(identity.identity_status)
        )
        if status_val == "IDENTITY_MISMATCH":
            has_identity_contradiction = True
    return has_evidence_contradiction or has_identity_contradiction


def _has_confirmed_threat_match(fingerprint: FingerprintAnalysis) -> bool:
    return bool(
        fingerprint.match_type in ("EXACT_MATCH", "STRUCTURAL_MATCH", "SEMANTIC_VARIANT")
        and (fingerprint.structural_equivalence or fingerprint.match_type == "EXACT_MATCH")
    )



# ==============================================================================
# BLOCK Rules
# ==============================================================================

def _rule_block_credential_harvesting(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)
    
    # Must involve credential capture or unauthorized account access
    if not _has_credential_action(actions, threat):
        return None

    # Must have active impersonation or direct factual contradiction or credential harvest combination
    has_impersonation = "AUTHORITY_IMPERSONATION" in sig_types
    if identity is not None and hasattr(identity, "identity_status"):
        status_val = (
            identity.identity_status.value
            if hasattr(identity.identity_status, "value")
            else str(identity.identity_status)
        )
        if status_val == "IDENTITY_MISMATCH":
            has_impersonation = True
    has_contradiction = _has_factual_contradiction(evidence, identity=identity)
    has_cred_combo = any(c.combination_type == "CREDENTIAL_HARVESTING" for c in threat.threat_combinations)

    if (has_impersonation or has_contradiction or has_cred_combo) and _has_confirmed_threat_match(fingerprint):
        return PolicyRuleResult(
            rule_id="RULE-BLOCK-01",
            rule_name="Critical Credential Access Request with Confirmed Threat Match",
            decision=PolicyDecisionType.BLOCK,
            severity=PolicySeverity.CRITICAL,
            scope=InterventionScope.CURRENT_FLOW,
            reason_codes=[
                ReasonCode.CREDENTIAL_ACCESS_REQUEST,
                ReasonCode.AUTHORITY_IMPERSONATION_DETECTED if has_impersonation else ReasonCode.IDENTITY_NOT_ESTABLISHED,
                ReasonCode.FACTUAL_CONTRADICTION if has_contradiction else ReasonCode.REGULATORY_CONFLICT,
                ReasonCode.KNOWN_THREAT_STRUCTURAL_MATCH,
                ReasonCode.IRREVERSIBLE_ACTION_DETECTED,
            ],
            primary_reason="Critical safety violation: Credential capture requested under contradicted or impersonated authority with matching threat pattern.",
            supporting_reasons=[
                "Content requests entry of sensitive financial or account credentials.",
                "Authoritative evidence directly contradicts the claimed authority or detects impersonation.",
                "Interaction structure matches a known collective credential harvesting threat pattern.",
            ],
            triggered_signals=list(sig_types.intersection({"AUTHORITY_IMPERSONATION", "CREDENTIAL_ACCESS", "IDENTITY_MISMATCH"})),
            required_user_confirmation=False,
            cooldown_seconds=DEFAULT_COOLDOWN_BLOCK_SECONDS,
        )
    return None


def _rule_block_contradicted_payment(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)

    # Must involve direct payment or financial transfer
    if not _has_payment_action(actions, threat):
        return None

    # Must have direct factual contradiction AND authority impersonation / active known threat match
    has_contradiction = _has_factual_contradiction(evidence, identity=identity)
    has_impersonation = "AUTHORITY_IMPERSONATION" in sig_types
    if identity is not None and hasattr(identity, "identity_status"):
        status_val = (
            identity.identity_status.value
            if hasattr(identity.identity_status, "value")
            else str(identity.identity_status)
        )
        if status_val == "IDENTITY_MISMATCH":
            has_impersonation = True
    is_confirmed_threat = _has_confirmed_threat_match(fingerprint)

    if (has_contradiction or has_impersonation) and is_confirmed_threat:
        return PolicyRuleResult(
            rule_id="RULE-BLOCK-02",
            rule_name="High-Impact Payment with Factual Contradiction and Confirmed Threat Structure",
            decision=PolicyDecisionType.BLOCK,
            severity=PolicySeverity.CRITICAL,
            scope=InterventionScope.CURRENT_ACTION,
            reason_codes=[
                ReasonCode.PAYMENT_REQUEST,
                ReasonCode.FACTUAL_CONTRADICTION if has_contradiction else ReasonCode.AUTHORITY_IMPERSONATION_DETECTED,
                ReasonCode.KNOWN_THREAT_STRUCTURAL_MATCH,
                ReasonCode.IRREVERSIBLE_ACTION_DETECTED,
                ReasonCode.HIGH_IMPACT_ACTION,
            ],
            primary_reason="High-impact payment blocked: Evidence directly contradicts central claims and matches a confirmed threat pattern.",
            supporting_reasons=[
                "A direct financial payment is requested.",
                "Retrieved authoritative evidence directly contradicts the central authority or registration claim.",
                "Underlying attack mechanics match an active structural threat fingerprint in collective memory.",
            ],
            triggered_signals=list(sig_types.intersection({"AUTHORITY_IMPERSONATION", "PAYMENT_REQUEST", "REGULATORY_CLAIM_CONFLICT"})),
            required_user_confirmation=False,
            cooldown_seconds=DEFAULT_COOLDOWN_BLOCK_SECONDS,
        )
    return None


# ==============================================================================
# PAUSE Rules
# ==============================================================================

def _rule_pause_high_impact_payment_threat_pattern(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)

    # Payment requested
    if not _has_payment_action(actions, threat):
        return None

    has_unverified_auth = _has_unverified_authority(threat, evidence, identity=identity)
    has_reg_conflict = _has_regulatory_conflict(threat, evidence, identity=identity)
    has_guaranteed_ret = "GUARANTEED_RETURN_LANGUAGE" in sig_types or any(c.claim_type == "FINANCIAL_RETURN" for c in claims.claims)
    has_channel_or_app = _has_channel_migration_action(actions, threat) or _has_software_action(actions, threat)
    has_fp_match = fingerprint.match_type in ("EXACT_MATCH", "STRUCTURAL_MATCH", "SEMANTIC_VARIANT")

    has_rapid_escalation = False
    has_persistent_payment = False
    behaviour_triggered_signals: list[str] = []
    if kwargs.get("behaviour") is not None:
        beh = kwargs["behaviour"]
        hints = getattr(beh, "policy_hints", None)
        if hints:
            if hints.rapid_escalation_present or hints.high_impact_action_progression:
                has_rapid_escalation = True
            if hints.persistent_payment_present or hints.repeated_request_present:
                has_persistent_payment = True
        for sig in getattr(beh, "signals", []):
            stype = getattr(sig, "signal_type", None)
            stype_val = stype.value if hasattr(stype, "value") else str(stype)
            if stype_val in ("RAPID_ACTION_ESCALATION", "PERSISTENT_PAYMENT_REQUEST", "LOW_TO_HIGH_IMPACT_TRANSITION", "INFORMATION_TO_TRANSACTION_SHIFT", "RETRY_AFTER_DECLINE"):
                behaviour_triggered_signals.append(stype_val)

    # Condition: Payment requested combined with unverified authority / regulatory conflict AND either software/channel or known pattern
    if (has_unverified_auth or has_reg_conflict or has_guaranteed_ret) and (has_channel_or_app or has_fp_match or has_rapid_escalation or has_persistent_payment or "PAYMENT_REQUEST" in sig_types):
        reasons_list = [
            ReasonCode.PAYMENT_REQUEST,
            ReasonCode.HIGH_IMPACT_ACTION,
            ReasonCode.IRREVERSIBLE_ACTION_DETECTED,
            ReasonCode.USER_CONFIRMATION_REQUIRED,
        ]
        if has_unverified_auth:
            reasons_list.append(ReasonCode.IDENTITY_NOT_ESTABLISHED)
        if has_reg_conflict:
            reasons_list.append(ReasonCode.REGULATORY_CONFLICT)
        if has_guaranteed_ret:
            reasons_list.append(ReasonCode.GUARANTEED_RETURN_LANGUAGE)
        if _has_channel_migration_action(actions, threat):
            reasons_list.append(ReasonCode.PRIVATE_CHANNEL_MIGRATION)
        if _has_software_action(actions, threat):
            reasons_list.append(ReasonCode.EXTERNAL_APP_INSTALLATION)
        if has_rapid_escalation:
            reasons_list.append(ReasonCode.RAPID_ACTION_ESCALATION)
        if has_persistent_payment:
            reasons_list.append(ReasonCode.PERSISTENT_PAYMENT_REQUEST)
        if has_fp_match:
            reasons_list.append(
                ReasonCode.KNOWN_THREAT_STRUCTURAL_MATCH if fingerprint.match_type in ("EXACT_MATCH", "STRUCTURAL_MATCH")
                else ReasonCode.KNOWN_THREAT_SEMANTIC_VARIANT
            )

        supporting = [
            "Content instructs the user to make an irreversible financial payment.",
            "Claimed regulatory registration could not be established from authoritative sources.",
            "Content promises guaranteed or assured financial returns conflicting with regulatory guidelines.",
            "Action sequence involves channel migration, external software, or matches a previously observed threat variant.",
        ]
        if has_rapid_escalation or has_persistent_payment:
            supporting.append("Interaction sequence displays rapid action escalation or persistent payment requests.")

        triggered_sigs = list(sig_types.intersection({
            "REGULATORY_AUTHORITY_CLAIM", "IDENTITY_NOT_ESTABLISHED", "GUARANTEED_RETURN_LANGUAGE",
            "REGULATORY_CLAIM_CONFLICT", "CHANNEL_MIGRATION", "PRIVATE_CHANNEL_MIGRATION", "EXTERNAL_APP", "PAYMENT_REQUEST"
        }))
        for bsig in behaviour_triggered_signals:
            if bsig not in triggered_sigs:
                triggered_sigs.append(bsig)

        return PolicyRuleResult(
            rule_id="RULE-PAUSE-01",
            rule_name="Payment Request with Multi-Signal Threat Pattern",
            decision=PolicyDecisionType.PAUSE,
            severity=PolicySeverity.HIGH,
            scope=InterventionScope.CURRENT_ACTION,
            reason_codes=reasons_list,
            primary_reason="Pause before proceeding: This payment request is linked to an unverified identity claim, guaranteed return promise, or matching threat structure.",
            supporting_reasons=supporting,
            triggered_signals=triggered_sigs,
            required_user_confirmation=True,
            cooldown_seconds=DEFAULT_COOLDOWN_PAUSE_SECONDS,
        )
    return None


def _rule_pause_software_installation_unverified(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)

    # Software installation requested
    if not _has_software_action(actions, threat):
        return None

    has_unverified_auth = _has_unverified_authority(threat, evidence, identity=identity)
    has_reg_conflict = _has_regulatory_conflict(threat, evidence, identity=identity)
    has_guaranteed_ret = "GUARANTEED_RETURN_LANGUAGE" in sig_types
    has_fp_match = fingerprint.match_type in ("EXACT_MATCH", "STRUCTURAL_MATCH", "SEMANTIC_VARIANT")

    if has_unverified_auth or has_reg_conflict or has_guaranteed_ret or has_fp_match or "EXTERNAL_APP" in sig_types:
        reasons_list = [
            ReasonCode.EXTERNAL_APP_INSTALLATION,
            ReasonCode.HIGH_IMPACT_ACTION,
            ReasonCode.USER_CONFIRMATION_REQUIRED,
        ]
        if has_unverified_auth:
            reasons_list.append(ReasonCode.IDENTITY_NOT_ESTABLISHED)
        if has_reg_conflict:
            reasons_list.append(ReasonCode.REGULATORY_CONFLICT)
        if has_guaranteed_ret:
            reasons_list.append(ReasonCode.GUARANTEED_RETURN_LANGUAGE)
        if has_fp_match:
            reasons_list.append(ReasonCode.KNOWN_THREAT_SEMANTIC_VARIANT)

        return PolicyRuleResult(
            rule_id="RULE-PAUSE-02",
            rule_name="External Software Installation with Unverified Financial Context",
            decision=PolicyDecisionType.PAUSE,
            severity=PolicySeverity.HIGH,
            scope=InterventionScope.CURRENT_ACTION,
            reason_codes=reasons_list,
            primary_reason="Pause before downloading software: Application installation requested in conjunction with unverified financial claims.",
            supporting_reasons=[
                "User is instructed to download or install third-party mobile or desktop software.",
                "Financial authority or registration claim could not be established from authoritative records.",
                "Third-party software execution introduces heightened device security considerations.",
            ],
            triggered_signals=list(sig_types.intersection({
                "EXTERNAL_APP", "REGULATORY_AUTHORITY_CLAIM", "IDENTITY_NOT_ESTABLISHED", "GUARANTEED_RETURN_LANGUAGE"
            })),
            required_user_confirmation=True,
            cooldown_seconds=20,
        )
    return None


def _rule_pause_credential_disclosure(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)

    if not _has_credential_action(actions, threat):
        return None

    has_unverified = _has_unverified_authority(threat, evidence, identity=identity)
    if has_unverified or "IDENTITY_NOT_ESTABLISHED" in sig_types or "CREDENTIAL_HARVESTING" in sig_types:
        return PolicyRuleResult(
            rule_id="RULE-PAUSE-03",
            rule_name="Sensitive Data or Credential Request by Unverified Entity",
            decision=PolicyDecisionType.PAUSE,
            severity=PolicySeverity.HIGH,
            scope=InterventionScope.CURRENT_FLOW,
            reason_codes=[
                ReasonCode.CREDENTIAL_ACCESS_REQUEST,
                ReasonCode.IDENTITY_NOT_ESTABLISHED,
                ReasonCode.HIGH_IMPACT_ACTION,
                ReasonCode.USER_CONFIRMATION_REQUIRED,
            ],
            primary_reason="Pause: Sensitive credentials or personal identification requested by an unverified intermediary.",
            supporting_reasons=[
                "Interaction requests authentication credentials, OTPs, or personal identification.",
                "Entity claiming financial regulatory authority is unverified in official registries.",
            ],
            triggered_signals=list(sig_types.intersection({"CREDENTIAL_ACCESS", "IDENTITY_NOT_ESTABLISHED"})),
            required_user_confirmation=True,
            cooldown_seconds=30,
        )
    return None


# ==============================================================================
# WARN Rules
# ==============================================================================

def _rule_warn_channel_migration_unverified(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)

    # Private channel migration (e.g. Telegram, WhatsApp)
    if not _has_channel_migration_action(actions, threat):
        return None

    # No immediate payment or software install (which would be handled by PAUSE)
    if _has_payment_action(actions, threat) or _has_software_action(actions, threat):
        return None

    has_unverified = _has_unverified_authority(threat, evidence, identity=identity)
    has_guaranteed_ret = "GUARANTEED_RETURN_LANGUAGE" in sig_types
    has_reg_conflict = _has_regulatory_conflict(threat, evidence, identity=identity)
    has_auth_claim = "REGULATORY_AUTHORITY_CLAIM" in sig_types or any(c.claim_type == "REGULATORY_STATUS" for c in claims.claims)

    if has_unverified or has_guaranteed_ret or has_reg_conflict or has_auth_claim:
        reasons_list = [
            ReasonCode.PRIVATE_CHANNEL_MIGRATION,
        ]
        if has_unverified:
            reasons_list.append(ReasonCode.IDENTITY_NOT_ESTABLISHED)
        if has_reg_conflict:
            reasons_list.append(ReasonCode.REGULATORY_CONFLICT)
        if has_guaranteed_ret:
            reasons_list.append(ReasonCode.GUARANTEED_RETURN_LANGUAGE)

        return PolicyRuleResult(
            rule_id="RULE-WARN-01",
            rule_name="Private Channel Migration with Unverified Authority",
            decision=PolicyDecisionType.WARN,
            severity=PolicySeverity.MEDIUM,
            scope=InterventionScope.CURRENT_ACTION,
            reason_codes=reasons_list,
            primary_reason="Exercise caution: Content encourages migrating to private messaging channels alongside unverified financial assertions.",
            supporting_reasons=[
                "User is invited to join a private communication group (e.g., Telegram or WhatsApp).",
                "Promotional claims include unverified regulatory registration or assured returns.",
                "Private channels reduce regulatory visibility and public dispute resolution options.",
            ],
            triggered_signals=list(sig_types.intersection({
                "CHANNEL_MIGRATION", "PRIVATE_CHANNEL_MIGRATION", "REGULATORY_AUTHORITY_CLAIM", "IDENTITY_NOT_ESTABLISHED", "GUARANTEED_RETURN_LANGUAGE"
            })),
            required_user_confirmation=False,
        )
    return None


def _rule_warn_guaranteed_return_language(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)
    act_types = _get_action_types(actions)

    # Guaranteed return claim present without high impact action
    if "GUARANTEED_RETURN_LANGUAGE" not in sig_types:
        return None
    if act_types.intersection(HIGH_IMPACT_ACTION_TYPES):
        return None

    return PolicyRuleResult(
        rule_id="RULE-WARN-02",
        rule_name="Guaranteed Return Language in Financial Promotion",
        decision=PolicyDecisionType.WARN,
        severity=PolicySeverity.MEDIUM,
        scope=InterventionScope.INFORMATION_ONLY,
        reason_codes=[
            ReasonCode.GUARANTEED_RETURN_LANGUAGE,
            ReasonCode.REGULATORY_CONFLICT,
        ],
        primary_reason="Regulatory awareness notice: Guaranteed or assured return promises conflict with statutory financial advisory regulations.",
        supporting_reasons=[
            "Claims promise guaranteed or assured percentage returns on capital investments.",
            "Securities regulations prohibit covered market intermediaries from assuring specific returns.",
        ],
        triggered_signals=list(sig_types.intersection({"GUARANTEED_RETURN_LANGUAGE", "REGULATORY_CLAIM_CONFLICT"})),
        required_user_confirmation=False,
    )


def _rule_warn_unverified_regulatory_claim(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    sig_types = _get_threat_signal_types(threat)
    act_types = _get_action_types(actions)

    has_auth_claim = (
        "REGULATORY_AUTHORITY_CLAIM" in sig_types
        or any(c.claim_type == "REGULATORY_STATUS" for c in claims.claims)
        or bool(identity and getattr(identity, "authority_alignments", None))
    )
    if not has_auth_claim:
        return None
    if not _has_unverified_authority(threat, evidence, identity=identity):
        return None
    if act_types.intersection(HIGH_IMPACT_ACTION_TYPES):
        return None

    return PolicyRuleResult(
        rule_id="RULE-WARN-03",
        rule_name="Unverified Regulatory Status Claim",
        decision=PolicyDecisionType.WARN,
        severity=PolicySeverity.MEDIUM,
        scope=InterventionScope.INFORMATION_ONLY,
        reason_codes=[
            ReasonCode.UNVERIFIED_REGULATORY_CLAIM,
            ReasonCode.IDENTITY_NOT_ESTABLISHED,
        ],
        primary_reason="Unverified claim: Claimed financial regulatory registration could not be established from authoritative registry checks.",
        supporting_reasons=[
            "Content asserts official regulatory registration (e.g. SEBI registered).",
            "Authoritative public registry queries returned no matching registration for the specified details.",
        ],
        triggered_signals=list(sig_types.intersection({"REGULATORY_AUTHORITY_CLAIM", "IDENTITY_NOT_ESTABLISHED"})),
        required_user_confirmation=False,
    )


def _rule_warn_threat_pattern_resemblance(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    act_types = _get_action_types(actions)

    # Matches a pattern but without high-impact actions
    if fingerprint.match_type in ("SEMANTIC_VARIANT", "STRUCTURAL_MATCH", "RELATED_PATTERN"):
        # Ensure observable threat indicators or active attack stages exist beyond informational discovery
        non_weakness_signals = [s for s in threat.threat_signals if getattr(s, "type", "") not in ("UNSUPPORTED_CLAIM", "EVIDENCE_GAP", "MISSING_EVIDENCE")]
        active_nodes = [n for n in getattr(threat.attack_path, "nodes", []) if (getattr(n.stage, "value", str(n.stage)) if hasattr(n, "stage") else "") not in ("DISCOVERY", "INFORMATIONAL", "")]
        has_threat_context = bool(non_weakness_signals or active_nodes or threat.threat_families)
        if not has_threat_context:
            return None

        if not act_types.intersection(HIGH_IMPACT_ACTION_TYPES):
            rc = (
                ReasonCode.KNOWN_THREAT_STRUCTURAL_MATCH if fingerprint.match_type == "STRUCTURAL_MATCH"
                else ReasonCode.KNOWN_THREAT_SEMANTIC_VARIANT if fingerprint.match_type == "SEMANTIC_VARIANT"
                else ReasonCode.KNOWN_THREAT_RELATED_PATTERN
            )
            return PolicyRuleResult(
                rule_id="RULE-WARN-04",
                rule_name="Interaction Resembles Previously Observed Threat Structure",
                decision=PolicyDecisionType.WARN,
                severity=PolicySeverity.MEDIUM,
                scope=InterventionScope.CURRENT_FLOW,
                reason_codes=[rc, ReasonCode.MULTI_SIGNAL_THREAT_PATTERN],
                primary_reason="Pattern notice: The structure of this financial interaction resembles a previously observed collective threat pattern.",
                supporting_reasons=[
                    f"Structural match classified as {fingerprint.match_type} against collective memory ID {fingerprint.primary_match.fingerprint_id if fingerprint.primary_match else 'None'}.",
                    "Observed attack path and action sequence align with past reported promotions.",
                ],
                triggered_signals=[
                    n.stage.value if hasattr(n.stage, "value") else str(n.stage)
                    for n in getattr(threat.attack_path, "nodes", [])
                ],
                required_user_confirmation=False,
            )
    return None


# ==============================================================================
# INFORM Rules
# ==============================================================================

def _rule_inform_market_opinion_prediction(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    act_types = _get_action_types(actions)
    if act_types.intersection(HIGH_IMPACT_ACTION_TYPES):
        return None

    # Check for claims with modality OPINION or PREDICTION
    has_prediction = any(
        (hasattr(c, "modality") and getattr(c.modality, "type", "").upper() in ("OPINION", "PREDICTION"))
        or str(getattr(c, "modality", "")).upper() in ("OPINION", "PREDICTION")
        or str(c.claim_type).upper() in ("OPINION", "PREDICTION", "MARKET_PREDICTION")
        for c in claims.claims
    )
    if has_prediction:
        return PolicyRuleResult(
            rule_id="RULE-INFORM-01",
            rule_name="Market Opinion or Prediction Disclosure",
            decision=PolicyDecisionType.INFORM,
            severity=PolicySeverity.LOW,
            scope=InterventionScope.INFORMATION_ONLY,
            reason_codes=[
                ReasonCode.OPINION_OR_PREDICTION_DISCLOSED,
                ReasonCode.FINANCIAL_CONTENT_DETECTED,
            ],
            primary_reason="Informational note: Content contains forward-looking market projections or subjective investment opinions.",
            supporting_reasons=[
                "Statements reflect forward-looking market sentiment rather than historical or guaranteed facts.",
                "Market projections are subject to unforeseen economic volatility.",
            ],
            triggered_signals=["MARKET_PREDICTION_MODALITY"],
            required_user_confirmation=False,
        )
    return None


def _rule_inform_financial_content_context(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    act_types = _get_action_types(actions)
    if act_types.intersection(HIGH_IMPACT_ACTION_TYPES):
        return None

    # Informational context is for non-critical content where specific financial claims
    # (e.g. corporate debt, financial performance, regulatory disclosures) warrant neutral contextual awareness.
    # Benign educational content or heuristic general text must remain ALLOW.
    if not claims or len(claims.claims) == 0:
        return None

    has_specific_claims = any(
        c.claim_type in ("REGULATORY_STATUS", "CORPORATE_FINANCIAL", "FINANCIAL_RETURN")
        or not c.attributes.get("heuristic", False)
        for c in claims.claims
    )
    if not has_specific_claims:
        return None

    return PolicyRuleResult(
        rule_id="RULE-INFORM-02",
        rule_name="General Financial Content Informational Context",
        decision=PolicyDecisionType.INFORM,
        severity=PolicySeverity.LOW,
        scope=InterventionScope.INFORMATION_ONLY,
        reason_codes=[
            ReasonCode.FINANCIAL_CONTENT_DETECTED,
        ],
        primary_reason="Contextual verification: Financial claims detected with no critical threat indicators.",
        supporting_reasons=[
            "Content references financial assets or makes factual claims.",
            "No high-impact or suspicious action flow detected.",
        ],
        triggered_signals=[],
        required_user_confirmation=False,
    )


# ==============================================================================
# ALLOW Rules (Baseline)
# ==============================================================================

def _rule_allow_benign_educational_or_general(
    content: NormalizedContent,
    claims: ClaimAnalysis,
    actions: ActionAnalysis,
    sources: SourceAnalysis,
    evidence: EvidenceAnalysis,
    threat: ThreatAnalysis,
    fingerprint: FingerprintAnalysis,
    identity: Optional[Any] = None,
    context: Optional[PolicyContext] = None,
    **kwargs: Any,
) -> Optional[PolicyRuleResult]:
    # Default benign rule fires when no high-impact actions and no high severity threat patterns exist
    act_types = _get_action_types(actions)
    if act_types.intersection(HIGH_IMPACT_ACTION_TYPES):
        return None

    return PolicyRuleResult(
        rule_id="RULE-ALLOW-01",
        rule_name="Benign Educational or General Information",
        decision=PolicyDecisionType.ALLOW,
        severity=PolicySeverity.INFORMATIONAL,
        scope=InterventionScope.INFORMATION_ONLY,
        reason_codes=[
            ReasonCode.NO_INTERVENTION_REQUIRED,
        ],
        primary_reason="No policy intervention required: Content is informational or educational without high-impact requested actions.",
        supporting_reasons=[
            "No harmful attack paths or malicious action sequences identified.",
            "No unverified authority claims combined with financial transfer requests.",
            "Interaction is safe to proceed under active policy.",
        ],
        triggered_signals=[],
        required_user_confirmation=False,
    )


# ==============================================================================
# Canonical Ordered Rule Registry
# ==============================================================================

POLICY_RULES: list[PolicyRule] = [
    # 1. BLOCK Rules
    PolicyRule("RULE-BLOCK-01", "Critical Credential Access Request", PolicyDecisionType.BLOCK, PolicySeverity.CRITICAL, InterventionScope.CURRENT_FLOW, _rule_block_credential_harvesting, "Blocks credential theft under impersonated or contradicted authority."),
    PolicyRule("RULE-BLOCK-02", "Contradicted Payment Request with Threat Match", PolicyDecisionType.BLOCK, PolicySeverity.CRITICAL, InterventionScope.CURRENT_ACTION, _rule_block_contradicted_payment, "Blocks payments directly contradicted by evidence and matching a threat fingerprint."),

    # 2. PAUSE Rules
    PolicyRule("RULE-PAUSE-01", "Payment Request with Multi-Signal Threat Pattern", PolicyDecisionType.PAUSE, PolicySeverity.HIGH, InterventionScope.CURRENT_ACTION, _rule_pause_high_impact_payment_threat_pattern, "Pauses payments linked to unverified authority, guaranteed returns, or threat patterns."),
    PolicyRule("RULE-PAUSE-02", "Software Installation with Unverified Authority", PolicyDecisionType.PAUSE, PolicySeverity.HIGH, InterventionScope.CURRENT_ACTION, _rule_pause_software_installation_unverified, "Pauses app downloads requested under unverified financial authority."),
    PolicyRule("RULE-PAUSE-03", "Sensitive Credential Disclosure Request", PolicyDecisionType.PAUSE, PolicySeverity.HIGH, InterventionScope.CURRENT_FLOW, _rule_pause_credential_disclosure, "Pauses requests for credentials or OTPs by unverified entities."),

    # 3. WARN Rules
    PolicyRule("RULE-WARN-01", "Private Channel Migration with Unverified Authority", PolicyDecisionType.WARN, PolicySeverity.MEDIUM, InterventionScope.CURRENT_ACTION, _rule_warn_channel_migration_unverified, "Warns on Telegram/WhatsApp migration with unverified claims."),
    PolicyRule("RULE-WARN-02", "Guaranteed Return Language in Promotion", PolicyDecisionType.WARN, PolicySeverity.MEDIUM, InterventionScope.INFORMATION_ONLY, _rule_warn_guaranteed_return_language, "Warns on prohibited guaranteed return statements."),
    PolicyRule("RULE-WARN-03", "Unverified Regulatory Status Claim", PolicyDecisionType.WARN, PolicySeverity.MEDIUM, InterventionScope.INFORMATION_ONLY, _rule_warn_unverified_regulatory_claim, "Warns when claiming regulatory registration that could not be verified."),
    PolicyRule("RULE-WARN-04", "Interaction Resembles Known Threat Structure", PolicyDecisionType.WARN, PolicySeverity.MEDIUM, InterventionScope.CURRENT_FLOW, _rule_warn_threat_pattern_resemblance, "Warns when an exploratory flow matches a known threat fingerprint."),

    # 4. INFORM Rules
    PolicyRule("RULE-INFORM-01", "Market Opinion or Prediction Disclosure", PolicyDecisionType.INFORM, PolicySeverity.LOW, InterventionScope.INFORMATION_ONLY, _rule_inform_market_opinion_prediction, "Informs user regarding subjective opinions or price projections."),
    PolicyRule("RULE-INFORM-02", "General Financial Content Context", PolicyDecisionType.INFORM, PolicySeverity.LOW, InterventionScope.INFORMATION_ONLY, _rule_inform_financial_content_context, "Provides neutral financial context for relevant content."),

    # 5. ALLOW Rules
    PolicyRule("RULE-ALLOW-01", "Benign Educational or General Information", PolicyDecisionType.ALLOW, PolicySeverity.NONE, InterventionScope.INFORMATION_ONLY, _rule_allow_benign_educational_or_general, "Permits benign financial educational content without intervention."),
]

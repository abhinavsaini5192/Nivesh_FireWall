"""Structured findings generator for Engine 10: Behavioural Signal Intelligence.

Transforms atomic behavioural signals into high-level, explainable BehaviouralFinding
records for downstream policy context.
"""

from typing import Sequence
from nivesh.behaviour.schemas import (
    BehaviouralSignal,
    BehaviouralFinding,
    BehaviouralFindingType,
    BehaviouralSignalType,
)


FINDING_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    BehaviouralSignalType.TIME_PRESSURE.value: (
        "Explicit time-limited urgency or expiration deadlines detected.",
        "Content or prompt commands user to act before an immediate time limit.",
    ),
    BehaviouralSignalType.FOMO_PRESSURE.value: (
        "Fear-of-missing-out language emphasizing scarcity or exclusivity observed.",
        "Prompts highlight restricted access or impending loss of opportunity.",
    ),
    BehaviouralSignalType.REPEATED_URGENCY.value: (
        "Urgency demands were repeated across multiple steps in the interaction sequence.",
        "Multiple distinct urgency calls were recorded across successive prompts.",
    ),
    BehaviouralSignalType.URGENCY_ESCALATION.value: (
        "Interaction urgency escalated progressively from neutral content.",
        "Initial steps were unpressured, while later steps introduced strict time limits.",
    ),
    BehaviouralSignalType.PROGRESSIVE_COMMITMENT.value: (
        "Interaction progressed stepwise across ascending action commitment tiers.",
        "User was guided through sequential escalation stages.",
    ),
    BehaviouralSignalType.RAPID_ACTION_ESCALATION.value: (
        "High-impact commitment was requested in rapid succession.",
        "Elapsed time between initiation and high-impact action is within rapid threshold.",
    ),
    BehaviouralSignalType.LOW_TO_HIGH_IMPACT_TRANSITION.value: (
        "Sequence transitioned from informational/low-impact steps to high-impact commitments.",
        "Low-impact contact/joining was followed by payment, credential, or app installation requests.",
    ),
    BehaviouralSignalType.INFORMATION_TO_TRANSACTION_SHIFT.value: (
        "Interaction began with informational/educational content and shifted to financial extraction.",
        "Content presented education/program material then directed user to payment or fund transfer.",
    ),
    BehaviouralSignalType.REPEATED_ACTION_REQUEST.value: (
        "Identical action request was presented multiple times.",
        "Same action was repeatedly requested within the recorded session history.",
    ),
    BehaviouralSignalType.RETRY_AFTER_DECLINE.value: (
        "Action or payment request was repeated after explicit user decline.",
        "User declined action; interaction re-prompted for action or payment.",
    ),
    BehaviouralSignalType.PERSISTENT_PAYMENT_REQUEST.value: (
        "Payment requested repeatedly across the interaction sequence.",
        "Multiple payment request events occurred within the session.",
    ),
    BehaviouralSignalType.PERSISTENT_CREDENTIAL_REQUEST.value: (
        "Authentication credential disclosure requested repeatedly across session.",
        "Multiple credential request events occurred within the session.",
    ),
    BehaviouralSignalType.CHANNEL_MIGRATION.value: (
        "Interaction directs user across distinct communication platforms.",
        "Originating context migrated to external communication channel.",
    ),
    BehaviouralSignalType.RAPID_CHANNEL_MIGRATION.value: (
        "Channel transition occurred rapidly in sequence.",
        "Channel switch executed within rapid channel migration timing threshold.",
    ),
    BehaviouralSignalType.PRIVATE_CHANNEL_ESCALATION.value: (
        "Interaction migrated from public/web surface to private direct messaging.",
        "Direction given to join private group or direct messaging chat.",
    ),
    BehaviouralSignalType.USER_OVERRIDE.value: (
        "User chose to continue interaction following a safety intervention.",
        "Recorded continuation past a warning or pause prompt.",
    ),
    BehaviouralSignalType.WARNING_OVERRIDE.value: (
        "Warning was shown and user opted to proceed.",
        "Safety warning was presented and user selected continuation.",
    ),
    BehaviouralSignalType.REPEATED_WARNING_OVERRIDE.value: (
        "Multiple warnings were overridden within the same session.",
        "Session recorded successive warning presentations followed by user overrides.",
    ),
}


class FindingsBuilder:
    """Builds structured BehaviouralFinding objects from detected signals."""

    @staticmethod
    def build_findings(signals: Sequence[BehaviouralSignal]) -> list[BehaviouralFinding]:
        """Aggregate signals into cohesive behavioural findings."""
        findings: list[BehaviouralFinding] = []
        # Group by signal type
        grouped: dict[str, list[BehaviouralSignal]] = {}
        for sig in signals:
            grouped.setdefault(sig.signal_type.value, []).append(sig)

        for sig_type_val, sig_list in grouped.items():
            first_sig = sig_list[0]
            default_desc, default_basis = FINDING_DESCRIPTIONS.get(
                sig_type_val,
                (first_sig.description, "Identified by behavioural sequence evaluation."),
            )

            all_event_ids: list[str] = []
            all_action_ids: list[str] = []
            for s in sig_list:
                all_event_ids.extend(s.event_ids)
                all_action_ids.extend(s.action_ids)

            # Finding type enum
            try:
                ftype = BehaviouralFindingType(sig_type_val)
            except ValueError:
                continue

            findings.append(
                BehaviouralFinding(
                    finding_id=f"BHF-{len(findings) + 1:03d}",
                    finding_type=ftype,
                    description=default_desc,
                    basis=first_sig.evidence[0] if first_sig.evidence else default_basis,
                    supporting_signal_ids=[s.signal_id for s in sig_list],
                    event_ids=list(dict.fromkeys(all_event_ids)),
                    action_ids=list(dict.fromkeys(all_action_ids)),
                    confidence=max(s.confidence for s in sig_list),
                    provenance={"signal_count": len(sig_list), "signal_type": sig_type_val},
                )
            )

        return findings

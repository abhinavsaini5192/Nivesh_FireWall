"""Action Intelligence Engine (Engine 3 of Nivesh Firewall).

Converts Engine 1 NormalizedContent and Engine 2 ClaimAnalysis into
structured, atomic, canonical actions.
Answers: 'What is the content asking the user to do?'
Never performs truth evaluation, risk scoring, threat path construction, or blocking.
"""

import time
import re
from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, SourceSpan
from nivesh.schemas.actions import (
    ActionAnalysis,
    CanonicalAction,
    ActionRelation,
    ActionAnalysisMetadata,
    ActionText,
    ActionSequence,
    ActionType,
    ActionCategory,
    ActionTarget,
)
from nivesh.actions.segmenter import ActionSegmenter
from nivesh.actions.classifier import ActionClassifier
from nivesh.actions.target_extractor import ActionTargetExtractor
from nivesh.actions.parameter_extractor import ActionParameterExtractor
from nivesh.actions.modality import ActionModalityDetector
from nivesh.actions.fingerprint import ActionFingerprintGenerator
from nivesh.actions.rationale_linker import ActionRationaleLinker
from nivesh.actions.deduplicator import ActionDeduplicator
from nivesh.actions.llm_adapter import LlmActionAdapter

ENGINE_VERSION = "1.0.0"


class ActionIntelligenceEngine:
    """Core Engine 3 service interface."""

    def __init__(
        self,
        llm_adapter: Optional[LlmActionAdapter] = None,
    ):
        self.segmenter = ActionSegmenter()
        self.classifier = ActionClassifier()
        self.target_extractor = ActionTargetExtractor()
        self.parameter_extractor = ActionParameterExtractor()
        self.modality_detector = ActionModalityDetector()
        self.fingerprint_gen = ActionFingerprintGenerator()
        self.rationale_linker = ActionRationaleLinker()
        self.deduplicator = ActionDeduplicator()
        self.llm_adapter = llm_adapter or LlmActionAdapter()

    def analyze(
        self,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None
    ) -> ActionAnalysis:
        """Analyzes content and claims, producing structured ActionAnalysis.
        
        Directly callable from unit tests and service layer without HTTP.
        """
        start_time = time.perf_counter()
        content_id = content.content_id
        full_text = content.normalized.text if content.normalized and content.normalized.text else ""
        if not full_text and content.raw:
            full_text = content.raw.text

        # 1. Candidate Segmentation
        candidates = self.segmenter.segment(content, claims)

        # 2. Canonical Action Construction
        raw_actions: list[CanonicalAction] = []
        for idx, cand in enumerate(candidates, start=1):
            action_type, category, objects = self.classifier.classify(cand.text, cand.cta_category)
            target = self.target_extractor.extract_target(cand.text, action_type, content)
            parameters = self.parameter_extractor.extract_parameters(cand.text, action_type, content)
            modality = self.modality_detector.detect(cand.text)
            fingerprint = self.fingerprint_gen.generate(action_type, category, target, objects, parameters)
            normalized_stmt = self._format_normalized_statement(action_type, target, objects, parameters)

            action = CanonicalAction(
                action_id=f"ACTION-{idx:03d}",
                source_content_id=content_id,
                text=ActionText(original=cand.text.strip(), normalized=normalized_stmt),
                action_type=action_type,
                category=category,
                target=target,
                objects=objects,
                parameters=parameters,
                sequence=ActionSequence(index=idx),
                modality=modality,
                source_span=cand.span,
                source_spans=[cand.span],
                confidence=0.95,
                canonical_fingerprint=fingerprint,
                rationale_claim_ids=[]
            )

            # Link rationale claims if present
            self.rationale_linker.link_rationales(action, cand.rationale_text, claims)
            raw_actions.append(action)

        # 3. Deduplication of identical underlying actions
        deduped_actions, duplicates_merged = self.deduplicator.deduplicate(raw_actions)

        # 4. Action Relationship Detection
        relations = self.rationale_linker.detect_action_relations(deduped_actions, full_text)

        # 5. Metadata compilation
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        type_counts: dict[str, int] = {}
        for a in deduped_actions:
            type_counts[a.action_type] = type_counts.get(a.action_type, 0) + 1

        metadata = ActionAnalysisMetadata(
            processing_time_ms=duration_ms,
            total_actions=len(deduped_actions),
            action_types_count=type_counts,
            duplicate_actions_merged=duplicates_merged
        )

        return ActionAnalysis(
            content_id=content_id,
            actions=deduped_actions,
            action_relations=relations,
            analysis_metadata=metadata
        )

    @staticmethod
    def _format_normalized_statement(
        action_type: ActionType,
        target: ActionTarget,
        objects: list[str],
        parameters: dict[str, Any]
    ) -> str:
        """Formats a clean, standardized English imperative statement for the action."""
        if action_type in {"JOIN_CHANNEL", "JOIN_GROUP"}:
            dest = target.value or "channel"
            return f"Join {dest}."
        elif action_type == "DOWNLOAD":
            app = target.value or "application"
            return f"Download {app}."
        elif action_type == "INSTALL":
            item = objects[0] if objects else (target.value or "application")
            return f"Install {item}."
        elif action_type in {"UPLOAD_DOCUMENT", "UPLOAD_IDENTITY"}:
            doc = objects[0] if objects else "document"
            return f"Upload {doc}."
        elif action_type == "ENTER_CREDENTIALS":
            cred = objects[0] if objects else "credentials"
            return f"Enter {cred}."
        elif action_type == "SHARE_OTP":
            return "Share OTP."
        elif action_type == "CONNECT_BANK":
            return "Connect bank account."
        elif action_type == "AUTHORIZE_ACCESS":
            return "Authorize account access."
        elif action_type in {"PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY"}:
            verb = "Pay" if action_type == "PAYMENT" else ("Transfer" if action_type == "TRANSFER_MONEY" else "Deposit")
            amt = parameters.get("amount")
            curr = parameters.get("currency", "INR")
            if amt is not None:
                amt_clean = int(amt) if int(amt) == amt else amt
                return f"{verb} {curr} {amt_clean}."
            return f"{verb} funds."
        elif action_type == "CONTACT":
            recipient = f" {target.value}" if target.value else ""
            return f"Contact{recipient}."
        elif action_type == "CLICK_LINK":
            return "Click link."
        elif action_type == "OPEN_WEBSITE":
            site = f" {target.value}" if target.value else ""
            return f"Open website{site}."

        return f"{action_type.lower().replace('_', ' ').capitalize()}."

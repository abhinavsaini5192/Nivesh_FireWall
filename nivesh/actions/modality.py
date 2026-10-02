"""Action modality and presentation strength component for Engine 3.

Distinguishes between explicit instructions, requests, suggestions, invitations,
warnings, and implicit actions.
"""

import re
from nivesh.schemas.actions import ActionModality, ActionModalityType, ModalityStrength


class ActionModalityDetector:
    """Classifies the modality type and strength of an action assertion."""

    def detect(self, text: str) -> ActionModality:
        """Determines ActionModality (type and strength) from text."""
        clean = text.lower().strip()

        # 1. Suggestions (indirect strength)
        if any(w in clean for w in ["you should consider", "consider joining", "we recommend", "suggest", "might want to", "why not"]):
            return ActionModality(type="suggestion", strength="indirect")

        # 2. Implicit actions (indirect strength)
        if any(w in clean for w in ["must be completed", "is required to", "activation requires", "required before", "needed to continue"]):
            return ActionModality(type="implicit", strength="indirect")

        # 3. Warnings (direct strength)
        if any(w in clean for w in ["or your account will be", "or you will lose", "warning:", "last chance before"]):
            return ActionModality(type="warning", strength="direct")

        # 4. Invitations (direct strength)
        if any(w in clean for w in ["join us", "join our", "welcome to join", "feel free to", "invite you"]):
            return ActionModality(type="invitation", strength="direct")

        # 5. Polite requests (direct strength)
        if any(w in clean for w in ["please", "kindly"]):
            return ActionModality(type="request", strength="direct")

        # 6. Direct imperatives / Instructions (default)
        return ActionModality(type="instruction", strength="direct")

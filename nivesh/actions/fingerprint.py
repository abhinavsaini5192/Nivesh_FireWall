"""Deterministic action fingerprint generator for Engine 3.

Produces normalized, deterministic string representations of canonical actions
for downstream deduplication and Engine 8 (Scam Fingerprint Engine) indexing.
"""

import re
from typing import Optional, Any
from nivesh.schemas.actions import ActionType, ActionCategory, ActionTarget


class ActionFingerprintGenerator:
    """Generates deterministic canonical action fingerprints."""

    @staticmethod
    def generate(
        action_type: ActionType,
        category: ActionCategory,
        target: ActionTarget,
        objects: list[str],
        parameters: dict[str, Any],
    ) -> str:
        """Constructs a deterministic canonical fingerprint for an action."""
        t_type = action_type.upper()
        c_type = category.upper()
        
        target_val = (target.value or target.type or "NONE").strip().upper()
        target_clean = re.sub(r"[^\w]", "_", target_val)

        # Financial parameters
        amt = parameters.get("amount")
        curr = parameters.get("currency", "INR")

        if amt is not None:
            amt_clean = int(amt) if int(amt) == amt else amt
            return f"ACTION:{t_type}|AMOUNT:{amt_clean}|CURRENCY:{curr}"

        # Objects (e.g. APK, PAN, trading password)
        if objects:
            obj_clean = re.sub(r"[^\w]", "_", objects[0].strip().upper())
            return f"ACTION:{t_type}|OBJECT:{obj_clean}"

        return f"ACTION:{t_type}|TARGET:{target_clean}|CATEGORY:{c_type}"

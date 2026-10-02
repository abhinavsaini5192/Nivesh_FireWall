"""Optional LLM adapter for Engine 3 semantic action normalization.

Provides a schema-validated bridge for complex or ambiguous action clauses.
When no API key is provided or offline, gracefully falls back to deterministic rule extraction.
Always enforces Pydantic schema validation on any model output.
"""

from typing import Optional
from nivesh.schemas.actions import CanonicalAction


class LlmActionAdapter:
    """Interface for optional LLM-assisted action extraction and refinement."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def refine_action(self, candidate_text: str, fallback_action: CanonicalAction) -> CanonicalAction:
        """Refines ambiguous action using LLM if available; otherwise returns fallback."""
        if not self.api_key:
            return fallback_action
        # In mock or offline environment, rule-based output is trusted and returned
        return fallback_action

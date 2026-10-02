"""LLM Semantic Structuring Adapter with Strict Schema Validation and Fallback for Engine 2.

Follows Section 20 & 21 prompting rules:
- Extract claims, do not fact-check
- Do not invent facts
- Preserve uncertainty
- Distinguish opinion from prediction
- Distinguish claims from actions
- Preserve exact wording, numbers, and dates
- Never infer missing entities
- Enforce strict Pydantic JSON schema validation
- Gracefully fall back to deterministic extraction if LLM is unavailable or fails.
"""

import json
import os
from typing import Optional, Any
from nivesh.schemas.claims import CanonicalClaim

CLAIM_EXTRACTION_SYSTEM_PROMPT = """
You are the Claim Intelligence Engine (Engine 2) of Nivesh Firewall.
Your sole job is to extract and structure atomic, canonical claims from financial text.

STRICT OPERATIONAL RULES:
1. Extract claims only; DO NOT fact-check or verify truth.
2. DO NOT invent facts, numbers, or entities.
3. Preserve uncertainty and certainty language exactly as written.
4. Distinguish opinion ('I think XYZ is undervalued') from prediction ('XYZ will reach ₹500').
5. Distinguish claims from actions. Pure actions like 'Join Telegram', 'Download app', 'Pay ₹5,000' must NOT become claims.
6. Preserve exact wording, numbers, percentages, and dates.
7. Do not infer missing entities; use 'UNKNOWN' if ambiguous.
8. Output MUST strictly match the requested JSON schema.
"""


class LlmClaimAdapter:
    """Optional LLM adapter for deep semantic structuring with strict validation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.model = model or "gpt-4o-mini"

    def is_available(self) -> bool:
        """Checks if an LLM backend is configured with credentials."""
        return bool(self.api_key)

    def structure_claims(
        self,
        candidate_texts: list[str],
        content_id: str
    ) -> Optional[list[dict[str, Any]]]:
        """Invokes LLM if configured and validates output against CanonicalClaim.
        
        Returns None on any error or missing credentials to trigger rule fallback.
        """
        if not self.is_available() or not candidate_texts:
            return None

        try:
            # Check for OpenAI client if installed
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            prompt = (
                f"Extract atomic claims for these candidate segments:\n"
                f"{json.dumps(candidate_texts, indent=2)}\n\n"
                f"Format as a JSON array of claim objects matching the schema."
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLAIM_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            if not content:
                return None

            data = json.loads(content)
            raw_claims = data.get("claims", data if isinstance(data, list) else [])

            # Strictly validate every claim against CanonicalClaim schema
            validated = []
            for rc in raw_claims:
                try:
                    c = CanonicalClaim.model_validate(rc)
                    validated.append(c.model_dump())
                except Exception:
                    continue

            return validated if validated else None

        except Exception:
            # Graceful fallback: never let an LLM network or validation glitch crash the engine
            return None

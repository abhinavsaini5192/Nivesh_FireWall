"""Configuration for the Product Orchestrator."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class OrchestratorConfig(BaseModel):
    """Execution options for the Product Orchestrator."""
    source_mode: Literal["LIVE", "CACHE", "FIXTURE"] = Field(
        default="FIXTURE",
        description="Source Intelligence retrieval mode for Engine 4",
    )
    enable_identity: bool = Field(
        default=True,
        description="Whether to execute Engine 9 (Identity Verification & Entity Resolution)",
    )
    enable_behaviour: bool = Field(
        default=True,
        description="Whether to execute Engine 10 (Behavioural Signal Intelligence)",
    )
    enable_threat: bool = Field(
        default=True,
        description="Whether to execute Engine 6 (Threat & Attack-Path Intelligence)",
    )
    enable_fingerprint: bool = Field(
        default=True,
        description="Whether to execute Engine 7 (Scam Fingerprint & Collective Intelligence)",
    )
    fail_fast: bool = Field(
        default=False,
        description="If True, any engine exception raises immediately; if False, recoverable errors degrade gracefully",
    )
    timeout_ms: Optional[float] = Field(
        default=None,
        description="Optional maximum pipeline timeout in milliseconds",
    )

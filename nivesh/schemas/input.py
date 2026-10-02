"""Input schemas for the Content Intelligence Engine."""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

SourceType = Literal["text", "url", "image"]
ChannelType = Literal[
    "browser",
    "telegram",
    "whatsapp",
    "instagram",
    "youtube",
    "email",
    "unknown"
]


class ContentInput(BaseModel):
    """Unified input container for Engine 1 processing."""
    text: Optional[str] = Field(default=None, description="Raw text content to analyze")
    url: Optional[str] = Field(default=None, description="URL to analyze or fetch content from")
    image_bytes: Optional[bytes] = Field(default=None, description="Raw image bytes for OCR")
    image_path: Optional[str] = Field(default=None, description="Local file path to an image")
    image_base64: Optional[str] = Field(default=None, description="Base64-encoded image string")
    channel: ChannelType = Field(default="unknown", description="Source channel if known")
    fetch_url: bool = Field(default=True, description="Whether to ingest webpage body text for URL inputs")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="Arbitrary client metadata")

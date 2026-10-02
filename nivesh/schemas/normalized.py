"""Normalized content schema for downstream engines in Nivesh Firewall."""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    type: Literal["text", "url", "image"]
    channel: Literal[
        "browser",
        "telegram",
        "whatsapp",
        "instagram",
        "youtube",
        "email",
        "unknown"
    ] = "unknown"


class RawContent(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    image_reference: Optional[str] = None
    image_metadata: Optional[dict[str, Any]] = None


class NormalizedText(BaseModel):
    text: str = ""
    language: str = "en"
    language_confidence: float = 1.0


class EntityItem(BaseModel):
    text: str
    normalized: str
    type: str  # person, organization, regulator, financial_instrument
    confidence: float = 1.0
    span: Optional[list[int]] = None  # [start, end] offset in normalized text


class EntitiesContainer(BaseModel):
    people: list[EntityItem] = Field(default_factory=list)
    organizations: list[EntityItem] = Field(default_factory=list)
    regulators: list[EntityItem] = Field(default_factory=list)
    financial_instruments: list[EntityItem] = Field(default_factory=list)


class UrlSignal(BaseModel):
    original_url: str
    normalized_url: str
    scheme: str
    domain: str
    path: str
    query: Optional[str] = None
    fragment: Optional[str] = None
    port: Optional[int] = None


class DomainSignal(BaseModel):
    domain: str
    effective_domain: str
    subdomain: Optional[str] = None
    port: Optional[int] = None


class SocialHandleSignal(BaseModel):
    platform: Literal["telegram", "instagram", "youtube", "twitter", "whatsapp", "unknown"]
    handle: str
    raw: str


class RegistrationNumberSignal(BaseModel):
    type: str  # "SEBI", "GSTIN", "CIN", "PAN", "UNKNOWN"
    value: str
    raw: str


class CurrencyAmountSignal(BaseModel):
    value: float
    currency: str  # "INR", "USD", etc.
    raw: str
    span: Optional[list[int]] = None


class PercentageSignal(BaseModel):
    value: float
    raw: str
    span: Optional[list[int]] = None


class DateSignal(BaseModel):
    value: str
    raw: str
    span: Optional[list[int]] = None


class CallToAction(BaseModel):
    phrase: str
    category: Literal[
        "contact",
        "click",
        "join_channel",
        "download",
        "install",
        "upload",
        "credential_request",
        "payment",
        "transfer",
        "share",
        "unknown"
    ]
    confidence: float = 1.0
    span: Optional[list[int]] = None


class StructuredSignals(BaseModel):
    urls: list[UrlSignal] = Field(default_factory=list)
    domains: list[DomainSignal] = Field(default_factory=list)
    email_addresses: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    social_handles: list[SocialHandleSignal] = Field(default_factory=list)
    registration_numbers: list[RegistrationNumberSignal] = Field(default_factory=list)
    currency_amounts: list[CurrencyAmountSignal] = Field(default_factory=list)
    dates: list[DateSignal] = Field(default_factory=list)
    percentages: list[PercentageSignal] = Field(default_factory=list)
    financial_terms: list[str] = Field(default_factory=list)


class ContentFeatures(BaseModel):
    contains_financial_content: bool = False
    confidence: float = 0.0
    financial_terms_detected: list[str] = Field(default_factory=list)
    call_to_action_present: bool = False
    calls_to_action: list[CallToAction] = Field(default_factory=list)


class Provenance(BaseModel):
    created_at: str
    processing_version: str = "1.0.0"
    input_type: str
    ocr_used: bool = False
    ocr_metadata: Optional[dict[str, Any]] = None


class NormalizedContent(BaseModel):
    content_id: str
    source: SourceInfo
    raw: RawContent
    normalized: NormalizedText
    entities: EntitiesContainer = Field(default_factory=EntitiesContainer)
    structured_signals: StructuredSignals = Field(default_factory=StructuredSignals)
    content_features: ContentFeatures = Field(default_factory=ContentFeatures)
    provenance: Provenance
    warnings: list[str] = Field(default_factory=list)
    status: Literal["success", "partial", "failed"] = "success"

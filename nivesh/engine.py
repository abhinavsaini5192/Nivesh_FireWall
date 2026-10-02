"""Content Intelligence Engine (Engine 1 of Nivesh Firewall).

Orchestrates input ingestion, normalization, deterministic signal extraction,
entity recognition, and language/relevance classification into the shared
NormalizedContent schema.

Strict constraint: Never performs final risk assessment or scam scoring.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any

from nivesh.schemas.input import ContentInput, SourceType
from nivesh.schemas.normalized import (
    NormalizedContent,
    SourceInfo,
    RawContent,
    NormalizedText,
    EntitiesContainer,
    StructuredSignals,
    ContentFeatures,
    Provenance,
)
from nivesh.normalizers.text_normalizer import TextNormalizer
from nivesh.extractors.url_extractor import UrlExtractor
from nivesh.extractors.social_extractor import SocialExtractor
from nivesh.extractors.contact_extractor import ContactExtractor
from nivesh.extractors.financial_extractor import FinancialExtractor
from nivesh.extractors.entity_extractor import EntityExtractor
from nivesh.extractors.cta_extractor import CtaExtractor
from nivesh.classifiers.language_detector import LanguageDetector
from nivesh.classifiers.financial_relevance import FinancialRelevanceClassifier
from nivesh.adapters.ocr_adapter import OcrAdapter, OcrResult
from nivesh.adapters.url_adapter import UrlAdapter, UrlIngestionResult

ENGINE_VERSION = "1.0.0"


class ContentIntelligenceEngine:
    """Core Engine 1 service interface."""

    def __init__(
        self,
        ocr_adapter: Optional[OcrAdapter] = None,
        url_adapter: Optional[UrlAdapter] = None,
    ):
        self.text_normalizer = TextNormalizer()
        self.url_extractor = UrlExtractor()
        self.social_extractor = SocialExtractor()
        self.contact_extractor = ContactExtractor()
        self.financial_extractor = FinancialExtractor()
        self.entity_extractor = EntityExtractor()
        self.cta_extractor = CtaExtractor()
        self.language_detector = LanguageDetector()
        self.relevance_classifier = FinancialRelevanceClassifier()
        self.ocr_adapter = ocr_adapter or OcrAdapter()
        self.url_adapter = url_adapter or UrlAdapter()

    def process(self, content_input: ContentInput) -> NormalizedContent:
        """Processes a ContentInput and produces a complete NormalizedContent object.
        
        Callable directly from code and unit tests without HTTP overhead.
        """
        content_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        warnings: list[str] = []

        # 1. Determine Source Type and Channel
        input_type: SourceType = "text"
        if content_input.image_bytes or content_input.image_path or content_input.image_base64:
            input_type = "image"
        elif content_input.url and not content_input.text:
            input_type = "url"

        channel = content_input.channel

        # 2. Ingest raw text based on source type
        raw_text: str = ""
        raw_url: Optional[str] = content_input.url
        image_ref: Optional[str] = content_input.image_path or ("<base64_or_bytes>" if input_type == "image" else None)
        ocr_used: bool = False
        ocr_metadata: Optional[dict[str, Any]] = None

        if input_type == "image":
            ocr_used = True
            ocr_res: OcrResult = self.ocr_adapter.process(
                image_bytes=content_input.image_bytes,
                image_path=content_input.image_path,
                image_base64=content_input.image_base64,
            )
            raw_text = ocr_res.text
            ocr_metadata = {
                "engine": ocr_res.engine,
                "confidence": ocr_res.confidence,
                **ocr_res.metadata,
            }
            if ocr_res.warnings:
                warnings.extend(ocr_res.warnings)

        elif input_type == "url":
            raw_text = content_input.text or ""
            if content_input.url:
                ingest_res: UrlIngestionResult = self.url_adapter.ingest(
                    content_input.url,
                    fetch=content_input.fetch_url,
                )
                if ingest_res.text:
                    raw_text = f"{raw_text}\n{ingest_res.text}".strip() if raw_text else ingest_res.text
                if ingest_res.warnings:
                    warnings.extend(ingest_res.warnings)

        else:
            raw_text = content_input.text or ""

        # Check for empty content
        if not raw_text.strip() and not raw_url:
            warnings.append("No readable text or content provided")

        # 3. Text Normalization (preserving raw.text separately)
        normalized_text = self.text_normalizer.normalize(raw_text)

        # 4. Language Detection
        lang_code, lang_confidence = self.language_detector.detect(normalized_text)

        # 5. Extract Structured Signals
        # 5a. URLs & Domains
        extracted_urls, extracted_domains = self.url_extractor.extract(
            f"{normalized_text} {raw_url or ''}"
        )

        # 5b. Social handles
        social_handles = self.social_extractor.extract(normalized_text)

        # 5c. Contacts (Emails, Phones)
        emails = self.contact_extractor.extract_emails(normalized_text)
        phones = self.contact_extractor.extract_phones(normalized_text)

        # 5d. Financial Signals (Amounts, Percentages, Registration numbers, Dates, Terms)
        currency_amounts = self.financial_extractor.extract_currency_amounts(normalized_text)
        percentages = self.financial_extractor.extract_percentages(normalized_text)
        reg_numbers = self.financial_extractor.extract_registration_numbers(normalized_text)
        dates = self.financial_extractor.extract_dates(normalized_text)
        financial_terms = self.financial_extractor.extract_financial_terms(normalized_text)

        # 6. Entity Extraction (People, Orgs, Regulators, Instruments)
        entities = self.entity_extractor.extract(normalized_text)

        # 7. Call To Action Extraction
        ctas = self.cta_extractor.extract(normalized_text)

        # 8. Financial Relevance Classification
        content_features = self.relevance_classifier.classify(
            text=normalized_text,
            financial_terms=financial_terms,
            currency_amounts=currency_amounts,
            percentages=percentages,
            regulators=entities.regulators,
            instruments=entities.financial_instruments,
            ctas=ctas,
        )

        # 9. Determine Status
        status = "success"
        if warnings:
            if not normalized_text.strip() and not extracted_urls:
                status = "failed"
            else:
                status = "partial"

        # 10. Construct NormalizedContent Output
        return NormalizedContent(
            content_id=content_id,
            source=SourceInfo(
                type=input_type,
                channel=channel,
            ),
            raw=RawContent(
                text=raw_text,
                url=raw_url,
                image_reference=image_ref,
                image_metadata=ocr_metadata if input_type == "image" else None,
            ),
            normalized=NormalizedText(
                text=normalized_text,
                language=lang_code,
                language_confidence=lang_confidence,
            ),
            entities=entities,
            structured_signals=StructuredSignals(
                urls=extracted_urls,
                domains=extracted_domains,
                email_addresses=emails,
                phone_numbers=phones,
                social_handles=social_handles,
                registration_numbers=reg_numbers,
                currency_amounts=currency_amounts,
                dates=dates,
                percentages=percentages,
                financial_terms=financial_terms,
            ),
            content_features=content_features,
            provenance=Provenance(
                created_at=created_at,
                processing_version=ENGINE_VERSION,
                input_type=input_type,
                ocr_used=ocr_used,
                ocr_metadata=ocr_metadata,
            ),
            warnings=warnings,
            status=status,
        )

    # Convenience helper methods
    def process_text(self, text: str, channel: str = "unknown") -> NormalizedContent:
        """Processes plain text directly."""
        return self.process(ContentInput(text=text, channel=channel))

    def process_url(self, url: str, channel: str = "browser", fetch: bool = True) -> NormalizedContent:
        """Processes a URL input directly."""
        return self.process(ContentInput(url=url, channel=channel, fetch_url=fetch))

    def process_image(
        self,
        image_bytes: Optional[bytes] = None,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        channel: str = "unknown",
    ) -> NormalizedContent:
        """Processes an image input directly."""
        return self.process(ContentInput(
            image_bytes=image_bytes,
            image_path=image_path,
            image_base64=image_base64,
            channel=channel,
        ))

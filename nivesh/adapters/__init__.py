"""Adapter exports for Engine 1."""

from .ocr_adapter import OcrAdapter, OcrResult
from .url_adapter import UrlAdapter, UrlIngestionResult

__all__ = [
    "OcrAdapter",
    "OcrResult",
    "UrlAdapter",
    "UrlIngestionResult",
]

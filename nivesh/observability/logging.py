"""Centralized Structured Logging and Correlation for Nivesh Firewall.

Phase 14.4: Observability, Monitoring & Operations.
Provides:
- Context-propagated correlation IDs and request IDs via contextvars
- Production-grade JSON formatter with structured attributes
- Strict redaction of credentials, tokens, OTPs, PINs, and sensitive content
- Standardized access logging and exception handling
"""

import contextvars
import json
import logging
import re
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

from nivesh.config.settings import Settings, get_settings

# Context variables for correlation across async tasks and engine executions
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("correlation_id", default=None)
analysis_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("analysis_id", default=None)
engine_key_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("engine_key", default=None)


# Additional regex patterns for secrets and tokens
BEARER_PATTERN = re.compile(r"Bearer\s+([A-Za-z0-9\-_\.=]+)", re.IGNORECASE)
API_KEY_PATTERN = re.compile(r"(api[_-]?key|secret[_-]?key)[\"':=\s]+([A-Za-z0-9\-_]{8,})", re.IGNORECASE)
DB_CONN_PATTERN = re.compile(r"://([^:@\s]+):([^@\s]+)@", re.IGNORECASE)
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----")


def scrub_sensitive_tokens(text: str) -> str:
    """Scrub authentication tokens, API keys, private keys, and DB credentials from log messages."""
    if not isinstance(text, str):
        return str(text)

    # 1. Apply existing financial data sanitizer (OTPs, PINs, CVVs, card numbers, passwords)
    try:
        from nivesh.orchestrator.service import sanitize_sensitive_data
        cleaned = sanitize_sensitive_data(text)
    except ImportError:
        cleaned = text

    # 2. Scrub Bearer tokens and JWTs
    cleaned = BEARER_PATTERN.sub("Bearer [REDACTED_TOKEN]", cleaned)

    # 3. Scrub API keys and secret keys
    cleaned = API_KEY_PATTERN.sub(r"\1: [REDACTED_KEY]", cleaned)

    # 4. Scrub DB connection strings
    cleaned = DB_CONN_PATTERN.sub(r"://\1:[REDACTED]@", cleaned)

    # 5. Scrub Private Keys
    cleaned = PRIVATE_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", cleaned)

    return cleaned


class SensitiveDataScrubberFilter(logging.Filter):
    """Logging filter that guarantees sensitive credentials and tokens never enter log streams."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = scrub_sensitive_tokens(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: scrub_sensitive_tokens(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    scrub_sensitive_tokens(a) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


class StructuredJsonFormatter(logging.Formatter):
    """Production JSON log formatter outputting standardized machine-parsable logs."""

    def __init__(self, service_name: str = "nivesh-firewall", environment: str = "development", version: str = "1.0.0"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.version = version

    def format(self, record: logging.LogRecord) -> str:
        # Resolve contextual identifiers
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        corr_id = getattr(record, "correlation_id", None) or correlation_id_ctx.get()
        ana_id = getattr(record, "analysis_id", None) or analysis_id_ctx.get()
        eng_key = getattr(record, "engine_key", None) or engine_key_ctx.get()

        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub_sensitive_tokens(record.getMessage()),
            "service": self.service_name,
            "environment": self.environment,
            "version": self.version,
        }

        # Include tracing & correlation identifiers if set
        if req_id:
            log_data["request_id"] = req_id
        if corr_id:
            log_data["correlation_id"] = corr_id
        if ana_id:
            log_data["analysis_id"] = ana_id
        if eng_key:
            log_data["engine_key"] = eng_key

        # Extra structured attributes if passed via extra={}
        for attr in ("route", "http_method", "status_code", "duration_ms", "error_type", "reason_code", "client_ip"):
            val = getattr(record, attr, None)
            if val is not None:
                log_data[attr] = val

        # Exception information
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            log_data["error_type"] = exc_type.__name__ if exc_type else "Exception"
            log_data["error_message"] = scrub_sensitive_tokens(str(exc_val))
            tb_str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            log_data["stack_trace"] = scrub_sensitive_tokens(tb_str)

        return json.dumps(log_data)


class StandardTextFormatter(logging.Formatter):
    """Human-readable text formatter for local development with correlation IDs."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or request_id_ctx.get() or "-"
        corr_id = getattr(record, "correlation_id", None) or correlation_id_ctx.get() or "-"
        clean_msg = scrub_sensitive_tokens(record.getMessage())

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"{ts} [{record.levelname:<7}] [{record.name}] [req:{req_id} corr:{corr_id}]"

        formatted = f"{prefix}: {clean_msg}"
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            tb_str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            formatted += f"\n{scrub_sensitive_tokens(tb_str)}"

        return formatted


def configure_observability_logging(settings: Optional[Settings] = None) -> logging.Logger:
    """Configure structured logging and sensitive data scrubbing for Nivesh Firewall."""
    cfg = settings or get_settings()
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)
    logger = logging.getLogger("nivesh")
    logger.setLevel(level)

    # Remove existing StreamHandlers to prevent duplication
    for h in list(logger.handlers):
        if isinstance(h, logging.StreamHandler):
            logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if cfg.log_format == "json" or cfg.is_production():
        formatter = StructuredJsonFormatter(
            service_name=cfg.app_name,
            environment=cfg.env,
            version=cfg.version,
        )
    else:
        formatter = StandardTextFormatter()

    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataScrubberFilter())
    logger.addHandler(handler)

    return logger

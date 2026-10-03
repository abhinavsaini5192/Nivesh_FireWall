"""Centralized Logging Configuration for Nivesh Firewall.

Ensures environment-specific log levels and redacts sensitive financial data
(OTPs, PINs, CVVs, card numbers, passwords, bank accounts, tokens)
so raw confidential data is NEVER logged.
"""

import logging
from typing import Optional

from nivesh.config.settings import Settings


class SensitiveDataRedactor(logging.Filter):
    """Logging filter that sanitizes passwords, credentials, OTPs, PINs, and card numbers."""

    def filter(self, record: logging.LogRecord) -> bool:
        from nivesh.orchestrator.service import sanitize_sensitive_data
        if isinstance(record.msg, str):
            record.msg = sanitize_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: sanitize_sensitive_data(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_sensitive_data(a) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


def setup_logging(settings: Settings) -> logging.Logger:
    """Configure centralized logging based on application settings."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger = logging.getLogger("nivesh")
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataRedactor())
        logger.addHandler(handler)

    # Ensure redactor is on all handlers
    for h in logger.handlers:
        if not any(isinstance(f, SensitiveDataRedactor) for f in h.filters):
            h.addFilter(SensitiveDataRedactor())

    return logger

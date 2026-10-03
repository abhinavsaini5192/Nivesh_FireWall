"""Sanitized application-level storage exceptions for Nivesh Firewall.

Ensures that database connection strings, credentials, raw SQL statements,
and internal server paths are never exposed to clients.
"""

from typing import Optional, Any


class StorageError(Exception):
    """Base exception for all storage operations."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DatabaseUnavailableError(StorageError):
    """Raised when the persistent database is unreachable or connection fails."""
    pass


class ConstraintViolationError(StorageError):
    """Raised when a unique or referential constraint is violated."""
    pass


class AnalysisNotFoundError(StorageError):
    """Raised when an analysis record cannot be found in persistent storage."""
    pass


class FingerprintNotFoundError(StorageError):
    """Raised when a fingerprint record cannot be found in persistent storage."""
    pass


class SessionNotFoundError(StorageError):
    """Raised when a session record cannot be found in persistent storage."""
    pass


class ForbiddenFieldError(StorageError):
    """Raised when attempting to store forbidden raw sensitive credentials or PII."""
    pass

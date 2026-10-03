"""Nivesh Firewall Security & Access Control Subsystem.

Phase 14.3: Security, Access Control & Secrets.
"""

from nivesh.security.models import (
    UserRole,
    AuthenticatedUser,
    TokenPayload,
)
from nivesh.security.tokens import (
    create_access_token,
    decode_access_token,
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    MalformedTokenError,
)
from nivesh.security.api_keys import validate_api_key
from nivesh.security.rate_limiter import (
    SlidingWindowRateLimiter,
    rate_limiter,
)
from nivesh.security.audit import log_security_event
from nivesh.security.dependencies import (
    get_client_ip,
    get_current_user,
    get_optional_user,
    require_auth,
    require_role,
    require_admin,
    require_analyst,
    require_service,
    enforce_rate_limit,
)
from nivesh.security.middleware import (
    SecurityHeadersMiddleware,
    CorrelationIdMiddleware,
)

__all__ = [
    "UserRole",
    "AuthenticatedUser",
    "TokenPayload",
    "create_access_token",
    "decode_access_token",
    "AuthenticationError",
    "InvalidTokenError",
    "TokenExpiredError",
    "MalformedTokenError",
    "validate_api_key",
    "SlidingWindowRateLimiter",
    "rate_limiter",
    "log_security_event",
    "get_client_ip",
    "get_current_user",
    "get_optional_user",
    "require_auth",
    "require_role",
    "require_admin",
    "require_analyst",
    "require_service",
    "enforce_rate_limit",
    "SecurityHeadersMiddleware",
    "CorrelationIdMiddleware",
]

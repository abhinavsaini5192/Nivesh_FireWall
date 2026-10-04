"""Security and request correlation middleware for Nivesh Firewall.

Phase 14.3: Security, Access Control & Secrets.
Adds defense-in-depth HTTP security response headers, request correlation IDs,
and sensitive-endpoint cache-control.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from nivesh.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard HTTP security response headers across all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Baseline security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Cache control: prevent caching of sensitive intelligence or analysis responses
        path = request.url.path
        if (
            path.startswith("/api/v1/firewall/")
            or path.startswith("/api/v1/fingerprints/")
            or path.startswith("/api/v1/admin/")
            or path.startswith("/api/v1/behaviour/")
        ):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        # HSTS in production or over HTTPS / reverse proxy HTTPS
        settings = get_settings()
        if (
            settings.is_production()
            or request.url.scheme == "https"
            or request.headers.get("X-Forwarded-Proto") == "https"
        ):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Injects and propagates request correlation IDs for end-to-end auditability."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # Attach rate limit headers if set on request state
        if hasattr(request.state, "rate_limit_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
        if hasattr(request.state, "rate_limit_remaining"):
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)

        return response

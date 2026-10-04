"""FastAPI security dependencies for authentication, authorization, and rate limiting.

Phase 14.3: Security, Access Control & Secrets.
Provides server-side role-based access control, token extraction, and rate limit enforcement.
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, Depends, status
from fastapi.security.utils import get_authorization_scheme_param

from nivesh.config import get_settings
from nivesh.security.models import AuthenticatedUser, UserRole
from nivesh.security.tokens import (
    decode_access_token,
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError,
    MalformedTokenError,
)
from nivesh.security.api_keys import validate_api_key
from nivesh.security.rate_limiter import rate_limiter
from nivesh.security.audit import log_security_event


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request, safely validating proxy trust boundary."""
    client_host = request.client.host if request.client else "127.0.0.1"
    forwarded = request.headers.get("X-Forwarded-For")
    if not forwarded:
        return client_host

    # Validate proxy trust boundary against configured settings
    settings = get_settings()
    allow_ips = getattr(settings, "forwarded_allow_ips", "*")
    if allow_ips and allow_ips.strip() != "*":
        trusted_ips = {ip.strip() for ip in allow_ips.split(",") if ip.strip()}
        if client_host not in trusted_ips:
            # Immediate peer is not a trusted reverse proxy; reject spoofed X-Forwarded-For
            return client_host

    # Trusted proxy: extract leftmost original client IP
    return forwarded.split(",")[0].strip()


def get_optional_user(request: Request) -> Optional[AuthenticatedUser]:
    """Extract and validate authentication from request if present; returns None if omitted.

    Raises 401 if authentication headers are present but invalid or expired.
    """
    auth_header = request.headers.get("Authorization")
    api_key_header = request.headers.get("X-API-Key")

    # 1. Check X-API-Key header
    if api_key_header:
        user = validate_api_key(api_key_header)
        if user:
            return user
        log_security_event(
            action="AUTH_FAILURE",
            actor="unknown",
            ip_address=get_client_ip(request),
            status="DENIED",
            reason_code="INVALID_API_KEY",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 2. Check Authorization header
    if auth_header:
        scheme, param = get_authorization_scheme_param(auth_header)
        if not scheme or not param:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed Authorization header.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if scheme.lower() == "bearer":
            try:
                return decode_access_token(param)
            except TokenExpiredError:
                log_security_event(
                    action="AUTH_FAILURE",
                    actor="unknown",
                    ip_address=get_client_ip(request),
                    status="DENIED",
                    reason_code="TOKEN_EXPIRED",
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired.",
                    headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"token_expired\""},
                )
            except (InvalidTokenError, MalformedTokenError, AuthenticationError) as e:
                log_security_event(
                    action="AUTH_FAILURE",
                    actor="unknown",
                    ip_address=get_client_ip(request),
                    status="DENIED",
                    reason_code="INVALID_TOKEN",
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or malformed authentication token.",
                    headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
                ) from e
        elif scheme.lower() == "apikey":
            user = validate_api_key(param)
            if user:
                return user
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unauthorized API key.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported authorization scheme '{scheme}'.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return None


def get_current_user(request: Request) -> AuthenticatedUser:
    """Strict authentication dependency: requires valid Bearer token or API key.

    Raises 401 if missing, invalid, or expired.
    """
    user = get_optional_user(request)
    if not user:
        log_security_event(
            action="UNAUTHENTICATED_ACCESS_ATTEMPT",
            actor="anonymous",
            target_entity=str(request.url.path),
            ip_address=get_client_ip(request),
            status="DENIED",
            reason_code="MISSING_CREDENTIALS",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer token or API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


require_auth = get_current_user


def require_role(required_role: UserRole) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory checking that the authenticated user possesses the required role."""

    def role_dependency(
        request: Request,
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not user.has_role(required_role) and not user.is_admin():
            log_security_event(
                action="AUTHORIZATION_FAILURE",
                actor=user.user_id,
                target_entity=str(request.url.path),
                ip_address=get_client_ip(request),
                status="DENIED",
                reason_code=f"MISSING_ROLE_{required_role.value.upper()}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Principal lacks required '{required_role.value}' role.",
            )
        return user

    return role_dependency


# Predefined role dependencies
require_admin = require_role(UserRole.ADMIN)
require_analyst = require_role(UserRole.ANALYST)
require_service = require_role(UserRole.SERVICE)


def enforce_rate_limit(
    request: Request,
    user: Optional[AuthenticatedUser] = Depends(get_optional_user),
) -> None:
    """Enforce rate limits per authenticated principal or client IP address."""
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    # Use authenticated user_id if present; fallback to client IP
    client_id = f"user:{user.user_id}" if user else f"ip:{get_client_ip(request)}"
    limit = settings.rate_limit_requests_per_minute

    is_allowed, remaining, retry_after = rate_limiter.is_allowed(
        client_id=client_id,
        limit=limit,
        window_seconds=60,
    )

    # Attach rate limit info to request state
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = limit

    if not is_allowed:
        log_security_event(
            action="RATE_LIMIT_EXCEEDED",
            actor=user.user_id if user else "anonymous",
            target_entity=str(request.url.path),
            ip_address=get_client_ip(request),
            status="DENIED",
            reason_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

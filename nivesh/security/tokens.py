"""Cryptographic Bearer Token Management for Nivesh Firewall.

Phase 14.3: Security, Access Control & Secrets.
Provides HMAC-SHA256 (HS256) JWT-compatible token generation and verification
using only standard library primitives (zero third-party dependencies).
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Union, List

from nivesh.config import get_settings
from nivesh.security.models import AuthenticatedUser, TokenPayload, UserRole


class AuthenticationError(Exception):
    """Base error for authentication failures."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when a token signature is invalid or tampered with."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""
    pass


class MalformedTokenError(AuthenticationError):
    """Raised when a token string cannot be decoded or parsed."""
    pass


def _base64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data_str: str) -> bytes:
    """Decode URL-safe base64 string with appropriate padding."""
    rem = len(data_str) % 4
    if rem > 0:
        data_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data_str.encode("ascii"))


def create_access_token(
    user_id: str,
    organization_id: Optional[str] = None,
    roles: Optional[List[Union[UserRole, str]]] = None,
    session_id: Optional[str] = None,
    expires_in_seconds: Optional[int] = None,
    secret_key: Optional[str] = None,
) -> str:
    """Generate a signed HMAC-SHA256 (HS256) JWT access token."""
    settings = get_settings()
    key = (secret_key or settings.get_secret_key()).encode("utf-8")
    ttl = expires_in_seconds if expires_in_seconds is not None else settings.auth_token_expire_seconds

    now = int(time.time())
    exp = now + ttl
    jti = f"JTI-{secrets.token_hex(12).upper()}"

    role_strings = [
        r.value if isinstance(r, UserRole) else str(r).lower()
        for r in (roles or [UserRole.USER])
    ]

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "org_id": organization_id,
        "roles": role_strings,
        "session_id": session_id,
        "iat": now,
        "exp": exp,
        "jti": jti,
    }

    hdr_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    hdr_b64 = _base64url_encode(hdr_bytes)
    payload_b64 = _base64url_encode(payload_bytes)

    signing_input = f"{hdr_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(key, signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(sig)

    return f"{hdr_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(
    token_str: str,
    secret_key: Optional[str] = None,
) -> AuthenticatedUser:
    """Validate and decode a signed JWT access token.

    Verifies format, HMAC-SHA256 signature, and token expiration.
    """
    if not token_str or not isinstance(token_str, str):
        raise MalformedTokenError("Missing or empty token string.")

    parts = token_str.strip().split(".")
    if len(parts) != 3:
        raise MalformedTokenError("Invalid token format; expected 3 segments separated by dots.")

    hdr_b64, payload_b64, sig_b64 = parts

    # 1. Decode header
    try:
        hdr_bytes = _base64url_decode(hdr_b64)
        header = json.loads(hdr_bytes.decode("utf-8"))
        if header.get("alg") != "HS256":
            raise InvalidTokenError(f"Unsupported algorithm '{header.get('alg')}'; expected HS256.")
    except Exception as e:
        if isinstance(e, (InvalidTokenError, TokenExpiredError)):
            raise
        raise MalformedTokenError("Failed to decode token header.") from e

    # 2. Verify signature
    settings = get_settings()
    key = (secret_key or settings.get_secret_key()).encode("utf-8")
    signing_input = f"{hdr_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(key, signing_input, hashlib.sha256).digest()

    try:
        provided_sig = _base64url_decode(sig_b64)
    except Exception as e:
        raise MalformedTokenError("Failed to decode token signature.") from e

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise InvalidTokenError("Invalid token signature; token may have been tampered with.")

    # 3. Decode and validate payload
    try:
        payload_bytes = _base64url_decode(payload_b64)
        claims = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise MalformedTokenError("Failed to decode token payload.") from e

    now = int(time.time())
    exp = claims.get("exp")
    if exp is not None and now > exp:
        raise TokenExpiredError(f"Token has expired at {exp} (current time: {now}).")

    user_id = claims.get("sub")
    if not user_id:
        raise MalformedTokenError("Token payload missing subject ('sub') claim.")

    raw_roles = claims.get("roles", [])
    roles = []
    for r in raw_roles:
        try:
            roles.append(UserRole(r))
        except ValueError:
            roles.append(UserRole.USER)

    return AuthenticatedUser(
        user_id=str(user_id),
        organization_id=claims.get("org_id"),
        roles=roles,
        session_id=claims.get("session_id"),
        is_service="service" in raw_roles,
        auth_method="bearer_token",
    )

"""API Key authentication for administrative and service principals.

Phase 14.3: Security, Access Control & Secrets.
Provides timing-safe API key validation against configured administrative and service keys.
"""

import secrets
from typing import Optional

from nivesh.config import get_settings
from nivesh.security.models import AuthenticatedUser, UserRole


def validate_api_key(api_key: str) -> Optional[AuthenticatedUser]:
    """Validate an API key using constant-time comparison.

    Returns AuthenticatedUser with appropriate role if matched, else None.
    """
    if not api_key or not isinstance(api_key, str):
        return None

    clean_key = api_key.strip()
    settings = get_settings()

    # 1. Admin API key check
    if settings.admin_api_key and settings.admin_api_key.strip():
        if secrets.compare_digest(clean_key, settings.admin_api_key.strip()):
            return AuthenticatedUser(
                user_id="admin-api-key-principal",
                organization_id="system-admin",
                roles=[UserRole.ADMIN, UserRole.ANALYST, UserRole.USER],
                is_service=False,
                auth_method="api_key",
            )

    # 2. Internal Service API key check
    if settings.service_api_key and settings.service_api_key.strip():
        if secrets.compare_digest(clean_key, settings.service_api_key.strip()):
            return AuthenticatedUser(
                user_id="service-api-key-principal",
                organization_id="system-internal",
                roles=[UserRole.SERVICE, UserRole.USER],
                is_service=True,
                auth_method="api_key",
            )

    return None

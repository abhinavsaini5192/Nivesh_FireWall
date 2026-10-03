"""Security domain models and user authorization representations.

Phase 14.3: Security, Access Control & Secrets.
Defines user roles, authenticated principal models, and authorization checks.
"""

from enum import Enum
from typing import Optional, Union, List
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """System authorization roles for Nivesh Firewall."""
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"
    SERVICE = "service"
    ANONYMOUS = "anonymous"


class AuthenticatedUser(BaseModel):
    """Authenticated principal with authorization roles and organization scope."""

    user_id: str
    organization_id: Optional[str] = None
    roles: List[UserRole] = Field(default_factory=list)
    session_id: Optional[str] = None
    is_service: bool = False
    auth_method: str = "token"

    def has_role(self, role: Union[UserRole, str]) -> bool:
        """Check if user has the specified role."""
        target = role.value if isinstance(role, UserRole) else str(role).lower()
        return any(
            (r.value if isinstance(r, UserRole) else str(r)).lower() == target
            for r in self.roles
        )

    def is_admin(self) -> bool:
        """Check if principal has administrator privileges."""
        return self.has_role(UserRole.ADMIN)

    def is_analyst(self) -> bool:
        """Check if principal has analyst privileges."""
        return self.is_admin() or self.has_role(UserRole.ANALYST)

    def is_service_actor(self) -> bool:
        """Check if principal is an internal service actor."""
        return self.is_service or self.has_role(UserRole.SERVICE)

    def can_access_analysis(
        self,
        analysis_user_id: Optional[str],
        analysis_org_id: Optional[str],
    ) -> bool:
        """Check if this principal has permission to view or access an analysis record.

        Enforces strict server-side authorization:
        1. Administrators can access all analyses.
        2. Analysts can access analyses within their organization (or unassigned).
        3. Users can only access analyses they explicitly created (user_id match)
           or analyses belonging to their organization.
        4. Cross-user and cross-organization access is strictly forbidden.
        """
        # Admin privilege: full visibility
        if self.is_admin():
            return True

        # User ownership match
        if analysis_user_id and analysis_user_id == self.user_id:
            return True

        # Organization membership match
        if (
            self.organization_id
            and analysis_org_id
            and self.organization_id == analysis_org_id
        ):
            return True

        # Analyst in same org or reviewing unassigned org
        if self.is_analyst():
            if not analysis_org_id or (self.organization_id and self.organization_id == analysis_org_id):
                return True

        return False


class TokenPayload(BaseModel):
    """Standardized JWT claims payload structure."""

    sub: str  # user_id
    org_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    iat: int
    exp: int
    jti: str

"""FastAPI dependencies for authentication and authorization.

Provides dependencies for:
- Getting the current user from JWT token
- Role-based access control
- Tenant isolation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

# Try to import FastAPI components
try:
    from fastapi import HTTPException as FastAPIHTTPException
    from fastapi import status as fastapi_status
    from fastapi.security import HTTPBearer

    _security = HTTPBearer(auto_error=False)
    _FASTAPI_AVAILABLE = True
    # Use FastAPI types for runtime
    HTTPException = FastAPIHTTPException
    status = fastapi_status
except ImportError:
    _FASTAPI_AVAILABLE = False

    # Fallback HTTPException for testing without FastAPI
    class _FallbackHTTPException(Exception):
        """Fallback HTTPException when FastAPI is not available."""

        def __init__(self, status_code: int, detail: Any = None) -> None:
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")

    # Module-level names for runtime use
    HTTPException = _FallbackHTTPException

    class _FallbackStatus:
        """Fallback status codes when FastAPI is not available."""

        HTTP_401_UNAUTHORIZED: int = 401
        HTTP_403_FORBIDDEN: int = 403
        HTTP_404_NOT_FOUND: int = 404
        HTTP_422_UNPROCESSABLE_ENTITY: int = 422
        HTTP_500_INTERNAL_SERVER_ERROR: int = 500

    status = _FallbackStatus()

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    from fastapi import HTTPException
    from fastapi import status


@dataclass
class MockUser:
    """Mock user for testing without FastAPI."""

    id: str = "test-user"
    email: str = "test@example.com"
    tenant_id: str = "default-tenant"
    role: str = "user"
    is_active: bool = True
    is_superuser: bool = False


def get_current_user(
    credentials: Any = None,
) -> Any:
    """Get the current user from JWT token.

    This is a placeholder implementation.
    In production, it would:
    1. Extract JWT from Authorization header
    2. Validate and decode the token
    3. Look up user from database
    4. Return user object

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not _FASTAPI_AVAILABLE:
        # Return mock user for testing
        return MockUser()

    # Placeholder: In production, implement full JWT validation
    return MockUser()


def get_current_active_user(
    current_user: Any = None,
) -> Any:
    """Get the current active user.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not _FASTAPI_AVAILABLE:
        return MockUser()

    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")  # type: ignore[misc]

    return current_user


class RoleChecker:
    """Dependency for checking user roles.

    Example:
        >>> require_admin = RoleChecker(["admin"])
        >>> @app.delete("/users/{id}", dependencies=[Depends(require_admin)])
        ... async def delete_user(id: str): ...
    """

    def __init__(self, allowed_roles: list[str]):
        """Initialize with allowed roles.

        Args:
            allowed_roles: List of role names that are allowed
        """
        self.allowed_roles = allowed_roles

    def __call__(self, user: Any = None) -> Any:
        """Check if user has required role.

        Args:
            user: Current user

        Returns:
            User if authorized

        Raises:
            HTTPException: If user lacks required role
        """
        if not _FASTAPI_AVAILABLE:
            return MockUser()

        user_role = getattr(user, "role", "viewer")
        if isinstance(user_role, str):
            role_value = user_role
        else:
            role_value = user_role.value if hasattr(user_role, "value") else str(user_role)

        if role_value not in self.allowed_roles:
            raise HTTPException(  # type: ignore[misc]
                status_code=status.HTTP_403_FORBIDDEN,  # type: ignore[misc]
                detail=f"Operation not permitted. Required role: {self.allowed_roles}",
            )

        return user


class PermissionChecker:
    """Dependency for checking specific permissions.

    Example:
        >>> require_write = PermissionChecker("indexes:write")
        >>> @app.post("/indexes", dependencies=[Depends(require_write)])
        ... async def create_index(): ...
    """

    def __init__(self, permission: str):
        """Initialize with required permission.

        Args:
            permission: Permission string (e.g., "indexes:write")
        """
        self.permission = permission

    def __call__(self, user: Any = None) -> Any:
        """Check if user has required permission.

        Args:
            user: Current user

        Returns:
            User if authorized

        Raises:
            HTTPException: If user lacks required permission
        """
        if not _FASTAPI_AVAILABLE:
            return MockUser()

        # Superuser has all permissions
        if hasattr(user, "is_superuser") and user.is_superuser:
            return user

        # Check role permissions
        if hasattr(user, "has_permission"):
            if user.has_permission(self.permission):
                return user

        raise HTTPException(  # type: ignore[misc]
            status_code=status.HTTP_403_FORBIDDEN,  # type: ignore[misc]
            detail=f"Permission denied: {self.permission}",
        )


def get_tenant_id(user: Any = None) -> str:
    """Get tenant ID from user context.

    Used for multi-tenant data isolation.

    Args:
        user: Current user

    Returns:
        Tenant ID string
    """
    if user is not None and hasattr(user, "tenant_id"):
        tenant_id = user.tenant_id
        if isinstance(tenant_id, str):
            return tenant_id
        return str(tenant_id)
    return "default-tenant"


def is_fastapi_available() -> bool:
    """Check if FastAPI is available."""
    return _FASTAPI_AVAILABLE


# Convenience exports for FastAPI
require_admin = RoleChecker(["admin"])
require_manager = RoleChecker(["admin", "manager"])
require_user = RoleChecker(["admin", "manager", "user"])
require_viewer = RoleChecker(["admin", "manager", "user", "viewer"])
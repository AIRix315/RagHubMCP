"""FastAPI dependencies for authentication and authorization.

Provides dependencies for:
- Getting the current user from JWT token
- Role-based access control
- Tenant isolation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Try to import FastAPI components
_FASTAPI_AVAILABLE = False
try:
    from fastapi import HTTPException, status
    from fastapi.security import HTTPBearer

    _security = HTTPBearer(auto_error=False)
    _FASTAPI_AVAILABLE = True
except (ImportError, NameError):
    pass


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
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

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {self.permission}"
        )


def get_tenant_id(user: Any = None) -> str:
    """Get tenant ID from user context.

    Used for multi-tenant data isolation.

    Args:
        user: Current user

    Returns:
        Tenant ID string
    """
    if user and hasattr(user, "tenant_id"):
        return user.tenant_id
    return "default-tenant"


def is_fastapi_available() -> bool:
    """Check if FastAPI is available."""
    return _FASTAPI_AVAILABLE


# Convenience exports for FastAPI
if _FASTAPI_AVAILABLE:
    require_admin = RoleChecker(["admin"])
    require_manager = RoleChecker(["admin", "manager"])
    require_user = RoleChecker(["admin", "manager", "user"])
    require_viewer = RoleChecker(["admin", "manager", "user", "viewer"])
else:
    # Create dummy objects for import
    require_admin = RoleChecker(["admin"])
    require_manager = RoleChecker(["admin", "manager"])
    require_user = RoleChecker(["admin", "manager", "user"])
    require_viewer = RoleChecker(["admin", "manager", "user", "viewer"])

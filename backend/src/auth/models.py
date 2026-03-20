"""User, Role, and Tenant models for authentication.

Implements multi-tenant user management with RBAC.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


def _utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class Role(str, Enum):
    """User roles for RBAC."""
    
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"
    
    def get_permissions(self) -> set[str]:
        """Get permissions for this role."""
        permissions_map = {
            Role.ADMIN: {
                "indexes:read", "indexes:write", "indexes:delete",
                "collections:read", "collections:write", "collections:delete",
                "users:read", "users:write", "users:delete",
                "settings:read", "settings:write",
                "tenants:read", "tenants:write",
            },
            Role.MANAGER: {
                "indexes:read", "indexes:write", "indexes:delete",
                "collections:read", "collections:write", "collections:delete",
                "users:read", "users:write",
                "settings:read",
            },
            Role.USER: {
                "indexes:read", "indexes:write",
                "collections:read", "collections:write",
                "settings:read",
            },
            Role.VIEWER: {
                "indexes:read",
                "collections:read",
                "settings:read",
            },
        }
        return permissions_map.get(self, set())


@dataclass
class Tenant:
    """Represents a tenant (organization/workspace).
    
    Attributes:
        id: Unique tenant identifier
        name: Display name
        slug: URL-friendly identifier
        plan: Subscription plan (free, pro, enterprise)
        is_active: Whether tenant is active
        created_at: Creation timestamp
        metadata: Additional metadata
    """
    id: str
    name: str
    slug: str
    plan: str = "free"
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, name: str, slug: str, plan: str = "free") -> "Tenant":
        """Create a new tenant.
        
        Args:
            name: Display name
            slug: URL-friendly identifier
            plan: Subscription plan
            
        Returns:
            New Tenant instance
        """
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            plan=plan,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "plan": self.plan,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class User:
    """Represents a user in the system.
    
    Attributes:
        id: Unique user identifier
        email: User email address
        hashed_password: Bcrypt hashed password
        tenant_id: Tenant this user belongs to
        role: User role for RBAC
        is_active: Whether user account is active
        is_superuser: Whether user has superuser privileges
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        metadata: Additional metadata
    """
    id: str
    email: str
    hashed_password: str
    tenant_id: str
    role: Role = Role.USER
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        email: str,
        password: str,
        tenant_id: str,
        role: Role = Role.USER,
    ) -> "User":
        """Create a new user with hashed password.
        
        Args:
            email: User email address
            password: Plain text password (will be hashed)
            tenant_id: Tenant ID
            role: User role
            
        Returns:
            New User instance with hashed password
        """
        from src.auth.security import hash_password
        
        return cls(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hash_password(password),
            tenant_id=tenant_id,
            role=role,
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission.
        
        Args:
            permission: Permission string (e.g., "indexes:write")
            
        Returns:
            True if user has permission
        """
        if self.is_superuser:
            return True
        return permission in self.role.get_permissions()
    
    def check_permission(self, permission: str) -> None:
        """Check permission and raise exception if not allowed.
        
        Args:
            permission: Permission string
            
        Raises:
            PermissionError: If user lacks permission
        """
        if not self.has_permission(permission):
            raise PermissionError(
                f"User {self.email} lacks permission: {permission}"
            )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (without sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "tenant_id": self.tenant_id,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict())


@dataclass
class TokenPayload:
    """JWT token payload data.
    
    Attributes:
        sub: Subject (user ID)
        email: User email
        tenant_id: Tenant ID
        role: User role
        exp: Expiration timestamp
        iat: Issued at timestamp
    """
    sub: str
    email: str
    tenant_id: str
    role: str
    exp: datetime
    iat: datetime = field(default_factory=_utc_now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            "sub": self.sub,
            "email": self.email,
            "tenant_id": self.tenant_id,
            "role": self.role,
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
        }


@dataclass
class Token:
    """Authentication token response.
    
    Attributes:
        access_token: JWT access token
        token_type: Token type (always "bearer")
        expires_in: Seconds until expiration
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }
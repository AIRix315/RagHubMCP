"""Authentication and authorization module.

This module provides:
- JWT-based authentication
- User models and management
- Role-Based Access Control (RBAC)
- Tenant isolation for multi-user support
"""

from raghub_mcp.auth.dependencies import get_current_active_user, get_current_user
from raghub_mcp.auth.models import Role, Tenant, User
from raghub_mcp.auth.security import create_access_token, hash_password, verify_password

__all__ = [
    "User",
    "Role",
    "Tenant",
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_current_user",
    "get_current_active_user",
]

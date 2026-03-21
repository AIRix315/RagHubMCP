"""Authentication and authorization module.

This module provides:
- JWT-based authentication
- User models and management
- Role-Based Access Control (RBAC)
- Tenant isolation for multi-user support
"""

from src.auth.dependencies import get_current_active_user, get_current_user
from src.auth.models import Role, Tenant, User
from src.auth.security import create_access_token, hash_password, verify_password

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

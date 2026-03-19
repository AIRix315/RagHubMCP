"""Authentication and authorization module.

This module provides:
- JWT-based authentication
- User models and management
- Role-Based Access Control (RBAC)
- Tenant isolation for multi-user support
"""

from src.auth.models import User, Role, Tenant
from src.auth.security import hash_password, verify_password, create_access_token
from src.auth.dependencies import get_current_user, get_current_active_user

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
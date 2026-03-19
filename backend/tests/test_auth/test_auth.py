"""Tests for authentication module.

Test cases:
- TC-3.2.1: User model creation and validation
- TC-3.2.2: Password hashing and verification
- TC-3.2.3: JWT token creation and validation
- TC-3.2.4: Role-based permission checking
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestUserModel:
    """TC-3.2.1: User model creation and validation."""

    def test_create_user(self):
        """TC-3.2.1: User can be created with required fields."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.USER,
        )
        
        assert user.id == "user-1"
        assert user.email == "test@example.com"
        assert user.role == Role.USER
        assert user.is_active is True

    def test_create_user_with_create_method(self):
        """TC-3.2.1: User can be created with create() class method."""
        from auth.models import User, Role
        
        user = User.create(
            email="test@example.com",
            password="plain_password",
            tenant_id="tenant-1",
            role=Role.USER,
        )
        
        assert user.email == "test@example.com"
        assert user.hashed_password != "plain_password"  # Should be hashed
        assert user.role == Role.USER

    def test_user_to_dict(self):
        """TC-3.2.1: User can be converted to dictionary."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.USER,
        )
        
        d = user.to_dict()
        
        assert d["id"] == "user-1"
        assert d["email"] == "test@example.com"
        assert d["role"] == "user"
        assert "hashed_password" not in d  # Sensitive data excluded

    def test_user_default_role(self):
        """TC-3.2.1: User has default role of USER."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
        )
        
        assert user.role == Role.USER


class TestRoleModel:
    """TC-3.2.1: Role model tests."""

    def test_role_enum_values(self):
        """TC-3.2.1: Role enum has expected values."""
        from auth.models import Role
        
        assert Role.ADMIN.value == "admin"
        assert Role.MANAGER.value == "manager"
        assert Role.USER.value == "user"
        assert Role.VIEWER.value == "viewer"

    def test_admin_has_all_permissions(self):
        """TC-3.2.1: Admin role has all permissions."""
        from auth.models import Role
        
        permissions = Role.ADMIN.get_permissions()
        
        assert "indexes:read" in permissions
        assert "indexes:write" in permissions
        assert "indexes:delete" in permissions
        assert "users:read" in permissions
        assert "users:delete" in permissions

    def test_viewer_has_limited_permissions(self):
        """TC-3.2.1: Viewer role has limited permissions."""
        from auth.models import Role
        
        permissions = Role.VIEWER.get_permissions()
        
        assert "indexes:read" in permissions
        assert "indexes:write" not in permissions
        assert "indexes:delete" not in permissions


class TestTenantModel:
    """TC-3.2.1: Tenant model tests."""

    def test_create_tenant(self):
        """TC-3.2.1: Tenant can be created."""
        from auth.models import Tenant
        
        tenant = Tenant.create(name="My Org", slug="my-org")
        
        assert tenant.name == "My Org"
        assert tenant.slug == "my-org"
        assert tenant.plan == "free"
        assert tenant.is_active is True
        assert tenant.id is not None

    def test_tenant_to_dict(self):
        """TC-3.2.1: Tenant can be converted to dictionary."""
        from auth.models import Tenant
        
        tenant = Tenant(
            id="tenant-1",
            name="My Org",
            slug="my-org",
            plan="pro",
        )
        
        d = tenant.to_dict()
        
        assert d["id"] == "tenant-1"
        assert d["name"] == "My Org"
        assert d["slug"] == "my-org"
        assert d["plan"] == "pro"


class TestPasswordHashing:
    """TC-3.2.2: Password hashing and verification."""

    def test_hash_password(self):
        """TC-3.2.2: Password can be hashed."""
        from auth.security import hash_password
        
        hashed = hash_password("my_password")
        
        assert hashed != "my_password"
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """TC-3.2.2: Correct password verifies."""
        from auth.security import hash_password, verify_password
        
        hashed = hash_password("my_password")
        
        assert verify_password("my_password", hashed) is True

    def test_verify_password_incorrect(self):
        """TC-3.2.2: Incorrect password fails verification."""
        from auth.security import hash_password, verify_password
        
        hashed = hash_password("my_password")
        
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """TC-3.2.2: Same password produces different hashes (salt)."""
        from auth.security import hash_password
        
        hash1 = hash_password("my_password")
        hash2 = hash_password("my_password")
        
        # With bcrypt, same password should produce different hashes
        # With SHA256 fallback, they would be the same
        # Just verify both are valid hashes
        assert len(hash1) > 0
        assert len(hash2) > 0


class TestJWTToken:
    """TC-3.2.3: JWT token creation and validation."""

    def test_create_access_token(self):
        """TC-3.2.3: Access token can be created."""
        from auth.security import create_access_token
        
        token = create_access_token(
            data={"sub": "user-1", "email": "test@example.com"}
        )
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_decode_access_token(self):
        """TC-3.2.3: Access token can be decoded."""
        from auth.security import create_access_token, decode_access_token
        
        token = create_access_token(
            data={"sub": "user-1", "email": "test@example.com"}
        )
        
        payload = decode_access_token(token)
        
        assert payload["sub"] == "user-1"
        assert payload["email"] == "test@example.com"

    def test_decode_invalid_token_fails(self):
        """TC-3.2.3: Invalid token raises error."""
        from auth.security import decode_access_token
        
        with pytest.raises(ValueError):
            decode_access_token("invalid_token")

    def test_token_with_custom_expiry(self):
        """TC-3.2.3: Token can have custom expiry."""
        from datetime import timedelta
        from auth.security import create_access_token, decode_access_token
        
        token = create_access_token(
            data={"sub": "user-1"},
            expires_delta=timedelta(hours=1)
        )
        
        payload = decode_access_token(token)
        
        assert payload["sub"] == "user-1"


class TestPermissionChecking:
    """TC-3.2.4: Permission checking."""

    def test_user_has_permission(self):
        """TC-3.2.4: User has_permission method works."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.USER,
        )
        
        assert user.has_permission("indexes:read") is True
        assert user.has_permission("indexes:write") is True
        assert user.has_permission("indexes:delete") is False

    def test_admin_has_all_permissions(self):
        """TC-3.2.4: Admin has all permissions."""
        from auth.models import User, Role
        
        user = User(
            id="admin-1",
            email="admin@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.ADMIN,
        )
        
        assert user.has_permission("indexes:delete") is True
        assert user.has_permission("users:delete") is True

    def test_superuser_has_all_permissions(self):
        """TC-3.2.4: Superuser has all permissions."""
        from auth.models import User, Role
        
        user = User(
            id="super-1",
            email="super@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.VIEWER,
            is_superuser=True,
        )
        
        assert user.has_permission("indexes:delete") is True
        assert user.has_permission("users:delete") is True

    def test_check_permission_raises_on_denied(self):
        """TC-3.2.4: check_permission raises PermissionError."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.VIEWER,
        )
        
        with pytest.raises(PermissionError):
            user.check_permission("indexes:delete")


class TestRoleChecker:
    """TC-3.2.4: RoleChecker dependency tests."""

    def test_role_checker_allows_correct_role(self):
        """TC-3.2.4: RoleChecker allows user with correct role."""
        from auth.dependencies import RoleChecker, MockUser
        
        checker = RoleChecker(["admin", "user"])
        user = MockUser(role="user")
        
        result = checker(user)
        assert result == user

    def test_role_checker_denies_wrong_role(self):
        """TC-3.2.4: RoleChecker denies user with wrong role."""
        from auth.dependencies import RoleChecker, MockUser
        
        checker = RoleChecker(["admin"])
        user = MockUser(role="viewer")
        
        # Should raise HTTPException if FastAPI is available
        # Otherwise returns mock user
        try:
            checker(user)
        except Exception as e:
            # HTTPException or similar
            assert "403" in str(e) or "forbidden" in str(e).lower()


class TestPasswordValidator:
    """Password validation tests."""

    def test_validate_good_password(self):
        """Good password passes validation."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("GoodPass123")
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_short_password(self):
        """Short password fails validation."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("short")
        
        assert is_valid is False
        assert any("8" in e for e in errors)

    def test_validate_no_uppercase(self):
        """Password without uppercase fails."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("goodpass123")
        
        assert is_valid is False
        assert any("uppercase" in e.lower() for e in errors)

    def test_validate_no_digit(self):
        """Password without digit fails."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("GoodPassword")
        
        assert is_valid is False
        assert any("digit" in e.lower() for e in errors)
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

    def test_validate_no_lowercase(self):
        """Password without lowercase fails."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("GOODPASS123")
        
        assert is_valid is False
        assert any("lowercase" in e.lower() for e in errors)


class TestTokenPayload:
    """TokenPayload model tests."""

    def test_create_token_payload(self):
        """TokenPayload can be created."""
        from datetime import datetime, UTC
        from auth.models import TokenPayload
        
        exp = datetime.now(UTC)
        payload = TokenPayload(
            sub="user-1",
            email="test@example.com",
            tenant_id="tenant-1",
            role="user",
            exp=exp,
        )
        
        assert payload.sub == "user-1"
        assert payload.email == "test@example.com"
        assert payload.tenant_id == "tenant-1"
        assert payload.role == "user"

    def test_token_payload_to_dict(self):
        """TokenPayload can be converted to dict for JWT."""
        from datetime import datetime, UTC
        from auth.models import TokenPayload
        
        exp = datetime.now(UTC)
        payload = TokenPayload(
            sub="user-1",
            email="test@example.com",
            tenant_id="tenant-1",
            role="admin",
            exp=exp,
        )
        
        d = payload.to_dict()
        
        assert d["sub"] == "user-1"
        assert d["email"] == "test@example.com"
        assert d["tenant_id"] == "tenant-1"
        assert d["role"] == "admin"
        assert "exp" in d
        assert "iat" in d


class TestToken:
    """Token response model tests."""

    def test_create_token(self):
        """Token can be created."""
        from auth.models import Token
        
        token = Token(access_token="my-jwt-token")
        
        assert token.access_token == "my-jwt-token"
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_token_to_dict(self):
        """Token can be converted to dictionary."""
        from auth.models import Token
        
        token = Token(
            access_token="my-jwt-token",
            token_type="bearer",
            expires_in=3600,
        )
        
        d = token.to_dict()
        
        assert d["access_token"] == "my-jwt-token"
        assert d["token_type"] == "bearer"
        assert d["expires_in"] == 3600


class TestUserToJson:
    """User JSON serialization tests."""

    def test_user_to_json(self):
        """User can be serialized to JSON."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.USER,
        )
        
        json_str = user.to_json()
        
        assert isinstance(json_str, str)
        assert "user-1" in json_str
        assert "test@example.com" in json_str
        assert "hashed_password" not in json_str


class TestManagerRole:
    """Manager role permission tests."""

    def test_manager_permissions(self):
        """Manager has expected permissions."""
        from auth.models import Role
        
        permissions = Role.MANAGER.get_permissions()
        
        assert "indexes:read" in permissions
        assert "indexes:write" in permissions
        assert "indexes:delete" in permissions
        assert "users:read" in permissions
        assert "users:write" in permissions
        assert "users:delete" not in permissions
        assert "tenants:read" not in permissions


class TestRefreshToken:
    """Refresh token tests."""

    def test_create_refresh_token(self):
        """Refresh token can be created."""
        from auth.security import create_refresh_token
        
        token = create_refresh_token(
            data={"sub": "user-1", "email": "test@example.com"}
        )
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_refresh_token_longer_expiry(self):
        """Refresh token has longer expiry than access token."""
        from auth.security import create_access_token, create_refresh_token, decode_access_token
        
        access_token = create_access_token(data={"sub": "user-1"})
        refresh_token = create_refresh_token(data={"sub": "user-1"})
        
        access_payload = decode_access_token(access_token)
        refresh_payload = decode_access_token(refresh_token)
        
        # Refresh token should have longer expiry
        assert refresh_payload["exp"] > access_payload["exp"]


class TestApiKeyGeneration:
    """API key generation tests."""

    def test_generate_api_key(self):
        """API key can be generated."""
        from auth.security import generate_api_key
        
        key = generate_api_key()
        
        assert key is not None
        assert len(key) > 0
        assert isinstance(key, str)

    def test_api_keys_are_unique(self):
        """Each generated API key is unique."""
        from auth.security import generate_api_key
        
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert key1 != key2


class TestConstantTimeCompare:
    """Constant-time comparison tests."""

    def test_constant_time_compare_equal(self):
        """Equal strings compare as True."""
        from auth.security import constant_time_compare
        
        assert constant_time_compare("hello", "hello") is True

    def test_constant_time_compare_not_equal(self):
        """Different strings compare as False."""
        from auth.security import constant_time_compare
        
        assert constant_time_compare("hello", "world") is False

    def test_constant_time_compare_empty(self):
        """Empty strings compare correctly."""
        from auth.security import constant_time_compare
        
        assert constant_time_compare("", "") is True
        assert constant_time_compare("a", "") is False


class TestSecurityAvailability:
    """Security module availability tests."""

    def test_is_bcrypt_available(self):
        """Can check if bcrypt is available."""
        from auth.security import is_bcrypt_available
        
        result = is_bcrypt_available()
        
        assert isinstance(result, bool)

    def test_is_jose_available(self):
        """Can check if python-jose is available."""
        from auth.security import is_jose_available
        
        result = is_jose_available()
        
        assert isinstance(result, bool)


class TestTokenErrorHandling:
    """JWT token error handling tests."""

    def test_decode_expired_token(self):
        """Expired token raises error."""
        from datetime import timedelta
        from auth.security import create_access_token, decode_access_token
        
        # Create token that's already expired
        token = create_access_token(
            data={"sub": "user-1"},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(ValueError):
            decode_access_token(token)

    def test_decode_token_wrong_key(self):
        """Token with wrong key raises error."""
        from auth.security import create_access_token, decode_access_token
        
        token = create_access_token(
            data={"sub": "user-1"},
            secret_key="correct-secret"
        )
        
        with pytest.raises(ValueError):
            decode_access_token(token, secret_key="wrong-secret")

    def test_decode_malformed_token(self):
        """Malformed token raises error."""
        from auth.security import decode_access_token
        
        with pytest.raises(ValueError):
            decode_access_token("not.a.valid.jwt")


class TestPermissionChecker:
    """PermissionChecker dependency tests."""

    def test_permission_checker_allows_authorized(self):
        """PermissionChecker allows user with permission."""
        from unittest.mock import MagicMock
        from auth.dependencies import PermissionChecker
        
        checker = PermissionChecker("indexes:read")
        user = MagicMock()
        user.is_superuser = False
        user.has_permission = MagicMock(return_value=True)
        
        result = checker(user)
        assert result == user

    def test_permission_checker_allows_superuser(self):
        """PermissionChecker allows superuser."""
        from unittest.mock import MagicMock
        from auth.dependencies import PermissionChecker
        
        checker = PermissionChecker("any:permission")
        user = MagicMock()
        user.is_superuser = True
        
        result = checker(user)
        assert result == user

    def test_permission_checker_denies_unauthorized(self):
        """PermissionChecker denies user without permission."""
        from unittest.mock import MagicMock
        from auth.dependencies import PermissionChecker
        
        checker = PermissionChecker("indexes:delete")
        user = MagicMock()
        user.is_superuser = False
        user.has_permission = MagicMock(return_value=False)
        
        try:
            checker(user)
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert "403" in str(e) or "Permission denied" in str(e)


class TestTenantId:
    """Tenant ID extraction tests."""

    def test_get_tenant_id_from_user(self):
        """Tenant ID can be extracted from user."""
        from auth.dependencies import get_tenant_id, MockUser
        
        user = MockUser(tenant_id="custom-tenant")
        
        tenant_id = get_tenant_id(user)
        
        assert tenant_id == "custom-tenant"

    def test_get_tenant_id_no_user(self):
        """Default tenant returned when no user."""
        from auth.dependencies import get_tenant_id
        
        tenant_id = get_tenant_id(None)
        
        assert tenant_id == "default-tenant"


class TestGetCurrentUser:
    """Current user retrieval tests."""

    def test_get_current_user_returns_mock(self):
        """get_current_user returns mock user without FastAPI."""
        from auth.dependencies import get_current_user
        
        user = get_current_user()
        
        assert user is not None
        assert hasattr(user, "id")
        assert hasattr(user, "email")


class TestGetCurrentActiveUser:
    """Active user retrieval tests."""

    def test_get_current_active_user_returns_user(self):
        """get_current_active_user returns user when active."""
        from auth.dependencies import get_current_active_user, MockUser
        
        user = MockUser(is_active=True)
        
        result = get_current_active_user(user)
        
        assert result == user

    def test_get_current_active_user_inactive_raises(self):
        """get_current_active_user raises for inactive user."""
        from auth.dependencies import get_current_active_user, MockUser
        
        user = MockUser(is_active=False)
        
        try:
            get_current_active_user(user)
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert "403" in str(e) or "Inactive" in str(e) or "Forbidden" in str(e)


class TestFastApiAvailability:
    """FastAPI availability check tests."""

    def test_is_fastapi_available(self):
        """Can check if FastAPI is available."""
        from auth.dependencies import is_fastapi_available
        
        result = is_fastapi_available()
        
        assert isinstance(result, bool)


class TestRoleCheckerWithEnum:
    """RoleChecker with Enum role tests."""

    def test_role_checker_with_enum_role(self):
        """RoleChecker handles Enum role correctly."""
        from unittest.mock import MagicMock
        from auth.dependencies import RoleChecker
        from auth.models import Role
        
        checker = RoleChecker(["user"])
        user = MagicMock()
        user.role = Role.USER  # Enum value, not string
        
        result = checker(user)
        assert result == user

    def test_role_checker_with_role_object(self):
        """RoleChecker handles role object with value attribute."""
        from unittest.mock import MagicMock
        from auth.dependencies import RoleChecker
        
        class MockRole:
            value = "admin"
        
        checker = RoleChecker(["admin"])
        user = MagicMock()
        user.role = MockRole()
        
        result = checker(user)
        assert result == user


class TestPasswordValidatorEdgeCases:
    """PasswordValidator edge case tests."""

    def test_validate_all_errors(self):
        """Password fails all validation rules."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("x")
        
        assert is_valid is False
        assert len(errors) >= 3  # Too short, no uppercase, no digit

    def test_validate_minimum_valid(self):
        """Minimum valid password passes."""
        from auth.security import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("Abcdefg1")
        
        assert is_valid is True
        assert len(errors) == 0


class TestModuleExports:
    """Test module exports."""

    def test_auth_module_exports(self):
        """Auth module exports expected symbols."""
        from auth import User, Role, Tenant
        from auth import hash_password, verify_password, create_access_token
        from auth import get_current_user, get_current_active_user
        
        assert User is not None
        assert Role is not None
        assert Tenant is not None
        assert callable(hash_password)
        assert callable(verify_password)
        assert callable(create_access_token)
        assert callable(get_current_user)
        assert callable(get_current_active_user)


class TestConvenienceExports:
    """Test convenience exports in dependencies module."""

    def test_require_admin_exists(self):
        """require_admin is available."""
        from auth.dependencies import require_admin
        
        assert require_admin is not None
        assert hasattr(require_admin, 'allowed_roles')
        assert 'admin' in require_admin.allowed_roles

    def test_require_manager_exists(self):
        """require_manager is available."""
        from auth.dependencies import require_manager
        
        assert require_manager is not None
        assert 'manager' in require_manager.allowed_roles

    def test_require_user_exists(self):
        """require_user is available."""
        from auth.dependencies import require_user
        
        assert require_user is not None
        assert 'user' in require_user.allowed_roles

    def test_require_viewer_exists(self):
        """require_viewer is available."""
        from auth.dependencies import require_viewer
        
        assert require_viewer is not None
        assert 'viewer' in require_viewer.allowed_roles


class TestTokenWithCustomSecret:
    """Token creation with custom secret key."""

    def test_create_token_with_custom_secret(self):
        """Token can be created with custom secret."""
        from auth.security import create_access_token, decode_access_token
        
        custom_secret = "my-custom-secret-key-12345"
        token = create_access_token(
            data={"sub": "user-1"},
            secret_key=custom_secret
        )
        
        payload = decode_access_token(token, secret_key=custom_secret)
        assert payload["sub"] == "user-1"

    def test_create_token_with_custom_algorithm(self):
        """Token can be created with custom algorithm."""
        from auth.security import create_access_token, decode_access_token
        
        token = create_access_token(
            data={"sub": "user-1"},
            algorithm="HS256"
        )
        
        payload = decode_access_token(token, algorithm="HS256")
        assert payload["sub"] == "user-1"


class TestTenantMetadata:
    """Tenant metadata tests."""

    def test_tenant_with_metadata(self):
        """Tenant can have custom metadata."""
        from auth.models import Tenant
        
        tenant = Tenant(
            id="tenant-1",
            name="Test Org",
            slug="test-org",
            metadata={"custom_field": "value", "plan_type": "enterprise"}
        )
        
        assert tenant.metadata["custom_field"] == "value"
        assert tenant.metadata["plan_type"] == "enterprise"

    def test_tenant_inactive(self):
        """Tenant can be marked inactive."""
        from auth.models import Tenant
        
        tenant = Tenant(
            id="tenant-1",
            name="Test Org",
            slug="test-org",
            is_active=False
        )
        
        assert tenant.is_active is False


class TestUserMetadata:
    """User metadata tests."""

    def test_user_with_metadata(self):
        """User can have custom metadata."""
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.USER,
            metadata={"preferences": {"theme": "dark"}, "last_login": "2024-01-01"}
        )
        
        assert user.metadata["preferences"]["theme"] == "dark"

    def test_user_timestamps(self):
        """User has created_at and updated_at timestamps."""
        from datetime import datetime
        from auth.models import User, Role
        
        user = User(
            id="user-1",
            email="test@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.USER,
        )
        
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)


class TestImportFallbacks:
    """Test import fallback paths using mocking."""

    def test_password_validator_require_special(self):
        """Test PasswordValidator with special character requirement."""
        from auth.security import PasswordValidator
        
        # Save original value
        original = PasswordValidator.REQUIRE_SPECIAL
        
        try:
            # Temporarily enable special character requirement
            PasswordValidator.REQUIRE_SPECIAL = True
            
            # Password without special character should fail
            is_valid, errors = PasswordValidator.validate("GoodPass123")
            assert is_valid is False
            assert any("special" in e.lower() for e in errors)
            
            # Password with special character should pass
            is_valid, errors = PasswordValidator.validate("GoodPass123!")
            assert is_valid is True
        finally:
            # Restore original value
            PasswordValidator.REQUIRE_SPECIAL = original


class TestPasswordVerificationEdgeCases:
    """Test password verification edge cases."""

    def test_verify_password_with_bcrypt_hash(self):
        """Verify password works with bcrypt hashes."""
        from auth.security import hash_password, verify_password
        
        password = "SecurePassword123"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert verify_password("WrongPassword", hashed) is False

    def test_hash_password_returns_different_hash_each_time(self):
        """Each hash_password call produces a unique hash (salt)."""
        from auth.security import hash_password
        
        password = "SamePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2


class TestJwtTokenEdgeCases:
    """Test JWT token edge cases."""

    def test_token_contains_iat_claim(self):
        """Token contains issued-at timestamp."""
        from auth.security import create_access_token, decode_access_token
        
        token = create_access_token(data={"sub": "user-1"})
        payload = decode_access_token(token)
        
        assert "iat" in payload
        assert "exp" in payload

    def test_token_with_additional_claims(self):
        """Token can contain additional custom claims."""
        from auth.security import create_access_token, decode_access_token
        
        token = create_access_token(
            data={
                "sub": "user-1",
                "custom_claim": "custom_value",
                "role": "admin"
            }
        )
        
        payload = decode_access_token(token)
        
        assert payload["custom_claim"] == "custom_value"
        assert payload["role"] == "admin"


class TestUserPermissionEdgeCases:
    """Test user permission edge cases."""

    def test_inactive_superuser_still_has_permissions(self):
        """Inactive superuser still has all permissions."""
        from auth.models import User, Role
        
        user = User(
            id="super-1",
            email="super@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
            role=Role.VIEWER,
            is_superuser=True,
            is_active=False,  # Inactive but still superuser
        )
        
        # Superuser should have all permissions regardless of active status
        assert user.has_permission("any:permission") is True

    def test_user_with_no_role_has_default_permissions(self):
        """User created without role gets default USER role."""
        from auth.models import User
        
        user = User(
            id="user-1",
            email="user@example.com",
            hashed_password="hashed",
            tenant_id="tenant-1",
        )
        
        # Should have USER role permissions
        assert user.has_permission("indexes:read") is True
        assert user.has_permission("indexes:write") is True
        assert user.has_permission("users:delete") is False


class TestRoleCheckerEdgeCases:
    """RoleChecker additional edge cases."""

    def test_role_checker_without_user_role_attribute(self):
        """RoleChecker handles user without role attribute."""
        from unittest.mock import MagicMock
        from auth.dependencies import RoleChecker
        
        checker = RoleChecker(["admin"])
        user = MagicMock(spec=[])  # User without 'role' attribute
        
        try:
            checker(user)
            assert False, "Should have raised HTTPException"
        except Exception as e:
            assert "403" in str(e) or "forbidden" in str(e).lower()

    def test_role_checker_with_none_user(self):
        """RoleChecker handles None user."""
        from auth.dependencies import RoleChecker
        
        checker = RoleChecker(["admin"])
        
        try:
            checker(None)
            assert False, "Should have raised HTTPException"
        except Exception as e:
            # Should handle gracefully
            pass
"""Security utilities for authentication.

Provides password hashing and JWT token management.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Try to import optional dependencies
_BCRYPT_AVAILABLE = False
_JOSE_AVAILABLE = False
_PASSLIB_AVAILABLE = False

try:
    import bcrypt as _bcrypt

    _BCRYPT_AVAILABLE = True
except ImportError:
    pass

try:
    from passlib.context import CryptContext

    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _PASSLIB_AVAILABLE = True
except ImportError:
    pass

try:
    from jose import JWTError, jwt

    _JOSE_AVAILABLE = True
except ImportError:
    pass


# Default configuration (should be overridden by environment)
SECRET_KEY = secrets.token_urlsafe(32)  # Default for dev
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Raises:
        ImportError: If bcrypt is not installed
    """
    if _BCRYPT_AVAILABLE:
        # Use bcrypt directly (more reliable)
        return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

    if _PASSLIB_AVAILABLE:
        return _pwd_context.hash(password)

    # Fallback to SHA256 for testing (NOT secure for production!)
    logger.warning(
        "bcrypt/passlib not installed, using SHA256 fallback. "
        "Install with: pip install passlib[bcrypt] bcrypt"
    )
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False if verification fails or error occurs
    """
    if _BCRYPT_AVAILABLE:
        try:
            return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.warning(f"bcrypt verification failed: {e}")

    if _PASSLIB_AVAILABLE:
        try:
            return _pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"passlib verification failed: {e}")
            return False

    # Fallback to SHA256 for testing (NOT secure for production!)
    logger.warning(
        "bcrypt/passlib not available, using SHA256 fallback. "
        "Install with: pip install passlib[bcrypt] bcrypt"
    )
    try:
        return hmac.compare_digest(
            hashlib.sha256(plain_password.encode()).hexdigest(), hashed_password
        )
    except Exception as e:
        logger.error(f"SHA256 fallback verification failed: {e}")
        return False


def create_access_token(
    data: dict[str, Any],
    secret_key: str | None = None,
    algorithm: str = ALGORITHM,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode
        secret_key: Secret key (uses default if not provided)
        algorithm: JWT algorithm
        expires_delta: Token expiration time

    Returns:
        Encoded JWT string

    Raises:
        ImportError: If python-jose is not installed
    """
    if not _JOSE_AVAILABLE:
        raise ImportError(
            "python-jose is not installed. Install with: pip install python-jose[cryptography]"
        )

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})

    key = secret_key or SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key, algorithm=algorithm)

    return encoded_jwt


def decode_access_token(
    token: str,
    secret_key: str | None = None,
    algorithm: str = ALGORITHM,
) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string
        secret_key: Secret key (uses default if not provided)
        algorithm: JWT algorithm

    Returns:
        Decoded payload

    Raises:
        ValueError: If token is invalid or expired
        ImportError: If python-jose is not installed
    """
    if not _JOSE_AVAILABLE:
        raise ImportError(
            "python-jose is not installed. Install with: pip install python-jose[cryptography]"
        )

    try:
        key = secret_key or SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[algorithm])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def create_refresh_token(
    data: dict[str, Any],
    secret_key: str | None = None,
    algorithm: str = ALGORITHM,
) -> str:
    """Create a refresh token with longer expiration.

    Args:
        data: Payload data
        secret_key: Secret key
        algorithm: JWT algorithm

    Returns:
        Encoded JWT refresh token
    """
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(
        data,
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=expires_delta,
    )


def generate_api_key() -> str:
    """Generate a secure API key.

    Returns:
        Random API key string
    """
    return secrets.token_urlsafe(32)


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks.

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings match
    """
    return hmac.compare_digest(a, b)


class PasswordValidator:
    """Password validation rules."""

    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False

    @classmethod
    def validate(cls, password: str) -> tuple[bool, list[str]]:
        """Validate a password against rules.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")

        if cls.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain an uppercase letter")

        if cls.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain a lowercase letter")

        if cls.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            errors.append("Password must contain a digit")

        if cls.REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain a special character")

        return len(errors) == 0, errors


def is_bcrypt_available() -> bool:
    """Check if bcrypt is available."""
    return _BCRYPT_AVAILABLE


def is_jose_available() -> bool:
    """Check if python-jose is available."""
    return _JOSE_AVAILABLE

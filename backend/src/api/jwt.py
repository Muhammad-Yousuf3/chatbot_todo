"""JWT token encoding and decoding utilities.

Provides functions for creating and validating JWT tokens for authentication.
Uses HS256 symmetric signing with a secret key from environment variables.
"""

import os
from datetime import datetime, timedelta, timezone

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

# Configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


class JWTConfigError(Exception):
    """Raised when JWT configuration is invalid."""

    pass


def _validate_config() -> None:
    """Validate JWT configuration."""
    if not JWT_SECRET:
        raise JWTConfigError("JWT_SECRET environment variable is not set")
    if len(JWT_SECRET) < 32:
        raise JWTConfigError("JWT_SECRET must be at least 32 characters long")


def encode_token(user_id: str, email: str) -> str:
    """Create a JWT token with user claims.

    Args:
        user_id: The user's unique identifier (UUID as string).
        email: The user's email address.

    Returns:
        Encoded JWT token string.

    Raises:
        JWTConfigError: If JWT_SECRET is not configured properly.
    """
    _validate_config()

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": now,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        Decoded payload dictionary containing 'sub', 'email', 'exp', 'iat'.

    Raises:
        ExpiredSignatureError: If the token has expired.
        JWTError: If the token is invalid or malformed.
        JWTConfigError: If JWT_SECRET is not configured properly.
    """
    _validate_config()

    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# Re-export exceptions for convenience
__all__ = [
    "encode_token",
    "decode_token",
    "JWTConfigError",
    "ExpiredSignatureError",
    "JWTClaimsError",
    "JWTError",
]

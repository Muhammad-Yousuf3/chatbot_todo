"""Password hashing utilities using bcrypt.

This module provides centralized password hashing and verification
with proper validation for bcrypt's 72-byte limit.

Security considerations:
- Uses bcrypt with 12 rounds (recommended minimum)
- Enforces 72-byte password limit before hashing (bcrypt limitation)
- Rejects passwords exceeding limit instead of silent truncation
- Compatible with Python 3.13 and bcrypt 4.x
"""

import logging
from typing import Final

from passlib.context import CryptContext

# Suppress passlib warning about bcrypt version detection.
# This is a known compatibility issue between passlib 1.7.4 and bcrypt 4.x
# where bcrypt removed the __about__ module. The functionality works correctly.
logging.getLogger("passlib").setLevel(logging.ERROR)

# Maximum password length in bytes for bcrypt
# bcrypt internally truncates at 72 bytes, but we reject instead of silently truncating
MAX_PASSWORD_BYTES: Final[int] = 72

# Password hashing context using bcrypt with 12 rounds
# bcrypt 4.x is compatible with Python 3.13
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


class PasswordTooLongError(ValueError):
    """Raised when password exceeds bcrypt's 72-byte limit."""

    def __init__(self, byte_length: int) -> None:
        self.byte_length = byte_length
        super().__init__(
            f"Password is {byte_length} bytes, exceeding the maximum of {MAX_PASSWORD_BYTES} bytes. "
            "Please use a shorter password."
        )


def validate_password_length(password: str) -> None:
    """Validate password length does not exceed bcrypt's 72-byte limit.

    Args:
        password: The plaintext password to validate.

    Raises:
        PasswordTooLongError: If password exceeds 72 bytes when UTF-8 encoded.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(len(password_bytes))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash string.

    Raises:
        PasswordTooLongError: If password exceeds 72 bytes when UTF-8 encoded.
    """
    validate_password_length(password)
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The bcrypt hash to verify against.

    Returns:
        True if the password matches, False otherwise.

    Raises:
        PasswordTooLongError: If plain_password exceeds 72 bytes when UTF-8 encoded.
    """
    validate_password_length(plain_password)
    return _pwd_context.verify(plain_password, hashed_password)

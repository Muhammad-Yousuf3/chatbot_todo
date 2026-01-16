"""Unit tests for password hashing utilities.

Tests cover:
- Normal password hashing and verification
- Password length validation (72-byte bcrypt limit)
- Rejection of overly long passwords
- UTF-8 encoding edge cases
"""

import pytest

from src.api.password import (
    MAX_PASSWORD_BYTES,
    PasswordTooLongError,
    hash_password,
    validate_password_length,
    verify_password,
)


class TestPasswordLength:
    """Tests for password length validation."""

    def test_short_password_valid(self) -> None:
        """Short passwords should be accepted."""
        validate_password_length("short")

    def test_exactly_72_bytes_valid(self) -> None:
        """Password exactly at 72 bytes should be accepted."""
        password = "a" * 72  # 72 ASCII bytes
        validate_password_length(password)

    def test_73_bytes_rejected(self) -> None:
        """Password at 73 bytes should be rejected."""
        password = "a" * 73  # 73 ASCII bytes
        with pytest.raises(PasswordTooLongError) as exc_info:
            validate_password_length(password)
        assert exc_info.value.byte_length == 73

    def test_long_password_rejected(self) -> None:
        """Passwords significantly over 72 bytes should be rejected."""
        password = "a" * 100
        with pytest.raises(PasswordTooLongError) as exc_info:
            validate_password_length(password)
        assert exc_info.value.byte_length == 100

    def test_utf8_multibyte_characters(self) -> None:
        """UTF-8 multi-byte characters should count correctly.

        Example: 'test' (4 bytes) + 20 emoji (80 bytes) = 84 bytes > 72
        """
        # Each emoji is 4 bytes in UTF-8
        password = "test" + "\U0001f600" * 20  # 4 + 80 = 84 bytes
        with pytest.raises(PasswordTooLongError):
            validate_password_length(password)

    def test_utf8_at_boundary(self) -> None:
        """Test UTF-8 password exactly at 72 bytes."""
        # 18 emojis * 4 bytes = 72 bytes
        password = "\U0001f600" * 18
        validate_password_length(password)  # Should not raise

    def test_max_password_bytes_constant(self) -> None:
        """Verify MAX_PASSWORD_BYTES is set correctly."""
        assert MAX_PASSWORD_BYTES == 72


class TestHashPassword:
    """Tests for password hashing."""

    def test_hash_normal_password(self) -> None:
        """Normal passwords should hash successfully."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_empty_password(self) -> None:
        """Empty passwords should hash (validation is separate)."""
        hashed = hash_password("")
        assert hashed.startswith("$2b$")

    def test_hash_too_long_password_raises(self) -> None:
        """Passwords over 72 bytes should raise PasswordTooLongError."""
        password = "a" * 100
        with pytest.raises(PasswordTooLongError):
            hash_password(password)

    def test_hash_different_for_same_password(self) -> None:
        """Same password should produce different hashes (due to salt)."""
        password = "SamePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_special_characters(self) -> None:
        """Passwords with special characters should hash correctly."""
        password = "P@$$w0rd!#%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")


class TestVerifyPassword:
    """Tests for password verification."""

    def test_verify_correct_password(self) -> None:
        """Correct password should verify successfully."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self) -> None:
        """Wrong password should fail verification."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_similar_password(self) -> None:
        """Similar but different passwords should fail verification."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        assert verify_password("MySecurePassword123", hashed) is False  # Missing !

    def test_verify_too_long_password_raises(self) -> None:
        """Verifying a password over 72 bytes should raise PasswordTooLongError."""
        # First hash a normal password
        hashed = hash_password("short")
        # Then try to verify with a too-long password
        long_password = "a" * 100
        with pytest.raises(PasswordTooLongError):
            verify_password(long_password, hashed)

    def test_verify_empty_password(self) -> None:
        """Empty password should verify against its hash."""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestPasswordTooLongError:
    """Tests for PasswordTooLongError exception."""

    def test_error_message(self) -> None:
        """Error message should include byte length."""
        error = PasswordTooLongError(100)
        assert "100 bytes" in str(error)
        assert "72 bytes" in str(error)

    def test_error_byte_length_attribute(self) -> None:
        """Error should have byte_length attribute."""
        error = PasswordTooLongError(150)
        assert error.byte_length == 150

    def test_error_is_value_error(self) -> None:
        """PasswordTooLongError should be a ValueError subclass."""
        error = PasswordTooLongError(100)
        assert isinstance(error, ValueError)

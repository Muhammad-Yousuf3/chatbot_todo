"""Authentication API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    """User signup request schema."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=100)
    display_name: str = Field(min_length=1, max_length=100)


class SigninRequest(BaseModel):
    """User signin request schema."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class AuthResponse(BaseModel):
    """Authentication response with user data and JWT token."""

    user_id: UUID
    email: str
    display_name: str
    created_at: datetime
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """User profile response."""

    id: UUID
    email: str
    display_name: str
    created_at: datetime

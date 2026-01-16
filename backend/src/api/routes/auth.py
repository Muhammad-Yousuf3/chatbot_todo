"""Authentication REST API endpoints.

Provides signup, signin, and user profile functionality with JWT authentication.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from src.api.deps import CurrentUserId
from src.api.jwt import encode_token
from src.api.password import (
    MAX_PASSWORD_BYTES,
    PasswordTooLongError,
    hash_password,
    verify_password,
)
from src.api.schemas.auth import AuthResponse, SigninRequest, SignupRequest, UserResponse
from src.db.session import SessionDep
from src.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
    description="Register a new user with email, password, and display name. Returns JWT token.",
)
async def signup(
    request: SignupRequest,
    session: SessionDep,
) -> AuthResponse:
    """Create a new user account and return JWT token."""
    # Validate password length before hashing (bcrypt 72-byte limit)
    try:
        password_hash = hash_password(request.password)
    except PasswordTooLongError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "PASSWORD_TOO_LONG",
                    "message": f"Password exceeds maximum length of {MAX_PASSWORD_BYTES} bytes",
                }
            },
        )

    # Check if email already exists
    query = select(User).where(User.email == request.email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "EMAIL_EXISTS", "message": "Email already registered"}},
        )

    # Create new user
    user = User(
        email=request.email,
        password_hash=password_hash,
        display_name=request.display_name,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    # Generate JWT token
    access_token = encode_token(user_id=str(user.id), email=user.email)

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        access_token=access_token,
        token_type="bearer",
    )


@router.post(
    "/signin",
    response_model=AuthResponse,
    summary="Sign in to existing account",
    description="Authenticate with email and password. Returns JWT token.",
)
async def signin(
    request: SigninRequest,
    session: SessionDep,
) -> AuthResponse:
    """Authenticate a user and return JWT token."""
    # Find user by email
    query = select(User).where(User.email == request.email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}},
        )

    # Verify password
    try:
        password_valid = verify_password(request.password, user.password_hash)
    except PasswordTooLongError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "PASSWORD_TOO_LONG",
                    "message": f"Password exceeds maximum length of {MAX_PASSWORD_BYTES} bytes",
                }
            },
        )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}},
        )

    # Update last login time
    user.updated_at = datetime.utcnow()
    await session.flush()

    # Generate JWT token
    access_token = encode_token(user_id=str(user.id), email=user.email)

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user. Requires JWT token.",
)
async def get_current_user(
    session: SessionDep,
    user_id: CurrentUserId,
) -> UserResponse:
    """Get current user profile using JWT authentication."""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_USER_ID", "message": "Invalid user ID format"}},
        )

    query = select(User).where(User.id == user_uuid)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
    )

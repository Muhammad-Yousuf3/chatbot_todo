"""API dependencies for dependency injection.

Provides JWT-based authentication dependency for protected endpoints.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.jwt import JWTConfigError, decode_token
from jose.exceptions import ExpiredSignatureError, JWTError

# HTTPBearer security scheme for JWT token extraction
security = HTTPBearer(
    scheme_name="JWT",
    description="JWT Bearer token authentication. Use the token from /api/auth/signin or /api/auth/signup.",
    auto_error=False,  # Handle missing token manually for better error messages
)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> str:
    """Extract and validate user_id from JWT token in Authorization header.

    Expects: Authorization: Bearer <jwt_token>

    Args:
        credentials: HTTP Authorization credentials extracted by HTTPBearer.

    Returns:
        The verified user_id (sub claim) from the JWT token.

    Raises:
        HTTPException: 401 MISSING_TOKEN if no token provided.
        HTTPException: 401 INVALID_TOKEN if token is malformed or signature invalid.
        HTTPException: 401 TOKEN_EXPIRED if token has expired.
        HTTPException: 500 if JWT configuration is invalid.
    """
    # T010: Missing token error
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "MISSING_TOKEN", "message": "Authorization header required"}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Decode and validate the token
        payload = decode_token(token)

        # Extract user_id from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            # T011: Invalid token (missing sub claim)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token: missing user identifier"}},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except ExpiredSignatureError:
        # T012: Expired token error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        # T011: Invalid token (malformed or bad signature)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token"}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTConfigError as e:
        # Server configuration error - should not happen in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "SERVER_ERROR", "message": "Authentication configuration error"}},
        )


# Type alias for dependency injection
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

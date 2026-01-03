"""API dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends, Header


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Get current user ID from JWT token.

    NOTE: This is a stub implementation. In production, this should:
    1. Validate the JWT token from Better Auth
    2. Extract and return the user_id from the token claims

    For development/testing, returns a default user ID.
    """
    # TODO: Implement actual JWT validation with Better Auth
    # For now, return a stub user ID for development
    return "dev-user-001"


CurrentUserId = Annotated[str, Depends(get_current_user_id)]

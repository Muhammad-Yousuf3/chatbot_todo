"""Database session management for stateless conversation persistence."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.db.engine import get_engine

logger = logging.getLogger(__name__)

# Lazy initialization - session maker created on first use
_async_session_maker: sessionmaker | None = None

# Database availability flag - set during init_db()
_db_available: bool = False


def is_db_available() -> bool:
    """Check if database is available."""
    return _db_available


def _get_session_maker() -> sessionmaker:
    """Get or create the session maker (lazy initialization)."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def init_db(max_retries: int = 3, retry_delay: float = 2.0) -> None:
    """Initialize database tables with retry logic for Neon cold starts.

    This is called during application startup and will establish
    the first database connection. Includes retry logic to handle
    Neon's cold start latency.

    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds
    """
    global _db_available
    engine = get_engine()

    last_error = None
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            _db_available = True
            logger.info("Database tables initialized successfully")
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Database initialization failed after {max_retries} attempts: {e}")

    # If we get here, all retries failed
    _db_available = False
    raise last_error if last_error else RuntimeError("Database initialization failed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection.

    Raises:
        HTTPException: 503 if database is not available
    """
    if not _db_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database is temporarily unavailable. Please try again later.",
                }
            },
        )

    session_maker = _get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def require_db_available() -> None:
    """Dependency that requires database to be available.

    Use this for routes that need DB but don't use SessionDep directly.
    """
    if not _db_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database is temporarily unavailable. Please try again later.",
                }
            },
        )

"""Async database engine for MCP server.

This module provides a shared async engine that can be used by the MCP server
for task operations. It uses the same configuration as the main application.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.db.config import settings

# Shared async engine for MCP server
# This is created once and passed to the MCP server via lifespan context
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine.

    Returns:
        The shared async engine instance.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )
    return _engine


async def dispose_engine() -> None:
    """Dispose of the database engine and release connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None

"""Async database engine for MCP server.

This module provides a shared async engine that can be used by the MCP server
for task operations. It uses the same configuration as the main application.

The engine is lazily initialized on first use to avoid import-time side effects.
"""

import ssl
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.db.config import settings

# Shared async engine for MCP server and all database operations
# This is created once and shared across the application
_engine: AsyncEngine | None = None


def _fix_neon_url(url: str) -> tuple[str, dict]:
    """Fix Neon connection string for asyncpg compatibility.

    Neon uses sslmode=require which asyncpg doesn't understand.
    This function removes sslmode from the URL and returns SSL context.

    Args:
        url: Database connection URL

    Returns:
        Tuple of (fixed_url, connect_args)
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Check for SSL-related params that asyncpg handles differently
    needs_ssl = False
    if "sslmode" in query_params:
        sslmode = query_params.pop("sslmode", [""])[0]
        needs_ssl = sslmode in ("require", "verify-ca", "verify-full")

    # Remove channel_binding as well (not supported by asyncpg)
    query_params.pop("channel_binding", None)

    # Rebuild URL without problematic params
    new_query = urlencode({k: v[0] for k, v in query_params.items()}, doseq=False)
    fixed_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))

    # Build connect_args for SSL
    connect_args = {}
    if needs_ssl:
        # Create SSL context for Neon
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context

    return fixed_url, connect_args


def get_engine() -> AsyncEngine:
    """Get or create the async database engine.

    Returns:
        The shared async engine instance.
    """
    global _engine
    if _engine is None:
        # Fix Neon connection URL for asyncpg
        fixed_url, connect_args = _fix_neon_url(settings.database_url)

        _engine = create_async_engine(
            fixed_url,
            echo=settings.debug,
            future=True,
            # Connection pool settings for Neon
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=300,  # Recycle connections after 5 minutes
            connect_args=connect_args,
        )
    return _engine


async def dispose_engine() -> None:
    """Dispose of the database engine and release connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None

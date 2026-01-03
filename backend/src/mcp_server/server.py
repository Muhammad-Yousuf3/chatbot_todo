"""FastMCP server for AI-controlled task management.

This module sets up the MCP server that exposes task management tools
to AI agents. The server uses a lifespan context to manage the database
connection lifecycle.
"""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncEngine

from src.db.engine import dispose_engine, get_engine

# Configure logging for MCP server
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")


@dataclass
class AppContext:
    """Application context passed to MCP tools via lifespan.

    This context provides access to the database engine for all tools.
    """

    engine: AsyncEngine


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage MCP server lifecycle with database connection.

    This lifespan context:
    1. Creates the database engine on startup
    2. Passes the engine to all tools via AppContext
    3. Disposes the engine on shutdown

    Args:
        server: The FastMCP server instance

    Yields:
        AppContext with the database engine
    """
    logger.info("MCP server starting up...")
    engine = get_engine()

    try:
        yield AppContext(engine=engine)
    finally:
        logger.info("MCP server shutting down...")
        await dispose_engine()


# Create the FastMCP server instance
mcp = FastMCP("task-tools", lifespan=app_lifespan)

# Tool imports - each import registers the tool with FastMCP via @mcp.tool() decorator
# Import after mcp is defined to avoid circular imports
from src.mcp_server.tools import add_task  # noqa: E402, F401
from src.mcp_server.tools import list_tasks  # noqa: E402, F401
from src.mcp_server.tools import update_task  # noqa: E402, F401
from src.mcp_server.tools import complete_task  # noqa: E402, F401
from src.mcp_server.tools import delete_task  # noqa: E402, F401

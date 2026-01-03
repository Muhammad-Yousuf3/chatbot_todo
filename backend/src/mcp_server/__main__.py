"""Entry point for running the MCP server.

Run with: python -m src.mcp_server

This starts the MCP server using STDIO transport, which is suitable
for local development and integration with AI agents.
"""

from src.mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")

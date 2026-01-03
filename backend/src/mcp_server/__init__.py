"""MCP Server for AI-controlled task management.

This module provides MCP tools that allow AI agents to manage todo tasks
without direct database access. All task operations go through these tools.
"""

from src.mcp_server.server import mcp

__all__ = ["mcp"]

# Chatbot TODO Backend

Backend service for AI-powered todo task management via MCP (Model Context Protocol).

## Features

- MCP server with task management tools
- SQLModel-based database models
- Async PostgreSQL support via asyncpg

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run MCP server
uv run python -m src.mcp_server
```

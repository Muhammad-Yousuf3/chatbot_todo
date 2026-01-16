# Chatbot TODO Backend

Backend service for AI-powered todo task management via MCP (Model Context Protocol).

## Features

- FastAPI REST API with JWT authentication
- MCP server with task management tools
- LLM runtime with Gemini integration
- SQLModel-based database models
- Async PostgreSQL support via asyncpg
- Observability and logging

## Environment Variables

Set these in HuggingFace Spaces Secrets:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (e.g., `postgresql+asyncpg://user:pass@host/db`) |
| `JWT_SECRET` | Yes | Secret key for JWT tokens (min 32 chars) |
| `JWT_EXPIRATION_HOURS` | No | Token expiration (default: 24) |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GEMINI_MODEL` | No | Gemini model (default: gemini-2.5-flash) |
| `LLM_TEMPERATURE` | No | LLM temperature (default: 0.0) |
| `LLM_MAX_TOKENS` | No | Max tokens (default: 1024) |
| `LLM_TIMEOUT` | No | LLM timeout in seconds (default: 30) |
| `MAX_TOOL_ITERATIONS` | No | Max MCP tool iterations (default: 5) |
| `FRONTEND_URL` | No | CORS allowed origin (default: http://localhost:3000) |

## Development

```bash
# Install dependencies
uv sync

# Run API server
uv run uvicorn src.main:app --reload

# Run tests
uv run pytest

# Run MCP server
uv run python -m src.mcp_server
```

## Deployment

This backend is deployed on HuggingFace Spaces using Docker.

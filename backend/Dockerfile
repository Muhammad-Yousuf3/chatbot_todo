# HuggingFace Spaces compatible Dockerfile for FastAPI backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for asyncpg and bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY src/ ./src/

# Create data directory for SQLite (observability logs)
RUN mkdir -p /app/data

# HuggingFace Spaces uses port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Run the FastAPI application
# Note: Environment variables (DATABASE_URL, JWT_SECRET, etc.) should be set in HuggingFace Secrets
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]

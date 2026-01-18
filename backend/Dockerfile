# Multi-stage Dockerfile for FastAPI backend
# Supports both Kubernetes (port 8000) and HuggingFace Spaces (port 7860)
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies required for asyncpg and bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source for installation
COPY pyproject.toml README.md* ./
COPY src/ ./src/

# Create empty README if it doesn't exist (for build compatibility)
RUN touch README.md || true

# Install dependencies using pip
RUN pip install --no-cache-dir .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Create data directory for SQLite (observability logs)
RUN mkdir -p /app/data

# Create non-root user for security
RUN useradd -r -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default port for Kubernetes deployment (can be overridden)
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the FastAPI application
# Port can be overridden via environment variable
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]

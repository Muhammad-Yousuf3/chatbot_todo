"""FastAPI application entry point for conversation persistence API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import chat_router, conversations_router
from src.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup: Initialize database tables
    await init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Conversation Persistence API",
    description="Stateless chat API for AI-powered Todo Application",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(chat_router)
app.include_router(conversations_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

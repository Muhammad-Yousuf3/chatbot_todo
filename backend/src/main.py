"""FastAPI application entry point for conversation persistence API."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env file BEFORE any other imports that might need env vars
# This ensures os.environ.get() works for GEMINI_API_KEY etc.
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from src.api.routes import auth_router, chat_router, conversations_router, events_router, observability_router, tasks_router
from src.dapr.client import close_dapr_service, get_dapr_service, is_dapr_enabled
from src.db import init_db

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup Phase 1: Initialize PostgreSQL database tables
    # Note: Database connection happens here, not at module import.
    # If database is unavailable, app will start but DB operations will fail.
    try:
        await init_db()
        logger.info("PostgreSQL database initialized successfully")
    except Exception as e:
        # Log error but allow app to start - DB operations will fail at request time
        logger.error(f"PostgreSQL database initialization failed: {e}")
        logger.warning("Application starting without PostgreSQL - DB operations will return 503")

    # Startup Phase 2: Initialize SQLite observability database
    try:
        from src.observability.database import init_log_db
        await init_log_db()
        logger.info("Observability SQLite database initialized successfully")
    except ImportError:
        logger.warning("Observability module not available - skipping SQLite init")
    except Exception as e:
        logger.error(f"Observability SQLite initialization failed: {e}")
        logger.warning("Observability features may be limited")

    # Startup Phase 3: Initialize Dapr client
    try:
        dapr_service = get_dapr_service()
        if dapr_service.enabled:
            logger.info("Dapr client initialized successfully")
        else:
            logger.info("Running without Dapr sidecar - event publishing disabled")
    except Exception as e:
        logger.warning(f"Dapr client initialization failed: {e}")
        logger.info("Continuing without Dapr - event publishing disabled")

    yield

    # Shutdown: cleanup database connections
    try:
        from src.db import dispose_engine
        await dispose_engine()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error during database cleanup: {e}")

    # Shutdown: cleanup Dapr client
    try:
        await close_dapr_service()
        logger.info("Dapr client closed")
    except Exception as e:
        logger.warning(f"Error during Dapr cleanup: {e}")


app = FastAPI(
    title="Conversation Persistence API",
    description="Stateless chat API for AI-powered Todo Application",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
# Note: OPTIONS preflight requests are handled by CORS middleware before auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        os.getenv("FRONTEND_URL", "http://localhost:3000"),  # Configurable frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],  # Explicitly allow Authorization for JWT
    expose_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(events_router)
app.include_router(observability_router)
app.include_router(tasks_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    dapr_service = get_dapr_service()
    return {
        "status": "healthy",
        "service": "backend",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_enabled": is_dapr_enabled(),
    }


@app.get("/health/dapr")
async def dapr_health_check():
    """Dapr sidecar health check endpoint."""
    dapr_service = get_dapr_service()
    dapr_health = dapr_service.check_health()

    status = "healthy" if dapr_health.get("dapr_sidecar_healthy", False) else "degraded"
    if not dapr_health.get("dapr_enabled", False):
        status = "disabled"

    return {
        "status": status,
        "service": "backend",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **dapr_health,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness probe endpoint for Kubernetes."""
    dapr_service = get_dapr_service()
    dapr_health = dapr_service.check_health()

    # Ready if Dapr is disabled (non-Dapr mode) or Dapr is healthy
    dapr_ready = not dapr_health.get("dapr_enabled") or dapr_health.get("dapr_sidecar_healthy", False)

    return {
        "status": "ready" if dapr_ready else "not_ready",
        "service": "backend",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_ready": dapr_ready,
    }


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """Return Dapr subscription configuration.

    This endpoint is called by Dapr sidecar to discover event subscriptions.
    Backend subscribes to:
    - tasks topic: for RecurringTaskScheduled events
    - notifications topic: for ReminderTriggered events
    """
    return [
        {
            "pubsubname": "pubsub",
            "topic": "tasks",
            "route": "/events/tasks",
        },
        {
            "pubsubname": "pubsub",
            "topic": "notifications",
            "route": "/events/notifications",
        },
    ]

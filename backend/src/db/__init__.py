"""Database module for conversation persistence and MCP task tools."""

# CRITICAL: Import all SQLModel table models BEFORE init_db is called.
# SQLModel.metadata.create_all only creates tables for models that have been imported.
# These imports must happen at module load time, before the lifespan handler runs.
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.task import Task

from src.db.engine import dispose_engine, get_engine
from src.db.session import get_session, init_db

__all__ = [
    "get_session",
    "init_db",
    "get_engine",
    "dispose_engine",
    # Export models for convenience
    "Conversation",
    "Message",
    "Task",
]

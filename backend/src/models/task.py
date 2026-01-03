"""Task model for MCP-controlled todo items."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    COMPLETED = "completed"


class Task(SQLModel, table=True):
    """Todo task item owned by a user, managed via MCP tools.

    Tasks can only be created, read, updated, and deleted through MCP tools.
    AI agents cannot access the database directly.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, max_length=255)
    description: str = Field(max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.PENDING, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)

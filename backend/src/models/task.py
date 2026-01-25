"""Task model for MCP-controlled todo items."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from .enums import TaskPriority, TaskStatus

if TYPE_CHECKING:
    from .recurrence import Recurrence
    from .reminder import Reminder


class Task(SQLModel, table=True):
    """Todo task item owned by a user, managed via MCP tools.

    Tasks can only be created, read, updated, and deleted through MCP tools.
    AI agents cannot access the database directly.
    """

    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, max_length=255)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: TaskStatus = Field(default=TaskStatus.PENDING, max_length=20)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, max_length=10)
    tags: List[str] = Field(
        default=[],
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    due_date: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships with cascade delete
    reminders: List["Reminder"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    recurrence: Optional["Recurrence"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )

    __table_args__ = (
        Index("idx_tasks_user_id", "user_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_priority", "priority"),
        Index("idx_tasks_due_date", "due_date"),
        Index("idx_tasks_tags", "tags", postgresql_using="gin"),
    )

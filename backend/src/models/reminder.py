"""Reminder model for task due date notifications."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .task import Task


class Reminder(SQLModel, table=True):
    """Reminder entity for task notifications.

    Each task can have multiple reminders that trigger before the due date.
    Reminders are processed by the Scheduler service and published as events.
    """

    __tablename__ = "reminders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", index=True)
    trigger_at: datetime = Field(nullable=False)
    fired: bool = Field(default=False)
    cancelled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship back to task
    task: Optional["Task"] = Relationship(back_populates="reminders")

    __table_args__ = (
        Index("idx_reminders_task_id", "task_id"),
        Index("idx_reminders_trigger_at", "trigger_at"),
        # Partial index for pending reminders
        Index(
            "idx_reminders_pending",
            "fired",
            "cancelled",
            postgresql_where="fired = false AND cancelled = false",
        ),
    )

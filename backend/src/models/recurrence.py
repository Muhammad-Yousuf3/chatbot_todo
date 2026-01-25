"""Recurrence model for recurring task schedules."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

from .enums import RecurrenceType

if TYPE_CHECKING:
    from .task import Task


class Recurrence(SQLModel, table=True):
    """Recurrence schedule for a task.

    Each task can have at most one recurrence schedule.
    Recurrences are processed by the Scheduler service which creates
    new task instances based on the schedule.
    """

    __tablename__ = "recurrences"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", unique=True, index=True)
    recurrence_type: RecurrenceType = Field(nullable=False)
    cron_expression: Optional[str] = Field(default=None, max_length=100)
    next_occurrence: Optional[datetime] = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship back to task
    task: Optional["Task"] = Relationship(back_populates="recurrence")

    __table_args__ = (
        Index("idx_recurrences_task_id", "task_id"),
        Index("idx_recurrences_next_occurrence", "next_occurrence"),
        Index("idx_recurrences_active", "active"),
    )

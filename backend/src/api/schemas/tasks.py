"""Task API schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models import RecurrenceType, TaskPriority, TaskStatus


# --- Reminder Schemas ---


class ReminderCreate(BaseModel):
    """Reminder creation schema (embedded in task creation/update)."""

    trigger_at: datetime = Field(..., description="When the reminder should trigger")


class ReminderResponse(BaseModel):
    """Reminder response schema."""

    id: UUID
    trigger_at: datetime
    fired: bool = False
    cancelled: bool = False
    created_at: datetime


# --- Recurrence Schemas ---


class RecurrenceCreate(BaseModel):
    """Recurrence creation schema (embedded in task creation/update)."""

    recurrence_type: RecurrenceType = Field(..., description="Type: daily, weekly, or custom")
    cron_expression: Optional[str] = Field(
        None,
        description="Cron expression (required if type is 'custom')",
        max_length=100,
    )

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_for_custom(cls, v, info):
        """Validate cron_expression is provided for custom recurrence type."""
        if info.data.get("recurrence_type") == RecurrenceType.CUSTOM and not v:
            raise ValueError("cron_expression is required for custom recurrence type")
        return v


class RecurrenceResponse(BaseModel):
    """Recurrence response schema."""

    id: UUID
    recurrence_type: RecurrenceType
    cron_expression: Optional[str] = None
    next_occurrence: Optional[datetime] = None
    active: bool = True
    created_at: datetime


# --- Task Schemas ---


class TaskResponse(BaseModel):
    """Task response schema."""

    id: UUID
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    tags: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    reminders: List[ReminderResponse] = []
    recurrence: Optional[RecurrenceResponse] = None


class TaskListResponse(BaseModel):
    """Task list response schema."""

    tasks: List[TaskResponse]
    total: int


class TaskCreateRequest(BaseModel):
    """Task creation request schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    tags: List[str] = Field(
        default=[],
        description="List of tags (max 10 tags, each max 50 chars)",
    )
    due_date: Optional[datetime] = Field(None, description="Task due date")
    reminders: List[ReminderCreate] = Field(
        default=[],
        description="List of reminders (max 5)",
    )
    recurrence: Optional[RecurrenceCreate] = Field(
        None,
        description="Recurrence schedule",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags count and length."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
        return v

    @field_validator("reminders")
    @classmethod
    def validate_reminders(cls, v):
        """Validate reminders count."""
        if len(v) > 5:
            raise ValueError("Maximum 5 reminders per task")
        return v


class TaskUpdateRequest(BaseModel):
    """Task update request schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    tags: Optional[List[str]] = Field(None, description="List of tags")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    reminders: Optional[List[ReminderCreate]] = Field(
        None,
        description="List of reminders (replaces existing)",
    )
    recurrence: Optional[RecurrenceCreate] = Field(
        None,
        description="Recurrence schedule (replaces existing)",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags count and length."""
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
        return v

    @field_validator("reminders")
    @classmethod
    def validate_reminders(cls, v):
        """Validate reminders count."""
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("Maximum 5 reminders per task")
        return v

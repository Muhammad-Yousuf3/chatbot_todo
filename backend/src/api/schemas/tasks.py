"""Task API schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.models import TaskStatus


class TaskResponse(BaseModel):
    """Task response schema."""

    id: UUID
    description: str
    status: TaskStatus
    due_date: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskListResponse(BaseModel):
    """Task list response schema."""

    tasks: list[TaskResponse]
    total: int


class TaskCreateRequest(BaseModel):
    """Task creation request schema."""

    description: str
    due_date: Optional[datetime] = None


class TaskUpdateRequest(BaseModel):
    """Task update request schema."""

    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None

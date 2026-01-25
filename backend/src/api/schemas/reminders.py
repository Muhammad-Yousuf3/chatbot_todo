"""Reminder API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    """Reminder creation schema."""

    trigger_at: datetime = Field(..., description="When the reminder should trigger")


class ReminderResponse(BaseModel):
    """Reminder response schema."""

    id: UUID
    task_id: UUID
    trigger_at: datetime
    fired: bool = False
    cancelled: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

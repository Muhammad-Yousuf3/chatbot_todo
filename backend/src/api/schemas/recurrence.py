"""Recurrence API schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models import RecurrenceType


class RecurrenceCreate(BaseModel):
    """Recurrence creation schema."""

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
    task_id: UUID
    recurrence_type: RecurrenceType
    cron_expression: Optional[str] = None
    next_occurrence: Optional[datetime] = None
    active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

"""CloudEvents schemas for task lifecycle events.

All events follow the CloudEvents v1.0 specification.
https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CloudEvent(BaseModel):
    """CloudEvents v1.0 envelope.

    This is the standard envelope format for all events.
    The `data` field contains the event-specific payload.
    """

    specversion: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    type: str
    time: datetime = Field(default_factory=datetime.utcnow)
    datacontenttype: str = "application/json"
    data: Any

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        }


class ReminderData(BaseModel):
    """Embedded reminder in task event."""

    reminder_id: str
    trigger_at: datetime


class RecurrenceData(BaseModel):
    """Embedded recurrence in task event."""

    recurrence_id: str
    recurrence_type: str  # daily, weekly, custom
    cron_expression: Optional[str] = None
    next_occurrence: Optional[datetime] = None


class TaskCreatedData(BaseModel):
    """Payload for TaskCreated event.

    Emitted when a new task is created via API or MCP tools.
    """

    task_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: str  # TaskStatus value
    priority: str  # TaskPriority value
    tags: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime
    reminders: List[ReminderData] = []
    recurrence: Optional[RecurrenceData] = None


class FieldChange(BaseModel):
    """Represents a single field change in an update event."""

    old_value: Any
    new_value: Any


class TaskUpdatedData(BaseModel):
    """Payload for TaskUpdated event.

    Emitted when a task is modified. Only changed fields are included.
    """

    task_id: str
    user_id: str
    updated_at: datetime
    changes: Dict[str, FieldChange]


class TaskCompletedData(BaseModel):
    """Payload for TaskCompleted event.

    Emitted when a task is marked as completed.
    """

    task_id: str
    user_id: str
    completed_at: datetime


class TaskDeletedData(BaseModel):
    """Payload for TaskDeleted event.

    Emitted when a task is deleted.
    """

    task_id: str
    user_id: str

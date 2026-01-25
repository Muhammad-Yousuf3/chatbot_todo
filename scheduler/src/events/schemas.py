"""Event schemas for Scheduler service.

Includes schemas for events the scheduler receives and produces.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# --- CloudEvents Base ---


class CloudEvent(BaseModel):
    """CloudEvents v1.0 envelope."""

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


# --- Scheduler Output Events ---


class ReminderTriggeredData(BaseModel):
    """Payload for ReminderTriggered event.

    Emitted when a reminder reaches its trigger time.
    Published to the 'notifications' topic.
    """

    reminder_id: str
    task_id: str
    user_id: str
    task_title: str
    due_date: Optional[datetime] = None
    triggered_at: datetime


class RecurringTaskScheduledData(BaseModel):
    """Payload for RecurringTaskScheduled event.

    Emitted when a recurring task's next occurrence is due.
    Published to the 'tasks' topic for the backend to create a new task instance.
    """

    source_task_id: str  # Original recurring task
    new_task_id: str  # ID for the new task instance
    user_id: str
    title: str
    description: Optional[str] = None
    priority: str
    tags: List[str] = []
    recurrence_type: str
    scheduled_for: datetime


# --- Event Types and Constants ---


class EventType:
    """CloudEvents event type identifiers."""

    # Events received from Backend
    TASK_CREATED = "com.todo.task.created"
    TASK_UPDATED = "com.todo.task.updated"
    TASK_COMPLETED = "com.todo.task.completed"
    TASK_DELETED = "com.todo.task.deleted"

    # Events produced by Scheduler
    REMINDER_TRIGGERED = "com.todo.reminder.triggered"
    RECURRING_TASK_SCHEDULED = "com.todo.recurring.scheduled"


class EventSource:
    """CloudEvents source identifiers."""

    SCHEDULER_REMINDERS = "/scheduler/reminders"
    SCHEDULER_RECURRING = "/scheduler/recurring"


class Topic:
    """Dapr Pub/Sub topic names."""

    TASKS = "tasks"
    NOTIFICATIONS = "notifications"


# Dapr component names
PUBSUB_NAME = "pubsub"
STATESTORE_NAME = "statestore"

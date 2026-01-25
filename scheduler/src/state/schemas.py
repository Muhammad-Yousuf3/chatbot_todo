"""State store schemas for Scheduler service.

Defines the data structures stored in Dapr State Store (Redis).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RecurringTaskState(BaseModel):
    """State stored for recurring tasks.

    Key pattern: recurring:{task_id}
    """

    task_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    priority: str  # high, medium, low
    tags: List[str] = []
    recurrence_type: str  # daily, weekly, custom
    cron_expression: Optional[str] = None
    next_occurrence: datetime
    last_scheduled: Optional[datetime] = None
    created_from_event_id: str  # For idempotency


class ReminderState(BaseModel):
    """State stored for reminders.

    Key pattern: reminder:{reminder_id}
    """

    reminder_id: str
    task_id: str
    user_id: str
    task_title: str
    trigger_at: datetime
    due_date: Optional[datetime] = None
    fired: bool = False
    cancelled: bool = False
    created_from_event_id: str  # For idempotency


class ProcessedEventState(BaseModel):
    """State stored for processed events (idempotency tracking).

    Key pattern: processed:{service}:{event_id}
    TTL: 24 hours
    """

    event_id: str
    event_type: str
    processed_at: datetime


class Registry(BaseModel):
    """Registry to track active recurring tasks and reminders.

    Since Dapr state store doesn't support prefix queries natively,
    we maintain a registry of active IDs that can be queried.
    """

    ids: List[str] = []


# State key patterns
def recurring_task_key(task_id: str) -> str:
    """Generate state store key for recurring task."""
    return f"recurring:{task_id}"


def reminder_key(reminder_id: str) -> str:
    """Generate state store key for reminder."""
    return f"reminder:{reminder_id}"


def processed_event_key(service: str, event_id: str) -> str:
    """Generate state store key for processed event."""
    return f"processed:{service}:{event_id}"


# Registry keys
RECURRING_REGISTRY_KEY = "registry:recurring"
REMINDER_REGISTRY_KEY = "registry:reminders"

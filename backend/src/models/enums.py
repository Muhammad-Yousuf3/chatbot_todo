"""Enumeration types for task models."""

from enum import Enum


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    """Priority level of a task."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecurrenceType(str, Enum):
    """Type of recurrence pattern."""

    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

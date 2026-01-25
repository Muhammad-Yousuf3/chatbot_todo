"""Data models for conversation persistence and task management."""

from enum import Enum


class MessageRole(str, Enum):
    """Role of a message sender in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


from src.models.conversation import Conversation
from src.models.enums import RecurrenceType, TaskPriority, TaskStatus
from src.models.message import Message
from src.models.processed_event import ProcessedEvent
from src.models.recurrence import Recurrence
from src.models.reminder import Reminder
from src.models.task import Task
from src.models.user import User

__all__ = [
    "Conversation",
    "Message",
    "MessageRole",
    "ProcessedEvent",
    "Recurrence",
    "RecurrenceType",
    "Reminder",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "User",
]

"""Data models for conversation persistence and task management."""

from enum import Enum


class MessageRole(str, Enum):
    """Role of a message sender in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


from src.models.conversation import Conversation
from src.models.message import Message
from src.models.task import Task, TaskStatus

__all__ = ["Conversation", "Message", "MessageRole", "Task", "TaskStatus"]

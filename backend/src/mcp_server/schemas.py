"""Pydantic schemas for MCP tool responses.

These schemas define the structured responses returned by all MCP tools.
They ensure consistent response formats and enable AI agents to interpret
results programmatically.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TaskData(BaseModel):
    """Task data returned by MCP tools.

    This schema matches the contracts defined in contracts/mcp-tools.md.
    Extended for Phase V with priority, tags, reminders, and recurrence.
    """

    id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str = "medium"
    tags: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    has_reminders: bool = False
    has_recurrence: bool = False


class ToolResult(BaseModel):
    """Standard response from all MCP task tools.

    All tools return a structured response with:
    - success: Whether the operation succeeded
    - data: The result data (TaskData, list of TaskData, or None)
    - error: Human-readable error message if failed
    - error_code: Machine-readable error code if failed
    - event_published: Whether a Dapr event was published

    Error codes:
    - VALIDATION_ERROR: Input validation failed
    - NOT_FOUND: Task with given ID does not exist
    - ACCESS_DENIED: User does not own the task
    - DATABASE_ERROR: Database operation failed
    """

    success: bool
    data: Optional[TaskData | list[TaskData]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    event_published: bool = False

"""Pydantic schemas for MCP tool responses.

These schemas define the structured responses returned by all MCP tools.
They ensure consistent response formats and enable AI agents to interpret
results programmatically.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TaskData(BaseModel):
    """Task data returned by MCP tools.

    This schema matches the contracts defined in contracts/mcp-tools.md.
    """

    id: UUID
    description: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ToolResult(BaseModel):
    """Standard response from all MCP task tools.

    All tools return a structured response with:
    - success: Whether the operation succeeded
    - data: The result data (TaskData, list of TaskData, or None)
    - error: Human-readable error message if failed
    - error_code: Machine-readable error code if failed

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

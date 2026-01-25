"""MCP tool for updating tasks.

This tool allows AI agents to modify task fields including title, description,
priority, and tags. Status changes require complete_task for completion.
Extended for Phase V with priority, tags, and event publishing.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from mcp.server.fastmcp import Context
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.events.publisher import get_event_publisher
from src.events.schemas import FieldChange
from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models import Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


def _get_db_engine(ctx: Optional[Context]):
    """Get database engine from context or fallback to global engine."""
    if ctx is not None:
        app_context: AppContext = ctx.request_context.lifespan_context
        return app_context.engine
    return get_engine()


def _validate_priority(priority: Optional[str]) -> Optional[TaskPriority]:
    """Validate and convert priority string to enum."""
    if priority is None:
        return None
    priority_lower = priority.lower()
    if priority_lower not in ["high", "medium", "low"]:
        return None  # Invalid
    return TaskPriority(priority_lower)


def _validate_tags(tags: Optional[List[str]]) -> tuple[bool, str, List[str]]:
    """Validate tags list."""
    if tags is None:
        return True, "", []
    if len(tags) > 10:
        return False, "Maximum 10 tags allowed", []
    cleaned = []
    for tag in tags:
        if len(tag) > 50:
            return False, "Each tag must be 50 characters or less", []
        cleaned.append(tag.strip())
    return True, "", cleaned


@mcp.tool()
async def update_task(
    user_id: str,
    task_id: str,
    ctx: Optional[Context] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> ToolResult:
    """Update fields of an existing task.

    Args:
        user_id: The authenticated user's ID (externally provided)
        task_id: The UUID of the task to update
        ctx: MCP context (optional, uses global engine if not provided)
        title: New task title (1-200 characters)
        description: New task description (max 2000 characters)
        priority: New priority: "high", "medium", or "low"
        tags: New list of tags (replaces existing)
        status: New status: "pending", "in_progress" (not "completed" - use complete_task)

    Returns:
        ToolResult with the updated task data, or error if validation fails
    """
    # Validate user_id
    if not user_id or not user_id.strip():
        return ToolResult(
            success=False,
            error="user_id is required",
            error_code="VALIDATION_ERROR",
        )

    # Validate task_id format
    try:
        task_uuid = UUID(task_id)
    except (ValueError, AttributeError):
        return ToolResult(
            success=False,
            error="Invalid task_id format",
            error_code="VALIDATION_ERROR",
        )

    # Validate title length
    if title is not None and len(title) > 200:
        return ToolResult(
            success=False,
            error="Title exceeds 200 characters",
            error_code="VALIDATION_ERROR",
        )

    # Validate description length
    if description is not None and len(description) > 2000:
        return ToolResult(
            success=False,
            error="Description exceeds 2000 characters",
            error_code="VALIDATION_ERROR",
        )

    # Validate priority
    task_priority = None
    if priority is not None:
        task_priority = _validate_priority(priority)
        if task_priority is None:
            return ToolResult(
                success=False,
                error="Invalid priority. Must be 'high', 'medium', or 'low'",
                error_code="VALIDATION_ERROR",
            )

    # Validate tags
    if tags is not None:
        tags_valid, tags_error, cleaned_tags = _validate_tags(tags)
        if not tags_valid:
            return ToolResult(
                success=False,
                error=tags_error,
                error_code="VALIDATION_ERROR",
            )
    else:
        cleaned_tags = None

    # Validate status (not completed - use complete_task for that)
    task_status = None
    if status is not None:
        status_lower = status.lower()
        if status_lower == "completed":
            return ToolResult(
                success=False,
                error="Use complete_task to mark a task as completed",
                error_code="VALIDATION_ERROR",
            )
        if status_lower not in ["pending", "in_progress"]:
            return ToolResult(
                success=False,
                error="Invalid status. Must be 'pending' or 'in_progress'",
                error_code="VALIDATION_ERROR",
            )
        task_status = TaskStatus(status_lower)

    event_published = False

    try:
        engine = _get_db_engine(ctx)

        async with AsyncSession(engine) as session:
            stmt = select(Task).where(Task.id == task_uuid)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                return ToolResult(
                    success=False,
                    error="Task not found",
                    error_code="NOT_FOUND",
                )

            if task.user_id != user_id.strip():
                return ToolResult(
                    success=False,
                    error="Access denied",
                    error_code="ACCESS_DENIED",
                )

            # Track changes for event
            changes = {}

            if title is not None and title.strip() != task.title:
                changes["title"] = FieldChange(old_value=task.title, new_value=title.strip())
                task.title = title.strip()

            if description is not None and description.strip() != task.description:
                changes["description"] = FieldChange(old_value=task.description, new_value=description.strip())
                task.description = description.strip()

            if task_priority is not None and task_priority != task.priority:
                changes["priority"] = FieldChange(old_value=task.priority.value, new_value=task_priority.value)
                task.priority = task_priority

            if cleaned_tags is not None and cleaned_tags != task.tags:
                changes["tags"] = FieldChange(old_value=task.tags, new_value=cleaned_tags)
                task.tags = cleaned_tags

            if task_status is not None and task_status != task.status:
                changes["status"] = FieldChange(old_value=task.status.value, new_value=task_status.value)
                task.status = task_status

            task.updated_at = datetime.utcnow()

            session.add(task)
            await session.commit()
            await session.refresh(task)

            # Publish TaskUpdated event if there are changes
            if changes:
                try:
                    publisher = get_event_publisher()
                    event_published = await publisher.publish_task_updated(task, changes)
                except Exception as e:
                    logger.error(f"Failed to publish TaskUpdated event: {e}")

            return ToolResult(
                success=True,
                data=TaskData(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status.value,
                    priority=task.priority.value,
                    tags=task.tags or [],
                    due_date=task.due_date,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    completed_at=task.completed_at,
                    has_reminders=bool(task.reminders),
                    has_recurrence=task.recurrence is not None,
                ),
                event_published=event_published,
            )

    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Database error: {str(e)}",
            error_code="DATABASE_ERROR",
        )

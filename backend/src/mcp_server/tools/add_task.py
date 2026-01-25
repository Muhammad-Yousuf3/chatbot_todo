"""MCP tool for creating new tasks.

This tool allows AI agents to create new todo tasks for authenticated users.
Tasks are created with 'pending' status and the current timestamp.
Extended for Phase V with priority, tags, and event publishing.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from mcp.server.fastmcp import Context
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.events.publisher import get_event_publisher
from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models import Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


def _get_db_engine(ctx: Optional[Context]):
    """Get database engine from context or fallback to global engine.

    When called via MCP protocol, ctx provides the engine.
    When called directly via ToolExecutor, ctx is None, so we use get_engine().
    """
    if ctx is not None:
        app_context: AppContext = ctx.request_context.lifespan_context
        return app_context.engine
    return get_engine()


def _validate_priority(priority: Optional[str]) -> Optional[TaskPriority]:
    """Validate and convert priority string to enum."""
    if priority is None:
        return TaskPriority.MEDIUM
    priority_lower = priority.lower()
    if priority_lower not in ["high", "medium", "low"]:
        return None
    return TaskPriority(priority_lower)


def _validate_tags(tags: Optional[List[str]]) -> tuple[bool, str, List[str]]:
    """Validate tags list. Returns (valid, error_message, cleaned_tags)."""
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
async def add_task(
    user_id: str,
    title: str,
    ctx: Optional[Context] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> ToolResult:
    """Create a new task for the specified user.

    Args:
        user_id: The authenticated user's ID (externally provided)
        title: Task title (1-200 characters)
        ctx: MCP context (optional, uses global engine if not provided)
        description: Optional task description (max 2000 characters)
        due_date: Optional due date in ISO format (e.g., "2026-01-15" or "2026-01-15T10:00:00")
        priority: Optional priority: "high", "medium", or "low" (default: "medium")
        tags: Optional list of tags (max 10 tags, each max 50 characters)

    Returns:
        ToolResult with the created task data, or error if validation fails
    """
    # Validate user_id
    if not user_id or not user_id.strip():
        return ToolResult(
            success=False,
            error="user_id is required",
            error_code="VALIDATION_ERROR",
        )

    # Validate title is not empty
    if not title or not title.strip():
        return ToolResult(
            success=False,
            error="Title cannot be empty",
            error_code="VALIDATION_ERROR",
        )

    # Validate title length
    if len(title) > 200:
        return ToolResult(
            success=False,
            error="Title exceeds 200 characters",
            error_code="VALIDATION_ERROR",
        )

    # Validate description length
    if description and len(description) > 2000:
        return ToolResult(
            success=False,
            error="Description exceeds 2000 characters",
            error_code="VALIDATION_ERROR",
        )

    # Validate priority
    task_priority = _validate_priority(priority)
    if priority is not None and task_priority is None:
        return ToolResult(
            success=False,
            error="Invalid priority. Must be 'high', 'medium', or 'low'",
            error_code="VALIDATION_ERROR",
        )

    # Validate tags
    tags_valid, tags_error, cleaned_tags = _validate_tags(tags)
    if not tags_valid:
        return ToolResult(
            success=False,
            error=tags_error,
            error_code="VALIDATION_ERROR",
        )

    # Parse due_date if provided
    parsed_due_date: Optional[datetime] = None
    if due_date:
        try:
            # Try ISO format first
            if "T" in due_date:
                parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            else:
                # Date only - set to midnight
                parsed_due_date = datetime.fromisoformat(f"{due_date}T00:00:00")
        except ValueError:
            return ToolResult(
                success=False,
                error=f"Invalid due_date format: {due_date}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                error_code="VALIDATION_ERROR",
            )

    event_published = False

    try:
        # Get engine from context or fallback
        engine = _get_db_engine(ctx)

        # Create and persist task
        async with AsyncSession(engine) as session:
            now = datetime.utcnow()
            task = Task(
                id=uuid4(),
                user_id=user_id.strip(),
                title=title.strip(),
                description=description.strip() if description else None,
                status=TaskStatus.PENDING,
                priority=task_priority,
                tags=cleaned_tags,
                due_date=parsed_due_date,
                created_at=now,
                updated_at=now,
                completed_at=None,
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            # Publish TaskCreated event
            try:
                publisher = get_event_publisher()
                event_published = await publisher.publish_task_created(task)
            except Exception as e:
                logger.error(f"Failed to publish TaskCreated event: {e}")

            # Return success with task data
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
                    has_reminders=False,
                    has_recurrence=False,
                ),
                event_published=event_published,
            )

    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Database error: {str(e)}",
            error_code="DATABASE_ERROR",
        )

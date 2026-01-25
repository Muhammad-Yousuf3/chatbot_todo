"""MCP tool for listing user's tasks.

This tool allows AI agents to retrieve tasks belonging to an authenticated user.
Supports filtering by status, priority, and tags.
Tasks are returned sorted by created_at descending (newest first).
Extended for Phase V with filtering capabilities.
"""

from typing import List, Optional

from mcp.server.fastmcp import Context
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models import Task, TaskPriority, TaskStatus


def _get_db_engine(ctx: Optional[Context]):
    """Get database engine from context or fallback to global engine."""
    if ctx is not None:
        app_context: AppContext = ctx.request_context.lifespan_context
        return app_context.engine
    return get_engine()


@mcp.tool()
async def list_tasks(
    user_id: str,
    ctx: Optional[Context] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
) -> ToolResult:
    """Retrieve tasks for the specified user with optional filtering.

    Args:
        user_id: The authenticated user's ID (externally provided)
        ctx: MCP context (optional, uses global engine if not provided)
        status: Optional filter by status: "pending", "in_progress", or "completed"
        priority: Optional filter by priority: "high", "medium", or "low"
        tag: Optional filter by tag (must contain this tag)

    Returns:
        ToolResult with list of tasks sorted by created_at descending,
        or error if validation fails
    """
    # Validate user_id
    if not user_id or not user_id.strip():
        return ToolResult(
            success=False,
            error="user_id is required",
            error_code="VALIDATION_ERROR",
        )

    # Validate status filter
    task_status = None
    if status is not None:
        status_lower = status.lower()
        if status_lower not in ["pending", "in_progress", "completed"]:
            return ToolResult(
                success=False,
                error="Invalid status. Must be 'pending', 'in_progress', or 'completed'",
                error_code="VALIDATION_ERROR",
            )
        task_status = TaskStatus(status_lower)

    # Validate priority filter
    task_priority = None
    if priority is not None:
        priority_lower = priority.lower()
        if priority_lower not in ["high", "medium", "low"]:
            return ToolResult(
                success=False,
                error="Invalid priority. Must be 'high', 'medium', or 'low'",
                error_code="VALIDATION_ERROR",
            )
        task_priority = TaskPriority(priority_lower)

    try:
        engine = _get_db_engine(ctx)

        async with AsyncSession(engine) as session:
            stmt = select(Task).where(Task.user_id == user_id.strip())

            # Apply filters
            if task_status is not None:
                stmt = stmt.where(Task.status == task_status)

            if task_priority is not None:
                stmt = stmt.where(Task.priority == task_priority)

            if tag is not None:
                stmt = stmt.where(Task.tags.contains([tag.strip()]))

            # Sort by created_at descending
            stmt = stmt.order_by(Task.created_at.desc())

            result = await session.execute(stmt)
            tasks = result.scalars().all()

            # Convert to TaskData list
            task_data_list = [
                TaskData(
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
                )
                for task in tasks
            ]

            return ToolResult(
                success=True,
                data=task_data_list,
            )

    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Database error: {str(e)}",
            error_code="DATABASE_ERROR",
        )

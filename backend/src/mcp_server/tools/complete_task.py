"""MCP tool for completing tasks.

This tool allows AI agents to mark tasks as completed.
Completing a task sets status to 'completed' and records the completion timestamp.
The operation is idempotent - completing an already completed task succeeds without error.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from mcp.server.fastmcp import Context
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models.task import Task, TaskStatus


def _get_db_engine(ctx: Optional[Context]):
    """Get database engine from context or fallback to global engine."""
    if ctx is not None:
        app_context: AppContext = ctx.request_context.lifespan_context
        return app_context.engine
    return get_engine()


@mcp.tool()
async def complete_task(
    user_id: str,
    task_id: str,
    ctx: Optional[Context] = None,
) -> ToolResult:
    """Mark a task as completed.

    Args:
        user_id: The authenticated user's ID (externally provided)
        task_id: The UUID of the task to complete
        ctx: MCP context (optional, uses global engine if not provided)

    Returns:
        ToolResult with the completed task data, or error if validation fails
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

    try:
        # Get engine from context or fallback
        engine = _get_db_engine(ctx)

        async with AsyncSession(engine) as session:
            # Find the task
            stmt = select(Task).where(Task.id == task_uuid)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                return ToolResult(
                    success=False,
                    error="Task not found",
                    error_code="NOT_FOUND",
                )

            # Verify ownership
            if task.user_id != user_id.strip():
                return ToolResult(
                    success=False,
                    error="Access denied",
                    error_code="ACCESS_DENIED",
                )

            # Idempotent: if already completed, return success without updating
            if task.status == TaskStatus.COMPLETED:
                return ToolResult(
                    success=True,
                    data=TaskData(
                        id=task.id,
                        description=task.description,
                        status=task.status.value,
                        due_date=task.due_date,
                        created_at=task.created_at,
                        completed_at=task.completed_at,
                    ),
                )

            # Complete the task
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            session.add(task)
            await session.commit()
            await session.refresh(task)

            # Return success with completed task data
            return ToolResult(
                success=True,
                data=TaskData(
                    id=task.id,
                    description=task.description,
                    status=task.status.value,
                    due_date=task.due_date,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                ),
            )

    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Database error: {str(e)}",
            error_code="DATABASE_ERROR",
        )

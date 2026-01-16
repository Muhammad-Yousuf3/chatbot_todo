"""MCP tool for listing user's tasks.

This tool allows AI agents to retrieve all tasks belonging to an authenticated user.
Tasks are returned sorted by created_at descending (newest first).
"""

from typing import Optional

from mcp.server.fastmcp import Context
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models.task import Task


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
) -> ToolResult:
    """Retrieve all tasks for the specified user.

    Args:
        user_id: The authenticated user's ID (externally provided)
        ctx: MCP context (optional, uses global engine if not provided)

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

    try:
        # Get engine from context or fallback
        engine = _get_db_engine(ctx)

        # Query tasks for user, sorted by created_at descending
        async with AsyncSession(engine) as session:
            stmt = (
                select(Task)
                .where(Task.user_id == user_id.strip())
                .order_by(Task.created_at.desc())
            )
            result = await session.execute(stmt)
            tasks = result.scalars().all()

            # Convert to TaskData list
            task_data_list = [
                TaskData(
                    id=task.id,
                    description=task.description,
                    status=task.status.value,
                    due_date=task.due_date,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
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

"""MCP tool for creating new tasks.

This tool allows AI agents to create new todo tasks for authenticated users.
Tasks are created with 'pending' status and the current timestamp.
"""

from datetime import datetime
from uuid import uuid4

from mcp.server.fastmcp import Context
from sqlmodel.ext.asyncio.session import AsyncSession

from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models.task import Task, TaskStatus


@mcp.tool()
async def add_task(
    user_id: str,
    description: str,
    ctx: Context,
) -> ToolResult:
    """Create a new task for the specified user.

    Args:
        user_id: The authenticated user's ID (externally provided)
        description: Task description (1-1000 characters)

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

    # Validate description is not empty
    if not description or not description.strip():
        return ToolResult(
            success=False,
            error="Description cannot be empty",
            error_code="VALIDATION_ERROR",
        )

    # Validate description length
    if len(description) > 1000:
        return ToolResult(
            success=False,
            error="Description exceeds 1000 characters",
            error_code="VALIDATION_ERROR",
        )

    try:
        # Get engine from context
        app_context: AppContext = ctx.request_context.lifespan_context
        engine = app_context.engine

        # Create and persist task
        async with AsyncSession(engine) as session:
            task = Task(
                id=uuid4(),
                user_id=user_id.strip(),
                description=description.strip(),
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                completed_at=None,
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            # Return success with task data
            return ToolResult(
                success=True,
                data=TaskData(
                    id=task.id,
                    description=task.description,
                    status=task.status.value,
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

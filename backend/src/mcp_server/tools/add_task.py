"""MCP tool for creating new tasks.

This tool allows AI agents to create new todo tasks for authenticated users.
Tasks are created with 'pending' status and the current timestamp.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from mcp.server.fastmcp import Context
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.mcp_server.schemas import TaskData, ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models.task import Task, TaskStatus


def _get_db_engine(ctx: Optional[Context]):
    """Get database engine from context or fallback to global engine.

    When called via MCP protocol, ctx provides the engine.
    When called directly via ToolExecutor, ctx is None, so we use get_engine().
    """
    if ctx is not None:
        app_context: AppContext = ctx.request_context.lifespan_context
        return app_context.engine
    return get_engine()


@mcp.tool()
async def add_task(
    user_id: str,
    description: str,
    ctx: Optional[Context] = None,
    due_date: Optional[str] = None,
) -> ToolResult:
    """Create a new task for the specified user.

    Args:
        user_id: The authenticated user's ID (externally provided)
        description: Task description (1-1000 characters)
        ctx: MCP context (optional, uses global engine if not provided)
        due_date: Optional due date in ISO format (e.g., "2026-01-15" or "2026-01-15T10:00:00")

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

    try:
        # Get engine from context or fallback
        engine = _get_db_engine(ctx)

        # Create and persist task
        async with AsyncSession(engine) as session:
            task = Task(
                id=uuid4(),
                user_id=user_id.strip(),
                description=description.strip(),
                status=TaskStatus.PENDING,
                due_date=parsed_due_date,
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

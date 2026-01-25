"""MCP tool for deleting tasks.

This tool allows AI agents to permanently remove tasks.
The operation is idempotent - deleting a non-existent task succeeds without error.
Ownership is verified before deletion if the task exists.
Extended for Phase V with event publishing.
"""

import logging
from typing import Optional
from uuid import UUID

from mcp.server.fastmcp import Context
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.engine import get_engine
from src.events.publisher import get_event_publisher
from src.mcp_server.schemas import ToolResult
from src.mcp_server.server import AppContext, mcp
from src.models import Task

logger = logging.getLogger(__name__)


def _get_db_engine(ctx: Optional[Context]):
    """Get database engine from context or fallback to global engine."""
    if ctx is not None:
        app_context: AppContext = ctx.request_context.lifespan_context
        return app_context.engine
    return get_engine()


@mcp.tool()
async def delete_task(
    user_id: str,
    task_id: str,
    ctx: Optional[Context] = None,
) -> ToolResult:
    """Permanently delete a task.

    Args:
        user_id: The authenticated user's ID (externally provided)
        task_id: The UUID of the task to delete
        ctx: MCP context (optional, uses global engine if not provided)

    Returns:
        ToolResult with null data on success, or error if validation fails
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

    event_published = False

    try:
        engine = _get_db_engine(ctx)

        async with AsyncSession(engine) as session:
            stmt = select(Task).where(Task.id == task_uuid)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            # Idempotent: if task doesn't exist, return success
            if task is None:
                return ToolResult(
                    success=True,
                    data=None,
                    event_published=False,
                )

            # Verify ownership before deletion
            if task.user_id != user_id.strip():
                return ToolResult(
                    success=False,
                    error="Access denied",
                    error_code="ACCESS_DENIED",
                )

            # Store task info for event before deletion
            task_id_str = str(task.id)
            task_user_id = task.user_id

            # Delete the task
            await session.delete(task)
            await session.commit()

            # Publish TaskDeleted event
            try:
                publisher = get_event_publisher()
                event_published = await publisher.publish_task_deleted(task_id_str, task_user_id)
            except Exception as e:
                logger.error(f"Failed to publish TaskDeleted event: {e}")

            return ToolResult(
                success=True,
                data=None,
                event_published=event_published,
            )

    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Database error: {str(e)}",
            error_code="DATABASE_ERROR",
        )

"""Unit tests for delete_task MCP tool.

Tests cover:
- Deleting a task successfully
- Idempotent deletion (deleting non-existent task)
- Access denied (user doesn't own task)
- Validation errors (invalid task_id, missing user_id)
"""

import pytest
from uuid import uuid4

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from tests.mcp.conftest import create_test_task
from src.models.task import Task, TaskStatus
from src.mcp_server.tools.delete_task import delete_task


@pytest.mark.asyncio
async def test_delete_task_success(mock_ctx, test_session):
    """Test successfully deleting a task."""
    # Create a task
    task = await create_test_task(test_session, "test-user-1", "Task to delete")
    task_id = str(task.id)

    result = await delete_task(
        user_id="test-user-1",
        task_id=task_id,
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is None

    # Verify task no longer exists in database
    stmt = select(Task).where(Task.id == task.id)
    db_result = await test_session.execute(stmt)
    deleted_task = db_result.scalar_one_or_none()
    assert deleted_task is None


@pytest.mark.asyncio
async def test_delete_task_idempotent(mock_ctx):
    """Test that deleting a non-existent task is idempotent (returns success)."""
    non_existent_id = str(uuid4())

    result = await delete_task(
        user_id="test-user-1",
        task_id=non_existent_id,
        ctx=mock_ctx,
    )

    # Should succeed even if task doesn't exist
    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is None


@pytest.mark.asyncio
async def test_delete_task_access_denied(mock_ctx, test_session):
    """Test that users cannot delete tasks they don't own."""
    # Create a task for User A
    task = await create_test_task(test_session, "user-A", "User A's task")
    task_id = str(task.id)

    # Try to delete as User B
    result = await delete_task(
        user_id="user-B",
        task_id=task_id,
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "ACCESS_DENIED"
    assert "access denied" in result.error.lower()
    assert result.data is None

    # Verify task still exists
    stmt = select(Task).where(Task.id == task.id)
    db_result = await test_session.execute(stmt)
    existing_task = db_result.scalar_one_or_none()
    assert existing_task is not None


@pytest.mark.asyncio
async def test_delete_task_invalid_task_id_format(mock_ctx):
    """Test validation error for invalid task_id format."""
    result = await delete_task(
        user_id="test-user-1",
        task_id="not-a-uuid",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "task_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_delete_task_missing_user_id(mock_ctx, test_session):
    """Test validation error for missing user_id."""
    task = await create_test_task(test_session, "test-user-1", "Test task")

    result = await delete_task(
        user_id="",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "user_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_delete_completed_task(mock_ctx, test_session):
    """Test deleting a completed task."""
    # Create a completed task
    task = await create_test_task(
        test_session, "test-user-1", "Completed task", TaskStatus.COMPLETED
    )
    task_id = str(task.id)

    result = await delete_task(
        user_id="test-user-1",
        task_id=task_id,
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.data is None

    # Verify task is deleted
    stmt = select(Task).where(Task.id == task.id)
    db_result = await test_session.execute(stmt)
    deleted_task = db_result.scalar_one_or_none()
    assert deleted_task is None

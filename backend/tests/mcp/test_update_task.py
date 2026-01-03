"""Unit tests for update_task MCP tool.

Tests cover:
- Updating task description successfully
- Task not found
- Access denied (user doesn't own task)
- Validation errors (empty description, too long, invalid task_id)
"""

import pytest
from uuid import uuid4

from tests.mcp.conftest import create_test_task
from src.models.task import TaskStatus
from src.mcp_server.tools.update_task import update_task


@pytest.mark.asyncio
async def test_update_task_success(mock_ctx, test_session):
    """Test successfully updating a task's description."""
    # Create a task
    task = await create_test_task(test_session, "test-user-1", "Original description")

    result = await update_task(
        user_id="test-user-1",
        task_id=str(task.id),
        description="Updated description",
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is not None
    assert result.data.description == "Updated description"
    assert result.data.id == task.id


@pytest.mark.asyncio
async def test_update_task_not_found(mock_ctx):
    """Test error when task doesn't exist."""
    non_existent_id = str(uuid4())

    result = await update_task(
        user_id="test-user-1",
        task_id=non_existent_id,
        description="New description",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "NOT_FOUND"
    assert "not found" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_update_task_access_denied(mock_ctx, test_session):
    """Test that users cannot update tasks they don't own."""
    # Create a task for User A
    task = await create_test_task(test_session, "user-A", "User A's task")

    # Try to update as User B
    result = await update_task(
        user_id="user-B",
        task_id=str(task.id),
        description="Hijacked!",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "ACCESS_DENIED"
    assert "access denied" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_update_task_empty_description(mock_ctx, test_session):
    """Test validation error for empty description."""
    task = await create_test_task(test_session, "test-user-1", "Original")

    result = await update_task(
        user_id="test-user-1",
        task_id=str(task.id),
        description="",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "description" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_update_task_description_too_long(mock_ctx, test_session):
    """Test validation error for description exceeding 1000 characters."""
    task = await create_test_task(test_session, "test-user-1", "Original")
    long_description = "x" * 1001

    result = await update_task(
        user_id="test-user-1",
        task_id=str(task.id),
        description=long_description,
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "1000" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_update_task_invalid_task_id_format(mock_ctx):
    """Test validation error for invalid task_id format."""
    result = await update_task(
        user_id="test-user-1",
        task_id="not-a-uuid",
        description="New description",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "task_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_update_task_missing_user_id(mock_ctx, test_session):
    """Test validation error for missing user_id."""
    task = await create_test_task(test_session, "test-user-1", "Original")

    result = await update_task(
        user_id="",
        task_id=str(task.id),
        description="New description",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "user_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_update_task_preserves_status(mock_ctx, test_session):
    """Test that updating description doesn't change status."""
    # Create a completed task
    task = await create_test_task(
        test_session, "test-user-1", "Completed task", TaskStatus.COMPLETED
    )

    result = await update_task(
        user_id="test-user-1",
        task_id=str(task.id),
        description="Updated description",
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.data.status == "completed"  # Status unchanged


@pytest.mark.asyncio
async def test_update_task_preserves_timestamps(mock_ctx, test_session):
    """Test that updating description doesn't change created_at or completed_at."""
    task = await create_test_task(
        test_session, "test-user-1", "Original", TaskStatus.COMPLETED
    )
    original_created_at = task.created_at
    original_completed_at = task.completed_at

    result = await update_task(
        user_id="test-user-1",
        task_id=str(task.id),
        description="Updated",
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.data.created_at == original_created_at
    assert result.data.completed_at == original_completed_at

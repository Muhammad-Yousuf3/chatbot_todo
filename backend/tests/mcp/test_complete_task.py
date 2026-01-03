"""Unit tests for complete_task MCP tool.

Tests cover:
- Completing a pending task successfully
- Idempotent completion (already completed task)
- Task not found
- Access denied (user doesn't own task)
- Validation errors (invalid task_id, missing user_id)
"""

import pytest
from uuid import uuid4

from tests.mcp.conftest import create_test_task
from src.models.task import TaskStatus
from src.mcp_server.tools.complete_task import complete_task


@pytest.mark.asyncio
async def test_complete_task_success(mock_ctx, test_session):
    """Test successfully completing a pending task."""
    # Create a pending task
    task = await create_test_task(test_session, "test-user-1", "Task to complete")

    result = await complete_task(
        user_id="test-user-1",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is not None
    assert result.data.id == task.id
    assert result.data.status == "completed"
    assert result.data.completed_at is not None


@pytest.mark.asyncio
async def test_complete_task_idempotent(mock_ctx, test_session):
    """Test that completing an already completed task is idempotent."""
    # Create a completed task
    task = await create_test_task(
        test_session, "test-user-1", "Already completed", TaskStatus.COMPLETED
    )
    original_completed_at = task.completed_at

    result = await complete_task(
        user_id="test-user-1",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    # Should succeed without error
    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is not None
    assert result.data.status == "completed"
    # Should NOT update completed_at timestamp
    assert result.data.completed_at == original_completed_at


@pytest.mark.asyncio
async def test_complete_task_not_found(mock_ctx):
    """Test error when task doesn't exist."""
    non_existent_id = str(uuid4())

    result = await complete_task(
        user_id="test-user-1",
        task_id=non_existent_id,
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "NOT_FOUND"
    assert "not found" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_complete_task_access_denied(mock_ctx, test_session):
    """Test that users cannot complete tasks they don't own."""
    # Create a task for User A
    task = await create_test_task(test_session, "user-A", "User A's task")

    # Try to complete as User B
    result = await complete_task(
        user_id="user-B",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "ACCESS_DENIED"
    assert "access denied" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_complete_task_invalid_task_id_format(mock_ctx):
    """Test validation error for invalid task_id format."""
    result = await complete_task(
        user_id="test-user-1",
        task_id="not-a-uuid",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "task_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_complete_task_missing_user_id(mock_ctx, test_session):
    """Test validation error for missing user_id."""
    task = await create_test_task(test_session, "test-user-1", "Test task")

    result = await complete_task(
        user_id="",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "user_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_complete_task_preserves_description(mock_ctx, test_session):
    """Test that completing a task doesn't change description."""
    task = await create_test_task(
        test_session, "test-user-1", "Original description"
    )

    result = await complete_task(
        user_id="test-user-1",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.data.description == "Original description"


@pytest.mark.asyncio
async def test_complete_task_preserves_created_at(mock_ctx, test_session):
    """Test that completing a task doesn't change created_at."""
    task = await create_test_task(test_session, "test-user-1", "Test task")
    original_created_at = task.created_at

    result = await complete_task(
        user_id="test-user-1",
        task_id=str(task.id),
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.data.created_at == original_created_at

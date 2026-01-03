"""Unit tests for list_tasks MCP tool.

Tests cover:
- Listing tasks for a user with multiple tasks
- Empty list when user has no tasks
- User isolation (User A cannot see User B's tasks)
- Tasks sorted by created_at descending
"""

import pytest
from datetime import datetime, timedelta

from tests.mcp.conftest import create_test_task
from src.models.task import TaskStatus
from src.mcp_server.tools.list_tasks import list_tasks


@pytest.mark.asyncio
async def test_list_tasks_with_tasks(mock_ctx, test_session):
    """Test listing tasks for a user with multiple tasks."""
    # Create some tasks for the user
    await create_test_task(test_session, "test-user-1", "Task 1")
    await create_test_task(test_session, "test-user-1", "Task 2")
    await create_test_task(test_session, "test-user-1", "Task 3", TaskStatus.COMPLETED)

    result = await list_tasks(user_id="test-user-1", ctx=mock_ctx)

    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is not None
    assert isinstance(result.data, list)
    assert len(result.data) == 3


@pytest.mark.asyncio
async def test_list_tasks_empty_list(mock_ctx, test_session):
    """Test that empty list is returned when user has no tasks."""
    result = await list_tasks(user_id="user-with-no-tasks", ctx=mock_ctx)

    assert result.success is True
    assert result.error is None
    assert result.data is not None
    assert isinstance(result.data, list)
    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_list_tasks_user_isolation(mock_ctx, test_session):
    """Test that users can only see their own tasks."""
    # Create tasks for User A
    await create_test_task(test_session, "user-A", "User A task 1")
    await create_test_task(test_session, "user-A", "User A task 2")
    await create_test_task(test_session, "user-A", "User A task 3")

    # Create tasks for User B
    await create_test_task(test_session, "user-B", "User B task 1")
    await create_test_task(test_session, "user-B", "User B task 2")

    # User A should only see their 3 tasks
    result_a = await list_tasks(user_id="user-A", ctx=mock_ctx)
    assert result_a.success is True
    assert len(result_a.data) == 3
    for task in result_a.data:
        assert "User A" in task.description

    # User B should only see their 2 tasks
    result_b = await list_tasks(user_id="user-B", ctx=mock_ctx)
    assert result_b.success is True
    assert len(result_b.data) == 2
    for task in result_b.data:
        assert "User B" in task.description


@pytest.mark.asyncio
async def test_list_tasks_sorted_by_created_at_desc(mock_ctx, test_session):
    """Test that tasks are sorted by created_at descending (newest first)."""
    # Create tasks with specific order
    await create_test_task(test_session, "test-user-1", "Oldest task")
    await create_test_task(test_session, "test-user-1", "Middle task")
    await create_test_task(test_session, "test-user-1", "Newest task")

    result = await list_tasks(user_id="test-user-1", ctx=mock_ctx)

    assert result.success is True
    assert len(result.data) == 3
    # Verify descending order (newest first)
    dates = [task.created_at for task in result.data]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.asyncio
async def test_list_tasks_missing_user_id(mock_ctx):
    """Test validation error for missing user_id."""
    result = await list_tasks(user_id="", ctx=mock_ctx)

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "user_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_list_tasks_includes_all_statuses(mock_ctx, test_session):
    """Test that both pending and completed tasks are returned."""
    await create_test_task(test_session, "test-user-1", "Pending 1", TaskStatus.PENDING)
    await create_test_task(test_session, "test-user-1", "Pending 2", TaskStatus.PENDING)
    await create_test_task(test_session, "test-user-1", "Completed 1", TaskStatus.COMPLETED)

    result = await list_tasks(user_id="test-user-1", ctx=mock_ctx)

    assert result.success is True
    assert len(result.data) == 3

    statuses = [task.status for task in result.data]
    assert "pending" in statuses
    assert "completed" in statuses

"""Unit tests for add_task MCP tool.

Tests cover:
- Successful task creation
- Empty description validation
- Description too long validation
- Missing user_id validation
"""

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.task import Task, TaskStatus
from src.mcp_server.tools.add_task import add_task


@pytest.mark.asyncio
async def test_add_task_success(mock_ctx, test_session: AsyncSession):
    """Test successful task creation."""
    result = await add_task(
        user_id="test-user-1",
        description="Buy groceries",
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    assert result.data is not None
    assert result.data.description == "Buy groceries"
    assert result.data.status == "pending"
    assert result.data.completed_at is None


@pytest.mark.asyncio
async def test_add_task_empty_description(mock_ctx):
    """Test validation error for empty description."""
    result = await add_task(
        user_id="test-user-1",
        description="",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "empty" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_add_task_description_too_long(mock_ctx):
    """Test validation error for description exceeding 1000 characters."""
    long_description = "x" * 1001

    result = await add_task(
        user_id="test-user-1",
        description=long_description,
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "1000" in result.error
    assert result.data is None


@pytest.mark.asyncio
async def test_add_task_missing_user_id(mock_ctx):
    """Test validation error for missing user_id."""
    result = await add_task(
        user_id="",
        description="Buy groceries",
        ctx=mock_ctx,
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "user_id" in result.error.lower()
    assert result.data is None


@pytest.mark.asyncio
async def test_add_task_creates_pending_status(mock_ctx, test_session: AsyncSession):
    """Test that new tasks are created with pending status."""
    result = await add_task(
        user_id="test-user-1",
        description="Test task",
        ctx=mock_ctx,
    )

    assert result.success is True
    assert result.data.status == TaskStatus.PENDING.value


@pytest.mark.asyncio
async def test_add_task_concurrent_users(mock_ctx):
    """Test that concurrent task creation for different users doesn't mix data."""
    # Create tasks for two different users
    result1 = await add_task(
        user_id="user-A",
        description="Task for user A",
        ctx=mock_ctx,
    )
    result2 = await add_task(
        user_id="user-B",
        description="Task for user B",
        ctx=mock_ctx,
    )

    assert result1.success is True
    assert result2.success is True
    assert result1.data.id != result2.data.id
    assert result1.data.description == "Task for user A"
    assert result2.data.description == "Task for user B"

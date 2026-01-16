"""Tests for the ToolExecutor.

Tests cover:
- Tool execution with correct parameters
- User ID injection
- Tool whitelist enforcement
- Error handling
"""

import pytest

from src.llm_runtime.errors import ToolNotFoundError
from src.llm_runtime.executor import ALLOWED_TOOLS, ToolExecutor


@pytest.mark.asyncio
async def test_execute_add_task() -> None:
    """Test executing add_task with mock registry."""
    executor = ToolExecutor()

    # Register a mock tool
    async def mock_add_task(user_id: str, description: str, **kwargs):
        return {
            "success": True,
            "data": {"id": "task-123", "description": description},
        }

    executor.set_tool("add_task", mock_add_task)

    result = await executor.execute(
        tool_name="add_task",
        parameters={"description": "Buy groceries"},
        user_id="test-user",
    )

    assert result.success is True
    assert result.data is not None
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_execute_list_tasks() -> None:
    """Test executing list_tasks with mock registry."""
    executor = ToolExecutor()

    async def mock_list_tasks(user_id: str, status: str = "all", **kwargs):
        return {
            "success": True,
            "data": {
                "tasks": [
                    {"id": "task-1", "description": "Task 1"},
                    {"id": "task-2", "description": "Task 2"},
                ]
            },
        }

    executor.set_tool("list_tasks", mock_list_tasks)

    result = await executor.execute(
        tool_name="list_tasks",
        parameters={"status": "pending"},
        user_id="test-user",
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_user_id_injection() -> None:
    """Test that user_id is injected into tool parameters."""
    executor = ToolExecutor()
    received_user_id = None

    async def capture_user_id(user_id: str, **kwargs):
        nonlocal received_user_id
        received_user_id = user_id
        return {"success": True}

    executor.set_tool("add_task", capture_user_id)

    await executor.execute(
        tool_name="add_task",
        parameters={"description": "test"},
        user_id="injected-user-123",
    )

    assert received_user_id == "injected-user-123"


@pytest.mark.asyncio
async def test_tool_not_in_whitelist() -> None:
    """Test that non-whitelisted tools raise ToolNotFoundError."""
    executor = ToolExecutor()

    with pytest.raises(ToolNotFoundError) as exc_info:
        await executor.execute(
            tool_name="delete_database",
            parameters={},
            user_id="test-user",
        )

    assert exc_info.value.tool_name == "delete_database"


@pytest.mark.asyncio
async def test_tool_execution_error_handling() -> None:
    """Test that tool execution errors are caught and returned."""
    executor = ToolExecutor()

    async def failing_tool(**kwargs):
        raise ValueError("Something went wrong")

    executor.set_tool("add_task", failing_tool)

    result = await executor.execute(
        tool_name="add_task",
        parameters={"description": "test"},
        user_id="test-user",
    )

    assert result.success is False
    assert result.error is not None
    assert "Something went wrong" in result.error
    assert result.error_code == "EXECUTION_ERROR"


def test_get_available_tools() -> None:
    """Test that available tools are returned correctly."""
    executor = ToolExecutor()

    # Register some mock tools
    async def mock_tool(**kwargs):
        return {"success": True}

    executor.set_tool("add_task", mock_tool)
    executor.set_tool("list_tasks", mock_tool)

    available = executor.get_available_tools()

    assert "add_task" in available
    assert "list_tasks" in available
    # Non-whitelisted tools should not appear
    assert "delete_database" not in available


def test_get_tool_declarations() -> None:
    """Test that tool declarations are generated correctly."""
    executor = ToolExecutor()

    # Register mock tools
    async def mock_tool(**kwargs):
        return {"success": True}

    for tool_name in ALLOWED_TOOLS:
        executor.set_tool(tool_name, mock_tool)

    declarations = executor.get_tool_declarations()

    assert len(declarations) == len(ALLOWED_TOOLS)

    # Verify each declaration has required fields
    for decl in declarations:
        assert decl.name in ALLOWED_TOOLS
        assert decl.description
        assert decl.parameters
        assert "type" in decl.parameters


def test_cannot_register_non_whitelisted_tool() -> None:
    """Test that non-whitelisted tools cannot be registered."""
    executor = ToolExecutor()

    async def mock_tool(**kwargs):
        return {"success": True}

    with pytest.raises(ValueError) as exc_info:
        executor.set_tool("malicious_tool", mock_tool)

    assert "not in the allowed tools list" in str(exc_info.value)


@pytest.mark.asyncio
async def test_result_serialization() -> None:
    """Test that various result types are serialized correctly."""
    executor = ToolExecutor()

    # Test with Pydantic-like model
    class MockModel:
        def model_dump(self, mode=None):
            return {"id": "123", "name": "test"}

    async def return_model(**kwargs):
        return MockModel()

    executor.set_tool("add_task", return_model)

    result = await executor.execute(
        tool_name="add_task",
        parameters={},
        user_id="test-user",
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_duration_tracking() -> None:
    """Test that execution duration is tracked."""
    import asyncio

    executor = ToolExecutor()

    async def slow_tool(**kwargs):
        await asyncio.sleep(0.05)  # 50ms delay
        return {"success": True}

    executor.set_tool("add_task", slow_tool)

    result = await executor.execute(
        tool_name="add_task",
        parameters={},
        user_id="test-user",
    )

    # Duration should be at least 50ms
    assert result.duration_ms >= 40  # Allow some tolerance

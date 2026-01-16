"""Pytest fixtures for LLM runtime tests."""

from datetime import datetime
from pathlib import Path

import pytest

from src.agent.schemas import DecisionContext, Message
from src.llm_runtime.schemas import (
    FunctionCall,
    LLMMessage,
    LLMResponse,
    TokenUsage,
    ToolDeclaration,
)
from tests.llm_runtime.mocks import MockLLMAdapter, MockToolExecutor


@pytest.fixture
def mock_llm_adapter() -> MockLLMAdapter:
    """Create a fresh mock LLM adapter."""
    return MockLLMAdapter()


@pytest.fixture
def mock_tool_executor() -> MockToolExecutor:
    """Create a fresh mock tool executor."""
    return MockToolExecutor()


@pytest.fixture
def constitution_text() -> str:
    """Load the constitution text for testing."""
    constitution_path = Path(__file__).parent.parent.parent / "src" / "llm_runtime" / "constitution.md"
    if constitution_path.exists():
        return constitution_path.read_text()
    # Fallback for tests that don't need the full constitution
    return "You are a helpful task management assistant."


@pytest.fixture
def sample_decision_context() -> DecisionContext:
    """Create a sample decision context for testing."""
    return DecisionContext(
        user_id="test-user-123",
        message="Add a task to buy groceries",
        conversation_id="conv-456",
        message_history=[],
        pending_confirmation=None,
    )


@pytest.fixture
def sample_context_with_history() -> DecisionContext:
    """Create a decision context with message history."""
    return DecisionContext(
        user_id="test-user-123",
        message="Mark the first one as done",
        conversation_id="conv-456",
        message_history=[
            Message(
                role="user",
                content="Show my tasks",
                timestamp=datetime.now(),
            ),
            Message(
                role="assistant",
                content="Here are your tasks: 1. Buy groceries 2. Call mom",
                timestamp=datetime.now(),
            ),
        ],
        pending_confirmation=None,
    )


@pytest.fixture
def tool_declarations() -> list[ToolDeclaration]:
    """Create standard tool declarations for testing."""
    return [
        ToolDeclaration(
            name="add_task",
            description="Create a new task. Use when user wants to add, create, or remember something.",
            parameters={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Task description"}
                },
                "required": ["description"],
            },
        ),
        ToolDeclaration(
            name="list_tasks",
            description="Get user's tasks. Use when user wants to see, view, or list their tasks.",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed", "all"],
                        "description": "Filter by status (default: all)",
                    }
                },
            },
        ),
        ToolDeclaration(
            name="update_task",
            description="Update a task's description.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to update"},
                    "description": {"type": "string", "description": "New description"},
                },
                "required": ["task_id", "description"],
            },
        ),
        ToolDeclaration(
            name="complete_task",
            description="Mark a task as completed.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to complete"}
                },
                "required": ["task_id"],
            },
        ),
        ToolDeclaration(
            name="delete_task",
            description="Delete a task permanently.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to delete"}
                },
                "required": ["task_id"],
            },
        ),
    ]


@pytest.fixture
def tool_invoke_response() -> LLMResponse:
    """Create a sample response with tool calls."""
    return LLMResponse(
        content=None,
        function_calls=[
            FunctionCall(name="add_task", arguments={"description": "buy groceries"})
        ],
        finish_reason="tool_calls",
        usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
    )


@pytest.fixture
def direct_response() -> LLMResponse:
    """Create a sample direct response without tools."""
    return LLMResponse(
        content="Hello! How can I help you with your tasks today?",
        function_calls=None,
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
    )


@pytest.fixture
def clarification_response() -> LLMResponse:
    """Create a sample clarification response."""
    return LLMResponse(
        content="Would you like to add 'groceries' as a new task, or are you looking for an existing task about groceries?",
        function_calls=None,
        finish_reason="stop",
        usage=TokenUsage(prompt_tokens=30, completion_tokens=30, total_tokens=60),
    )


@pytest.fixture
def sample_llm_messages() -> list[LLMMessage]:
    """Create sample LLM messages for testing."""
    return [
        LLMMessage(role="user", content="Add a task to buy groceries"),
    ]

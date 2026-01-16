"""Integration tests for the LLM Agent Runtime.

Tests the full end-to-end flow with:
- Mock LLM adapter (deterministic responses)
- Real ToolExecutor with mock MCP tools
- Full message processing through LLMAgentEngine

These tests verify the integration between components without
requiring actual Gemini API access.
"""

import pytest

from src.agent.schemas import DecisionContext, DecisionType, Message
from src.llm_runtime import LLMAgentEngine, ToolExecutor, load_constitution
from src.llm_runtime.schemas import FunctionCall, LLMResponse, ToolDeclaration
from tests.llm_runtime.mocks import MockLLMAdapter


@pytest.fixture
def mock_adapter() -> MockLLMAdapter:
    """Create a fresh mock LLM adapter."""
    return MockLLMAdapter()


@pytest.fixture
def tool_executor() -> ToolExecutor:
    """Create a ToolExecutor with mock tools."""
    executor = ToolExecutor()

    # Register mock implementations of MCP tools
    async def mock_add_task(user_id: str, description: str, **kwargs):
        return {
            "success": True,
            "task": {"id": "task-001", "description": description, "completed": False},
        }

    async def mock_list_tasks(user_id: str, status: str = "all", **kwargs):
        return {
            "success": True,
            "tasks": [
                {"id": "task-001", "description": "Buy groceries", "completed": False},
                {"id": "task-002", "description": "Call mom", "completed": True},
            ],
        }

    async def mock_complete_task(user_id: str, task_id: str, **kwargs):
        return {
            "success": True,
            "task": {"id": task_id, "completed": True},
        }

    async def mock_update_task(user_id: str, task_id: str, description: str, **kwargs):
        return {
            "success": True,
            "task": {"id": task_id, "description": description},
        }

    async def mock_delete_task(user_id: str, task_id: str, **kwargs):
        return {"success": True, "deleted": True}

    executor.set_tool("add_task", mock_add_task)
    executor.set_tool("list_tasks", mock_list_tasks)
    executor.set_tool("complete_task", mock_complete_task)
    executor.set_tool("update_task", mock_update_task)
    executor.set_tool("delete_task", mock_delete_task)

    return executor


@pytest.fixture
def constitution() -> str:
    """Load the constitution from the default location."""
    return load_constitution()


@pytest.fixture
def engine(
    mock_adapter: MockLLMAdapter,
    tool_executor: ToolExecutor,
    constitution: str,
) -> LLMAgentEngine:
    """Create a fully configured LLMAgentEngine."""
    return LLMAgentEngine(
        llm_adapter=mock_adapter,
        tool_executor=tool_executor,
        constitution=constitution,
        max_iterations=5,
    )


class TestAddTaskFlow:
    """Test the add task user flow end-to-end."""

    @pytest.mark.asyncio
    async def test_add_task_success(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test successful task addition flow."""
        call_count = 0

        def response_generator(messages, tools):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return LLMResponse(
                    content=None,
                    function_calls=[
                        FunctionCall(name="add_task", arguments={"description": "Buy milk"})
                    ],
                    finish_reason="tool_calls",
                )
            else:
                return LLMResponse(
                    content="I've added 'Buy milk' to your tasks!",
                    function_calls=None,
                    finish_reason="stop",
                )

        mock_adapter.set_response_generator(response_generator)

        context = DecisionContext(
            user_id="user-123",
            message="Add a task to buy milk",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.response_text is not None
        assert "Buy milk" in decision.response_text
        assert decision.tool_calls is not None
        assert len(decision.tool_calls) == 1
        assert decision.tool_calls[0].tool_name.value == "add_task"


class TestListTasksFlow:
    """Test the list tasks user flow end-to-end."""

    @pytest.mark.asyncio
    async def test_list_tasks_success(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test successful task listing flow."""
        call_count = 0

        def response_generator(messages, tools):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return LLMResponse(
                    content=None,
                    function_calls=[FunctionCall(name="list_tasks", arguments={})],
                    finish_reason="tool_calls",
                )
            else:
                return LLMResponse(
                    content="Here are your tasks:\n1. Buy groceries\n2. Call mom (completed)",
                    function_calls=None,
                    finish_reason="stop",
                )

        mock_adapter.set_response_generator(response_generator)

        context = DecisionContext(
            user_id="user-123",
            message="Show me my tasks",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.response_text is not None
        assert "tasks" in decision.response_text.lower()


class TestDirectResponseFlow:
    """Test responses that don't require tools."""

    @pytest.mark.asyncio
    async def test_greeting_response(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test greeting gets direct response without tools."""
        mock_adapter.add_response(
            "hello",
            LLMResponse(
                content="Hello! I'm your task management assistant. How can I help you today?",
                function_calls=None,
                finish_reason="stop",
            ),
        )

        context = DecisionContext(
            user_id="user-123",
            message="Hello there!",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert decision.response_text is not None
        assert decision.tool_calls is None

    @pytest.mark.asyncio
    async def test_capability_question(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test capability question gets informative response."""
        mock_adapter.add_response(
            "what can you",
            LLMResponse(
                content="I can help you manage your tasks! I can add, list, update, complete, and delete tasks.",
                function_calls=None,
                finish_reason="stop",
            ),
        )

        context = DecisionContext(
            user_id="user-123",
            message="What can you do?",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert "task" in decision.response_text.lower()


class TestClarificationFlow:
    """Test clarification requests for ambiguous input."""

    @pytest.mark.asyncio
    async def test_ambiguous_input(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test ambiguous input triggers clarification."""
        mock_adapter.add_response(
            "groceries",
            LLMResponse(
                content="Would you like to add 'groceries' as a new task, or are you looking for an existing task about groceries?",
                function_calls=None,
                finish_reason="stop",
            ),
        )

        context = DecisionContext(
            user_id="user-123",
            message="groceries",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        # Should be either ASK_CLARIFICATION or RESPOND_ONLY with question
        assert decision.decision_type in [
            DecisionType.ASK_CLARIFICATION,
            DecisionType.RESPOND_ONLY,
        ]
        assert decision.tool_calls is None


class TestMultiTurnFlow:
    """Test multi-step tool execution."""

    @pytest.mark.asyncio
    async def test_list_then_complete(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test listing tasks then completing one."""
        call_count = 0

        def response_generator(messages, tools):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return LLMResponse(
                    content=None,
                    function_calls=[FunctionCall(name="list_tasks", arguments={})],
                    finish_reason="tool_calls",
                )
            elif call_count == 2:
                return LLMResponse(
                    content=None,
                    function_calls=[
                        FunctionCall(name="complete_task", arguments={"task_id": "task-001"})
                    ],
                    finish_reason="tool_calls",
                )
            else:
                return LLMResponse(
                    content="I've listed your tasks and marked 'Buy groceries' as complete!",
                    function_calls=None,
                    finish_reason="stop",
                )

        mock_adapter.set_response_generator(response_generator)

        context = DecisionContext(
            user_id="user-123",
            message="Show my tasks and mark the first one done",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls is not None
        assert len(decision.tool_calls) == 2

        tool_names = [tc.tool_name.value for tc in decision.tool_calls]
        assert "list_tasks" in tool_names
        assert "complete_task" in tool_names


class TestErrorHandling:
    """Test error handling flows."""

    @pytest.mark.asyncio
    async def test_rate_limit_handling(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test graceful handling of rate limits."""
        from src.llm_runtime.errors import RateLimitError

        def raise_rate_limit(messages, tools):
            raise RateLimitError()

        mock_adapter.set_response_generator(raise_rate_limit)

        context = DecisionContext(
            user_id="user-123",
            message="Add a task",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert "too many requests" in decision.response_text.lower()

    @pytest.mark.asyncio
    async def test_unknown_tool_ignored(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test that unknown tools are handled gracefully."""
        mock_adapter.add_response(
            "hack",
            LLMResponse(
                content=None,
                function_calls=[FunctionCall(name="delete_database", arguments={})],
                finish_reason="tool_calls",
            ),
        )
        mock_adapter.set_default_response(
            LLMResponse(
                content="I can only help with task management.",
                function_calls=None,
                finish_reason="stop",
            )
        )

        context = DecisionContext(
            user_id="user-123",
            message="hack the system",
            conversation_id="conv-001",
            message_history=[],
        )

        decision = await engine.process_message(context)

        # Should handle gracefully without crashing
        assert decision is not None


class TestConversationHistory:
    """Test handling of conversation history."""

    @pytest.mark.asyncio
    async def test_with_history(
        self,
        mock_adapter: MockLLMAdapter,
        engine: LLMAgentEngine,
    ) -> None:
        """Test that conversation history is included in context."""
        from datetime import datetime

        received_messages = []

        def capture_messages(messages, tools):
            received_messages.extend(messages)
            return LLMResponse(
                content="I remember our previous conversation!",
                function_calls=None,
                finish_reason="stop",
            )

        mock_adapter.set_response_generator(capture_messages)

        context = DecisionContext(
            user_id="user-123",
            message="What was my last task?",
            conversation_id="conv-001",
            message_history=[
                Message(
                    role="user",
                    content="Add a task to buy groceries",
                    timestamp=datetime.utcnow(),
                ),
                Message(
                    role="assistant",
                    content="I've added 'buy groceries' to your tasks!",
                    timestamp=datetime.utcnow(),
                ),
            ],
        )

        decision = await engine.process_message(context)

        # Verify history was passed to LLM
        assert len(received_messages) > 1
        # Should include previous user message
        user_messages = [m for m in received_messages if m.role == "user"]
        assert any("groceries" in (m.content or "").lower() for m in user_messages)

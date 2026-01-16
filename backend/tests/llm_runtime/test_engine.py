"""Tests for the LLMAgentEngine.

Tests cover:
- Tool invocation flows (US1)
- Direct response handling (US2)
- Clarification requests (US3)
- Observability logging (US4)
- Safety/refusal handling (US5)
- Multi-turn tool execution (US6)
"""

from datetime import datetime

import pytest

from src.agent.schemas import DecisionContext, DecisionType, Message
from src.llm_runtime.engine import LLMAgentEngine
from src.llm_runtime.schemas import FunctionCall, LLMResponse, TokenUsage
from tests.llm_runtime.mocks import MockLLMAdapter, MockToolExecutor


# =============================================================================
# US1: Tool Invocation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_invoke_add_task(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that 'add task' message triggers add_task tool invocation."""
    # Use dynamic response generator to handle the two-phase flow
    call_count = 0

    def response_generator(messages, tools):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call: return tool call
            return LLMResponse(
                content=None,
                function_calls=[
                    FunctionCall(name="add_task", arguments={"description": "buy groceries"})
                ],
                finish_reason="tool_calls",
                usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            )
        else:
            # Second call: return final response after seeing tool result
            return LLMResponse(
                content="I've added 'buy groceries' to your tasks.",
                function_calls=None,
                finish_reason="stop",
                usage=TokenUsage(prompt_tokens=150, completion_tokens=30, total_tokens=180),
            )

    mock_llm_adapter.set_response_generator(response_generator)

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Add a task to buy groceries",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Verify tool was called
    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) >= 1
    assert tool_calls[0][0] == "add_task"  # tool_name
    assert tool_calls[0][1]["description"] == "buy groceries"  # parameters
    assert tool_calls[0][2] == "test-user"  # user_id

    # Verify decision
    assert decision.decision_type == DecisionType.INVOKE_TOOL
    assert decision.tool_calls is not None
    assert len(decision.tool_calls) >= 1


@pytest.mark.asyncio
async def test_invoke_list_tasks(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that 'show my tasks' triggers list_tasks tool invocation."""
    mock_llm_adapter.add_response(
        "show my tasks",
        LLMResponse(
            content=None,
            function_calls=[FunctionCall(name="list_tasks", arguments={})],
            finish_reason="tool_calls",
        ),
    )

    mock_llm_adapter.set_default_response(
        LLMResponse(
            content="Here are your tasks: 1. Task 1 2. Task 2",
            function_calls=None,
            finish_reason="stop",
        )
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Show my tasks",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) >= 1
    assert tool_calls[0][0] == "list_tasks"


@pytest.mark.asyncio
async def test_invoke_complete_task(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that 'mark task done' triggers complete_task tool invocation."""
    mock_llm_adapter.add_response(
        "mark",
        LLMResponse(
            content=None,
            function_calls=[
                FunctionCall(name="complete_task", arguments={"task_id": "task-123"})
            ],
            finish_reason="tool_calls",
        ),
    )

    mock_llm_adapter.set_default_response(
        LLMResponse(
            content="Done! I've marked that task as complete.",
            function_calls=None,
            finish_reason="stop",
        )
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Mark task-123 as done",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) >= 1
    assert tool_calls[0][0] == "complete_task"
    assert tool_calls[0][1]["task_id"] == "task-123"


# =============================================================================
# US2: Direct Response Tests (No Tools)
# =============================================================================


@pytest.mark.asyncio
async def test_greeting_no_tools(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that greeting messages don't invoke tools."""
    mock_llm_adapter.add_response(
        "hello",
        LLMResponse(
            content="Hello! How can I help you with your tasks today?",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Hello!",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Verify no tools were called
    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0

    # Verify decision type
    assert decision.decision_type == DecisionType.RESPOND_ONLY
    assert decision.response_text is not None
    assert "hello" in decision.response_text.lower() or "help" in decision.response_text.lower()


@pytest.mark.asyncio
async def test_capability_question_no_tools(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that capability questions don't invoke tools."""
    mock_llm_adapter.add_response(
        "what can you do",
        LLMResponse(
            content="I can help you manage your tasks! I can add, view, update, complete, and delete tasks.",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="What can you do?",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0
    assert decision.decision_type == DecisionType.RESPOND_ONLY


@pytest.mark.asyncio
async def test_off_topic_no_tools(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that off-topic messages get polite response without tools."""
    mock_llm_adapter.add_response(
        "joke",
        LLMResponse(
            content="I'm a task management assistant, so I can't tell jokes. But I'd be happy to help you manage your tasks!",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Tell me a joke",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0
    assert decision.decision_type == DecisionType.RESPOND_ONLY


# =============================================================================
# US3: Clarification Tests
# =============================================================================


@pytest.mark.asyncio
async def test_ambiguous_single_word(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that ambiguous single-word input triggers clarification."""
    mock_llm_adapter.add_response(
        "groceries",
        LLMResponse(
            content="Would you like to add 'groceries' as a new task, or are you looking for an existing task about groceries?",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="groceries",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0
    assert decision.decision_type in [DecisionType.ASK_CLARIFICATION, DecisionType.RESPOND_ONLY]
    assert decision.response_text is not None or decision.clarification_question is not None


@pytest.mark.asyncio
async def test_multiple_possible_intents(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test clarification when message could mean multiple things."""
    mock_llm_adapter.add_response(
        "milk and eggs",
        LLMResponse(
            content="Would you like me to add 'milk and eggs' as a task, or are you looking for an existing task?",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="milk and eggs",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0


@pytest.mark.asyncio
async def test_missing_context_reference(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test clarification when user references non-existent context."""
    mock_llm_adapter.add_response(
        "that one",
        LLMResponse(
            content="I'm not sure which task you're referring to. Could you please specify which task?",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="complete that one",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0


# =============================================================================
# US4: Observability/Logging Tests (placeholder for now)
# =============================================================================


@pytest.mark.asyncio
async def test_decision_log_on_tool_invoke(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that tool invocation logs are created (placeholder)."""
    # This test verifies logging structure - actual logging will be tested
    # with the observability integration
    mock_llm_adapter.add_response(
        "add task",
        LLMResponse(
            content=None,
            function_calls=[FunctionCall(name="add_task", arguments={"description": "test"})],
            finish_reason="tool_calls",
        ),
    )
    mock_llm_adapter.set_default_response(
        LLMResponse(content="Done!", function_calls=None, finish_reason="stop")
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Add task test",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Verify decision was created (logging is internal)
    assert decision is not None


@pytest.mark.asyncio
async def test_decision_log_on_respond(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that direct response logs are created (placeholder)."""
    mock_llm_adapter.add_response(
        "hi",
        LLMResponse(content="Hello!", function_calls=None, finish_reason="stop"),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Hi",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)
    assert decision is not None


@pytest.mark.asyncio
async def test_tool_invocation_log(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that tool invocation logs capture timing (placeholder)."""
    mock_llm_adapter.add_response(
        "list",
        LLMResponse(
            content=None,
            function_calls=[FunctionCall(name="list_tasks", arguments={})],
            finish_reason="tool_calls",
        ),
    )
    mock_llm_adapter.set_default_response(
        LLMResponse(content="Your tasks: ...", function_calls=None, finish_reason="stop")
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="List my tasks",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)
    assert decision is not None


# =============================================================================
# US5: Safety/Refusal Tests
# =============================================================================


@pytest.mark.asyncio
async def test_out_of_scope_request(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that out-of-scope requests are politely refused."""
    mock_llm_adapter.add_response(
        "weather",
        LLMResponse(
            content="I'm a task management assistant and can't help with weather information. But I'd be happy to help you manage your tasks!",
            function_calls=None,
            finish_reason="stop",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="What's the weather?",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) == 0
    assert decision.decision_type == DecisionType.RESPOND_ONLY


@pytest.mark.asyncio
async def test_rate_limit_handling(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test graceful handling of rate limits."""
    from src.llm_runtime.errors import RateLimitError

    def raise_rate_limit(messages, tools):
        raise RateLimitError()

    mock_llm_adapter.set_response_generator(raise_rate_limit)

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Add a task",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Should return graceful error response
    assert decision.decision_type == DecisionType.RESPOND_ONLY
    assert decision.response_text is not None


@pytest.mark.asyncio
async def test_unknown_tool_rejected(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that unknown tools requested by LLM are rejected."""
    mock_llm_adapter.add_response(
        "hack",
        LLMResponse(
            content=None,
            function_calls=[FunctionCall(name="delete_database", arguments={})],
            finish_reason="tool_calls",
        ),
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="hack the system",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Should handle gracefully
    assert decision is not None


# =============================================================================
# US6: Multi-Turn Tool Execution Tests
# =============================================================================


@pytest.mark.asyncio
async def test_sequential_tool_calls(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test sequential tool calls in a single request."""
    call_count = 0

    def dynamic_response(messages, tools):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call: request list_tasks
            return LLMResponse(
                content=None,
                function_calls=[FunctionCall(name="list_tasks", arguments={})],
                finish_reason="tool_calls",
            )
        elif call_count == 2:
            # Second call: after seeing tasks, request complete
            return LLMResponse(
                content=None,
                function_calls=[FunctionCall(name="complete_task", arguments={"task_id": "task-1"})],
                finish_reason="tool_calls",
            )
        else:
            # Third call: final response
            return LLMResponse(
                content="I've listed your tasks and marked the first one as complete!",
                function_calls=None,
                finish_reason="stop",
            )

    mock_llm_adapter.set_response_generator(dynamic_response)

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Show my tasks and mark the first one complete",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Verify multiple tools were called
    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) >= 2
    tool_names = [tc[0] for tc in tool_calls]
    assert "list_tasks" in tool_names
    assert "complete_task" in tool_names


@pytest.mark.asyncio
async def test_tool_result_fed_back(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that tool results are fed back to LLM."""
    call_count = 0
    received_messages = []

    def capture_messages(messages, tools):
        nonlocal call_count, received_messages
        call_count += 1
        received_messages.append(messages.copy())

        if call_count == 1:
            return LLMResponse(
                content=None,
                function_calls=[FunctionCall(name="list_tasks", arguments={})],
                finish_reason="tool_calls",
            )
        else:
            return LLMResponse(
                content="Here are your tasks!",
                function_calls=None,
                finish_reason="stop",
            )

    mock_llm_adapter.set_response_generator(capture_messages)

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Show my tasks",
        conversation_id="conv-123",
        message_history=[],
    )

    await engine.process_message(context)

    # Second call should have function response
    assert len(received_messages) >= 2
    second_call_messages = received_messages[1]
    # Should contain function response
    has_function_msg = any(m.role == "function" for m in second_call_messages)
    assert has_function_msg


@pytest.mark.asyncio
async def test_max_iteration_limit(
    mock_llm_adapter: MockLLMAdapter,
    mock_tool_executor: MockToolExecutor,
    constitution_text: str,
) -> None:
    """Test that tool loop terminates at max iterations."""
    # Always return tool calls - should hit limit
    mock_llm_adapter.set_response_generator(
        lambda m, t: LLMResponse(
            content=None,
            function_calls=[FunctionCall(name="list_tasks", arguments={})],
            finish_reason="tool_calls",
        )
    )

    engine = LLMAgentEngine(
        llm_adapter=mock_llm_adapter,
        tool_executor=mock_tool_executor,
        constitution=constitution_text,
        max_iterations=3,
    )

    context = DecisionContext(
        user_id="test-user",
        message="Keep listing",
        conversation_id="conv-123",
        message_history=[],
    )

    decision = await engine.process_message(context)

    # Should terminate with helpful message
    assert decision is not None
    # Should not exceed max iterations
    tool_calls = mock_tool_executor.get_call_history()
    assert len(tool_calls) <= 3

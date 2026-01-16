"""Integration tests for the Agent Decision Engine."""

import pytest
from uuid import uuid4

from src.agent.engine import AgentDecisionEngine
from src.agent.schemas import (
    DecisionContext,
    DecisionType,
    ToolName,
)


@pytest.fixture
def engine() -> AgentDecisionEngine:
    """Create an AgentDecisionEngine instance for testing."""
    return AgentDecisionEngine()


@pytest.fixture
def basic_context() -> DecisionContext:
    """Basic decision context for testing."""
    return DecisionContext(
        user_id="test-user-123",
        message="test message",
        conversation_id=str(uuid4()),
        message_history=[],
        pending_confirmation=None,
    )


class TestCreateTaskFlow:
    """Integration tests for create task flow (T018, T024)."""

    @pytest.mark.asyncio
    async def test_remind_me_creates_task(self, engine):
        """'remind me to X' should create a task via add_task."""
        context = DecisionContext(
            user_id="test-user-123",
            message="remind me to buy groceries",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert len(decision.tool_calls) == 1
        assert decision.tool_calls[0].tool_name == ToolName.ADD_TASK
        assert decision.tool_calls[0].parameters["description"] == "buy groceries"
        assert decision.tool_calls[0].parameters["user_id"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_add_task_pattern(self, engine):
        """'add task X' should create a task."""
        context = DecisionContext(
            user_id="test-user-123",
            message="add task: call mom",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.ADD_TASK
        assert "call mom" in decision.tool_calls[0].parameters["description"]


class TestListTasksFlow:
    """Integration tests for list tasks flow (T026, T027, T033)."""

    @pytest.mark.asyncio
    async def test_what_are_my_tasks(self, engine):
        """'what are my tasks' should invoke list_tasks."""
        context = DecisionContext(
            user_id="test-user-123",
            message="what are my tasks?",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS
        assert decision.tool_calls[0].parameters["user_id"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_show_my_tasks(self, engine):
        """'show my tasks' should invoke list_tasks."""
        context = DecisionContext(
            user_id="test-user-123",
            message="show my tasks",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS


class TestGeneralChatFlow:
    """Integration tests for general chat flow (T036, T040)."""

    @pytest.mark.asyncio
    async def test_hello_no_tool_invocation(self, engine):
        """'hello' should NOT invoke any tools."""
        context = DecisionContext(
            user_id="test-user-123",
            message="hello",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert decision.tool_calls is None
        assert decision.response_text is not None

    @pytest.mark.asyncio
    async def test_how_are_you_no_tools(self, engine):
        """'how are you' should NOT invoke any tools."""
        context = DecisionContext(
            user_id="test-user-123",
            message="how are you?",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert decision.tool_calls is None


class TestAmbiguousFlow:
    """Integration tests for ambiguous input flow (T043, T047)."""

    @pytest.mark.asyncio
    async def test_single_word_asks_clarification(self, engine):
        """Single ambiguous word should ask for clarification."""
        context = DecisionContext(
            user_id="test-user-123",
            message="groceries",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.ASK_CLARIFICATION
        assert decision.clarification_question is not None
        assert decision.tool_calls is None


class TestCompleteTaskFlow:
    """Integration tests for complete task flow (T052, T060)."""

    @pytest.mark.asyncio
    async def test_i_finished_lists_tasks(self, engine):
        """'I finished X' should first list tasks to identify target."""
        context = DecisionContext(
            user_id="test-user-123",
            message="I finished the groceries",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        # First step is to list tasks
        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS


class TestUpdateTaskFlow:
    """Integration tests for update task flow (T063, T069)."""

    @pytest.mark.asyncio
    async def test_update_lists_tasks(self, engine):
        """Update request should first list tasks."""
        context = DecisionContext(
            user_id="test-user-123",
            message="change groceries to buy milk",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS


class TestDeleteTaskFlow:
    """Integration tests for delete task flow (T074, T075, T086)."""

    @pytest.mark.asyncio
    async def test_delete_lists_tasks(self, engine):
        """Delete request should first list tasks."""
        context = DecisionContext(
            user_id="test-user-123",
            message="delete the groceries task",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        # First step is to list tasks to identify target
        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS

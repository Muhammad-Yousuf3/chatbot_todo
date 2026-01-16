"""Tests for decision policy rules."""

import pytest
from uuid import uuid4

from src.agent.policy import apply_decision_rules
from src.agent.schemas import (
    DecisionContext,
    DecisionType,
    IntentType,
    ToolName,
    UserIntent,
)


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


class TestCreateTaskPolicy:
    """Tests for CREATE_TASK decision rules (T021)."""

    @pytest.mark.asyncio
    async def test_create_task_invokes_add_task(self, basic_context):
        """CREATE_TASK intent should invoke add_task tool."""
        intent = UserIntent(
            intent_type=IntentType.CREATE_TASK,
            confidence=0.95,
            extracted_params={"description": "buy groceries"},
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert len(decision.tool_calls) == 1
        assert decision.tool_calls[0].tool_name == ToolName.ADD_TASK
        assert decision.tool_calls[0].parameters["description"] == "buy groceries"
        assert decision.tool_calls[0].parameters["user_id"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_create_task_missing_description(self, basic_context):
        """CREATE_TASK without description should ask for clarification."""
        intent = UserIntent(
            intent_type=IntentType.CREATE_TASK,
            confidence=0.95,
            extracted_params={},
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.ASK_CLARIFICATION


class TestListTasksPolicy:
    """Tests for LIST_TASKS decision rules (T029)."""

    @pytest.mark.asyncio
    async def test_list_tasks_invokes_tool(self, basic_context):
        """LIST_TASKS intent should invoke list_tasks tool."""
        intent = UserIntent(
            intent_type=IntentType.LIST_TASKS,
            confidence=0.98,
            extracted_params=None,
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert len(decision.tool_calls) == 1
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS
        assert decision.tool_calls[0].parameters["user_id"] == "test-user-123"


class TestGeneralChatPolicy:
    """Tests for GENERAL_CHAT decision rules (T035, T038)."""

    @pytest.mark.asyncio
    async def test_general_chat_no_tool_calls(self, basic_context):
        """GENERAL_CHAT should return RESPOND_ONLY with no tool calls."""
        intent = UserIntent(
            intent_type=IntentType.GENERAL_CHAT,
            confidence=0.90,
            extracted_params=None,
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert decision.tool_calls is None
        assert decision.response_text is not None

    @pytest.mark.asyncio
    async def test_greeting_response(self):
        """Greeting message should get greeting response."""
        context = DecisionContext(
            user_id="test-user-123",
            message="hello",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )
        intent = UserIntent(
            intent_type=IntentType.GENERAL_CHAT,
            confidence=0.90,
            extracted_params=None,
        )

        decision = await apply_decision_rules(context, intent)

        assert decision.decision_type == DecisionType.RESPOND_ONLY
        assert "Hello" in decision.response_text or "hello" in decision.response_text.lower()


class TestAmbiguousPolicy:
    """Tests for AMBIGUOUS decision rules (T042, T045)."""

    @pytest.mark.asyncio
    async def test_ambiguous_asks_clarification(self, basic_context):
        """AMBIGUOUS intent should return ASK_CLARIFICATION."""
        intent = UserIntent(
            intent_type=IntentType.AMBIGUOUS,
            confidence=0.40,
            extracted_params={"possible_intents": ["CREATE_TASK", "COMPLETE_TASK"]},
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.ASK_CLARIFICATION
        assert decision.clarification_question is not None
        assert decision.tool_calls is None


class TestCompleteTaskPolicy:
    """Tests for COMPLETE_TASK decision rules (T057)."""

    @pytest.mark.asyncio
    async def test_complete_task_lists_first(self, basic_context):
        """COMPLETE_TASK should first invoke list_tasks."""
        intent = UserIntent(
            intent_type=IntentType.COMPLETE_TASK,
            confidence=0.90,
            extracted_params={"task_reference": "groceries"},
        )

        decision = await apply_decision_rules(basic_context, intent)

        # First step is to list tasks to identify the target
        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS

    @pytest.mark.asyncio
    async def test_complete_task_missing_reference(self, basic_context):
        """COMPLETE_TASK without reference should ask clarification."""
        intent = UserIntent(
            intent_type=IntentType.COMPLETE_TASK,
            confidence=0.90,
            extracted_params={},
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.ASK_CLARIFICATION


class TestUpdateTaskPolicy:
    """Tests for UPDATE_TASK decision rules (T066)."""

    @pytest.mark.asyncio
    async def test_update_task_lists_first(self, basic_context):
        """UPDATE_TASK should first invoke list_tasks."""
        intent = UserIntent(
            intent_type=IntentType.UPDATE_TASK,
            confidence=0.88,
            extracted_params={
                "task_reference": "groceries",
                "new_description": "buy milk",
            },
        )

        decision = await apply_decision_rules(basic_context, intent)

        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS


class TestDeleteTaskPolicy:
    """Tests for DELETE_TASK decision rules (T080)."""

    @pytest.mark.asyncio
    async def test_delete_task_lists_first(self, basic_context):
        """DELETE_TASK should first invoke list_tasks."""
        intent = UserIntent(
            intent_type=IntentType.DELETE_TASK,
            confidence=0.90,
            extracted_params={"task_reference": "groceries"},
        )

        decision = await apply_decision_rules(basic_context, intent)

        # First step is to list tasks to identify the target
        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls[0].tool_name == ToolName.LIST_TASKS


class TestAuthRequired:
    """Tests for authentication validation (T089)."""

    @pytest.mark.asyncio
    async def test_missing_user_id_rejected(self):
        """Missing user_id should be rejected at context validation level."""
        from pydantic import ValidationError

        # Empty user_id should fail context validation
        with pytest.raises(ValidationError):
            DecisionContext(
                user_id="",  # This will fail validation
                message="test",
                conversation_id=str(uuid4()),
            )
        # Validation is handled at the schema level, which is correct behavior

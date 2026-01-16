"""Unit tests for agent schema models and enums."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.agent.schemas import (
    AgentDecision,
    DecisionContext,
    DecisionType,
    IntentType,
    Message,
    PendingAction,
    ToolCall,
    ToolInvocationRecord,
    ToolName,
    UserIntent,
)


class TestIntentType:
    """Tests for IntentType enum."""

    def test_all_intent_types_defined(self):
        """Verify all expected intent types exist."""
        expected = {
            "CREATE_TASK",
            "LIST_TASKS",
            "COMPLETE_TASK",
            "UPDATE_TASK",
            "DELETE_TASK",
            "GENERAL_CHAT",
            "AMBIGUOUS",
            "MULTI_INTENT",
            "CONFIRM_YES",
            "CONFIRM_NO",
        }
        actual = {e.value for e in IntentType}
        assert actual == expected

    def test_intent_type_is_string_enum(self):
        """IntentType values should be strings."""
        assert IntentType.CREATE_TASK.value == "CREATE_TASK"
        assert isinstance(IntentType.CREATE_TASK.value, str)


class TestDecisionType:
    """Tests for DecisionType enum."""

    def test_all_decision_types_defined(self):
        """Verify all expected decision types exist."""
        expected = {
            "INVOKE_TOOL",
            "RESPOND_ONLY",
            "ASK_CLARIFICATION",
            "REQUEST_CONFIRMATION",
            "EXECUTE_PENDING",
            "CANCEL_PENDING",
        }
        actual = {e.value for e in DecisionType}
        assert actual == expected


class TestToolName:
    """Tests for ToolName enum."""

    def test_all_tool_names_defined(self):
        """Verify all expected tool names exist."""
        expected = {
            "add_task",
            "list_tasks",
            "update_task",
            "complete_task",
            "delete_task",
        }
        actual = {e.value for e in ToolName}
        assert actual == expected


class TestUserIntent:
    """Tests for UserIntent model."""

    def test_valid_create_task_intent(self):
        """Valid CREATE_TASK intent should be accepted."""
        intent = UserIntent(
            intent_type=IntentType.CREATE_TASK,
            confidence=0.95,
            extracted_params={"description": "buy groceries"},
        )
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.confidence == 0.95
        assert intent.extracted_params["description"] == "buy groceries"

    def test_intent_without_params(self):
        """Intent can have None params."""
        intent = UserIntent(
            intent_type=IntentType.LIST_TASKS,
            confidence=0.98,
            extracted_params=None,
        )
        assert intent.extracted_params is None

    def test_intent_confidence_bounds(self):
        """Confidence must be between 0 and 1."""
        # Valid bounds
        UserIntent(intent_type=IntentType.GENERAL_CHAT, confidence=0.0)
        UserIntent(intent_type=IntentType.GENERAL_CHAT, confidence=1.0)

        # Invalid bounds
        with pytest.raises(ValidationError):
            UserIntent(intent_type=IntentType.GENERAL_CHAT, confidence=-0.1)
        with pytest.raises(ValidationError):
            UserIntent(intent_type=IntentType.GENERAL_CHAT, confidence=1.1)

    def test_ambiguous_intent_requires_possible_intents(self):
        """AMBIGUOUS intent must include possible_intents in params."""
        # Valid
        UserIntent(
            intent_type=IntentType.AMBIGUOUS,
            confidence=0.4,
            extracted_params={"possible_intents": ["CREATE_TASK", "COMPLETE_TASK"]},
        )

        # Invalid - missing possible_intents
        with pytest.raises(ValidationError):
            UserIntent(
                intent_type=IntentType.AMBIGUOUS,
                confidence=0.4,
                extracted_params={"other": "value"},
            )


class TestMessage:
    """Tests for Message model."""

    def test_valid_user_message(self):
        """Valid user message should be accepted."""
        msg = Message(role="user", content="hello", timestamp=datetime.now())
        assert msg.role == "user"

    def test_valid_assistant_message(self):
        """Valid assistant message should be accepted."""
        msg = Message(role="assistant", content="hi there", timestamp=datetime.now())
        assert msg.role == "assistant"

    def test_invalid_role_rejected(self):
        """Invalid role should be rejected."""
        with pytest.raises(ValidationError):
            Message(role="system", content="test", timestamp=datetime.now())


class TestPendingAction:
    """Tests for PendingAction model."""

    def test_valid_delete_pending_action(self):
        """Valid DELETE_TASK pending action should be accepted."""
        now = datetime.now()
        action = PendingAction(
            action_type=IntentType.DELETE_TASK,
            task_id=str(uuid4()),
            task_description="buy groceries",
            created_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        assert action.action_type == IntentType.DELETE_TASK

    def test_only_delete_allowed(self):
        """Only DELETE_TASK is allowed as action_type."""
        now = datetime.now()
        with pytest.raises(ValidationError):
            PendingAction(
                action_type=IntentType.UPDATE_TASK,
                task_id=str(uuid4()),
                task_description="test",
                created_at=now,
                expires_at=now + timedelta(minutes=5),
            )

    def test_is_expired_false_when_valid(self):
        """is_expired should return False for valid action."""
        now = datetime.now()
        action = PendingAction(
            action_type=IntentType.DELETE_TASK,
            task_id=str(uuid4()),
            task_description="test",
            created_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        assert not action.is_expired()

    def test_is_expired_true_when_past(self):
        """is_expired should return True for expired action."""
        now = datetime.now()
        action = PendingAction(
            action_type=IntentType.DELETE_TASK,
            task_id=str(uuid4()),
            task_description="test",
            created_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=5),
        )
        assert action.is_expired()


class TestDecisionContext:
    """Tests for DecisionContext model."""

    def test_valid_context(self):
        """Valid context should be accepted."""
        context = DecisionContext(
            user_id="user-123",
            message="hello",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )
        assert context.user_id == "user-123"

    def test_user_id_required(self):
        """user_id cannot be empty."""
        with pytest.raises(ValidationError):
            DecisionContext(
                user_id="",
                message="hello",
                conversation_id=str(uuid4()),
            )

    def test_message_length_limit(self):
        """message cannot exceed 4000 characters."""
        long_message = "x" * 4001
        with pytest.raises(ValidationError):
            DecisionContext(
                user_id="user-123",
                message=long_message,
                conversation_id=str(uuid4()),
            )


class TestToolCall:
    """Tests for ToolCall model."""

    def test_valid_add_task_call(self):
        """Valid add_task call should be accepted."""
        call = ToolCall(
            tool_name=ToolName.ADD_TASK,
            parameters={"user_id": "user-123", "description": "buy groceries"},
            sequence=1,
        )
        assert call.tool_name == ToolName.ADD_TASK

    def test_user_id_required(self):
        """All tool calls require user_id."""
        with pytest.raises(ValidationError):
            ToolCall(
                tool_name=ToolName.LIST_TASKS,
                parameters={},
                sequence=1,
            )

    def test_add_task_requires_description(self):
        """add_task requires description parameter."""
        with pytest.raises(ValidationError):
            ToolCall(
                tool_name=ToolName.ADD_TASK,
                parameters={"user_id": "user-123"},
                sequence=1,
            )

    def test_complete_task_requires_task_id(self):
        """complete_task requires task_id parameter."""
        with pytest.raises(ValidationError):
            ToolCall(
                tool_name=ToolName.COMPLETE_TASK,
                parameters={"user_id": "user-123"},
                sequence=1,
            )

    def test_sequence_must_be_positive(self):
        """sequence must be >= 1."""
        with pytest.raises(ValidationError):
            ToolCall(
                tool_name=ToolName.LIST_TASKS,
                parameters={"user_id": "user-123"},
                sequence=0,
            )


class TestAgentDecision:
    """Tests for AgentDecision model."""

    def test_valid_invoke_tool_decision(self):
        """INVOKE_TOOL decision must have tool_calls."""
        decision = AgentDecision(
            decision_type=DecisionType.INVOKE_TOOL,
            tool_calls=[
                ToolCall(
                    tool_name=ToolName.ADD_TASK,
                    parameters={"user_id": "user-123", "description": "test"},
                    sequence=1,
                )
            ],
        )
        assert decision.decision_type == DecisionType.INVOKE_TOOL

    def test_invoke_tool_requires_tool_calls(self):
        """INVOKE_TOOL without tool_calls should fail."""
        with pytest.raises(ValidationError):
            AgentDecision(
                decision_type=DecisionType.INVOKE_TOOL,
                tool_calls=None,
            )

    def test_respond_only_no_tool_calls(self):
        """RESPOND_ONLY must not have tool_calls."""
        decision = AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text="Hello!",
        )
        assert decision.tool_calls is None

    def test_respond_only_with_tools_fails(self):
        """RESPOND_ONLY with tool_calls should fail."""
        with pytest.raises(ValidationError):
            AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                tool_calls=[
                    ToolCall(
                        tool_name=ToolName.LIST_TASKS,
                        parameters={"user_id": "user-123"},
                        sequence=1,
                    )
                ],
                response_text="Hello!",
            )

    def test_request_confirmation_requires_pending_action(self):
        """REQUEST_CONFIRMATION must have pending_action."""
        now = datetime.now()
        decision = AgentDecision(
            decision_type=DecisionType.REQUEST_CONFIRMATION,
            pending_action=PendingAction(
                action_type=IntentType.DELETE_TASK,
                task_id=str(uuid4()),
                task_description="test",
                created_at=now,
                expires_at=now + timedelta(minutes=5),
            ),
            response_text="Are you sure?",
        )
        assert decision.pending_action is not None

    def test_request_confirmation_without_pending_fails(self):
        """REQUEST_CONFIRMATION without pending_action should fail."""
        with pytest.raises(ValidationError):
            AgentDecision(
                decision_type=DecisionType.REQUEST_CONFIRMATION,
                response_text="Are you sure?",
            )


class TestToolInvocationRecord:
    """Tests for ToolInvocationRecord model."""

    def test_valid_audit_record(self):
        """Valid audit record should be accepted."""
        record = ToolInvocationRecord(
            id=uuid4(),
            conversation_id=str(uuid4()),
            message_id=str(uuid4()),
            user_id="user-123",
            tool_name="add_task",
            parameters={"user_id": "user-123", "description": "test"},
            intent_classification="CREATE_TASK",
            result={"id": "task-123", "description": "test"},
            success=True,
            error_message=None,
            invoked_at=datetime.now(),
            duration_ms=50,
        )
        assert record.success is True

    def test_failed_record_with_error(self):
        """Failed record should have error_message."""
        record = ToolInvocationRecord(
            id=uuid4(),
            conversation_id=str(uuid4()),
            message_id=str(uuid4()),
            user_id="user-123",
            tool_name="add_task",
            parameters={"user_id": "user-123", "description": "test"},
            intent_classification="CREATE_TASK",
            result=None,
            success=False,
            error_message="Database connection failed",
            invoked_at=datetime.now(),
            duration_ms=100,
        )
        assert record.success is False
        assert record.error_message is not None

    def test_duration_must_be_non_negative(self):
        """duration_ms must be >= 0."""
        with pytest.raises(ValidationError):
            ToolInvocationRecord(
                id=uuid4(),
                conversation_id=str(uuid4()),
                message_id=str(uuid4()),
                user_id="user-123",
                tool_name="add_task",
                parameters={},
                intent_classification="CREATE_TASK",
                success=True,
                invoked_at=datetime.now(),
                duration_ms=-1,
            )

"""Audit logging tests for the Agent Decision Engine.

Tests for ToolInvocationRecord logging (T095, T096).
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.agent.engine import AgentDecisionEngine
from src.agent.schemas import (
    DecisionContext,
    DecisionType,
    IntentType,
    ToolCall,
    ToolInvocationRecord,
    ToolName,
    UserIntent,
)


class TestToolInvocationRecord:
    """Tests for ToolInvocationRecord creation (T096)."""

    @pytest.fixture
    def engine(self) -> AgentDecisionEngine:
        """Create a fresh engine instance."""
        return AgentDecisionEngine()

    @pytest.fixture
    def sample_context(self) -> DecisionContext:
        """Sample context for testing."""
        return DecisionContext(
            user_id="test-user-123",
            message="remind me to buy groceries",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

    def test_audit_record_has_required_fields(self, engine, sample_context):
        """Audit record should have all required fields."""
        intent = UserIntent(
            intent_type=IntentType.CREATE_TASK,
            confidence=0.92,
            extracted_params={"description": "buy groceries"},
        )

        tool_call = ToolCall(
            tool_name=ToolName.ADD_TASK,
            parameters={"user_id": "test-user-123", "description": "buy groceries"},
            sequence=1,
        )

        record = engine._create_audit_record(
            context=sample_context,
            intent=intent,
            tool_call=tool_call,
            result={"task_id": "123", "description": "buy groceries"},
            success=True,
            error_message=None,
            duration_ms=50,
        )

        # Verify required fields
        assert record.id is not None
        assert record.conversation_id == sample_context.conversation_id
        assert record.user_id == sample_context.user_id
        assert record.tool_name == "add_task"
        assert record.parameters == tool_call.parameters
        assert record.intent_classification == "CREATE_TASK"
        assert record.success is True
        assert record.duration_ms == 50
        assert record.invoked_at is not None

    def test_audit_record_captures_errors(self, engine, sample_context):
        """Audit record should capture error details."""
        intent = UserIntent(
            intent_type=IntentType.COMPLETE_TASK,
            confidence=0.90,
            extracted_params={"task_reference": "groceries"},
        )

        tool_call = ToolCall(
            tool_name=ToolName.COMPLETE_TASK,
            parameters={"user_id": "test-user-123", "task_id": "nonexistent"},
            sequence=1,
        )

        record = engine._create_audit_record(
            context=sample_context,
            intent=intent,
            tool_call=tool_call,
            result=None,
            success=False,
            error_message="Task not found",
            duration_ms=25,
        )

        assert record.success is False
        assert record.error_message == "Task not found"
        assert record.result is None

    def test_audit_record_timestamps(self, engine, sample_context):
        """Audit record timestamps should be valid."""
        intent = UserIntent(
            intent_type=IntentType.LIST_TASKS,
            confidence=0.95,
            extracted_params=None,
        )

        tool_call = ToolCall(
            tool_name=ToolName.LIST_TASKS,
            parameters={"user_id": "test-user-123"},
            sequence=1,
        )

        before = datetime.now()
        record = engine._create_audit_record(
            context=sample_context,
            intent=intent,
            tool_call=tool_call,
            result={"tasks": []},
            success=True,
            error_message=None,
            duration_ms=10,
        )
        after = datetime.now()

        assert before <= record.invoked_at <= after


class TestAuditLogging:
    """Tests for audit logging behavior (T095)."""

    def test_audit_record_serializable(self):
        """Audit records should be JSON serializable."""
        record = ToolInvocationRecord(
            id=uuid4(),
            conversation_id=str(uuid4()),
            message_id=str(uuid4()),
            user_id="test-user",
            tool_name="add_task",
            parameters={"description": "test task"},
            intent_classification="CREATE_TASK",
            result={"task_id": "123"},
            success=True,
            error_message=None,
            invoked_at=datetime.now(),
            duration_ms=100,
        )

        # Should be serializable
        json_data = record.model_dump_json()
        assert json_data is not None
        assert "test-user" in json_data
        assert "add_task" in json_data

    def test_audit_record_from_dict(self):
        """Audit records should be reconstructible from dict."""
        original = ToolInvocationRecord(
            id=uuid4(),
            conversation_id=str(uuid4()),
            message_id=str(uuid4()),
            user_id="test-user",
            tool_name="list_tasks",
            parameters={"user_id": "test-user"},
            intent_classification="LIST_TASKS",
            result={"tasks": ["task1", "task2"]},
            success=True,
            error_message=None,
            invoked_at=datetime.now(),
            duration_ms=50,
        )

        # Convert to dict and back
        data = original.model_dump()
        reconstructed = ToolInvocationRecord(**data)

        assert reconstructed.id == original.id
        assert reconstructed.user_id == original.user_id
        assert reconstructed.tool_name == original.tool_name


class TestDecisionAuditability:
    """Tests for decision auditability."""

    @pytest.fixture
    def engine(self) -> AgentDecisionEngine:
        """Create a fresh engine instance."""
        return AgentDecisionEngine()

    @pytest.mark.asyncio
    async def test_decision_includes_tool_calls_for_audit(self, engine):
        """Decisions with tool invocations should have auditable tool calls."""
        context = DecisionContext(
            user_id="test-user-123",
            message="remind me to buy groceries",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        decision = await engine.process_message(context)

        # Tool calls should be present and auditable
        assert decision.decision_type == DecisionType.INVOKE_TOOL
        assert decision.tool_calls is not None
        assert len(decision.tool_calls) >= 1

        for tool_call in decision.tool_calls:
            # Each tool call should have required audit fields
            assert tool_call.tool_name is not None
            assert tool_call.parameters is not None
            assert "user_id" in tool_call.parameters
            assert tool_call.sequence >= 1

    @pytest.mark.asyncio
    async def test_decision_type_auditable(self, engine):
        """Decision types should be clearly identifiable for audit."""
        test_cases = [
            ("remind me to buy groceries", DecisionType.INVOKE_TOOL),
            ("hello", DecisionType.RESPOND_ONLY),
            ("groceries", DecisionType.ASK_CLARIFICATION),  # Ambiguous
        ]

        for message, expected_type in test_cases:
            context = DecisionContext(
                user_id="test-user",
                message=message,
                conversation_id=str(uuid4()),
                message_history=[],
                pending_confirmation=None,
            )
            decision = await engine.process_message(context)
            assert decision.decision_type == expected_type, f"Failed for: {message}"

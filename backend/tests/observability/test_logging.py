"""
Tests for the logging service.

Feature: 004-agent-observability
"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.observability.database import get_log_db
from src.observability.logging_service import (
    InvalidDecisionError,
    LoggingService,
    StorageError,
    ValidationError,
)
from src.observability.models import DecisionLog, ToolInvocationLog


class TestWriteDecisionLog:
    """Tests for write_decision_log method."""

    @pytest.mark.asyncio
    async def test_write_decision_log_success(self, log_db):
        """Test successful decision log creation."""
        service = LoggingService()
        decision_id = uuid4()

        log = await service.write_decision_log(
            decision_id=decision_id,
            conversation_id="conv-001",
            user_id="user-001",
            message="remind me to buy groceries",
            intent_type="CREATE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=150,
            confidence=0.95,
            extracted_params={"description": "buy groceries"},
            response_text="I've added 'buy groceries' to your tasks.",
        )

        assert log.decision_id == decision_id
        assert log.conversation_id == "conv-001"
        assert log.user_id == "user-001"
        assert log.message == "remind me to buy groceries"
        assert log.intent_type == "CREATE_TASK"
        assert log.outcome_category == "SUCCESS:TASK_COMPLETED"
        assert log.duration_ms == 150

        # Verify persisted in database
        async with get_log_db() as db:
            cursor = await db.execute(
                "SELECT * FROM decision_logs WHERE decision_id = ?",
                (str(decision_id),)
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row["conversation_id"] == "conv-001"

    @pytest.mark.asyncio
    async def test_write_decision_log_invalid_outcome_category(self, log_db):
        """Test that invalid outcome category raises ValidationError."""
        service = LoggingService()

        with pytest.raises(ValidationError) as exc_info:
            await service.write_decision_log(
                decision_id=uuid4(),
                conversation_id="conv-001",
                user_id="user-001",
                message="test",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="INVALID_CATEGORY",
                duration_ms=100,
            )

        assert "Invalid outcome_category format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_write_decision_log_truncates_long_message(self, log_db):
        """Test that messages longer than 4000 chars are truncated."""
        service = LoggingService()
        long_message = "x" * 5000

        log = await service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-001",
            user_id="user-001",
            message=long_message,
            intent_type="GENERAL_CHAT",
            decision_type="RESPOND_ONLY",
            outcome_category="SUCCESS:RESPONSE_GIVEN",
            duration_ms=100,
        )

        assert len(log.message) == 4000


class TestWriteToolInvocationLog:
    """Tests for write_tool_invocation_log method."""

    @pytest.mark.asyncio
    async def test_write_tool_invocation_log_success(self, log_db):
        """Test successful tool invocation log creation."""
        service = LoggingService()
        decision_id = uuid4()

        # First create a decision log
        await service.write_decision_log(
            decision_id=decision_id,
            conversation_id="conv-001",
            user_id="user-001",
            message="test",
            intent_type="CREATE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=100,
        )

        # Then create tool invocation log
        tool_log = await service.write_tool_invocation_log(
            decision_id=decision_id,
            tool_name="add_task",
            parameters={"description": "buy groceries"},
            result={"task_id": "task-123", "status": "pending"},
            success=True,
            duration_ms=45,
        )

        assert tool_log.decision_id == decision_id
        assert tool_log.tool_name == "add_task"
        assert tool_log.success is True
        assert tool_log.sequence == 1

        # Verify persisted in database
        async with get_log_db() as db:
            cursor = await db.execute(
                "SELECT * FROM tool_invocation_logs WHERE decision_id = ?",
                (str(decision_id),)
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row["tool_name"] == "add_task"

    @pytest.mark.asyncio
    async def test_write_tool_invocation_log_with_error(self, log_db):
        """Test tool invocation log with error details."""
        service = LoggingService()
        decision_id = uuid4()

        # First create a decision log
        await service.write_decision_log(
            decision_id=decision_id,
            conversation_id="conv-001",
            user_id="user-001",
            message="test",
            intent_type="DELETE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="ERROR:TOOL_INVOCATION",
            duration_ms=100,
        )

        # Then create failed tool invocation log
        tool_log = await service.write_tool_invocation_log(
            decision_id=decision_id,
            tool_name="delete_task",
            parameters={"task_id": "invalid"},
            success=False,
            error_code="VALIDATION_ERROR",
            error_message="Task not found",
            duration_ms=25,
        )

        assert tool_log.success is False
        assert tool_log.error_code == "VALIDATION_ERROR"
        assert tool_log.error_message == "Task not found"

    @pytest.mark.asyncio
    async def test_write_tool_invocation_log_invalid_decision(self, log_db):
        """Test that invalid decision_id raises InvalidDecisionError."""
        service = LoggingService()

        with pytest.raises(InvalidDecisionError):
            await service.write_tool_invocation_log(
                decision_id=uuid4(),  # Non-existent decision
                tool_name="add_task",
                parameters={},
                success=True,
                duration_ms=100,
            )

    @pytest.mark.asyncio
    async def test_write_multiple_tool_invocations_sequence(self, log_db):
        """Test that multiple tool invocations get sequential sequence numbers."""
        service = LoggingService()
        decision_id = uuid4()

        # Create decision log
        await service.write_decision_log(
            decision_id=decision_id,
            conversation_id="conv-001",
            user_id="user-001",
            message="test",
            intent_type="MULTI_INTENT",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=200,
        )

        # Create multiple tool invocations
        log1 = await service.write_tool_invocation_log(
            decision_id=decision_id,
            tool_name="list_tasks",
            parameters={},
            success=True,
            duration_ms=50,
        )

        log2 = await service.write_tool_invocation_log(
            decision_id=decision_id,
            tool_name="add_task",
            parameters={"description": "new task"},
            success=True,
            duration_ms=45,
        )

        assert log1.sequence == 1
        assert log2.sequence == 2


class TestDecisionTraceCapture:
    """Tests for complete decision trace capture (US1 acceptance criteria)."""

    @pytest.mark.asyncio
    async def test_complete_decision_trace_captured(self, log_db):
        """Test that a complete decision trace is captured for audit."""
        service = LoggingService()
        decision_id = uuid4()
        conversation_id = "conv-audit-test"

        # Create decision log
        await service.write_decision_log(
            decision_id=decision_id,
            conversation_id=conversation_id,
            user_id="user-audit",
            message="remind me to buy groceries",
            intent_type="CREATE_TASK",
            confidence=0.95,
            extracted_params={"description": "buy groceries"},
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=150,
            response_text="I've added 'buy groceries' to your tasks.",
        )

        # Create tool invocation log
        await service.write_tool_invocation_log(
            decision_id=decision_id,
            tool_name="add_task",
            parameters={"description": "buy groceries"},
            result={"task_id": "task-789", "status": "pending"},
            success=True,
            duration_ms=45,
        )

        # Verify complete trace in database
        async with get_log_db() as db:
            # Check decision log
            cursor = await db.execute(
                "SELECT * FROM decision_logs WHERE decision_id = ?",
                (str(decision_id),)
            )
            decision_row = await cursor.fetchone()
            assert decision_row is not None
            assert decision_row["message"] == "remind me to buy groceries"
            assert decision_row["intent_type"] == "CREATE_TASK"
            assert decision_row["decision_type"] == "INVOKE_TOOL"
            assert decision_row["outcome_category"] == "SUCCESS:TASK_COMPLETED"

            # Check tool invocation log
            cursor = await db.execute(
                "SELECT * FROM tool_invocation_logs WHERE decision_id = ?",
                (str(decision_id),)
            )
            tool_row = await cursor.fetchone()
            assert tool_row is not None
            assert tool_row["tool_name"] == "add_task"
            assert tool_row["success"] == 1

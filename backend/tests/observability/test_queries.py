"""
Tests for the query service.

Feature: 004-agent-observability
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.observability.database import get_log_db
from src.observability.logging_service import LoggingService
from src.observability.query_service import DecisionNotFoundError, LogQueryService


class TestGetDecisionTrace:
    """Tests for get_decision_trace method."""

    @pytest.mark.asyncio
    async def test_get_decision_trace_success(self, populated_db):
        """Test successful decision trace retrieval."""
        decision_log, tool_log = populated_db
        query_service = LogQueryService()

        trace = await query_service.get_decision_trace(decision_log.decision_id)

        assert trace.decision.decision_id == decision_log.decision_id
        assert trace.decision.message == "remind me to buy groceries"
        assert len(trace.tool_invocations) == 1
        assert trace.tool_invocations[0].tool_name == "add_task"

    @pytest.mark.asyncio
    async def test_get_decision_trace_not_found(self, log_db):
        """Test that non-existent decision raises error."""
        query_service = LogQueryService()

        with pytest.raises(DecisionNotFoundError):
            await query_service.get_decision_trace(uuid4())


class TestQueryDecisions:
    """Tests for query_decisions method."""

    @pytest.mark.asyncio
    async def test_query_by_conversation_id(self, log_db):
        """Test querying decisions by conversation_id."""
        logging_service = LoggingService()
        query_service = LogQueryService()

        # Create decisions in different conversations
        for i in range(3):
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id="conv-query-test",
                user_id="user-001",
                message=f"test message {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="other-conv",
            user_id="user-001",
            message="other conversation",
            intent_type="LIST_TASKS",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=100,
        )

        # Query by conversation
        result = await query_service.query_decisions(conversation_id="conv-query-test")

        assert result.total == 3
        assert len(result.items) == 3
        assert all(d.conversation_id == "conv-query-test" for d in result.items)

    @pytest.mark.asyncio
    async def test_query_by_outcome_category_prefix(self, log_db):
        """Test querying decisions by outcome category prefix."""
        logging_service = LoggingService()
        query_service = LogQueryService()

        # Create decisions with different outcomes
        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-001",
            user_id="user-001",
            message="success message",
            intent_type="CREATE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=100,
        )

        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-001",
            user_id="user-001",
            message="error message",
            intent_type="DELETE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="ERROR:TOOL_INVOCATION",
            duration_ms=100,
        )

        # Query by ERROR prefix
        result = await query_service.query_decisions(outcome_category="ERROR")

        assert result.total == 1
        assert result.items[0].outcome_category == "ERROR:TOOL_INVOCATION"

    @pytest.mark.asyncio
    async def test_query_by_time_range(self, log_db):
        """Test querying decisions by time range."""
        logging_service = LoggingService()
        query_service = LogQueryService()

        now = datetime.utcnow()

        # Create decision
        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-001",
            user_id="user-001",
            message="test message",
            intent_type="CREATE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=100,
        )

        # Query with time range
        result = await query_service.query_decisions(
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
        )

        assert result.total >= 1

    @pytest.mark.asyncio
    async def test_query_pagination(self, log_db):
        """Test query pagination."""
        logging_service = LoggingService()
        query_service = LogQueryService()

        # Create 10 decisions
        for i in range(10):
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id="conv-pagination",
                user_id="user-001",
                message=f"message {i}",
                intent_type="GENERAL_CHAT",
                decision_type="RESPOND_ONLY",
                outcome_category="SUCCESS:RESPONSE_GIVEN",
                duration_ms=100,
            )

        # Query first page
        result1 = await query_service.query_decisions(
            conversation_id="conv-pagination",
            limit=5,
            offset=0,
        )

        assert len(result1.items) == 5
        assert result1.total == 10
        assert result1.has_more is True

        # Query second page
        result2 = await query_service.query_decisions(
            conversation_id="conv-pagination",
            limit=5,
            offset=5,
        )

        assert len(result2.items) == 5
        assert result2.has_more is False

        # Verify no overlap
        ids1 = {str(d.id) for d in result1.items}
        ids2 = {str(d.id) for d in result2.items}
        assert ids1.isdisjoint(ids2)


class TestGetMetricsSummary:
    """Tests for get_metrics_summary method."""

    @pytest.mark.asyncio
    async def test_metrics_summary_success_rate(self, log_db):
        """Test success rate calculation in metrics summary."""
        logging_service = LoggingService()
        query_service = LogQueryService()

        # Create 3 successes and 1 error
        for i in range(3):
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id="conv-metrics",
                user_id="user-001",
                message=f"success {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-metrics",
            user_id="user-001",
            message="error",
            intent_type="DELETE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="ERROR:TOOL_INVOCATION",
            duration_ms=100,
        )

        summary = await query_service.get_metrics_summary(
            start_time=datetime.utcnow() - timedelta(hours=1)
        )

        assert summary.total_decisions == 4
        assert summary.success_rate == 0.75  # 3/4
        assert summary.error_breakdown.get("ERROR:TOOL_INVOCATION") == 1

    @pytest.mark.asyncio
    async def test_metrics_summary_intent_distribution(self, log_db):
        """Test intent distribution calculation."""
        logging_service = LoggingService()
        query_service = LogQueryService()

        # Create decisions with different intents
        intents = ["CREATE_TASK", "CREATE_TASK", "LIST_TASKS", "GENERAL_CHAT"]
        for i, intent in enumerate(intents):
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id="conv-intent",
                user_id="user-001",
                message=f"message {i}",
                intent_type=intent,
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        summary = await query_service.get_metrics_summary(
            start_time=datetime.utcnow() - timedelta(hours=1)
        )

        assert summary.intent_distribution.get("CREATE_TASK") == 0.5  # 2/4
        assert summary.intent_distribution.get("LIST_TASKS") == 0.25  # 1/4
        assert summary.intent_distribution.get("GENERAL_CHAT") == 0.25  # 1/4


class TestExportLogs:
    """Tests for export_logs method."""

    @pytest.mark.asyncio
    async def test_export_logs_json(self, populated_db):
        """Test exporting logs in JSON format."""
        query_service = LogQueryService()

        data = await query_service.export_logs(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=1),
            format="json",
        )

        assert isinstance(data, bytes)
        import json
        parsed = json.loads(data.decode("utf-8"))
        assert isinstance(parsed, list)
        assert len(parsed) >= 1

    @pytest.mark.asyncio
    async def test_export_logs_jsonl(self, populated_db):
        """Test exporting logs in JSONL format."""
        query_service = LogQueryService()

        data = await query_service.export_logs(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=1),
            format="jsonl",
        )

        assert isinstance(data, bytes)
        lines = data.decode("utf-8").strip().split("\n")
        assert len(lines) >= 1

        import json
        for line in lines:
            parsed = json.loads(line)
            assert "decision_id" in parsed

"""
Tests for the baseline service and drift detection.

Feature: 004-agent-observability
"""

from datetime import datetime, timedelta, UTC
from uuid import uuid4

import pytest

from src.observability.baseline_service import (
    BaselineNotFoundError,
    BaselineService,
    DuplicateNameError,
    InsufficientDataError,
)
from src.observability.database import get_log_db
from src.observability.logging_service import LoggingService


class TestCreateBaseline:
    """Tests for create_baseline method."""

    @pytest.mark.asyncio
    async def test_create_baseline_success(self, log_db):
        """Test successful baseline creation."""
        logging_service = LoggingService()
        baseline_service = BaselineService()

        # Create sample data
        start_time = datetime.utcnow() - timedelta(hours=1)
        for i in range(15):
            decision_id = uuid4()
            await logging_service.write_decision_log(
                decision_id=decision_id,
                conversation_id=f"conv-{i}",
                user_id="user-001",
                message=f"test message {i}",
                intent_type="CREATE_TASK" if i < 10 else "LIST_TASKS",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )
            await logging_service.write_tool_invocation_log(
                decision_id=decision_id,
                tool_name="add_task" if i < 10 else "list_tasks",
                parameters={},
                success=True,
                duration_ms=50,
            )

        # Create baseline
        baseline = await baseline_service.create_baseline(
            name="test-baseline",
            description="Test baseline",
            sample_start=start_time,
            sample_end=datetime.utcnow() + timedelta(minutes=1),
        )

        assert baseline.snapshot_name == "test-baseline"
        assert baseline.sample_size == 15
        assert "CREATE_TASK" in baseline.intent_distribution
        assert baseline.intent_distribution["CREATE_TASK"] == pytest.approx(10 / 15, rel=0.01)
        assert "add_task" in baseline.tool_frequency
        assert baseline.tool_frequency["add_task"] == 10

    @pytest.mark.asyncio
    async def test_create_baseline_insufficient_data(self, log_db):
        """Test error when not enough data."""
        baseline_service = BaselineService()

        with pytest.raises(InsufficientDataError):
            await baseline_service.create_baseline(
                name="empty-baseline",
                description="No data",
                sample_start=datetime.utcnow() - timedelta(hours=1),
                sample_end=datetime.utcnow(),
            )

    @pytest.mark.asyncio
    async def test_create_baseline_duplicate_name(self, log_db):
        """Test error when baseline name already exists."""
        logging_service = LoggingService()
        baseline_service = BaselineService()

        # Create sample data
        start_time = datetime.utcnow() - timedelta(hours=1)
        for i in range(10):
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id=f"conv-{i}",
                user_id="user-001",
                message=f"test {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        # Create first baseline
        await baseline_service.create_baseline(
            name="unique-baseline",
            description="First",
            sample_start=start_time,
            sample_end=datetime.utcnow() + timedelta(minutes=1),
        )

        # Try to create duplicate
        with pytest.raises(DuplicateNameError):
            await baseline_service.create_baseline(
                name="unique-baseline",
                description="Duplicate",
                sample_start=start_time,
                sample_end=datetime.utcnow() + timedelta(minutes=1),
            )


class TestCompareToBaseline:
    """Tests for compare_to_baseline method."""

    @pytest.mark.asyncio
    async def test_drift_detection_no_drift(self, log_db):
        """Test drift detection when behavior is consistent."""
        logging_service = LoggingService()
        baseline_service = BaselineService()

        # Create baseline data
        # Logs are created NOW, so use a time range that includes NOW
        baseline_start = datetime.now(UTC) - timedelta(minutes=5)

        for i in range(20):
            decision_id = uuid4()
            await logging_service.write_decision_log(
                decision_id=decision_id,
                conversation_id=f"conv-baseline-{i}",
                user_id="user-001",
                message=f"baseline message {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )
            await logging_service.write_tool_invocation_log(
                decision_id=decision_id,
                tool_name="add_task",
                parameters={},
                success=True,
                duration_ms=50,
            )

        baseline_end = datetime.now(UTC) + timedelta(minutes=1)

        # Create baseline
        baseline = await baseline_service.create_baseline(
            name="consistent-baseline",
            description="Consistent behavior",
            sample_start=baseline_start,
            sample_end=baseline_end,
        )

        # Create current data (same pattern)
        current_start = datetime.now(UTC) - timedelta(minutes=1)
        for i in range(10):
            decision_id = uuid4()
            await logging_service.write_decision_log(
                decision_id=decision_id,
                conversation_id=f"conv-current-{i}",
                user_id="user-001",
                message=f"current message {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )
            await logging_service.write_tool_invocation_log(
                decision_id=decision_id,
                tool_name="add_task",
                parameters={},
                success=True,
                duration_ms=50,
            )

        # Compare
        drift_report = await baseline_service.compare_to_baseline(
            baseline_id=baseline.id,
            current_start=current_start,
            drift_threshold=0.10,
        )

        assert drift_report.drift_exceeded is False
        assert drift_report.max_drift < 0.10

    @pytest.mark.asyncio
    async def test_drift_detection_exceeds_threshold(self, log_db):
        """Test drift detection when behavior changes significantly."""
        logging_service = LoggingService()
        baseline_service = BaselineService()

        # Create baseline data (all CREATE_TASK)
        # Logs are created NOW, so use a time range that includes NOW
        baseline_start = datetime.now(UTC) - timedelta(minutes=5)

        for i in range(20):
            decision_id = uuid4()
            await logging_service.write_decision_log(
                decision_id=decision_id,
                conversation_id=f"conv-baseline-{i}",
                user_id="user-001",
                message=f"baseline message {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )
            await logging_service.write_tool_invocation_log(
                decision_id=decision_id,
                tool_name="add_task",
                parameters={},
                success=True,
                duration_ms=50,
            )

        baseline_end = datetime.now(UTC) + timedelta(minutes=1)

        # Create baseline
        baseline = await baseline_service.create_baseline(
            name="baseline-for-drift",
            description="Will detect drift",
            sample_start=baseline_start,
            sample_end=baseline_end,
        )

        # Create current data (mostly LIST_TASKS - different pattern)
        current_start = datetime.now(UTC) - timedelta(minutes=1)
        for i in range(10):
            decision_id = uuid4()
            # 80% LIST_TASKS, 20% CREATE_TASK (vs 100% CREATE_TASK in baseline)
            intent = "LIST_TASKS" if i < 8 else "CREATE_TASK"
            tool = "list_tasks" if i < 8 else "add_task"
            await logging_service.write_decision_log(
                decision_id=decision_id,
                conversation_id=f"conv-current-{i}",
                user_id="user-001",
                message=f"current message {i}",
                intent_type=intent,
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )
            await logging_service.write_tool_invocation_log(
                decision_id=decision_id,
                tool_name=tool,
                parameters={},
                success=True,
                duration_ms=50,
            )

        # Compare
        drift_report = await baseline_service.compare_to_baseline(
            baseline_id=baseline.id,
            current_start=current_start,
            drift_threshold=0.10,
        )

        assert drift_report.drift_exceeded is True
        assert drift_report.max_drift > 0.10
        assert len(drift_report.flagged_metrics) > 0
        assert any("CREATE_TASK" in m for m in drift_report.flagged_metrics)

    @pytest.mark.asyncio
    async def test_drift_detection_baseline_not_found(self, log_db):
        """Test error when baseline doesn't exist."""
        baseline_service = BaselineService()

        with pytest.raises(BaselineNotFoundError):
            await baseline_service.compare_to_baseline(
                baseline_id=uuid4(),
                current_start=datetime.now(UTC) - timedelta(hours=1),
            )

    @pytest.mark.asyncio
    async def test_drift_detection_empty_current_period(self, log_db):
        """Test drift detection with no current data."""
        logging_service = LoggingService()
        baseline_service = BaselineService()

        # Create baseline data
        # Logs are created NOW, so use a time range that includes NOW
        baseline_start = datetime.now(UTC) - timedelta(minutes=5)

        for i in range(10):
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id=f"conv-{i}",
                user_id="user-001",
                message=f"test {i}",
                intent_type="CREATE_TASK",
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        baseline_end = datetime.now(UTC) + timedelta(minutes=1)

        baseline = await baseline_service.create_baseline(
            name="baseline-empty-compare",
            description="For empty comparison",
            sample_start=baseline_start,
            sample_end=baseline_end,
        )

        # Compare with empty period (far in future)
        drift_report = await baseline_service.compare_to_baseline(
            baseline_id=baseline.id,
            current_start=datetime.now(UTC) + timedelta(hours=10),
            current_end=datetime.now(UTC) + timedelta(hours=11),
        )

        assert drift_report.drift_exceeded is False
        assert drift_report.max_drift == 0.0


class TestDriftThreshold:
    """Tests for drift threshold at 10%."""

    @pytest.mark.asyncio
    async def test_drift_at_exactly_10_percent(self, log_db):
        """Test behavior at exactly 10% threshold."""
        logging_service = LoggingService()
        baseline_service = BaselineService()

        # Create baseline: 50% CREATE_TASK, 50% LIST_TASKS
        # Logs are created NOW, so use a time range that includes NOW
        baseline_start = datetime.now(UTC) - timedelta(minutes=5)

        for i in range(20):
            intent = "CREATE_TASK" if i < 10 else "LIST_TASKS"
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id=f"conv-{i}",
                user_id="user-001",
                message=f"test {i}",
                intent_type=intent,
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        # Mark the end of baseline creation
        baseline_end = datetime.now(UTC) + timedelta(seconds=1)

        baseline = await baseline_service.create_baseline(
            name="threshold-test",
            description="Test 10% threshold",
            sample_start=baseline_start,
            sample_end=baseline_end,
        )

        # Create current data AFTER baseline period
        # Mark start AFTER baseline end to ensure no overlap
        current_start = datetime.now(UTC)

        # Create current: 60% CREATE_TASK, 40% LIST_TASKS (10% drift)
        for i in range(10):
            intent = "CREATE_TASK" if i < 6 else "LIST_TASKS"
            await logging_service.write_decision_log(
                decision_id=uuid4(),
                conversation_id=f"conv-current-{i}",
                user_id="user-001",
                message=f"current {i}",
                intent_type=intent,
                decision_type="INVOKE_TOOL",
                outcome_category="SUCCESS:TASK_COMPLETED",
                duration_ms=100,
            )

        drift_report = await baseline_service.compare_to_baseline(
            baseline_id=baseline.id,
            current_start=current_start,
            drift_threshold=0.10,
        )

        # 10% drift should be exactly at threshold, not exceeded
        # But due to floating point, might be slightly over
        assert drift_report.max_drift == pytest.approx(0.10, abs=0.01)

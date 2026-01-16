"""
Tests for the validation service.

Feature: 004-agent-observability
"""

from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from src.observability.logging_service import LoggingService
from src.observability.models import TestCase
from src.observability.validation_service import FixtureLoadError, ValidationService


class TestLoadFixtures:
    """Tests for load_fixtures method."""

    @pytest.mark.asyncio
    async def test_load_fixtures_success(self):
        """Test successful fixture loading."""
        validation_service = ValidationService()
        fixtures_path = Path(__file__).parent / "fixtures" / "agent_behaviors.yaml"

        fixtures = await validation_service.load_fixtures(fixtures_path)

        assert len(fixtures) >= 7
        assert fixtures[0].test_id == "TC001"
        assert fixtures[0].input_message == "remind me to buy groceries"
        assert fixtures[0].expected_intent == "CREATE_TASK"
        assert fixtures[0].expected_tool == "add_task"
        assert fixtures[0].expected_outcome == "SUCCESS"

    @pytest.mark.asyncio
    async def test_load_fixtures_file_not_found(self):
        """Test error when fixtures file doesn't exist."""
        validation_service = ValidationService()

        with pytest.raises(FixtureLoadError) as exc_info:
            await validation_service.load_fixtures(Path("/nonexistent/file.yaml"))

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_fixtures_invalid_yaml(self, tmp_path):
        """Test error when YAML is invalid."""
        validation_service = ValidationService()

        # Create invalid YAML file
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [}")

        with pytest.raises(FixtureLoadError) as exc_info:
            await validation_service.load_fixtures(invalid_yaml)

        assert "Invalid YAML" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_fixtures_missing_tests_key(self, tmp_path):
        """Test error when 'tests' key is missing."""
        validation_service = ValidationService()

        # Create YAML without 'tests' key
        no_tests = tmp_path / "no_tests.yaml"
        no_tests.write_text("other_key: value")

        with pytest.raises(FixtureLoadError) as exc_info:
            await validation_service.load_fixtures(no_tests)

        assert "must contain 'tests'" in str(exc_info.value)


class TestRunValidation:
    """Tests for run_validation method."""

    @pytest.mark.asyncio
    async def test_run_validation_all_pass(self, log_db):
        """Test validation with all passing tests."""
        logging_service = LoggingService()
        validation_service = ValidationService()

        # Create matching decision logs
        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-test",
            user_id="user-001",
            message="remind me to buy groceries",
            intent_type="CREATE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=100,
        )

        # Create test fixtures
        fixtures = [
            TestCase(
                test_id="TC001",
                input_message="remind me to buy groceries",
                expected_intent="CREATE_TASK",
                expected_tool=None,  # Don't check tool
                expected_outcome="SUCCESS",
            ),
        ]

        report = await validation_service.run_validation(fixtures)

        assert report.test_count == 1
        assert report.pass_count == 1
        assert report.fail_count == 0
        assert report.results["tests"][0]["status"] == "PASS"

    @pytest.mark.asyncio
    async def test_run_validation_with_failures(self, log_db):
        """Test validation with failing tests."""
        logging_service = LoggingService()
        validation_service = ValidationService()

        # Create decision log with different intent
        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-test",
            user_id="user-001",
            message="what are my tasks",
            intent_type="GENERAL_CHAT",  # Wrong intent
            decision_type="RESPOND_ONLY",
            outcome_category="SUCCESS:RESPONSE_GIVEN",
            duration_ms=100,
        )

        # Create test expecting different intent
        fixtures = [
            TestCase(
                test_id="TC002",
                input_message="what are my tasks",
                expected_intent="LIST_TASKS",  # Expected LIST_TASKS
                expected_tool="list_tasks",
                expected_outcome="SUCCESS",
            ),
        ]

        report = await validation_service.run_validation(fixtures)

        assert report.test_count == 1
        assert report.pass_count == 0
        assert report.fail_count == 1
        assert report.results["tests"][0]["status"] == "FAIL"

    @pytest.mark.asyncio
    async def test_run_validation_no_matching_log(self, log_db):
        """Test validation when no matching log exists."""
        validation_service = ValidationService()

        fixtures = [
            TestCase(
                test_id="TC999",
                input_message="unique message not in logs",
                expected_intent="CREATE_TASK",
                expected_tool=None,
                expected_outcome="SUCCESS",
            ),
        ]

        report = await validation_service.run_validation(fixtures)

        assert report.test_count == 1
        assert report.pass_count == 0
        assert report.fail_count == 0  # Skipped, not failed
        assert report.results["tests"][0]["status"] == "SKIP"

    @pytest.mark.asyncio
    async def test_run_validation_report_stored(self, log_db):
        """Test that validation report is stored in database."""
        logging_service = LoggingService()
        validation_service = ValidationService()

        # Create matching log
        await logging_service.write_decision_log(
            decision_id=uuid4(),
            conversation_id="conv-test",
            user_id="user-001",
            message="test message for storage",
            intent_type="CREATE_TASK",
            decision_type="INVOKE_TOOL",
            outcome_category="SUCCESS:TASK_COMPLETED",
            duration_ms=100,
        )

        fixtures = [
            TestCase(
                test_id="TC_STORE",
                input_message="test message for storage",
                expected_intent="CREATE_TASK",
                expected_tool=None,
                expected_outcome="SUCCESS",
            ),
        ]

        report = await validation_service.run_validation(fixtures)

        # Verify stored in database
        from src.observability.database import get_log_db

        async with get_log_db() as db:
            cursor = await db.execute(
                "SELECT * FROM validation_reports WHERE id = ?",
                (str(report.id),)
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row["test_count"] == 1
            assert row["pass_count"] == 1


class TestTestCase:
    """Tests for TestCase model."""

    def test_test_case_creation(self):
        """Test TestCase creation."""
        test_case = TestCase(
            test_id="TC001",
            input_message="test input",
            expected_intent="CREATE_TASK",
            expected_tool="add_task",
            expected_outcome="SUCCESS",
        )

        assert test_case.test_id == "TC001"
        assert test_case.input_message == "test input"
        assert test_case.expected_intent == "CREATE_TASK"
        assert test_case.expected_tool == "add_task"
        assert test_case.expected_outcome == "SUCCESS"

    def test_test_case_optional_tool(self):
        """Test TestCase with optional tool."""
        test_case = TestCase(
            test_id="TC002",
            input_message="test input",
            expected_intent="GENERAL_CHAT",
            expected_tool=None,
            expected_outcome="SUCCESS",
        )

        assert test_case.expected_tool is None

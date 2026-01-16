"""
Test fixtures for observability module.

Provides temporary SQLite database and sample data for testing.

Feature: 004-agent-observability
"""

import tempfile
from datetime import datetime, timedelta, UTC
from pathlib import Path
from uuid import uuid4

import pytest

from src.observability.database import get_log_db, init_log_db, set_db_path
from src.observability.models import DecisionLog, ToolInvocationLog


@pytest.fixture
async def log_db(tmp_path):
    """
    Provide a temporary SQLite database for testing.

    Automatically initializes tables and cleans up after each test.
    Uses a temp file to ensure database persistence across connections.
    """
    # Use temporary file database for testing
    db_path = tmp_path / "test_logs.db"
    set_db_path(db_path)
    await init_log_db()

    yield

    # Reset to default path after test
    from src.observability.database import _DEFAULT_DB_PATH
    set_db_path(_DEFAULT_DB_PATH)


@pytest.fixture
def sample_decision_log() -> DecisionLog:
    """Provide a sample decision log for testing."""
    return DecisionLog(
        decision_id=uuid4(),
        conversation_id="conv-test-001",
        user_id="user-test-001",
        message="remind me to buy groceries",
        intent_type="CREATE_TASK",
        confidence=0.95,
        extracted_params={"description": "buy groceries"},
        decision_type="INVOKE_TOOL",
        outcome_category="SUCCESS:TASK_COMPLETED",
        response_text="I've added 'buy groceries' to your tasks.",
        duration_ms=150,
    )


@pytest.fixture
def sample_tool_invocation_log(sample_decision_log: DecisionLog) -> ToolInvocationLog:
    """Provide a sample tool invocation log for testing."""
    return ToolInvocationLog(
        decision_id=sample_decision_log.decision_id,
        tool_name="add_task",
        parameters={"description": "buy groceries"},
        result={"task_id": "task-123", "status": "pending"},
        success=True,
        duration_ms=45,
        invoked_at=datetime.now(UTC),
        sequence=1,
    )


@pytest.fixture
def sample_error_decision_log() -> DecisionLog:
    """Provide a sample error decision log for testing."""
    return DecisionLog(
        decision_id=uuid4(),
        conversation_id="conv-test-002",
        user_id="user-test-001",
        message="delete all tasks",
        intent_type="DELETE_TASK",
        confidence=0.88,
        extracted_params={},
        decision_type="INVOKE_TOOL",
        outcome_category="ERROR:TOOL_INVOCATION",
        response_text="Sorry, there was an error processing your request.",
        duration_ms=200,
    )


@pytest.fixture
def sample_failed_tool_log(sample_error_decision_log: DecisionLog) -> ToolInvocationLog:
    """Provide a sample failed tool invocation log for testing."""
    return ToolInvocationLog(
        decision_id=sample_error_decision_log.decision_id,
        tool_name="delete_task",
        parameters={"task_id": "all"},
        result=None,
        success=False,
        error_code="VALIDATION_ERROR",
        error_message="Cannot delete all tasks without confirmation",
        duration_ms=25,
        invoked_at=datetime.now(UTC),
        sequence=1,
    )


@pytest.fixture
async def populated_db(
    log_db,
    sample_decision_log: DecisionLog,
    sample_tool_invocation_log: ToolInvocationLog,
):
    """
    Provide a database populated with sample data.

    Includes one decision log and one tool invocation log.
    """
    async with get_log_db() as db:
        # Insert decision log
        data = sample_decision_log.to_dict()
        await db.execute(
            """
            INSERT INTO decision_logs
            (id, decision_id, conversation_id, user_id, message, intent_type,
             confidence, extracted_params, decision_type, outcome_category,
             response_text, created_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"], data["decision_id"], data["conversation_id"],
                data["user_id"], data["message"], data["intent_type"],
                data["confidence"], data["extracted_params"], data["decision_type"],
                data["outcome_category"], data["response_text"], data["created_at"],
                data["duration_ms"],
            ),
        )

        # Insert tool invocation log
        tool_data = sample_tool_invocation_log.to_dict()
        await db.execute(
            """
            INSERT INTO tool_invocation_logs
            (id, decision_id, tool_name, parameters, result, success,
             error_code, error_message, duration_ms, invoked_at, sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tool_data["id"], tool_data["decision_id"], tool_data["tool_name"],
                tool_data["parameters"], tool_data["result"], tool_data["success"],
                tool_data["error_code"], tool_data["error_message"],
                tool_data["duration_ms"], tool_data["invoked_at"], tool_data["sequence"],
            ),
        )

        await db.commit()

    yield sample_decision_log, sample_tool_invocation_log


@pytest.fixture
async def large_dataset(log_db):
    """
    Provide a database with many records for performance testing.

    Creates 1000 decision logs with varying outcomes.
    """
    async with get_log_db() as db:
        base_time = datetime.now(UTC) - timedelta(days=7)
        outcomes = [
            "SUCCESS:TASK_COMPLETED",
            "SUCCESS:RESPONSE_GIVEN",
            "ERROR:TOOL_INVOCATION",
            "AMBIGUITY:UNCLEAR_INTENT",
        ]
        intents = ["CREATE_TASK", "LIST_TASKS", "COMPLETE_TASK", "GENERAL_CHAT"]

        for i in range(1000):
            decision_id = uuid4()
            created_at = base_time + timedelta(minutes=i * 10)
            outcome = outcomes[i % len(outcomes)]
            intent = intents[i % len(intents)]

            await db.execute(
                """
                INSERT INTO decision_logs
                (id, decision_id, conversation_id, user_id, message, intent_type,
                 confidence, extracted_params, decision_type, outcome_category,
                 response_text, created_at, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()), str(decision_id), f"conv-{i % 100:03d}",
                    f"user-{i % 10:03d}", f"Test message {i}", intent,
                    0.9, "{}", "INVOKE_TOOL", outcome,
                    f"Response {i}", created_at.isoformat(), 100 + (i % 100),
                ),
            )

            # Add tool invocation for some decisions
            if "TASK" in intent:
                await db.execute(
                    """
                    INSERT INTO tool_invocation_logs
                    (id, decision_id, tool_name, parameters, result, success,
                     error_code, error_message, duration_ms, invoked_at, sequence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid4()), str(decision_id), "add_task",
                        '{"description": "test"}', '{"task_id": "t1"}',
                        1 if "SUCCESS" in outcome else 0,
                        None if "SUCCESS" in outcome else "TOOL_EXECUTION_ERROR",
                        None if "SUCCESS" in outcome else "Test error",
                        50, created_at.isoformat(), 1,
                    ),
                )

        await db.commit()

    yield

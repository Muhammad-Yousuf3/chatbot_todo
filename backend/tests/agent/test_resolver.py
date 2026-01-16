"""Tests for task reference resolution."""

import pytest
from uuid import uuid4

from src.agent.resolver import (
    find_matching_tasks,
    resolve_task_reference,
    resolve_task_for_operation,
)


@pytest.fixture
def sample_tasks() -> list[dict]:
    """Sample tasks for testing."""
    return [
        {
            "id": str(uuid4()),
            "user_id": "test-user",
            "description": "buy groceries",
            "completed": False,
        },
        {
            "id": str(uuid4()),
            "user_id": "test-user",
            "description": "call mom",
            "completed": False,
        },
        {
            "id": str(uuid4()),
            "user_id": "test-user",
            "description": "finish report",
            "completed": True,
        },
        {
            "id": str(uuid4()),
            "user_id": "test-user",
            "description": "buy milk",
            "completed": False,
        },
    ]


class TestResolveTaskReference:
    """Tests for resolve_task_reference function (T050, T051)."""

    def test_exact_match(self, sample_tasks):
        """Exact description match should return the task."""
        result = resolve_task_reference("buy groceries", sample_tasks)
        assert result is not None
        assert result["description"] == "buy groceries"

    def test_exact_match_case_insensitive(self, sample_tasks):
        """Match should be case-insensitive."""
        result = resolve_task_reference("BUY GROCERIES", sample_tasks)
        assert result is not None
        assert result["description"] == "buy groceries"

    def test_partial_match(self, sample_tasks):
        """Partial match should return the task."""
        result = resolve_task_reference("groceries", sample_tasks)
        assert result is not None
        assert result["description"] == "buy groceries"

    def test_multiple_matches_returns_none(self, sample_tasks):
        """Multiple matches should return None (requires clarification)."""
        # "buy" matches both "buy groceries" and "buy milk"
        result = resolve_task_reference("buy", sample_tasks)
        assert result is None

    def test_no_match_returns_none(self, sample_tasks):
        """No match should return None."""
        result = resolve_task_reference("nonexistent task", sample_tasks)
        assert result is None

    def test_position_reference_first(self, sample_tasks):
        """'first' should return the first pending task."""
        result = resolve_task_reference("first task", sample_tasks)
        assert result is not None
        assert result["description"] == "buy groceries"

    def test_position_reference_last(self, sample_tasks):
        """'last' should return the last pending task."""
        result = resolve_task_reference("last task", sample_tasks)
        assert result is not None
        # Last pending task is "buy milk"
        assert result["description"] == "buy milk"

    def test_position_reference_second(self, sample_tasks):
        """'second' should return the second pending task."""
        result = resolve_task_reference("second task", sample_tasks)
        assert result is not None
        assert result["description"] == "call mom"

    def test_numeric_reference(self, sample_tasks):
        """'task 1' should return the first pending task."""
        result = resolve_task_reference("task 1", sample_tasks)
        assert result is not None
        assert result["description"] == "buy groceries"

    def test_numeric_reference_hash(self, sample_tasks):
        """'#2' should return the second pending task."""
        result = resolve_task_reference("#2", sample_tasks)
        assert result is not None
        assert result["description"] == "call mom"

    def test_empty_reference_returns_none(self, sample_tasks):
        """Empty reference should return None."""
        result = resolve_task_reference("", sample_tasks)
        assert result is None

    def test_empty_tasks_returns_none(self):
        """Empty task list should return None."""
        result = resolve_task_reference("groceries", [])
        assert result is None

    def test_completed_tasks_excluded(self, sample_tasks):
        """Completed tasks should be excluded from resolution."""
        result = resolve_task_reference("finish report", sample_tasks)
        assert result is None  # This task is completed


class TestFindMatchingTasks:
    """Tests for find_matching_tasks function."""

    def test_finds_single_match(self, sample_tasks):
        """Should find single matching task."""
        matches = find_matching_tasks("groceries", sample_tasks)
        assert len(matches) == 1
        assert matches[0]["description"] == "buy groceries"

    def test_finds_multiple_matches(self, sample_tasks):
        """Should find multiple matching tasks."""
        matches = find_matching_tasks("buy", sample_tasks)
        assert len(matches) == 2
        descriptions = [m["description"] for m in matches]
        assert "buy groceries" in descriptions
        assert "buy milk" in descriptions

    def test_no_matches_returns_empty(self, sample_tasks):
        """Should return empty list when no matches."""
        matches = find_matching_tasks("nonexistent", sample_tasks)
        assert len(matches) == 0


class TestResolveTaskForOperation:
    """Tests for resolve_task_for_operation function."""

    def test_unique_match_returns_task(self, sample_tasks):
        """Unique match should return (task, [task])."""
        task, matches = resolve_task_for_operation("groceries", sample_tasks)
        assert task is not None
        assert task["description"] == "buy groceries"
        assert len(matches) == 1

    def test_multiple_matches_returns_none_with_list(self, sample_tasks):
        """Multiple matches should return (None, matches_list)."""
        task, matches = resolve_task_for_operation("buy", sample_tasks)
        assert task is None
        assert len(matches) == 2

    def test_no_matches_returns_none_empty_list(self, sample_tasks):
        """No matches should return (None, [])."""
        task, matches = resolve_task_for_operation("nonexistent", sample_tasks)
        assert task is None
        assert len(matches) == 0

    def test_include_completed(self, sample_tasks):
        """With include_completed=True, completed tasks should be findable."""
        task, matches = resolve_task_for_operation(
            "finish report", sample_tasks, include_completed=True
        )
        assert task is not None
        assert task["description"] == "finish report"

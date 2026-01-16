"""
Validation service for automated behavior testing.

This service runs test fixtures against expected behaviors and generates
validation reports for CI/CD integration.

Feature: 004-agent-observability
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml

from .baseline_service import BaselineService
from .database import get_log_db
from .models import TestCase, ValidationReport


class FixtureLoadError(Exception):
    """Raised when fixture loading fails."""
    pass


class ValidationService:
    """
    Service for running automated validation tests.

    Validates agent behavior against expected patterns and
    generates reports for CI/CD.
    """

    def __init__(self):
        """Initialize the validation service."""
        self._baseline_service = BaselineService()

    async def load_fixtures(self, fixtures_path: Path) -> list[TestCase]:
        """
        Load test fixtures from a YAML file.

        Args:
            fixtures_path: Path to the fixtures file

        Returns:
            List of TestCase objects

        Raises:
            FixtureLoadError: If file cannot be loaded or parsed
        """
        try:
            with open(fixtures_path, "r") as f:
                data = yaml.safe_load(f)

            if not data or "tests" not in data:
                raise FixtureLoadError("Fixtures file must contain 'tests' key")

            test_cases = []
            for test_data in data["tests"]:
                test_case = TestCase(
                    test_id=test_data["test_id"],
                    input_message=test_data["input"],
                    expected_intent=test_data["expected_intent"],
                    expected_tool=test_data.get("expected_tool"),
                    expected_outcome=test_data["expected_outcome"],
                )
                test_cases.append(test_case)

            return test_cases

        except FileNotFoundError:
            raise FixtureLoadError(f"Fixtures file not found: {fixtures_path}")
        except yaml.YAMLError as e:
            raise FixtureLoadError(f"Invalid YAML in fixtures file: {e}")
        except KeyError as e:
            raise FixtureLoadError(f"Missing required field in test case: {e}")

    async def run_validation(
        self,
        test_fixtures: list[TestCase],
        baseline_id: UUID | None = None,
    ) -> ValidationReport:
        """
        Execute validation test suite against recent logs.

        Args:
            test_fixtures: Test cases to validate
            baseline_id: Optional baseline for drift check

        Returns:
            ValidationReport with test results
        """
        start_time = datetime.utcnow()
        test_results: list[dict[str, Any]] = []
        pass_count = 0
        fail_count = 0

        async with get_log_db() as db:
            for test_case in test_fixtures:
                # Find matching decision log by message
                cursor = await db.execute(
                    """
                    SELECT *
                    FROM decision_logs
                    WHERE message LIKE ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (f"%{test_case.input_message}%",),
                )
                row = await cursor.fetchone()

                if row is None:
                    # No matching log found - test cannot be validated
                    test_result = {
                        "test_id": test_case.test_id,
                        "input": test_case.input_message,
                        "expected_intent": test_case.expected_intent,
                        "actual_intent": None,
                        "expected_tool": test_case.expected_tool,
                        "actual_tool": None,
                        "expected_outcome": test_case.expected_outcome,
                        "actual_outcome": None,
                        "status": "SKIP",
                        "reason": "No matching log found",
                    }
                    test_results.append(test_result)
                    continue

                # Get tool invocations for this decision
                tool_cursor = await db.execute(
                    """
                    SELECT tool_name
                    FROM tool_invocation_logs
                    WHERE decision_id = ?
                    ORDER BY sequence
                    LIMIT 1
                    """,
                    (row["decision_id"],),
                )
                tool_row = await tool_cursor.fetchone()
                actual_tool = tool_row["tool_name"] if tool_row else None

                # Compare expectations
                intent_match = row["intent_type"] == test_case.expected_intent
                tool_match = (
                    test_case.expected_tool is None
                    or actual_tool == test_case.expected_tool
                )
                outcome_match = row["outcome_category"].startswith(
                    test_case.expected_outcome
                )

                passed = intent_match and tool_match and outcome_match

                if passed:
                    pass_count += 1
                    status = "PASS"
                else:
                    fail_count += 1
                    status = "FAIL"

                test_result = {
                    "test_id": test_case.test_id,
                    "input": test_case.input_message,
                    "expected_intent": test_case.expected_intent,
                    "actual_intent": row["intent_type"],
                    "expected_tool": test_case.expected_tool,
                    "actual_tool": actual_tool,
                    "expected_outcome": test_case.expected_outcome,
                    "actual_outcome": row["outcome_category"],
                    "status": status,
                }
                test_results.append(test_result)

        # Check drift if baseline provided
        drift_detected = False
        drift_metrics: dict[str, Any] = {}

        if baseline_id:
            try:
                drift_report = await self._baseline_service.compare_to_baseline(
                    baseline_id=baseline_id,
                    current_start=start_time - datetime.timedelta(hours=24),
                )
                drift_detected = drift_report.drift_exceeded
                drift_metrics = {
                    "intent_drift": drift_report.intent_drift,
                    "max_drift": drift_report.max_drift,
                    "threshold_exceeded": drift_report.drift_exceeded,
                }
            except Exception:
                # Drift check failed, continue without it
                pass

        # Build results
        results = {
            "tests": test_results,
            "drift_metrics": drift_metrics,
        }

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        report = ValidationReport(
            test_count=len(test_fixtures),
            pass_count=pass_count,
            fail_count=fail_count,
            results=results,
            duration_ms=duration_ms,
            drift_detected=drift_detected,
            baseline_id=baseline_id,
        )

        # Store in database
        async with get_log_db() as db:
            data = report.to_dict()
            await db.execute(
                """
                INSERT INTO validation_reports
                (id, run_at, baseline_id, test_count, pass_count, fail_count,
                 results, duration_ms, drift_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["run_at"], data["baseline_id"],
                    data["test_count"], data["pass_count"], data["fail_count"],
                    data["results"], data["duration_ms"], data["drift_detected"],
                ),
            )
            await db.commit()

        return report

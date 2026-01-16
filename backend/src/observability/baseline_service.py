"""
Baseline service for drift detection.

This service manages behavioral baselines and detects drift from
expected behavior patterns.

Feature: 004-agent-observability
"""

from datetime import datetime
from uuid import UUID, uuid4

from .database import get_log_db
from .models import BaselineSnapshot, DriftReport


class InsufficientDataError(Exception):
    """Raised when there isn't enough data for an operation."""
    pass


class DuplicateNameError(Exception):
    """Raised when a baseline name already exists."""
    pass


class BaselineNotFoundError(Exception):
    """Raised when a baseline is not found."""
    pass


class BaselineService:
    """
    Service for managing behavioral baselines and detecting drift.

    Provides functionality to:
    - Create baselines from historical log data
    - Compare current behavior to stored baselines
    - Generate drift reports with flagged metrics
    """

    async def create_baseline(
        self,
        name: str,
        description: str | None,
        sample_start: datetime,
        sample_end: datetime,
        min_sample_size: int = 10,
    ) -> BaselineSnapshot:
        """
        Create a new baseline snapshot from historical logs.

        Args:
            name: Unique baseline name
            description: Purpose of baseline
            sample_start: Start of sample period
            sample_end: End of sample period
            min_sample_size: Minimum number of decisions required

        Returns:
            BaselineSnapshot: Created baseline

        Raises:
            InsufficientDataError: Not enough decisions in sample period
            DuplicateNameError: Baseline name already exists
        """
        async with get_log_db() as db:
            # Check for duplicate name
            cursor = await db.execute(
                "SELECT 1 FROM baseline_snapshots WHERE snapshot_name = ?",
                (name,)
            )
            if await cursor.fetchone():
                raise DuplicateNameError(f"Baseline name already exists: {name}")

            # Get sample size
            cursor = await db.execute(
                """
                SELECT COUNT(*) as count
                FROM decision_logs
                WHERE created_at >= ? AND created_at <= ?
                """,
                (sample_start.isoformat(), sample_end.isoformat()),
            )
            row = await cursor.fetchone()
            sample_size = row["count"] if row else 0

            if sample_size < min_sample_size:
                raise InsufficientDataError(
                    f"Need at least {min_sample_size} decisions, found {sample_size}"
                )

            # Calculate intent distribution
            cursor = await db.execute(
                """
                SELECT
                    intent_type,
                    COUNT(*) * 1.0 / ? as percentage
                FROM decision_logs
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY intent_type
                """,
                (sample_size, sample_start.isoformat(), sample_end.isoformat()),
            )
            rows = await cursor.fetchall()
            intent_distribution = {r["intent_type"]: r["percentage"] for r in rows}

            # Calculate tool frequency
            cursor = await db.execute(
                """
                SELECT
                    tool_name,
                    COUNT(*) as count
                FROM tool_invocation_logs
                WHERE invoked_at >= ? AND invoked_at <= ?
                GROUP BY tool_name
                """,
                (sample_start.isoformat(), sample_end.isoformat()),
            )
            rows = await cursor.fetchall()
            tool_frequency = {r["tool_name"]: r["count"] for r in rows}

            # Calculate error rate
            cursor = await db.execute(
                """
                SELECT
                    COUNT(*) * 1.0 / ? as error_rate
                FROM decision_logs
                WHERE created_at >= ? AND created_at <= ?
                AND outcome_category LIKE 'ERROR:%'
                """,
                (sample_size, sample_start.isoformat(), sample_end.isoformat()),
            )
            row = await cursor.fetchone()
            error_rate = row["error_rate"] if row and row["error_rate"] else 0.0

            # Create baseline
            baseline = BaselineSnapshot(
                snapshot_name=name,
                description=description,
                sample_start=sample_start,
                sample_end=sample_end,
                intent_distribution=intent_distribution,
                tool_frequency=tool_frequency,
                error_rate=error_rate,
                sample_size=sample_size,
            )

            # Store in database
            data = baseline.to_dict()
            await db.execute(
                """
                INSERT INTO baseline_snapshots
                (id, snapshot_name, description, created_at, sample_start, sample_end,
                 intent_distribution, tool_frequency, error_rate, sample_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["snapshot_name"], data["description"],
                    data["created_at"], data["sample_start"], data["sample_end"],
                    data["intent_distribution"], data["tool_frequency"],
                    data["error_rate"], data["sample_size"],
                ),
            )
            await db.commit()

            return baseline

    async def get_baseline(self, baseline_id: UUID) -> BaselineSnapshot:
        """
        Get a baseline by ID.

        Args:
            baseline_id: The baseline ID to retrieve

        Returns:
            BaselineSnapshot

        Raises:
            BaselineNotFoundError: If baseline doesn't exist
        """
        async with get_log_db() as db:
            cursor = await db.execute(
                "SELECT * FROM baseline_snapshots WHERE id = ?",
                (str(baseline_id),)
            )
            row = await cursor.fetchone()

            if not row:
                raise BaselineNotFoundError(f"Baseline not found: {baseline_id}")

            return BaselineSnapshot.from_row(row)

    async def compare_to_baseline(
        self,
        baseline_id: UUID,
        current_start: datetime,
        current_end: datetime | None = None,
        drift_threshold: float = 0.10,
    ) -> DriftReport:
        """
        Compare current behavior to a stored baseline.

        Args:
            baseline_id: The baseline to compare against
            current_start: Start of current period
            current_end: End of current period (defaults to now)
            drift_threshold: Threshold for flagging drift (default 10%)

        Returns:
            DriftReport with comparison results
        """
        current_end = current_end or datetime.utcnow()

        # Get baseline
        baseline = await self.get_baseline(baseline_id)

        async with get_log_db() as db:
            # Get current sample size
            cursor = await db.execute(
                """
                SELECT COUNT(*) as count
                FROM decision_logs
                WHERE created_at >= ? AND created_at <= ?
                """,
                (current_start.isoformat(), current_end.isoformat()),
            )
            row = await cursor.fetchone()
            current_sample_size = row["count"] if row else 0

            if current_sample_size == 0:
                # No data to compare
                return DriftReport(
                    baseline_id=baseline_id,
                    baseline_name=baseline.snapshot_name,
                    comparison_period=(current_start, current_end),
                    intent_drift={},
                    tool_drift={},
                    max_drift=0.0,
                    drift_exceeded=False,
                    flagged_metrics=[],
                )

            # Calculate current intent distribution
            cursor = await db.execute(
                """
                SELECT
                    intent_type,
                    COUNT(*) * 1.0 / ? as percentage
                FROM decision_logs
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY intent_type
                """,
                (current_sample_size, current_start.isoformat(), current_end.isoformat()),
            )
            rows = await cursor.fetchall()
            current_intent_dist = {r["intent_type"]: r["percentage"] for r in rows}

            # Calculate current tool frequency
            cursor = await db.execute(
                """
                SELECT
                    tool_name,
                    COUNT(*) as count
                FROM tool_invocation_logs
                WHERE invoked_at >= ? AND invoked_at <= ?
                GROUP BY tool_name
                """,
                (current_start.isoformat(), current_end.isoformat()),
            )
            rows = await cursor.fetchall()
            current_tool_freq = {r["tool_name"]: r["count"] for r in rows}

        # Calculate intent drift
        all_intents = set(baseline.intent_distribution.keys()) | set(current_intent_dist.keys())
        intent_drift = {}
        for intent in all_intents:
            baseline_pct = baseline.intent_distribution.get(intent, 0.0)
            current_pct = current_intent_dist.get(intent, 0.0)
            intent_drift[intent] = current_pct - baseline_pct

        # Calculate tool drift (normalized by sample size)
        total_baseline_tools = sum(baseline.tool_frequency.values()) or 1
        total_current_tools = sum(current_tool_freq.values()) or 1

        all_tools = set(baseline.tool_frequency.keys()) | set(current_tool_freq.keys())
        tool_drift = {}
        for tool in all_tools:
            baseline_pct = baseline.tool_frequency.get(tool, 0) / total_baseline_tools
            current_pct = current_tool_freq.get(tool, 0) / total_current_tools
            tool_drift[tool] = current_pct - baseline_pct

        # Find max drift and flagged metrics
        max_drift = 0.0
        flagged_metrics = []

        for intent, drift in intent_drift.items():
            abs_drift = abs(drift)
            if abs_drift > max_drift:
                max_drift = abs_drift
            if abs_drift > drift_threshold:
                direction = "increased" if drift > 0 else "decreased"
                flagged_metrics.append(f"intent:{intent} {direction} by {abs_drift:.1%}")

        for tool, drift in tool_drift.items():
            abs_drift = abs(drift)
            if abs_drift > max_drift:
                max_drift = abs_drift
            if abs_drift > drift_threshold:
                direction = "increased" if drift > 0 else "decreased"
                flagged_metrics.append(f"tool:{tool} {direction} by {abs_drift:.1%}")

        drift_exceeded = max_drift > drift_threshold

        return DriftReport(
            baseline_id=baseline_id,
            baseline_name=baseline.snapshot_name,
            comparison_period=(current_start, current_end),
            intent_drift=intent_drift,
            tool_drift=tool_drift,
            max_drift=max_drift,
            drift_exceeded=drift_exceeded,
            flagged_metrics=flagged_metrics,
        )

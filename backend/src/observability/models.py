"""
Data models for the observability layer.

These models define the structure of decision logs, tool invocation logs,
baselines, and validation reports stored in SQLite.

Feature: 004-agent-observability
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DecisionLog:
    """
    A complete record of a single agent decision.

    Captures the full lifecycle from user input to final outcome.
    """

    decision_id: UUID
    conversation_id: str
    user_id: str
    message: str
    intent_type: str
    decision_type: str
    outcome_category: str
    duration_ms: int
    id: UUID = field(default_factory=uuid4)
    confidence: float | None = None
    extracted_params: dict[str, Any] = field(default_factory=dict)
    response_text: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "decision_id": str(self.decision_id),
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "message": self.message,
            "intent_type": self.intent_type,
            "confidence": self.confidence,
            "extracted_params": json.dumps(self.extracted_params),
            "decision_type": self.decision_type,
            "outcome_category": self.outcome_category,
            "response_text": self.response_text,
            "created_at": self.created_at.isoformat(),
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_row(cls, row: Any) -> "DecisionLog":
        """Create from database row."""
        return cls(
            id=UUID(row["id"]),
            decision_id=UUID(row["decision_id"]),
            conversation_id=row["conversation_id"],
            user_id=row["user_id"],
            message=row["message"],
            intent_type=row["intent_type"],
            confidence=row["confidence"],
            extracted_params=json.loads(row["extracted_params"] or "{}"),
            decision_type=row["decision_type"],
            outcome_category=row["outcome_category"],
            response_text=row["response_text"],
            created_at=datetime.fromisoformat(row["created_at"]),
            duration_ms=row["duration_ms"],
        )


@dataclass
class ToolInvocationLog:
    """
    A record of a single MCP tool call within a decision.

    Links to parent DecisionLog via decision_id.
    """

    decision_id: UUID
    tool_name: str
    parameters: dict[str, Any]
    success: bool
    duration_ms: int
    invoked_at: datetime
    sequence: int
    id: UUID = field(default_factory=uuid4)
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "decision_id": str(self.decision_id),
            "tool_name": self.tool_name,
            "parameters": json.dumps(self.parameters),
            "result": json.dumps(self.result) if self.result else None,
            "success": 1 if self.success else 0,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "invoked_at": self.invoked_at.isoformat(),
            "sequence": self.sequence,
        }

    @classmethod
    def from_row(cls, row: Any) -> "ToolInvocationLog":
        """Create from database row."""
        return cls(
            id=UUID(row["id"]),
            decision_id=UUID(row["decision_id"]),
            tool_name=row["tool_name"],
            parameters=json.loads(row["parameters"]),
            result=json.loads(row["result"]) if row["result"] else None,
            success=bool(row["success"]),
            error_code=row["error_code"],
            error_message=row["error_message"],
            duration_ms=row["duration_ms"],
            invoked_at=datetime.fromisoformat(row["invoked_at"]),
            sequence=row["sequence"],
        )


@dataclass
class BaselineSnapshot:
    """
    A stored pattern of expected behavior for drift comparison.

    Contains aggregated metrics from a sample period.
    """

    snapshot_name: str
    sample_start: datetime
    sample_end: datetime
    intent_distribution: dict[str, float]
    tool_frequency: dict[str, int]
    error_rate: float
    sample_size: int
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "snapshot_name": self.snapshot_name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "sample_start": self.sample_start.isoformat(),
            "sample_end": self.sample_end.isoformat(),
            "intent_distribution": json.dumps(self.intent_distribution),
            "tool_frequency": json.dumps(self.tool_frequency),
            "error_rate": self.error_rate,
            "sample_size": self.sample_size,
        }

    @classmethod
    def from_row(cls, row: Any) -> "BaselineSnapshot":
        """Create from database row."""
        return cls(
            id=UUID(row["id"]),
            snapshot_name=row["snapshot_name"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]),
            sample_start=datetime.fromisoformat(row["sample_start"]),
            sample_end=datetime.fromisoformat(row["sample_end"]),
            intent_distribution=json.loads(row["intent_distribution"]),
            tool_frequency=json.loads(row["tool_frequency"]),
            error_rate=row["error_rate"],
            sample_size=row["sample_size"],
        )


@dataclass
class ValidationReport:
    """
    Results of automated comparison between actual and expected behavior.

    Contains test results and optional drift metrics.
    """

    test_count: int
    pass_count: int
    fail_count: int
    results: dict[str, Any]
    duration_ms: int
    drift_detected: bool
    id: UUID = field(default_factory=uuid4)
    run_at: datetime = field(default_factory=datetime.utcnow)
    baseline_id: UUID | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id),
            "run_at": self.run_at.isoformat(),
            "baseline_id": str(self.baseline_id) if self.baseline_id else None,
            "test_count": self.test_count,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "results": json.dumps(self.results),
            "duration_ms": self.duration_ms,
            "drift_detected": 1 if self.drift_detected else 0,
        }

    @classmethod
    def from_row(cls, row: Any) -> "ValidationReport":
        """Create from database row."""
        return cls(
            id=UUID(row["id"]),
            run_at=datetime.fromisoformat(row["run_at"]),
            baseline_id=UUID(row["baseline_id"]) if row["baseline_id"] else None,
            test_count=row["test_count"],
            pass_count=row["pass_count"],
            fail_count=row["fail_count"],
            results=json.loads(row["results"]),
            duration_ms=row["duration_ms"],
            drift_detected=bool(row["drift_detected"]),
        )


@dataclass
class DecisionTrace:
    """
    Complete trace of a decision including all tool invocations.

    Used for detailed inspection of a single agent decision.
    """

    decision: DecisionLog
    tool_invocations: list[ToolInvocationLog] = field(default_factory=list)


@dataclass
class QueryResult:
    """
    Paginated query result with total count.
    """

    items: list[DecisionLog]
    total: int
    has_more: bool


@dataclass
class MetricsSummary:
    """
    Aggregated metrics for a time period.
    """

    total_decisions: int
    success_rate: float
    error_breakdown: dict[str, int]
    avg_decision_duration_ms: float
    avg_tool_duration_ms: float
    intent_distribution: dict[str, float]
    tool_usage: dict[str, int]


@dataclass
class DriftReport:
    """
    Results of comparing current behavior to a baseline.
    """

    baseline_id: UUID
    baseline_name: str
    comparison_period: tuple[datetime, datetime]
    intent_drift: dict[str, float]
    tool_drift: dict[str, float]
    max_drift: float
    drift_exceeded: bool
    flagged_metrics: list[str] = field(default_factory=list)


@dataclass
class TestCase:
    """
    A single test case for validation.
    """

    test_id: str
    input_message: str
    expected_intent: str
    expected_tool: str | None
    expected_outcome: str

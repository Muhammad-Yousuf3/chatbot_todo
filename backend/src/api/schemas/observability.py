"""
Pydantic schemas for observability API endpoints.

Feature: 006-frontend-chat-ui
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ToolInvocationLogResponse(BaseModel):
    """Response schema for tool invocation log."""

    tool_name: str
    parameters: dict[str, Any]
    result: dict[str, Any] | None = None
    success: bool
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: int
    invoked_at: datetime
    sequence: int


class DecisionLogResponse(BaseModel):
    """Response schema for decision log."""

    decision_id: UUID
    conversation_id: str
    user_id: str
    message: str
    intent_type: str
    confidence: float | None = None
    decision_type: str
    outcome_category: str
    response_text: str | None = None
    created_at: datetime
    duration_ms: int


class DecisionTraceResponse(BaseModel):
    """Response schema for decision trace with tool invocations."""

    decision: DecisionLogResponse
    tool_invocations: list[ToolInvocationLogResponse] = Field(default_factory=list)


class DecisionQueryResponse(BaseModel):
    """Response schema for paginated decision query."""

    items: list[DecisionLogResponse]
    total: int
    has_more: bool


class MetricsSummaryResponse(BaseModel):
    """Response schema for metrics summary."""

    total_decisions: int
    success_rate: float
    error_breakdown: dict[str, int]
    avg_decision_duration_ms: float
    avg_tool_duration_ms: float
    intent_distribution: dict[str, float]
    tool_usage: dict[str, int]

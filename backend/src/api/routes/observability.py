"""
Observability REST API endpoints.

Exposes decision logs, traces, and metrics for the frontend dashboard.

Feature: 006-frontend-chat-ui
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas.observability import (
    DecisionLogResponse,
    DecisionQueryResponse,
    DecisionTraceResponse,
    MetricsSummaryResponse,
    ToolInvocationLogResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/observability", tags=["observability"])

# Service instance and availability flag
_query_service = None
_observability_available: bool = False


def _init_query_service():
    """Initialize the query service if observability is available."""
    global _query_service, _observability_available
    try:
        from src.observability.query_service import LogQueryService
        _query_service = LogQueryService()
        _observability_available = True
    except ImportError as e:
        logger.warning(f"Observability query service not available: {e}")
        _observability_available = False


def get_query_service():
    """Get or create the query service instance."""
    global _query_service, _observability_available
    if _query_service is None:
        _init_query_service()
    if not _observability_available or _query_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "OBSERVABILITY_UNAVAILABLE",
                    "message": "Observability service is temporarily unavailable.",
                }
            },
        )
    return _query_service


def handle_sqlite_error(e: Exception) -> None:
    """Handle SQLite errors and raise appropriate HTTP exceptions."""
    if isinstance(e, sqlite3.OperationalError):
        if "no such table" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "OBSERVABILITY_NOT_INITIALIZED",
                        "message": "Observability database not initialized. Please restart the server.",
                    }
                },
            )
    logger.error(f"SQLite error: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": {
                "code": "OBSERVABILITY_ERROR",
                "message": "An error occurred querying observability data.",
            }
        },
    )


def decision_log_to_response(log) -> DecisionLogResponse:
    """Convert internal DecisionLog to API response."""
    return DecisionLogResponse(
        decision_id=log.decision_id,
        conversation_id=log.conversation_id,
        user_id=log.user_id,
        message=log.message,
        intent_type=log.intent_type,
        confidence=log.confidence,
        decision_type=log.decision_type,
        outcome_category=log.outcome_category,
        response_text=log.response_text,
        created_at=log.created_at,
        duration_ms=log.duration_ms,
    )


def tool_invocation_to_response(log) -> ToolInvocationLogResponse:
    """Convert internal ToolInvocationLog to API response."""
    return ToolInvocationLogResponse(
        tool_name=log.tool_name,
        parameters=log.parameters,
        result=log.result,
        success=log.success,
        error_code=log.error_code,
        error_message=log.error_message,
        duration_ms=log.duration_ms,
        invoked_at=log.invoked_at,
        sequence=log.sequence,
    )


@router.get(
    "/decisions",
    response_model=DecisionQueryResponse,
    summary="Query decision logs",
    description="Query decision logs with optional filters and pagination.",
)
async def query_decisions(
    conversation_id: Optional[str] = Query(
        None, description="Filter by conversation ID"
    ),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_time: Optional[datetime] = Query(
        None, description="Filter decisions after this time"
    ),
    end_time: Optional[datetime] = Query(
        None, description="Filter decisions before this time"
    ),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    outcome_category: Optional[str] = Query(
        None, description="Filter by outcome category (supports prefix match)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> DecisionQueryResponse:
    """
    Query decision logs with filters.

    Supports filtering by conversation, user, time range, decision type,
    and outcome category. Results are paginated.
    """
    try:
        service = get_query_service()

        result = await service.query_decisions(
            conversation_id=conversation_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            decision_type=decision_type,
            outcome_category=outcome_category,
            limit=limit,
            offset=offset,
        )

        return DecisionQueryResponse(
            items=[decision_log_to_response(d) for d in result.items],
            total=result.total,
            has_more=result.has_more,
        )
    except HTTPException:
        raise
    except Exception as e:
        handle_sqlite_error(e)


@router.get(
    "/decisions/{decision_id}/trace",
    response_model=DecisionTraceResponse,
    summary="Get decision trace",
    description="Get the complete trace for a single decision including tool invocations.",
)
async def get_decision_trace(decision_id: UUID) -> DecisionTraceResponse:
    """
    Get complete decision trace including all tool invocations.

    Returns the decision log and all associated tool invocation records.
    """
    try:
        from src.observability.query_service import DecisionNotFoundError

        service = get_query_service()
        trace = await service.get_decision_trace(decision_id)

        return DecisionTraceResponse(
            decision=decision_log_to_response(trace.decision),
            tool_invocations=[tool_invocation_to_response(t) for t in trace.tool_invocations],
        )
    except HTTPException:
        raise
    except Exception as e:
        # Check if it's DecisionNotFoundError
        if "DecisionNotFoundError" in type(e).__name__ or "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "DECISION_NOT_FOUND",
                        "message": f"Decision not found: {decision_id}",
                    }
                },
            )
        handle_sqlite_error(e)


@router.get(
    "/metrics",
    response_model=MetricsSummaryResponse,
    summary="Get metrics summary",
    description="Get aggregated metrics for a time period.",
)
async def get_metrics(
    start_time: datetime = Query(..., description="Start of analysis period"),
    end_time: Optional[datetime] = Query(
        None, description="End of analysis period (defaults to now)"
    ),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
) -> MetricsSummaryResponse:
    """
    Get aggregated metrics for a time period.

    Returns total decisions, success rate, error breakdown, intent distribution,
    and tool usage statistics.
    """
    try:
        service = get_query_service()

        metrics = await service.get_metrics_summary(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
        )

        return MetricsSummaryResponse(
            total_decisions=metrics.total_decisions,
            success_rate=metrics.success_rate,
            error_breakdown=metrics.error_breakdown,
            avg_decision_duration_ms=metrics.avg_decision_duration_ms,
            avg_tool_duration_ms=metrics.avg_tool_duration_ms,
            intent_distribution=metrics.intent_distribution,
            tool_usage=metrics.tool_usage,
        )
    except HTTPException:
        raise
    except Exception as e:
        handle_sqlite_error(e)

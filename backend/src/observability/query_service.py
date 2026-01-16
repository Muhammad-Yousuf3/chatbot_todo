"""
Query service for reading and analyzing observability logs.

This service provides read-only access to decision logs, tool invocation logs,
and aggregated metrics.

Feature: 004-agent-observability
"""

import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from .database import get_log_db
from .models import (
    DecisionLog,
    DecisionTrace,
    MetricsSummary,
    QueryResult,
    ToolInvocationLog,
)


class DecisionNotFoundError(Exception):
    """Raised when a decision_id is not found."""
    pass


class QueryTimeoutError(Exception):
    """Raised when a query exceeds time limit."""
    pass


class LogQueryService:
    """
    Service for querying and analyzing observability logs.

    Provides read-only access to decision and tool invocation logs.
    """

    async def get_decision_trace(self, decision_id: UUID) -> DecisionTrace:
        """
        Get the complete decision trace for a single decision.

        Args:
            decision_id: The decision to retrieve

        Returns:
            DecisionTrace containing the decision and all tool invocations

        Raises:
            DecisionNotFoundError: If decision_id doesn't exist
        """
        async with get_log_db() as db:
            # Get decision log
            cursor = await db.execute(
                "SELECT * FROM decision_logs WHERE decision_id = ?",
                (str(decision_id),)
            )
            row = await cursor.fetchone()

            if not row:
                raise DecisionNotFoundError(f"Decision not found: {decision_id}")

            decision = DecisionLog.from_row(row)

            # Get tool invocations
            cursor = await db.execute(
                """
                SELECT * FROM tool_invocation_logs
                WHERE decision_id = ?
                ORDER BY sequence ASC
                """,
                (str(decision_id),)
            )
            rows = await cursor.fetchall()

            tool_invocations = [ToolInvocationLog.from_row(r) for r in rows]

            return DecisionTrace(decision=decision, tool_invocations=tool_invocations)

    async def query_decisions(
        self,
        *,
        conversation_id: str | None = None,
        user_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        decision_type: str | None = None,
        outcome_category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> QueryResult:
        """
        Query decision logs with filters.

        Args:
            conversation_id: Filter by conversation
            user_id: Filter by user
            start_time: Filter after timestamp
            end_time: Filter before timestamp
            decision_type: Filter by decision type
            outcome_category: Filter by outcome (exact or prefix match)
            limit: Max results (max 1000)
            offset: Pagination offset

        Returns:
            QueryResult with matching decisions and pagination info
        """
        # Cap limit at 1000
        limit = min(limit, 1000)

        # Build query
        conditions = []
        params = []

        if conversation_id:
            conditions.append("conversation_id = ?")
            params.append(conversation_id)

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time.isoformat())

        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time.isoformat())

        if decision_type:
            conditions.append("decision_type = ?")
            params.append(decision_type)

        if outcome_category:
            # Support prefix match (e.g., "ERROR" matches "ERROR:TOOL_INVOCATION")
            if ":" in outcome_category:
                conditions.append("outcome_category = ?")
                params.append(outcome_category)
            else:
                conditions.append("outcome_category LIKE ?")
                params.append(f"{outcome_category}:%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        async with get_log_db() as db:
            # Get total count
            count_cursor = await db.execute(
                f"SELECT COUNT(*) FROM decision_logs WHERE {where_clause}",
                params,
            )
            count_row = await count_cursor.fetchone()
            total = count_row[0] if count_row else 0

            # Get items
            cursor = await db.execute(
                f"""
                SELECT * FROM decision_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            )
            rows = await cursor.fetchall()

            items = [DecisionLog.from_row(r) for r in rows]
            has_more = (offset + len(items)) < total

            return QueryResult(items=items, total=total, has_more=has_more)

    async def get_metrics_summary(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
        user_id: str | None = None,
    ) -> MetricsSummary:
        """
        Get aggregated metrics for a time period.

        Args:
            start_time: Start of analysis period
            end_time: End of analysis period (defaults to now)
            user_id: Optional filter by user

        Returns:
            MetricsSummary with aggregated metrics
        """
        end_time = end_time or datetime.utcnow()

        conditions = ["created_at >= ?", "created_at <= ?"]
        params: list = [start_time.isoformat(), end_time.isoformat()]

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        where_clause = " AND ".join(conditions)

        async with get_log_db() as db:
            # Total decisions and average duration
            cursor = await db.execute(
                f"""
                SELECT
                    COUNT(*) as total,
                    AVG(duration_ms) as avg_duration
                FROM decision_logs
                WHERE {where_clause}
                """,
                params,
            )
            row = await cursor.fetchone()
            total_decisions = row["total"] if row else 0
            avg_decision_duration = row["avg_duration"] if row and row["avg_duration"] else 0.0

            # Success rate and error breakdown
            cursor = await db.execute(
                f"""
                SELECT
                    outcome_category,
                    COUNT(*) as count
                FROM decision_logs
                WHERE {where_clause}
                GROUP BY outcome_category
                """,
                params,
            )
            rows = await cursor.fetchall()

            success_count = 0
            error_breakdown: dict[str, int] = {}
            for r in rows:
                category = r["outcome_category"]
                count = r["count"]
                if category.startswith("SUCCESS:"):
                    success_count += count
                elif category.startswith("ERROR:"):
                    error_breakdown[category] = count

            success_rate = success_count / total_decisions if total_decisions > 0 else 0.0

            # Intent distribution
            cursor = await db.execute(
                f"""
                SELECT
                    intent_type,
                    COUNT(*) * 1.0 / (SELECT COUNT(*) FROM decision_logs WHERE {where_clause}) as percentage
                FROM decision_logs
                WHERE {where_clause}
                GROUP BY intent_type
                """,
                params + params,  # Need params twice for subquery
            )
            rows = await cursor.fetchall()
            intent_distribution = {r["intent_type"]: r["percentage"] for r in rows}

            # Tool usage
            tool_conditions = ["invoked_at >= ?", "invoked_at <= ?"]
            tool_params: list = [start_time.isoformat(), end_time.isoformat()]

            cursor = await db.execute(
                f"""
                SELECT
                    tool_name,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration
                FROM tool_invocation_logs
                WHERE invoked_at >= ? AND invoked_at <= ?
                GROUP BY tool_name
                """,
                tool_params,
            )
            rows = await cursor.fetchall()

            tool_usage = {r["tool_name"]: r["count"] for r in rows}
            avg_tool_duration = 0.0
            if rows:
                total_tool_duration = sum(
                    r["avg_duration"] * r["count"] for r in rows if r["avg_duration"]
                )
                total_tool_count = sum(r["count"] for r in rows)
                if total_tool_count > 0:
                    avg_tool_duration = total_tool_duration / total_tool_count

            return MetricsSummary(
                total_decisions=total_decisions,
                success_rate=success_rate,
                error_breakdown=error_breakdown,
                avg_decision_duration_ms=avg_decision_duration,
                avg_tool_duration_ms=avg_tool_duration,
                intent_distribution=intent_distribution,
                tool_usage=tool_usage,
            )

    async def export_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        format: Literal["json", "jsonl"] = "json",
    ) -> bytes:
        """
        Export logs in portable JSON format.

        Args:
            start_time: Start of export period
            end_time: End of export period
            format: Output format ("json" or "jsonl")

        Returns:
            JSON-formatted log data as bytes
        """
        async with get_log_db() as db:
            # Get all decisions in range
            cursor = await db.execute(
                """
                SELECT * FROM decision_logs
                WHERE created_at >= ? AND created_at <= ?
                ORDER BY created_at ASC
                """,
                (start_time.isoformat(), end_time.isoformat()),
            )
            decision_rows = await cursor.fetchall()

            export_data = []

            for d_row in decision_rows:
                decision = DecisionLog.from_row(d_row)
                decision_id = str(decision.decision_id)

                # Get tool invocations for this decision
                cursor = await db.execute(
                    """
                    SELECT * FROM tool_invocation_logs
                    WHERE decision_id = ?
                    ORDER BY sequence ASC
                    """,
                    (decision_id,),
                )
                tool_rows = await cursor.fetchall()
                tools = [ToolInvocationLog.from_row(t) for t in tool_rows]

                # Build export record
                record = {
                    "decision_id": decision_id,
                    "conversation_id": decision.conversation_id,
                    "user_id": decision.user_id,
                    "message": decision.message,
                    "intent_type": decision.intent_type,
                    "confidence": decision.confidence,
                    "extracted_params": decision.extracted_params,
                    "decision_type": decision.decision_type,
                    "outcome_category": decision.outcome_category,
                    "response_text": decision.response_text,
                    "created_at": decision.created_at.isoformat(),
                    "duration_ms": decision.duration_ms,
                    "tool_invocations": [
                        {
                            "tool_name": t.tool_name,
                            "parameters": t.parameters,
                            "result": t.result,
                            "success": t.success,
                            "error_code": t.error_code,
                            "error_message": t.error_message,
                            "duration_ms": t.duration_ms,
                            "invoked_at": t.invoked_at.isoformat(),
                            "sequence": t.sequence,
                        }
                        for t in tools
                    ],
                }
                export_data.append(record)

            if format == "jsonl":
                lines = [json.dumps(record) for record in export_data]
                return "\n".join(lines).encode("utf-8")
            else:
                return json.dumps(export_data, indent=2).encode("utf-8")

"""
Logging service for recording agent decisions and tool invocations.

This service provides a facade for writing decision logs and tool invocation
logs to the SQLite database.

Feature: 004-agent-observability
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from .categories import validate_outcome_category
from .database import get_log_db
from .models import DecisionLog, ToolInvocationLog


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class StorageError(Exception):
    """Raised when database storage fails."""
    pass


class InvalidDecisionError(Exception):
    """Raised when a decision_id is not found."""
    pass


class LoggingService:
    """
    Service for recording agent decisions and tool invocations.

    Provides write-only access to the observability log database.
    """

    def __init__(self):
        """Initialize the logging service."""
        self._tool_sequence: dict[UUID, int] = {}

    async def write_decision_log(
        self,
        *,
        decision_id: UUID,
        conversation_id: str,
        user_id: str,
        message: str,
        intent_type: str,
        decision_type: str,
        outcome_category: str,
        duration_ms: int,
        confidence: float | None = None,
        extracted_params: dict[str, Any] | None = None,
        response_text: str | None = None,
    ) -> DecisionLog:
        """
        Record a complete agent decision.

        Args:
            decision_id: Unique identifier for this decision
            conversation_id: Conversation context
            user_id: User who sent the message
            message: Original user message (max 4000 chars)
            intent_type: Classified intent type
            decision_type: Type of decision made
            outcome_category: Outcome classification (format: "CATEGORY:SUBCATEGORY")
            duration_ms: Total processing time in milliseconds
            confidence: Classification confidence score (0.0-1.0)
            extracted_params: Parameters extracted from message
            response_text: Final response to user

        Returns:
            DecisionLog: The persisted log entry

        Raises:
            ValidationError: If outcome_category format is invalid
            StorageError: If database operation fails
        """
        # Validate outcome category
        if not validate_outcome_category(outcome_category):
            raise ValidationError(
                f"Invalid outcome_category format: {outcome_category}. "
                "Expected format: 'CATEGORY:SUBCATEGORY'"
            )

        # Truncate message if too long
        if len(message) > 4000:
            message = message[:4000]

        # Create log entry
        log = DecisionLog(
            decision_id=decision_id,
            conversation_id=conversation_id,
            user_id=user_id,
            message=message,
            intent_type=intent_type,
            confidence=confidence,
            extracted_params=extracted_params or {},
            decision_type=decision_type,
            outcome_category=outcome_category,
            response_text=response_text,
            duration_ms=duration_ms,
        )

        # Store in database
        try:
            async with get_log_db() as db:
                data = log.to_dict()
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
                await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to persist decision log: {e}") from e

        # Initialize tool sequence counter
        self._tool_sequence[decision_id] = 0

        return log

    async def write_tool_invocation_log(
        self,
        *,
        decision_id: UUID,
        tool_name: str,
        parameters: dict[str, Any],
        success: bool,
        duration_ms: int,
        result: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        invoked_at: datetime | None = None,
    ) -> ToolInvocationLog:
        """
        Record a tool invocation within a decision.

        Args:
            decision_id: Parent decision ID
            tool_name: MCP tool that was called
            parameters: Parameters passed to tool
            success: Whether invocation succeeded
            duration_ms: Tool execution time in milliseconds
            result: Tool response (if successful)
            error_code: Error category (if failed)
            error_message: Detailed error (if failed)
            invoked_at: When tool was called (defaults to now)

        Returns:
            ToolInvocationLog: The persisted log entry

        Raises:
            InvalidDecisionError: If decision_id not found
            StorageError: If database operation fails
        """
        # Get and increment sequence number
        if decision_id not in self._tool_sequence:
            # Check if decision exists in database
            async with get_log_db() as db:
                cursor = await db.execute(
                    "SELECT 1 FROM decision_logs WHERE decision_id = ?",
                    (str(decision_id),)
                )
                row = await cursor.fetchone()
                if not row:
                    raise InvalidDecisionError(f"Decision not found: {decision_id}")
                self._tool_sequence[decision_id] = 0

        self._tool_sequence[decision_id] += 1
        sequence = self._tool_sequence[decision_id]

        # Create log entry
        log = ToolInvocationLog(
            decision_id=decision_id,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            success=success,
            error_code=error_code,
            error_message=error_message,
            duration_ms=duration_ms,
            invoked_at=invoked_at or datetime.utcnow(),
            sequence=sequence,
        )

        # Store in database
        try:
            async with get_log_db() as db:
                data = log.to_dict()
                await db.execute(
                    """
                    INSERT INTO tool_invocation_logs
                    (id, decision_id, tool_name, parameters, result, success,
                     error_code, error_message, duration_ms, invoked_at, sequence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["id"], data["decision_id"], data["tool_name"],
                        data["parameters"], data["result"], data["success"],
                        data["error_code"], data["error_message"],
                        data["duration_ms"], data["invoked_at"], data["sequence"],
                    ),
                )
                await db.commit()
        except Exception as e:
            raise StorageError(f"Failed to persist tool invocation log: {e}") from e

        return log

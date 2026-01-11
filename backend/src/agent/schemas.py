"""Pydantic models and enums for the Agent Decision Engine.

This module defines all data structures used by the agent for:
- Intent classification
- Decision making
- Tool invocation
- Audit logging
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# T004: Intent Type Enum
# =============================================================================
class IntentType(str, Enum):
    """Classified intent categories for user messages.

    The agent classifies each user message into one of these categories
    to determine the appropriate action.
    """

    CREATE_TASK = "CREATE_TASK"  # User wants to create a new task
    LIST_TASKS = "LIST_TASKS"  # User wants to see their tasks
    COMPLETE_TASK = "COMPLETE_TASK"  # User wants to mark a task as done
    UPDATE_TASK = "UPDATE_TASK"  # User wants to modify a task
    DELETE_TASK = "DELETE_TASK"  # User wants to remove a task
    GENERAL_CHAT = "GENERAL_CHAT"  # Non-task conversation
    AMBIGUOUS = "AMBIGUOUS"  # Intent cannot be determined
    MULTI_INTENT = "MULTI_INTENT"  # Message contains multiple intents
    CONFIRM_YES = "CONFIRM_YES"  # User confirms a pending action
    CONFIRM_NO = "CONFIRM_NO"  # User denies a pending action


# =============================================================================
# T005: Decision Type Enum
# =============================================================================
class DecisionType(str, Enum):
    """Types of decisions the agent can make.

    After classifying intent, the agent determines what action to take.
    """

    INVOKE_TOOL = "INVOKE_TOOL"  # Call one or more MCP tools
    RESPOND_ONLY = "RESPOND_ONLY"  # Return natural language without tools
    ASK_CLARIFICATION = "ASK_CLARIFICATION"  # Ask user for more information
    REQUEST_CONFIRMATION = "REQUEST_CONFIRMATION"  # Ask user to confirm destructive action
    EXECUTE_PENDING = "EXECUTE_PENDING"  # Execute previously confirmed action
    CANCEL_PENDING = "CANCEL_PENDING"  # Cancel previously requested action


# =============================================================================
# T006: Tool Name Enum
# =============================================================================
class ToolName(str, Enum):
    """MCP tools that the agent can invoke.

    These correspond to the tools defined in Spec 002.
    """

    ADD_TASK = "add_task"
    LIST_TASKS = "list_tasks"
    UPDATE_TASK = "update_task"
    COMPLETE_TASK = "complete_task"
    DELETE_TASK = "delete_task"


# =============================================================================
# T007: UserIntent Model
# =============================================================================
class UserIntent(BaseModel):
    """Represents the classified purpose of a user message.

    The agent uses this to determine what action to take.
    """

    intent_type: IntentType = Field(..., description="Classified intent category")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Classification confidence (0.0-1.0)",
    )
    extracted_params: dict[str, Any] | None = Field(
        default=None,
        description="Parameters extracted from the message",
    )

    @field_validator("extracted_params")
    @classmethod
    def validate_params_for_intent(
        cls, v: dict[str, Any] | None, info
    ) -> dict[str, Any] | None:
        """Validate that extracted_params matches the intent type."""
        if v is None:
            return v

        intent_type = info.data.get("intent_type")
        if intent_type == IntentType.AMBIGUOUS and "possible_intents" not in v:
            raise ValueError("AMBIGUOUS intent must include 'possible_intents' list")

        return v


# =============================================================================
# T008: Message Model (for history)
# =============================================================================
class Message(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., pattern="^(user|assistant)$", description="Message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="When the message was sent")


# =============================================================================
# T009: PendingAction Model
# =============================================================================
class PendingAction(BaseModel):
    """Represents a destructive action awaiting user confirmation.

    Currently only DELETE_TASK requires confirmation.
    """

    action_type: IntentType = Field(
        ...,
        description="Type of pending action (DELETE_TASK only)",
    )
    task_id: str = Field(..., description="Task targeted for action")
    task_description: str = Field(..., description="Human-readable task description")
    created_at: datetime = Field(..., description="When confirmation was requested")
    expires_at: datetime = Field(..., description="Confirmation timeout")

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: IntentType) -> IntentType:
        """Only DELETE_TASK requires confirmation."""
        if v != IntentType.DELETE_TASK:
            raise ValueError("Only DELETE_TASK requires confirmation")
        return v

    def is_expired(self) -> bool:
        """Check if the pending action has expired."""
        return datetime.now() > self.expires_at


# =============================================================================
# T008: DecisionContext Model
# =============================================================================
class DecisionContext(BaseModel):
    """The complete context used to make an agent decision.

    This enables reproducibility - the same context should produce
    the same decision.
    """

    user_id: str = Field(..., min_length=1, description="Authenticated user identifier")
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Current user message",
    )
    conversation_id: str = Field(..., description="Reference to conversation")
    message_history: list[Message] = Field(
        default_factory=list,
        description="Recent conversation history",
    )
    pending_confirmation: PendingAction | None = Field(
        default=None,
        description="Action awaiting user confirmation",
    )


# =============================================================================
# T010: ToolCall Model
# =============================================================================
class ToolCall(BaseModel):
    """Represents a single MCP tool invocation request."""

    tool_name: ToolName = Field(..., description="MCP tool to invoke")
    parameters: dict[str, Any] = Field(..., description="Parameters for the tool")
    sequence: int = Field(..., ge=1, description="Execution order (1-based)")

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: dict[str, Any], info) -> dict[str, Any]:
        """Validate that required parameters are present for each tool."""
        tool_name = info.data.get("tool_name")

        # All tools require user_id
        if "user_id" not in v:
            raise ValueError("All tool calls must include 'user_id'")

        # Tool-specific validation
        if tool_name == ToolName.ADD_TASK:
            if "description" not in v:
                raise ValueError("add_task requires 'description' parameter")
            if not (1 <= len(v["description"]) <= 1000):
                raise ValueError("description must be 1-1000 characters")

        if tool_name in (ToolName.UPDATE_TASK, ToolName.COMPLETE_TASK, ToolName.DELETE_TASK):
            if "task_id" not in v:
                raise ValueError(f"{tool_name.value} requires 'task_id' parameter")

        if tool_name == ToolName.UPDATE_TASK:
            if "description" not in v:
                raise ValueError("update_task requires 'description' parameter")

        return v


# =============================================================================
# T011: AgentDecision Model
# =============================================================================
class AgentDecision(BaseModel):
    """The output of the agent's decision process.

    Determines what action to take in response to a user message.
    """

    decision_type: DecisionType = Field(..., description="Type of decision made")
    tool_calls: list[ToolCall] | None = Field(
        default=None,
        description="MCP tools to invoke",
    )
    response_text: str | None = Field(
        default=None,
        description="Natural language response",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask user",
    )
    pending_action: PendingAction | None = Field(
        default=None,
        description="Action awaiting confirmation (for REQUEST_CONFIRMATION)",
    )

    @model_validator(mode="after")
    def validate_decision_consistency(self) -> "AgentDecision":
        """Validate decision consistency after all fields are set."""
        # Validate tool_calls based on decision type
        if self.decision_type == DecisionType.INVOKE_TOOL:
            if self.tool_calls is None or len(self.tool_calls) == 0:
                raise ValueError("INVOKE_TOOL decision must include tool_calls")

        if self.decision_type in (
            DecisionType.RESPOND_ONLY,
            DecisionType.ASK_CLARIFICATION,
            DecisionType.REQUEST_CONFIRMATION,
            DecisionType.CANCEL_PENDING,
        ):
            if self.tool_calls is not None and len(self.tool_calls) > 0:
                raise ValueError(
                    f"{self.decision_type.value} decision must not include tool_calls"
                )

        # Validate pending_action based on decision type
        if self.decision_type == DecisionType.REQUEST_CONFIRMATION:
            if self.pending_action is None:
                raise ValueError(
                    "REQUEST_CONFIRMATION decision must include pending_action"
                )

        if self.decision_type != DecisionType.REQUEST_CONFIRMATION:
            if self.pending_action is not None:
                raise ValueError(
                    "pending_action can only be set for REQUEST_CONFIRMATION decisions"
                )

        return self


# =============================================================================
# T012: ToolInvocationRecord Model
# =============================================================================
class ToolInvocationRecord(BaseModel):
    """Audit record of a tool invocation.

    Stored for traceability and debugging.
    """

    id: UUID = Field(..., description="Unique record identifier")
    conversation_id: str = Field(..., description="Parent conversation")
    message_id: str = Field(..., description="Triggering user message")
    user_id: str = Field(..., description="User who triggered the action")
    tool_name: str = Field(..., description="MCP tool that was called")
    parameters: dict[str, Any] = Field(..., description="Parameters passed to tool")
    intent_classification: str = Field(
        ...,
        description="Classified intent that led to this call",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="Tool response",
    )
    success: bool = Field(..., description="Whether tool call succeeded")
    error_message: str | None = Field(
        default=None,
        description="Error details if failed",
    )
    invoked_at: datetime = Field(..., description="Timestamp of invocation")
    duration_ms: int = Field(..., ge=0, description="Execution time in milliseconds")

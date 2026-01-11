"""Agent Decision Engine - core orchestration logic.

This module implements the main AgentDecisionEngine class that:
1. Checks for pending confirmations
2. Classifies user intent
3. Applies decision rules
4. Generates tool calls or responses

The engine is stateless - all state is passed via DecisionContext.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.agent.responses import (
    ClarificationResponses,
    ConfirmationResponses,
    ErrorResponses,
    GeneralResponses,
    SuccessResponses,
)
from src.agent.schemas import (
    AgentDecision,
    DecisionContext,
    DecisionType,
    IntentType,
    PendingAction,
    ToolCall,
    ToolInvocationRecord,
    ToolName,
    UserIntent,
)

logger = logging.getLogger(__name__)


class AgentDecisionEngine:
    """Main entry point for agent processing.

    The engine processes user messages and determines appropriate actions
    based solely on the provided DecisionContext.

    Usage:
        engine = AgentDecisionEngine()
        decision = await engine.process_message(context)
    """

    def __init__(self) -> None:
        """Initialize the decision engine."""
        # Will be populated by intent classification module
        self._intent_classifier = None
        # Will be populated by policy module
        self._policy = None
        # Will be populated by resolver module
        self._resolver = None

    async def process_message(self, context: DecisionContext) -> AgentDecision:
        """Process a user message and determine the appropriate action.

        This is the main entry point following the contract in agent-interface.md:
        1. Check for pending confirmations
        2. Classify intent
        3. Apply decision rules
        4. Return AgentDecision

        Args:
            context: The complete decision context including user message,
                    conversation history, and any pending confirmations.

        Returns:
            AgentDecision indicating what action to take.

        Raises:
            ValueError: If context is invalid (e.g., missing user_id).
        """
        # Validate context
        if not context.user_id:
            return AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                response_text=ErrorResponses.auth_required(),
            )

        # Step 1: Check for pending confirmation
        if context.pending_confirmation:
            return await self._handle_pending_confirmation(context)

        # Step 2: Classify intent
        intent = await self._classify_intent(context)

        # Step 3: Apply decision rules and return decision
        return await self._apply_decision_rules(context, intent)

    async def _handle_pending_confirmation(
        self, context: DecisionContext
    ) -> AgentDecision:
        """Handle a message when there's a pending confirmation.

        Per the contract:
        - If message is CONFIRM_YES: Execute pending action
        - If message is CONFIRM_NO: Cancel pending action
        - Otherwise: Cancel pending and process as new message
        """
        pending = context.pending_confirmation

        # Check if confirmation has expired
        if pending.is_expired():
            # Expired - cancel and process message normally
            logger.info(f"Pending confirmation expired for task {pending.task_id}")
            return AgentDecision(
                decision_type=DecisionType.RESPOND_ONLY,
                response_text=ConfirmationResponses.confirmation_expired(),
            )

        # Classify the current message to check if it's a confirmation
        intent = await self._classify_intent(context)

        if intent.intent_type == IntentType.CONFIRM_YES:
            # Execute the pending delete
            return AgentDecision(
                decision_type=DecisionType.EXECUTE_PENDING,
                tool_calls=[
                    ToolCall(
                        tool_name=ToolName.DELETE_TASK,
                        parameters={
                            "user_id": context.user_id,
                            "task_id": pending.task_id,
                        },
                        sequence=1,
                    )
                ],
                response_text=SuccessResponses.task_deleted(pending.task_description),
            )

        if intent.intent_type == IntentType.CONFIRM_NO:
            # Cancel the pending action
            return AgentDecision(
                decision_type=DecisionType.CANCEL_PENDING,
                response_text=ConfirmationResponses.delete_cancelled(),
            )

        # Any other message cancels the pending action and processes normally
        logger.info(
            f"Pending confirmation cancelled due to new message: {context.message}"
        )
        return await self._apply_decision_rules(context, intent)

    async def _classify_intent(self, context: DecisionContext) -> UserIntent:
        """Classify the intent of the user's message.

        This is a placeholder that will be implemented by the intent module.
        For now, returns GENERAL_CHAT as default.
        """
        # Import here to avoid circular imports - will be replaced with proper implementation
        from src.agent.intent import classify_intent

        return await classify_intent(context.message, context.message_history)

    async def _apply_decision_rules(
        self, context: DecisionContext, intent: UserIntent
    ) -> AgentDecision:
        """Apply decision rules based on classified intent.

        This is a placeholder that will be implemented by the policy module.
        """
        from src.agent.policy import apply_decision_rules

        return await apply_decision_rules(context, intent)

    def _build_tool_call(
        self,
        tool_name: ToolName,
        user_id: str,
        sequence: int = 1,
        **extra_params: Any,
    ) -> ToolCall:
        """Build a tool call with the required parameters.

        Args:
            tool_name: The MCP tool to invoke.
            user_id: The authenticated user ID.
            sequence: Execution order (1-based).
            **extra_params: Additional tool-specific parameters.

        Returns:
            A validated ToolCall instance.
        """
        parameters = {"user_id": user_id, **extra_params}
        return ToolCall(tool_name=tool_name, parameters=parameters, sequence=sequence)

    def _create_audit_record(
        self,
        context: DecisionContext,
        intent: UserIntent,
        tool_call: ToolCall,
        result: dict[str, Any] | None,
        success: bool,
        error_message: str | None,
        duration_ms: int,
    ) -> ToolInvocationRecord:
        """Create an audit record for a tool invocation.

        Args:
            context: The decision context.
            intent: The classified intent.
            tool_call: The tool that was invoked.
            result: The tool's response.
            success: Whether the invocation succeeded.
            error_message: Error details if failed.
            duration_ms: Execution time in milliseconds.

        Returns:
            A ToolInvocationRecord for audit logging.
        """
        return ToolInvocationRecord(
            id=uuid4(),
            conversation_id=context.conversation_id,
            message_id=str(uuid4()),  # Would come from actual message
            user_id=context.user_id,
            tool_name=tool_call.tool_name.value,
            parameters=tool_call.parameters,
            intent_classification=intent.intent_type.value,
            result=result,
            success=success,
            error_message=error_message,
            invoked_at=datetime.now(),
            duration_ms=duration_ms,
        )

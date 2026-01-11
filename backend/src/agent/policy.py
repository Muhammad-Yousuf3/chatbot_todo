"""Decision policy rules for the Agent Decision Engine.

This module implements the decision rules that map classified intents
to agent decisions (tool calls or responses).
"""

from datetime import datetime, timedelta

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
    ToolName,
    UserIntent,
)

# Confirmation timeout in minutes
CONFIRMATION_TIMEOUT_MINUTES = 5


async def apply_decision_rules(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Apply decision rules based on classified intent.

    This function maps intents to appropriate agent decisions following
    the contract in agent-interface.md.

    Args:
        context: The complete decision context.
        intent: The classified user intent.

    Returns:
        AgentDecision indicating what action to take.
    """
    # Validate user_id is present
    if not context.user_id:
        return AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text=ErrorResponses.auth_required(),
        )

    # Route to appropriate handler based on intent type
    handlers = {
        IntentType.CREATE_TASK: _handle_create_task,
        IntentType.LIST_TASKS: _handle_list_tasks,
        IntentType.COMPLETE_TASK: _handle_complete_task,
        IntentType.UPDATE_TASK: _handle_update_task,
        IntentType.DELETE_TASK: _handle_delete_task,
        IntentType.GENERAL_CHAT: _handle_general_chat,
        IntentType.AMBIGUOUS: _handle_ambiguous,
        IntentType.MULTI_INTENT: _handle_multi_intent,
        IntentType.CONFIRM_YES: _handle_confirm_yes,
        IntentType.CONFIRM_NO: _handle_confirm_no,
    }

    handler = handlers.get(intent.intent_type, _handle_general_chat)
    return await handler(context, intent)


async def _handle_create_task(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle CREATE_TASK intent - invoke add_task tool."""
    params = intent.extracted_params or {}
    description = params.get("description", "")

    if not description:
        return AgentDecision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_question=ClarificationResponses.missing_description(),
        )

    # Validate description length
    if len(description) > 1000:
        return AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text=ErrorResponses.description_too_long(),
        )

    return AgentDecision(
        decision_type=DecisionType.INVOKE_TOOL,
        tool_calls=[
            ToolCall(
                tool_name=ToolName.ADD_TASK,
                parameters={
                    "user_id": context.user_id,
                    "description": description,
                },
                sequence=1,
            )
        ],
        response_text=SuccessResponses.task_created(description),
    )


async def _handle_list_tasks(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle LIST_TASKS intent - invoke list_tasks tool."""
    return AgentDecision(
        decision_type=DecisionType.INVOKE_TOOL,
        tool_calls=[
            ToolCall(
                tool_name=ToolName.LIST_TASKS,
                parameters={"user_id": context.user_id},
                sequence=1,
            )
        ],
        # Response text will be generated after tool execution with actual results
        response_text=None,
    )


async def _handle_complete_task(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle COMPLETE_TASK intent - list tasks then complete.

    Per contract: FIRST list_tasks to identify, THEN complete_task.
    The actual task matching will be done after list_tasks returns.
    """
    params = intent.extracted_params or {}
    task_reference = params.get("task_reference", "")

    if not task_reference:
        return AgentDecision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_question=ClarificationResponses.which_task(),
        )

    # Pass operation context for task resolution after list_tasks returns
    return AgentDecision(
        decision_type=DecisionType.INVOKE_TOOL,
        tool_calls=[
            ToolCall(
                tool_name=ToolName.LIST_TASKS,
                parameters={
                    "user_id": context.user_id,
                    "_operation": "complete",
                    "_task_reference": task_reference,
                },
                sequence=1,
            )
        ],
        response_text=None,
    )


async def _handle_update_task(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle UPDATE_TASK intent - list tasks then update.

    Per contract: FIRST list_tasks to identify, THEN update_task.
    """
    params = intent.extracted_params or {}
    task_reference = params.get("task_reference", "")
    new_description = params.get("new_description", "")

    if not task_reference:
        return AgentDecision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_question=ClarificationResponses.which_task(),
        )

    if not new_description:
        return AgentDecision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_question=ClarificationResponses.missing_description(),
        )

    # Pass operation context for task resolution after list_tasks returns
    return AgentDecision(
        decision_type=DecisionType.INVOKE_TOOL,
        tool_calls=[
            ToolCall(
                tool_name=ToolName.LIST_TASKS,
                parameters={
                    "user_id": context.user_id,
                    "_operation": "update",
                    "_task_reference": task_reference,
                    "_new_description": new_description,
                },
                sequence=1,
            )
        ],
        response_text=None,
    )


async def _handle_delete_task(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle DELETE_TASK intent - list tasks, then request confirmation.

    Per contract: DELETE requires two-step confirmation.
    FIRST list_tasks to identify, THEN request confirmation.
    """
    params = intent.extracted_params or {}
    task_reference = params.get("task_reference", "")

    if not task_reference:
        return AgentDecision(
            decision_type=DecisionType.ASK_CLARIFICATION,
            clarification_question=ClarificationResponses.which_task(),
        )

    # Pass operation context for task resolution after list_tasks returns
    return AgentDecision(
        decision_type=DecisionType.INVOKE_TOOL,
        tool_calls=[
            ToolCall(
                tool_name=ToolName.LIST_TASKS,
                parameters={
                    "user_id": context.user_id,
                    "_operation": "delete",
                    "_task_reference": task_reference,
                },
                sequence=1,
            )
        ],
        response_text=None,
    )


async def _handle_general_chat(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle GENERAL_CHAT intent - respond without tools."""
    message_lower = context.message.lower().strip()

    # Detect greetings
    greetings = {"hello", "hi", "hey", "good morning", "good afternoon", "good evening"}
    if any(g in message_lower for g in greetings):
        return AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text=GeneralResponses.greeting(),
        )

    # Detect capability questions
    capability_patterns = [
        "what can you",
        "help me",
        "how do i",
        "what do you do",
        "what are you",
    ]
    if any(p in message_lower for p in capability_patterns):
        return AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text=GeneralResponses.capabilities(),
        )

    # Default fallback
    return AgentDecision(
        decision_type=DecisionType.RESPOND_ONLY,
        response_text=GeneralResponses.fallback(),
    )


async def _handle_ambiguous(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle AMBIGUOUS intent - ask for clarification."""
    params = intent.extracted_params or {}
    possible_intents = params.get("possible_intents", ["CREATE_TASK", "COMPLETE_TASK"])

    return AgentDecision(
        decision_type=DecisionType.ASK_CLARIFICATION,
        clarification_question=ClarificationResponses.ambiguous_intent(possible_intents),
    )


async def _handle_multi_intent(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle MULTI_INTENT - ask user to provide one request at a time.

    When multiple intents are detected (e.g., "add groceries and show my list"),
    we ask the user to break it down for clarity.
    """
    params = intent.extracted_params or {}
    intents = params.get("intents", [])

    return AgentDecision(
        decision_type=DecisionType.ASK_CLARIFICATION,
        clarification_question=ClarificationResponses.multi_intent(intents),
    )


async def _handle_confirm_yes(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle CONFIRM_YES when there's no pending action.

    If we get here, there was no pending action, so treat as general chat.
    """
    return AgentDecision(
        decision_type=DecisionType.RESPOND_ONLY,
        response_text=GeneralResponses.fallback(),
    )


async def _handle_confirm_no(
    context: DecisionContext, intent: UserIntent
) -> AgentDecision:
    """Handle CONFIRM_NO when there's no pending action.

    If we get here, there was no pending action, so treat as general chat.
    """
    return AgentDecision(
        decision_type=DecisionType.RESPOND_ONLY,
        response_text=GeneralResponses.fallback(),
    )


def create_pending_action(
    task_id: str,
    task_description: str,
) -> PendingAction:
    """Create a pending action for delete confirmation.

    Args:
        task_id: The task to be deleted.
        task_description: Human-readable description.

    Returns:
        PendingAction with expiration set.
    """
    now = datetime.now()
    return PendingAction(
        action_type=IntentType.DELETE_TASK,
        task_id=task_id,
        task_description=task_description,
        created_at=now,
        expires_at=now + timedelta(minutes=CONFIRMATION_TIMEOUT_MINUTES),
    )


def validate_user_id(context: DecisionContext) -> AgentDecision | None:
    """Validate that user_id is present.

    Returns:
        AgentDecision with error if user_id is missing, None otherwise.
    """
    if not context.user_id:
        return AgentDecision(
            decision_type=DecisionType.RESPOND_ONLY,
            response_text=ErrorResponses.auth_required(),
        )
    return None


def is_out_of_scope(message: str) -> bool:
    """Check if request is outside agent capabilities.

    The agent only handles task management. Other requests should be
    politely redirected.
    """
    out_of_scope_patterns = [
        "weather",
        "news",
        "stock",
        "calculate",
        "translate",
        "search",
        "browse",
        "email",
        "send",
        "call",
        "text",
        "sms",
    ]
    message_lower = message.lower()
    return any(p in message_lower for p in out_of_scope_patterns)

"""Chat endpoint for sending messages.

This endpoint integrates the LLM Agent Runtime to process user messages
with Gemini-powered decision making and MCP tool execution.

Includes observability logging for decision auditing (Spec 004).
"""

import logging
import os
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from src.agent.schemas import DecisionContext, DecisionType, Message
from src.api.deps import CurrentUserId
from src.api.schemas.chat import MessageResponse, SendMessageRequest, SendMessageResponse
from src.api.schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from src.db.session import SessionDep
from src.models import MessageRole
from src.services import (
    create_conversation,
    create_message,
    generate_conversation_title,
    get_conversation_by_id,
    get_conversation_messages,
    update_conversation_timestamp,
    verify_conversation_ownership,
)

# LLM Runtime imports (Spec 005)
try:
    from src.llm_runtime import GeminiAdapter, LLMAgentEngine, ToolExecutor, load_constitution

    _llm_runtime_available = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"LLM runtime not available: {e}")
    _llm_runtime_available = False

# Fallback to rule-based engine if LLM runtime not available
if not _llm_runtime_available:
    from src.agent.engine import AgentDecisionEngine
    from src.agent.executor import ToolExecutor as LegacyToolExecutor
    from src.agent.responses import format_list_tasks_result

# Observability imports (Spec 004)
try:
    from src.observability.categories import assign_outcome_category
    from src.observability.database import init_log_db
    from src.observability.logging_service import LoggingService

    _observability_available = True
    _logging_service = LoggingService()
except ImportError:
    _observability_available = False
    _logging_service = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])

# Initialize engine based on availability
_engine = None
_use_llm_runtime = False


def _init_engine():
    """Initialize the agent engine (LLM or rule-based fallback)."""
    global _engine, _use_llm_runtime

    if _engine is not None:
        return

    if _llm_runtime_available:
        # Try to initialize LLM runtime
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                adapter = GeminiAdapter(
                    api_key=api_key,
                    model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                    timeout=int(os.environ.get("LLM_TIMEOUT", "30")),
                )
                executor = ToolExecutor()
                constitution = load_constitution()

                _engine = LLMAgentEngine(
                    llm_adapter=adapter,
                    tool_executor=executor,
                    constitution=constitution,
                    max_iterations=int(os.environ.get("MAX_TOOL_ITERATIONS", "5")),
                    temperature=float(os.environ.get("LLM_TEMPERATURE", "0.0")),
                    max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "1024")),
                )
                _use_llm_runtime = True
                logger.info("Initialized LLM agent engine with Gemini")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize LLM engine: {e}")
        else:
            logger.warning("GEMINI_API_KEY not set, falling back to rule-based engine")

    # Fallback to rule-based engine
    if not _llm_runtime_available:
        _engine = AgentDecisionEngine()
        logger.info("Initialized rule-based agent engine (fallback)")
    else:
        # LLM runtime available but no API key - create a placeholder
        logger.error("LLM runtime available but GEMINI_API_KEY not set")
        raise RuntimeError("GEMINI_API_KEY environment variable required")


@router.post(
    "/chat",
    response_model=SendMessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def send_message(
    request: SendMessageRequest,
    session: SessionDep,
    user_id: CurrentUserId,
) -> SendMessageResponse:
    """Send a chat message.

    If conversation_id is omitted, creates a new conversation.
    If conversation_id is provided, appends to existing conversation.

    Uses LLM-powered agent when GEMINI_API_KEY is set, otherwise
    falls back to rule-based agent (legacy).
    """
    # Initialize engine on first request
    _init_engine()

    conversation = None

    if request.conversation_id is not None:
        # Continue existing conversation
        try:
            conv_id = request.conversation_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.INVALID_ID_FORMAT,
                        message="Conversation ID must be a valid UUID",
                    )
                ).model_dump(),
            )

        conversation = await get_conversation_by_id(session, conv_id)

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.CONVERSATION_NOT_FOUND,
                        message="Conversation does not exist",
                    )
                ).model_dump(),
            )

        if not verify_conversation_ownership(conversation, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.ACCESS_DENIED,
                        message="You do not have access to this conversation",
                    )
                ).model_dump(),
            )
    else:
        # Create new conversation
        title = generate_conversation_title(request.content)
        conversation = await create_conversation(session, user_id, title)

    # Create the user message
    user_message = await create_message(
        session,
        conversation.id,
        MessageRole.USER,
        request.content,
    )

    # Build decision context from conversation history
    existing_messages = await get_conversation_messages(session, conversation.id)
    message_history = [
        Message(
            role="user" if m.role == MessageRole.USER else "assistant",
            content=m.content,
            timestamp=m.created_at,
        )
        for m in existing_messages[:-1]  # Exclude the message we just added
    ]

    context = DecisionContext(
        user_id=user_id,
        message=request.content,
        conversation_id=str(conversation.id),
        message_history=message_history,
        pending_confirmation=None,  # Would load from session/cache in production
    )

    # Observability: Generate decision_id and track start time
    decision_id = uuid4()
    start_time = datetime.utcnow()
    tool_used = False
    tool_succeeded: bool | None = None
    intent_type = "UNKNOWN"
    decision_type_str = "UNKNOWN"

    # Process message through the agent
    decision = await _engine.process_message(context)

    # Track decision metadata for observability
    decision_type_str = decision.decision_type.value if decision.decision_type else "UNKNOWN"

    agent_response = ""

    if _use_llm_runtime:
        # LLM Runtime: Tools are already executed internally by the engine
        # The decision contains the final response after all tool calls
        if decision.decision_type == DecisionType.INVOKE_TOOL and decision.tool_calls:
            tool_used = True
            # Log tool invocations from the decision (already executed)
            for tool_call in decision.tool_calls:
                # Check for success/failure from tool call parameters
                tc_success = tool_call.parameters.get("_success", True)
                tc_result = tool_call.parameters.get("_result")
                tc_error = tool_call.parameters.get("_error")

                if tool_succeeded is None:
                    tool_succeeded = tc_success
                else:
                    tool_succeeded = tool_succeeded and tc_success

                # Log tool invocation (Spec 004)
                if _observability_available and _logging_service:
                    try:
                        await _logging_service.write_tool_invocation_log(
                            decision_id=decision_id,
                            tool_name=tool_call.tool_name.value,
                            parameters={k: v for k, v in tool_call.parameters.items() if not k.startswith("_")},
                            result=tc_result if tc_success else None,
                            success=tc_success,
                            error_code="TOOL_EXECUTION_ERROR" if not tc_success else None,
                            error_message=tc_error if not tc_success else None,
                            duration_ms=0,  # Duration tracked internally by engine
                        )
                    except Exception as log_error:
                        logger.warning(f"Failed to log tool invocation: {log_error}")

        # Get response text from the LLM decision
        if decision.response_text:
            agent_response = decision.response_text
        elif decision.clarification_question:
            agent_response = decision.clarification_question
        else:
            agent_response = "I'm here to help with your tasks."

    else:
        # Legacy mode: Execute tool calls via legacy executor
        legacy_executor = LegacyToolExecutor(session)

        if decision.decision_type == DecisionType.INVOKE_TOOL and decision.tool_calls:
            tool_used = True
            for tool_call in decision.tool_calls:
                tool_start = datetime.utcnow()
                result, success, error = await legacy_executor.execute(tool_call, user_id)
                tool_duration_ms = int((datetime.utcnow() - tool_start).total_seconds() * 1000)

                # Track tool success for outcome categorization
                if tool_succeeded is None:
                    tool_succeeded = success
                else:
                    tool_succeeded = tool_succeeded and success

                # Log tool invocation (Spec 004)
                if _observability_available and _logging_service:
                    try:
                        await _logging_service.write_tool_invocation_log(
                            decision_id=decision_id,
                            tool_name=tool_call.tool_name.value,
                            parameters=tool_call.parameters,
                            result=result if success else None,
                            success=success,
                            error_code="TOOL_EXECUTION_ERROR" if not success else None,
                            error_message=error if not success else None,
                            duration_ms=tool_duration_ms,
                        )
                    except Exception as log_error:
                        logger.warning(f"Failed to log tool invocation: {log_error}")

                if success and tool_call.tool_name.value == "list_tasks":
                    # Format response based on resolution (supports numbered task selection)
                    agent_response = format_list_tasks_result(result)
                elif decision.response_text:
                    agent_response = decision.response_text
        elif decision.response_text:
            agent_response = decision.response_text
        elif decision.clarification_question:
            agent_response = decision.clarification_question
        else:
            agent_response = "I'm here to help with your tasks."

    # Log decision (Spec 004)
    if _observability_available and _logging_service:
        try:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            outcome_category = assign_outcome_category(
                tool_used=tool_used,
                tool_succeeded=tool_succeeded,
                is_clarification=decision.clarification_question is not None,
            )

            await _logging_service.write_decision_log(
                decision_id=decision_id,
                conversation_id=str(conversation.id),
                user_id=user_id,
                message=request.content,
                intent_type=intent_type,
                decision_type=decision_type_str,
                outcome_category=outcome_category,
                duration_ms=duration_ms,
                response_text=agent_response,
            )
        except Exception as log_error:
            logger.warning(f"Failed to log decision: {log_error}")

    # Create the assistant message with agent response
    assistant_message = await create_message(
        session,
        conversation.id,
        MessageRole.ASSISTANT,
        agent_response,
    )

    # Update conversation timestamp
    await update_conversation_timestamp(session, conversation)

    # Get all messages in chronological order
    all_messages = await get_conversation_messages(session, conversation.id)

    return SendMessageResponse(
        conversation_id=conversation.id,
        message=MessageResponse(
            id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
        ),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in all_messages
        ],
    )

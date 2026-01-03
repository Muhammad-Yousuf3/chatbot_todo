"""Chat endpoint for sending messages."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

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

router = APIRouter(prefix="/api", tags=["Chat"])


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
    """
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
    message = await create_message(
        session,
        conversation.id,
        MessageRole.USER,
        request.content,
    )

    # Update conversation timestamp
    await update_conversation_timestamp(session, conversation)

    # Get all messages in chronological order
    messages = await get_conversation_messages(session, conversation.id)

    return SendMessageResponse(
        conversation_id=conversation.id,
        message=MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        ),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )

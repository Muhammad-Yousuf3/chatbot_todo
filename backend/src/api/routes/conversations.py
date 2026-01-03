"""Conversations endpoints for listing and retrieving conversation history."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import CurrentUserId
from src.api.schemas.chat import MessageResponse
from src.api.schemas.conversations import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
)
from src.api.schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from src.db.session import SessionDep
from src.services import (
    get_conversation_by_id,
    get_conversation_message_count,
    get_conversation_messages,
    list_user_conversations,
    verify_conversation_ownership,
)

router = APIRouter(prefix="/api", tags=["Conversations"])


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ID format"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Conversation not found"},
    },
)
async def get_conversation(
    conversation_id: UUID,
    session: SessionDep,
    user_id: CurrentUserId,
) -> ConversationDetailResponse:
    """Get a conversation with all messages in chronological order."""
    conversation = await get_conversation_by_id(session, conversation_id)

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

    messages = await get_conversation_messages(session, conversation_id)

    return ConversationDetailResponse(
        conversation=ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
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


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
)
async def list_conversations(
    session: SessionDep,
    user_id: CurrentUserId,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConversationListResponse:
    """List all conversations for the authenticated user."""
    conversations, total = await list_user_conversations(
        session, user_id, limit=limit, offset=offset
    )

    # Get message counts for each conversation
    summaries = []
    for conv in conversations:
        message_count = await get_conversation_message_count(session, conv.id)
        summaries.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                updated_at=conv.updated_at,
                message_count=message_count,
            )
        )

    return ConversationListResponse(
        conversations=summaries,
        total=total,
        limit=limit,
        offset=offset,
    )

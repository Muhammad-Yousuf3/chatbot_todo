"""Chat API request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models import MessageRole


class SendMessageRequest(BaseModel):
    """Request schema for sending a chat message."""

    conversation_id: UUID | None = Field(
        default=None,
        description="UUID of existing conversation. Omit to create new conversation.",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=32000,
        description="Message text content",
    )


class MessageResponse(BaseModel):
    """Response schema for a single message."""

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    """Response schema after sending a message."""

    conversation_id: UUID
    message: MessageResponse
    messages: list[MessageResponse]

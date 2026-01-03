"""Conversation API schemas for listing and retrieval."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.api.schemas.chat import MessageResponse


class ConversationResponse(BaseModel):
    """Response schema for a conversation."""

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """Response schema for conversation with messages."""

    conversation: ConversationResponse
    messages: list[MessageResponse]


class ConversationSummary(BaseModel):
    """Summary schema for conversation listing."""

    id: UUID
    title: str
    updated_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Response schema for listing conversations."""

    conversations: list[ConversationSummary]
    total: int
    limit: int
    offset: int

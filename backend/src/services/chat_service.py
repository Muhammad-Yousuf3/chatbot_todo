"""Chat service for conversation persistence business logic."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Conversation, Message, MessageRole


async def create_conversation(
    session: AsyncSession,
    user_id: str,
    title: str = "",
) -> Conversation:
    """Create a new conversation for a user.

    Args:
        session: Database session
        user_id: ID of the user creating the conversation
        title: Optional title for the conversation

    Returns:
        The created Conversation instance
    """
    conversation = Conversation(
        user_id=user_id,
        title=title,
    )
    session.add(conversation)
    await session.flush()
    return conversation


async def create_message(
    session: AsyncSession,
    conversation_id: UUID,
    role: MessageRole,
    content: str,
) -> Message:
    """Create a new message in a conversation.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        role: Role of the message sender (user/assistant/system)
        content: Text content of the message

    Returns:
        The created Message instance
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    session.add(message)
    await session.flush()
    return message


def generate_conversation_title(first_message: str, max_length: int = 50) -> str:
    """Generate a conversation title from the first message.

    Args:
        first_message: The first message content
        max_length: Maximum length of the title

    Returns:
        A truncated title string
    """
    title = first_message.strip()
    if len(title) > max_length:
        title = title[: max_length - 3] + "..."
    return title


async def get_conversation_by_id(
    session: AsyncSession,
    conversation_id: UUID,
) -> Conversation | None:
    """Get a conversation by ID.

    Args:
        session: Database session
        conversation_id: UUID of the conversation

    Returns:
        Conversation if found, None otherwise
    """
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


def verify_conversation_ownership(conversation: Conversation, user_id: str) -> bool:
    """Verify that a user owns a conversation.

    Args:
        conversation: The conversation to check
        user_id: ID of the user to verify

    Returns:
        True if user owns the conversation, False otherwise
    """
    return conversation.user_id == user_id


async def get_conversation_messages(
    session: AsyncSession,
    conversation_id: UUID,
) -> list[Message]:
    """Get all messages for a conversation in chronological order.

    Args:
        session: Database session
        conversation_id: UUID of the conversation

    Returns:
        List of messages ordered by created_at
    """
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    return list(result.scalars().all())


async def update_conversation_timestamp(
    session: AsyncSession,
    conversation: Conversation,
) -> Conversation:
    """Update the conversation's updated_at timestamp.

    Args:
        session: Database session
        conversation: The conversation to update

    Returns:
        Updated conversation
    """
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    await session.flush()
    return conversation


async def list_user_conversations(
    session: AsyncSession,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Conversation], int]:
    """List all conversations for a user.

    Args:
        session: Database session
        user_id: ID of the user
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip

    Returns:
        Tuple of (list of conversations, total count)
    """
    # Get total count
    count_result = await session.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )
    total = count_result.scalar_one()

    # Get conversations ordered by most recent first
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    conversations = list(result.scalars().all())

    return conversations, total


async def get_conversation_message_count(
    session: AsyncSession,
    conversation_id: UUID,
) -> int:
    """Get the number of messages in a conversation.

    Args:
        session: Database session
        conversation_id: UUID of the conversation

    Returns:
        Number of messages
    """
    result = await session.execute(
        select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    )
    return result.scalar_one()

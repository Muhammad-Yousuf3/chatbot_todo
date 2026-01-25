"""ProcessedEvent model for event idempotency tracking."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ProcessedEvent(SQLModel, table=True):
    """Tracks processed events for idempotency.

    This model ensures that duplicate events are not processed multiple times.
    Events are identified by their unique event_id from CloudEvents specification.
    """

    __tablename__ = "processed_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: str = Field(max_length=100, unique=True, index=True)
    event_type: str = Field(max_length=100, index=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    @classmethod
    async def is_processed(cls, session, event_id: str) -> bool:
        """Check if an event has already been processed.

        Args:
            session: Database session
            event_id: The CloudEvents event ID to check

        Returns:
            True if the event was already processed, False otherwise
        """
        from sqlmodel import select

        stmt = select(cls).where(cls.event_id == event_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def mark_processed(cls, session, event_id: str, event_type: str) -> "ProcessedEvent":
        """Mark an event as processed.

        Args:
            session: Database session
            event_id: The CloudEvents event ID
            event_type: The event type string

        Returns:
            The created ProcessedEvent record
        """
        record = cls(event_id=event_id, event_type=event_type)
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

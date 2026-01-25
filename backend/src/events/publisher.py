"""Event publisher for task lifecycle events using Dapr Pub/Sub."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.dapr.client import get_dapr_service
from src.models import Recurrence, Reminder, Task

from .constants import PUBSUB_NAME, EventSource, EventType, Topic
from .schemas import (
    CloudEvent,
    FieldChange,
    RecurrenceData,
    ReminderData,
    TaskCompletedData,
    TaskCreatedData,
    TaskDeletedData,
    TaskUpdatedData,
)

logger = logging.getLogger(__name__)


def _log_event_publish(
    event_type: str,
    event_id: str,
    topic: str,
    success: bool,
    latency_ms: float,
    task_id: Optional[str] = None,
    user_id: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Log structured event publish information."""
    log_data = {
        "action": "event_publish",
        "event_type": event_type,
        "event_id": event_id,
        "topic": topic,
        "success": success,
        "latency_ms": round(latency_ms, 2),
    }
    if task_id:
        log_data["task_id"] = task_id
    if user_id:
        log_data["user_id"] = user_id
    if error:
        log_data["error"] = error

    if success:
        logger.info(f"Event published: {log_data}")
    else:
        logger.error(f"Event publish failed: {log_data}")


class EventPublisher:
    """Publisher for task lifecycle events.

    Events are published to Dapr Pub/Sub in CloudEvents format.
    If Dapr is not available, events are logged but not published.
    """

    def __init__(self):
        self._dapr = get_dapr_service()

    @property
    def enabled(self) -> bool:
        """Check if event publishing is enabled."""
        return self._dapr.enabled

    async def _publish(
        self,
        topic: str,
        event: CloudEvent,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Publish a CloudEvent to a topic.

        Args:
            topic: The topic name to publish to
            event: The CloudEvent to publish
            task_id: Optional task ID for logging
            user_id: Optional user ID for logging

        Returns:
            True if published successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Dapr disabled, skipping event: {event.type} to topic {topic}")
            return False

        start_time = time.time()
        try:
            self._dapr.client.publish_event(
                pubsub_name=PUBSUB_NAME,
                topic_name=topic,
                data=event.model_dump_json(),
                data_content_type="application/json",
            )
            latency_ms = (time.time() - start_time) * 1000
            _log_event_publish(
                event_type=event.type,
                event_id=event.id,
                topic=topic,
                success=True,
                latency_ms=latency_ms,
                task_id=task_id,
                user_id=user_id,
            )
            return True
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            _log_event_publish(
                event_type=event.type,
                event_id=event.id,
                topic=topic,
                success=False,
                latency_ms=latency_ms,
                task_id=task_id,
                user_id=user_id,
                error=str(e),
            )
            return False

    async def publish_task_created(
        self,
        task: Task,
        reminders: Optional[List[Reminder]] = None,
        recurrence: Optional[Recurrence] = None,
    ) -> bool:
        """Publish a TaskCreated event.

        Args:
            task: The created task
            reminders: Optional list of reminders attached to the task
            recurrence: Optional recurrence schedule for the task

        Returns:
            True if published successfully
        """
        reminder_data = []
        if reminders:
            reminder_data = [
                ReminderData(
                    reminder_id=str(r.id),
                    trigger_at=r.trigger_at,
                )
                for r in reminders
            ]

        recurrence_data = None
        if recurrence:
            recurrence_data = RecurrenceData(
                recurrence_id=str(recurrence.id),
                recurrence_type=recurrence.recurrence_type.value,
                cron_expression=recurrence.cron_expression,
                next_occurrence=recurrence.next_occurrence,
            )

        data = TaskCreatedData(
            task_id=str(task.id),
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            tags=task.tags or [],
            due_date=task.due_date,
            created_at=task.created_at,
            reminders=reminder_data,
            recurrence=recurrence_data,
        )

        event = CloudEvent(
            source=EventSource.BACKEND_TASKS,
            type=EventType.TASK_CREATED,
            data=data.model_dump(mode="json"),
        )

        return await self._publish(Topic.TASKS, event, task_id=str(task.id), user_id=task.user_id)

    async def publish_task_updated(
        self,
        task: Task,
        changes: Dict[str, FieldChange],
    ) -> bool:
        """Publish a TaskUpdated event.

        Args:
            task: The updated task
            changes: Dictionary of field changes with old/new values

        Returns:
            True if published successfully
        """
        data = TaskUpdatedData(
            task_id=str(task.id),
            user_id=task.user_id,
            updated_at=task.updated_at or datetime.utcnow(),
            changes={k: v.model_dump() for k, v in changes.items()},
        )

        event = CloudEvent(
            source=EventSource.BACKEND_TASKS,
            type=EventType.TASK_UPDATED,
            data=data.model_dump(mode="json"),
        )

        return await self._publish(Topic.TASKS, event, task_id=str(task.id), user_id=task.user_id)

    async def publish_task_completed(self, task: Task) -> bool:
        """Publish a TaskCompleted event.

        Args:
            task: The completed task

        Returns:
            True if published successfully
        """
        data = TaskCompletedData(
            task_id=str(task.id),
            user_id=task.user_id,
            completed_at=task.completed_at or datetime.utcnow(),
        )

        event = CloudEvent(
            source=EventSource.BACKEND_TASKS,
            type=EventType.TASK_COMPLETED,
            data=data.model_dump(mode="json"),
        )

        return await self._publish(Topic.TASKS, event, task_id=str(task.id), user_id=task.user_id)

    async def publish_task_deleted(self, task_id: str, user_id: str) -> bool:
        """Publish a TaskDeleted event.

        Args:
            task_id: ID of the deleted task
            user_id: ID of the user who owned the task

        Returns:
            True if published successfully
        """
        data = TaskDeletedData(
            task_id=task_id,
            user_id=user_id,
        )

        event = CloudEvent(
            source=EventSource.BACKEND_TASKS,
            type=EventType.TASK_DELETED,
            data=data.model_dump(mode="json"),
        )

        return await self._publish(Topic.TASKS, event, task_id=task_id, user_id=user_id)


# Global publisher instance
_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get or create the global event publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher

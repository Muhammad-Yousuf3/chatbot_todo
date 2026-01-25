"""Event publisher for Scheduler service."""

import logging
import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

from src.events.schemas import (
    CloudEvent,
    EventSource,
    EventType,
    PUBSUB_NAME,
    RecurringTaskScheduledData,
    ReminderTriggeredData,
    Topic,
)

from .client import get_dapr_service

logger = logging.getLogger(__name__)


def _log_event_publish(
    event_type: str,
    event_id: str,
    topic: str,
    success: bool,
    latency_ms: float,
    task_id: Optional[str] = None,
    reminder_id: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Log structured event publish information."""
    log_data = {
        "action": "event_publish",
        "service": "scheduler",
        "event_type": event_type,
        "event_id": event_id,
        "topic": topic,
        "success": success,
        "latency_ms": round(latency_ms, 2),
    }
    if task_id:
        log_data["task_id"] = task_id
    if reminder_id:
        log_data["reminder_id"] = reminder_id
    if error:
        log_data["error"] = error

    if success:
        logger.info(f"Event published: {log_data}")
    else:
        logger.error(f"Event publish failed: {log_data}")


class SchedulerEventPublisher:
    """Publisher for scheduler events (ReminderTriggered, RecurringTaskScheduled)."""

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
        reminder_id: Optional[str] = None,
    ) -> bool:
        """Publish a CloudEvent to a topic."""
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
                reminder_id=reminder_id,
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
                reminder_id=reminder_id,
                error=str(e),
            )
            return False

    async def publish_reminder_triggered(
        self,
        reminder_id: str,
        task_id: str,
        user_id: str,
        task_title: str,
        due_date: Optional[datetime] = None,
    ) -> bool:
        """Publish a ReminderTriggered event to notifications topic."""
        data = ReminderTriggeredData(
            reminder_id=reminder_id,
            task_id=task_id,
            user_id=user_id,
            task_title=task_title,
            due_date=due_date,
            triggered_at=datetime.utcnow(),
        )

        event = CloudEvent(
            source=EventSource.SCHEDULER_REMINDERS,
            type=EventType.REMINDER_TRIGGERED,
            data=data.model_dump(mode="json"),
        )

        return await self._publish(Topic.NOTIFICATIONS, event, task_id=task_id, reminder_id=reminder_id)

    async def publish_recurring_task_scheduled(
        self,
        source_task_id: str,
        user_id: str,
        title: str,
        description: Optional[str],
        priority: str,
        tags: list,
        recurrence_type: str,
        scheduled_for: datetime,
    ) -> tuple[bool, str]:
        """Publish a RecurringTaskScheduled event to tasks topic.

        Returns:
            Tuple of (success, new_task_id)
        """
        new_task_id = str(uuid4())

        data = RecurringTaskScheduledData(
            source_task_id=source_task_id,
            new_task_id=new_task_id,
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags,
            recurrence_type=recurrence_type,
            scheduled_for=scheduled_for,
        )

        event = CloudEvent(
            source=EventSource.SCHEDULER_RECURRING,
            type=EventType.RECURRING_TASK_SCHEDULED,
            data=data.model_dump(mode="json"),
        )

        success = await self._publish(Topic.TASKS, event, task_id=source_task_id)
        return success, new_task_id


# Global publisher instance
_publisher: Optional[SchedulerEventPublisher] = None


def get_scheduler_publisher() -> SchedulerEventPublisher:
    """Get or create the global scheduler event publisher."""
    global _publisher
    if _publisher is None:
        _publisher = SchedulerEventPublisher()
    return _publisher

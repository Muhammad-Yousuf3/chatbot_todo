"""Recurring task scheduler service.

Handles:
- Storing recurring task schedules from TaskCreated events
- Checking for due recurring tasks on cron trigger
- Publishing RecurringTaskScheduled events
- Updating next occurrence after scheduling
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from src.dapr.publisher import get_scheduler_publisher
from src.dapr.state import (
    add_to_registry,
    delete_state,
    get_state,
    is_event_processed,
    mark_event_processed,
    remove_from_registry,
    save_state,
)
from src.state.schemas import (
    RECURRING_REGISTRY_KEY,
    RecurringTaskState,
    recurring_task_key,
)

logger = logging.getLogger(__name__)


def _calculate_next_occurrence(
    recurrence_type: str,
    cron_expression: Optional[str] = None,
    from_date: Optional[datetime] = None,
) -> datetime:
    """Calculate the next occurrence based on recurrence type."""
    base = from_date or datetime.utcnow()

    if recurrence_type == "daily":
        return base + timedelta(days=1)
    elif recurrence_type == "weekly":
        return base + timedelta(weeks=1)
    elif recurrence_type == "custom" and cron_expression:
        try:
            from croniter import croniter
            cron = croniter(cron_expression, base)
            return cron.get_next(datetime)
        except Exception as e:
            logger.warning(f"Failed to parse cron expression: {e}")
            return base + timedelta(days=1)

    return base + timedelta(days=1)


class RecurringTaskService:
    """Service for managing recurring task schedules."""

    SERVICE_NAME = "scheduler"

    async def handle_task_created(self, event_data: dict, event_id: str) -> bool:
        """Handle TaskCreated event - extract and store recurrence schedule.

        Args:
            event_data: The TaskCreated event data
            event_id: The CloudEvents event ID for idempotency

        Returns:
            True if processed successfully
        """
        # Idempotency check
        if await is_event_processed(self.SERVICE_NAME, event_id):
            logger.info(f"Event {event_id} already processed, skipping")
            return True

        recurrence = event_data.get("recurrence")
        if not recurrence:
            # No recurrence data, nothing to do
            return True

        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        title = event_data.get("title")

        if not task_id or not user_id:
            logger.error("TaskCreated event missing task_id or user_id")
            return False

        # Calculate next occurrence
        recurrence_type = recurrence.get("recurrence_type", "daily")
        cron_expression = recurrence.get("cron_expression")
        next_occ = recurrence.get("next_occurrence")

        if next_occ:
            if isinstance(next_occ, str):
                next_occurrence = datetime.fromisoformat(next_occ.replace("Z", "+00:00"))
            else:
                next_occurrence = next_occ
        else:
            next_occurrence = _calculate_next_occurrence(recurrence_type, cron_expression)

        # Create recurring task state
        state = RecurringTaskState(
            task_id=task_id,
            user_id=user_id,
            title=title or "Untitled",
            description=event_data.get("description"),
            priority=event_data.get("priority", "medium"),
            tags=event_data.get("tags", []),
            recurrence_type=recurrence_type,
            cron_expression=cron_expression,
            next_occurrence=next_occurrence,
            created_from_event_id=event_id,
        )

        # Save to State Store
        key = recurring_task_key(task_id)
        success = await save_state(key, state)

        if success:
            # Add to registry for trigger queries
            await add_to_registry(RECURRING_REGISTRY_KEY, task_id)
            await mark_event_processed(self.SERVICE_NAME, event_id, "com.todo.task.created")
            logger.info(f"Saved recurring task schedule for task {task_id}, next: {next_occurrence}")
        else:
            logger.error(f"Failed to save recurring task schedule for task {task_id}")

        return success

    async def handle_task_deleted(self, event_data: dict, event_id: str) -> bool:
        """Handle TaskDeleted event - remove recurring schedule from state.

        Args:
            event_data: The TaskDeleted event data
            event_id: The CloudEvents event ID

        Returns:
            True if processed successfully
        """
        if await is_event_processed(self.SERVICE_NAME, event_id):
            logger.info(f"Event {event_id} already processed, skipping")
            return True

        task_id = event_data.get("task_id")
        if not task_id:
            logger.error("TaskDeleted event missing task_id")
            return False

        # Delete from State Store
        key = recurring_task_key(task_id)
        success = await delete_state(key)

        # Remove from registry
        await remove_from_registry(RECURRING_REGISTRY_KEY, task_id)

        await mark_event_processed(self.SERVICE_NAME, event_id, "com.todo.task.deleted")
        logger.info(f"Removed recurring task schedule for task {task_id}")

        return success

    async def handle_task_completed(self, event_data: dict, event_id: str) -> bool:
        """Handle TaskCompleted event - individual completion doesn't stop recurrence.

        Args:
            event_data: The TaskCompleted event data
            event_id: The CloudEvents event ID

        Returns:
            True (recurrence continues on individual task completion)
        """
        if await is_event_processed(self.SERVICE_NAME, event_id):
            return True

        # Individual task completion doesn't affect recurring schedule
        # The schedule creates new instances based on the original task
        await mark_event_processed(self.SERVICE_NAME, event_id, "com.todo.task.completed")
        return True

    async def process_due_recurring_tasks(self, recurring_keys: list[str]) -> int:
        """Process all due recurring tasks.

        Args:
            recurring_keys: List of state store keys for recurring tasks

        Returns:
            Number of tasks successfully scheduled
        """
        now = datetime.utcnow()
        scheduled_count = 0

        for key in recurring_keys:
            state = await get_state(key, RecurringTaskState)
            if not state:
                continue

            # Check if due
            if state.next_occurrence and state.next_occurrence <= now:
                success = await self._schedule_recurring_task(state)
                if success:
                    scheduled_count += 1

        return scheduled_count

    async def _schedule_recurring_task(self, state: RecurringTaskState) -> bool:
        """Schedule a single recurring task.

        Args:
            state: The recurring task state

        Returns:
            True if scheduled successfully
        """
        publisher = get_scheduler_publisher()

        success, new_task_id = await publisher.publish_recurring_task_scheduled(
            source_task_id=state.task_id,
            user_id=state.user_id,
            title=state.title,
            description=state.description,
            priority=state.priority,
            tags=state.tags,
            recurrence_type=state.recurrence_type,
            scheduled_for=state.next_occurrence,
        )

        if success:
            # Calculate and update next occurrence
            new_next = _calculate_next_occurrence(
                state.recurrence_type,
                state.cron_expression,
                state.next_occurrence,
            )
            state.next_occurrence = new_next
            state.last_scheduled = datetime.utcnow()

            key = recurring_task_key(state.task_id)
            await save_state(key, state)

            logger.info(f"Scheduled recurring task {state.task_id} as {new_task_id}, next: {new_next}")

        return success


# Global service instance
_service: Optional[RecurringTaskService] = None


def get_recurring_service() -> RecurringTaskService:
    """Get or create the recurring task service instance."""
    global _service
    if _service is None:
        _service = RecurringTaskService()
    return _service

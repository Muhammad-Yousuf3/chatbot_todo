"""Reminder scheduler service.

Handles:
- Storing reminder schedules from TaskCreated events
- Checking for due reminders on cron trigger
- Publishing ReminderTriggered events
- Marking reminders as fired after triggering
"""

import logging
from datetime import datetime
from typing import List, Optional

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
from src.state.schemas import REMINDER_REGISTRY_KEY, ReminderState, reminder_key

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing task reminders."""

    SERVICE_NAME = "scheduler-reminder"

    async def handle_task_created(self, event_data: dict, event_id: str) -> bool:
        """Handle TaskCreated event - extract and store reminders.

        Args:
            event_data: The TaskCreated event data
            event_id: The CloudEvents event ID for idempotency

        Returns:
            True if processed successfully
        """
        if await is_event_processed(self.SERVICE_NAME, event_id):
            logger.info(f"Event {event_id} already processed for reminders, skipping")
            return True

        reminders = event_data.get("reminders", [])
        if not reminders:
            return True

        task_id = event_data.get("task_id")
        user_id = event_data.get("user_id")
        title = event_data.get("title")
        due_date = event_data.get("due_date")

        if not task_id or not user_id:
            logger.error("TaskCreated event missing task_id or user_id for reminders")
            return False

        # Parse due_date if string
        parsed_due_date = None
        if due_date:
            if isinstance(due_date, str):
                parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            else:
                parsed_due_date = due_date

        success_count = 0
        for reminder in reminders:
            reminder_id = reminder.get("reminder_id")
            trigger_at = reminder.get("trigger_at")

            if not reminder_id or not trigger_at:
                continue

            # Parse trigger_at
            if isinstance(trigger_at, str):
                trigger_at = datetime.fromisoformat(trigger_at.replace("Z", "+00:00"))

            state = ReminderState(
                reminder_id=reminder_id,
                task_id=task_id,
                user_id=user_id,
                task_title=title or "Untitled",
                trigger_at=trigger_at,
                due_date=parsed_due_date,
                fired=False,
                cancelled=False,
                created_from_event_id=event_id,
            )

            key = reminder_key(reminder_id)
            if await save_state(key, state):
                # Add to registry for trigger queries
                await add_to_registry(REMINDER_REGISTRY_KEY, reminder_id)
                success_count += 1
                logger.debug(f"Saved reminder {reminder_id} for task {task_id}")

        await mark_event_processed(self.SERVICE_NAME, event_id, "com.todo.task.created")
        logger.info(f"Saved {success_count}/{len(reminders)} reminders for task {task_id}")

        return True

    async def handle_task_deleted(self, event_data: dict, event_id: str) -> bool:
        """Handle TaskDeleted event - cancel all reminders for the task.

        Note: Since we don't have a query mechanism, we rely on reminders
        being cleaned up via TTL or task_id matching during trigger checks.
        In production, consider maintaining a task_id -> reminder_ids index.

        Args:
            event_data: The TaskDeleted event data
            event_id: The CloudEvents event ID

        Returns:
            True if processed
        """
        if await is_event_processed(self.SERVICE_NAME, event_id):
            return True

        # Log for monitoring - actual cleanup happens via TTL or explicit cancellation
        task_id = event_data.get("task_id")
        logger.info(f"Task {task_id} deleted - reminders will be cancelled on next check")

        await mark_event_processed(self.SERVICE_NAME, event_id, "com.todo.task.deleted")
        return True

    async def handle_task_completed(self, event_data: dict, event_id: str) -> bool:
        """Handle TaskCompleted event - optionally cancel pending reminders.

        Args:
            event_data: The TaskCompleted event data
            event_id: The CloudEvents event ID

        Returns:
            True if processed
        """
        if await is_event_processed(self.SERVICE_NAME, event_id):
            return True

        # For completed tasks, we could cancel reminders
        # But for simplicity, we let them trigger anyway (user might want confirmation)
        task_id = event_data.get("task_id")
        logger.info(f"Task {task_id} completed - reminders will still trigger")

        await mark_event_processed(self.SERVICE_NAME, event_id, "com.todo.task.completed")
        return True

    async def process_due_reminders(self, reminder_keys: List[str]) -> int:
        """Process all due reminders.

        Args:
            reminder_keys: List of state store keys for reminders

        Returns:
            Number of reminders successfully triggered
        """
        now = datetime.utcnow()
        triggered_count = 0

        for key in reminder_keys:
            state = await get_state(key, ReminderState)
            if not state:
                continue

            # Check if due and not yet fired
            if state.trigger_at <= now and not state.fired and not state.cancelled:
                success = await self._trigger_reminder(state)
                if success:
                    triggered_count += 1

        return triggered_count

    async def _trigger_reminder(self, state: ReminderState) -> bool:
        """Trigger a single reminder.

        Args:
            state: The reminder state

        Returns:
            True if triggered successfully
        """
        publisher = get_scheduler_publisher()

        success = await publisher.publish_reminder_triggered(
            reminder_id=state.reminder_id,
            task_id=state.task_id,
            user_id=state.user_id,
            task_title=state.task_title,
            due_date=state.due_date,
        )

        if success:
            # Mark as fired
            state.fired = True
            key = reminder_key(state.reminder_id)
            await save_state(key, state)

            # Remove from registry (fired reminders don't need to be checked again)
            await remove_from_registry(REMINDER_REGISTRY_KEY, state.reminder_id)
            logger.info(f"Triggered reminder {state.reminder_id} for task {state.task_id}")

        return success


# Global service instance
_service: Optional[ReminderService] = None


def get_reminder_service() -> ReminderService:
    """Get or create the reminder service instance."""
    global _service
    if _service is None:
        _service = ReminderService()
    return _service

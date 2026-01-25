"""Dapr Pub/Sub event subscription endpoints.

Handles events from scheduler service:
- RecurringTaskScheduled: Create new task instances from recurring schedules
- ReminderTriggered: Mark reminders as fired in the database
"""

import logging
from datetime import datetime
from typing import Set
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlmodel import select

from src.db.session import SessionDep
from src.events.constants import EventType
from src.events.publisher import get_event_publisher
from src.models import Reminder, Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events"])

# In-memory idempotency cache (for production, use Redis or database)
_processed_events: Set[str] = set()
_MAX_CACHE_SIZE = 10000


def _is_event_processed(event_id: str) -> bool:
    """Check if an event has already been processed."""
    return event_id in _processed_events


def _mark_event_processed(event_id: str) -> None:
    """Mark an event as processed."""
    # Simple LRU-like cleanup
    if len(_processed_events) >= _MAX_CACHE_SIZE:
        # Remove oldest entries (first 1000)
        entries = list(_processed_events)
        for entry in entries[:1000]:
            _processed_events.discard(entry)
    _processed_events.add(event_id)


@router.post("/events/tasks")
async def handle_task_events(request: Request, session: SessionDep):
    """Handle task events from Dapr Pub/Sub.

    Events handled:
    - com.todo.recurring.scheduled: Create new task instance from recurring schedule
    """
    try:
        event = await request.json()
        event_type = event.get("type", "unknown")
        event_id = event.get("id", "unknown")
        event_data = event.get("data", {})

        logger.info(f"Backend received task event: type={event_type}, id={event_id}")

        # Idempotency check
        if _is_event_processed(event_id):
            logger.info(f"Event {event_id} already processed, skipping")
            return JSONResponse(content={"status": "SUCCESS"}, status_code=200)

        if event_type == EventType.RECURRING_TASK_SCHEDULED:
            await _handle_recurring_task_scheduled(event_data, event_id, session)

        _mark_event_processed(event_id)
        return JSONResponse(content={"status": "SUCCESS"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing task event: {e}")
        # Return success to prevent Dapr from retrying (we log the error)
        return JSONResponse(content={"status": "SUCCESS"}, status_code=200)


@router.post("/events/notifications")
async def handle_notification_events(request: Request, session: SessionDep):
    """Handle notification events from Dapr Pub/Sub.

    Events handled:
    - com.todo.reminder.triggered: Mark reminder as fired in database
    """
    try:
        event = await request.json()
        event_type = event.get("type", "unknown")
        event_id = event.get("id", "unknown")
        event_data = event.get("data", {})

        logger.info(f"Backend received notification event: type={event_type}, id={event_id}")

        # Idempotency check
        if _is_event_processed(event_id):
            logger.info(f"Event {event_id} already processed, skipping")
            return JSONResponse(content={"status": "SUCCESS"}, status_code=200)

        if event_type == EventType.REMINDER_TRIGGERED:
            await _handle_reminder_triggered(event_data, event_id, session)

        _mark_event_processed(event_id)
        return JSONResponse(content={"status": "SUCCESS"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing notification event: {e}")
        # Return success to prevent Dapr from retrying
        return JSONResponse(content={"status": "SUCCESS"}, status_code=200)


async def _handle_recurring_task_scheduled(
    event_data: dict,
    event_id: str,
    session: SessionDep,
) -> None:
    """Handle RecurringTaskScheduled event - create new task instance.

    Args:
        event_data: The RecurringTaskScheduled event payload
        event_id: The CloudEvents event ID
        session: Database session
    """
    new_task_id = event_data.get("new_task_id")
    user_id = event_data.get("user_id")
    title = event_data.get("title")
    description = event_data.get("description")
    priority_str = event_data.get("priority", "medium")
    tags = event_data.get("tags", [])
    source_task_id = event_data.get("source_task_id")
    scheduled_for = event_data.get("scheduled_for")

    if not new_task_id or not user_id or not title:
        logger.error(f"RecurringTaskScheduled missing required fields: {event_id}")
        return

    # Parse priority
    try:
        priority = TaskPriority(priority_str.lower())
    except (ValueError, AttributeError):
        priority = TaskPriority.MEDIUM

    # Parse scheduled_for as due_date
    due_date = None
    if scheduled_for:
        try:
            if isinstance(scheduled_for, str):
                due_date = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
            else:
                due_date = scheduled_for
        except Exception as e:
            logger.warning(f"Failed to parse scheduled_for: {e}")

    # Check if task already exists (idempotency)
    try:
        task_uuid = UUID(new_task_id)
        existing = await session.execute(
            select(Task).where(Task.id == task_uuid)
        )
        if existing.scalar_one_or_none():
            logger.info(f"Task {new_task_id} already exists, skipping creation")
            return
    except ValueError:
        logger.error(f"Invalid new_task_id format: {new_task_id}")
        return

    # Create the new task instance
    now = datetime.utcnow()
    task = Task(
        id=task_uuid,
        user_id=user_id,
        title=f"{title}",  # Could append date or instance number
        description=description,
        status=TaskStatus.PENDING,
        priority=priority,
        tags=tags,
        due_date=due_date,
        created_at=now,
        updated_at=now,
    )

    session.add(task)
    await session.flush()
    await session.refresh(task)

    logger.info(
        f"Created recurring task instance: id={task.id}, "
        f"source={source_task_id}, user={user_id}"
    )

    # Emit TaskCreated event for the new task instance
    try:
        publisher = get_event_publisher()
        await publisher.publish_task_created(task)
    except Exception as e:
        logger.error(f"Failed to publish TaskCreated for recurring instance: {e}")


async def _handle_reminder_triggered(
    event_data: dict,
    event_id: str,
    session: SessionDep,
) -> None:
    """Handle ReminderTriggered event - mark reminder as fired in database.

    Args:
        event_data: The ReminderTriggered event payload
        event_id: The CloudEvents event ID
        session: Database session
    """
    reminder_id = event_data.get("reminder_id")
    task_id = event_data.get("task_id")
    user_id = event_data.get("user_id")
    task_title = event_data.get("task_title")

    if not reminder_id:
        logger.error(f"ReminderTriggered missing reminder_id: {event_id}")
        return

    # Find and update the reminder
    try:
        reminder_uuid = UUID(reminder_id)
        result = await session.execute(
            select(Reminder).where(Reminder.id == reminder_uuid)
        )
        reminder = result.scalar_one_or_none()

        if not reminder:
            logger.warning(f"Reminder {reminder_id} not found in database")
            return

        if reminder.fired:
            logger.info(f"Reminder {reminder_id} already marked as fired")
            return

        # Mark as fired
        reminder.fired = True
        session.add(reminder)

        logger.info(
            f"Marked reminder as fired: id={reminder_id}, "
            f"task={task_id}, title={task_title}"
        )

    except ValueError:
        logger.error(f"Invalid reminder_id format: {reminder_id}")
    except Exception as e:
        logger.error(f"Error updating reminder {reminder_id}: {e}")

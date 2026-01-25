"""Scheduler service for recurring tasks and reminders using Dapr.

This service handles:
- Recurring task scheduling via Dapr cron bindings
- Reminder triggering and notification publishing
- State management via Dapr State Store
- Event subscription for task lifecycle events
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.dapr.client import get_dapr_service, is_dapr_enabled
from src.events.schemas import EventType
from src.services.recurring import get_recurring_service
from src.services.reminder import get_reminder_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Scheduler service...")
    logger.info(f"Dapr enabled: {is_dapr_enabled()}")

    # Initialize Dapr service
    dapr = get_dapr_service()
    if dapr.enabled:
        logger.info("Dapr client initialized")
    else:
        logger.warning("Running without Dapr - event processing disabled")

    yield
    logger.info("Shutting down Scheduler service...")


app = FastAPI(
    title="Todo Scheduler Service",
    description="Scheduler service for recurring tasks and reminders",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "scheduler",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_enabled": is_dapr_enabled(),
    }


@app.get("/health/dapr")
async def dapr_health_check():
    """Dapr sidecar health check endpoint."""
    dapr = get_dapr_service()
    dapr_health = dapr.check_health()

    status = "healthy" if dapr_health.get("dapr_sidecar_healthy", False) else "degraded"
    if not dapr_health.get("dapr_enabled", False):
        status = "disabled"

    return {
        "status": status,
        "service": "scheduler",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **dapr_health,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness probe endpoint for Kubernetes."""
    dapr = get_dapr_service()
    dapr_health = dapr.check_health()

    # Scheduler requires Dapr to be ready for full functionality
    dapr_ready = dapr_health.get("dapr_sidecar_healthy", False)
    status = "ready" if dapr_ready else "degraded"

    return {
        "status": status,
        "service": "scheduler",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dapr_ready": dapr_ready,
    }


@app.get("/dapr/subscribe")
async def dapr_subscribe():
    """Return Dapr subscription configuration.

    This endpoint is called by Dapr sidecar to discover event subscriptions.
    """
    return [
        {
            "pubsubname": "pubsub",
            "topic": "tasks",
            "route": "/events/tasks",
        },
    ]


@app.post("/events/tasks")
async def handle_task_event(request: Request):
    """Handle task lifecycle events from Dapr Pub/Sub.

    Events handled:
    - com.todo.task.created: Extract recurrence/reminders, store in State Store
    - com.todo.task.updated: Update stored schedules/reminders
    - com.todo.task.completed: Cancel pending reminders, deactivate recurrence
    - com.todo.task.deleted: Remove all schedules and reminders
    """
    try:
        event = await request.json()
        event_type = event.get("type", "unknown")
        event_id = event.get("id", "unknown")
        event_data = event.get("data", {})

        logger.info(f"Received event: type={event_type}, id={event_id}")

        recurring_service = get_recurring_service()
        reminder_service = get_reminder_service()

        if event_type == EventType.TASK_CREATED:
            # Process recurrence and reminders
            await recurring_service.handle_task_created(event_data, event_id)
            await reminder_service.handle_task_created(event_data, event_id)

        elif event_type == EventType.TASK_COMPLETED:
            # Handle completion (reminders may still trigger)
            await recurring_service.handle_task_completed(event_data, event_id)
            await reminder_service.handle_task_completed(event_data, event_id)

        elif event_type == EventType.TASK_DELETED:
            # Remove schedules and cancel reminders
            await recurring_service.handle_task_deleted(event_data, event_id)
            await reminder_service.handle_task_deleted(event_data, event_id)

        elif event_type == EventType.TASK_UPDATED:
            # For updates, we may need to update recurrence/reminders
            # For simplicity, this is not implemented in Phase V Part 1
            logger.debug(f"TaskUpdated event received, no action taken: {event_id}")

        return JSONResponse(content={"status": "SUCCESS"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing task event: {e}")
        # Return success to prevent Dapr from retrying
        return JSONResponse(content={"status": "SUCCESS"}, status_code=200)


@app.post("/triggers/recurring")
async def handle_recurring_trigger(request: Request):
    """Handle cron binding trigger for recurring tasks.

    Called by Dapr cron binding every minute.
    Checks state store for recurring tasks due now and publishes events.
    """
    logger.info("Recurring task trigger invoked")

    try:
        from src.dapr.state import query_state_by_prefix

        recurring_service = get_recurring_service()

        # Query state store for all recurring task keys via registry
        recurring_keys = await query_state_by_prefix("recurring")

        if recurring_keys:
            count = await recurring_service.process_due_recurring_tasks(recurring_keys)
            logger.info(f"Processed {count} due recurring tasks")
        else:
            logger.debug("No recurring tasks registered")

        return {
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tasks_checked": len(recurring_keys),
        }

    except Exception as e:
        logger.error(f"Error in recurring trigger: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/triggers/reminders")
async def handle_reminder_trigger(request: Request):
    """Handle cron binding trigger for reminders.

    Called by Dapr cron binding every minute.
    Checks state store for reminders due now and publishes notifications.
    """
    logger.info("Reminder trigger invoked")

    try:
        from src.dapr.state import query_state_by_prefix

        reminder_service = get_reminder_service()

        # Query state store for all reminder keys via registry
        reminder_keys = await query_state_by_prefix("reminder")

        if reminder_keys:
            count = await reminder_service.process_due_reminders(reminder_keys)
            logger.info(f"Triggered {count} due reminders")
        else:
            logger.debug("No reminders registered")

        return {
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reminders_checked": len(reminder_keys),
        }

    except Exception as e:
        logger.error(f"Error in reminder trigger: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

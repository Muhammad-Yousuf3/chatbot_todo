"""Event constants for Dapr Pub/Sub."""


class Topic:
    """Dapr Pub/Sub topic names."""

    TASKS = "tasks"
    NOTIFICATIONS = "notifications"


class EventType:
    """CloudEvents event type identifiers."""

    # Task lifecycle events
    TASK_CREATED = "com.todo.task.created"
    TASK_UPDATED = "com.todo.task.updated"
    TASK_COMPLETED = "com.todo.task.completed"
    TASK_DELETED = "com.todo.task.deleted"

    # Scheduler events
    REMINDER_TRIGGERED = "com.todo.reminder.triggered"
    RECURRING_TASK_SCHEDULED = "com.todo.recurring.scheduled"


class EventSource:
    """CloudEvents source identifiers."""

    BACKEND_TASKS = "/backend/tasks"
    SCHEDULER_REMINDERS = "/scheduler/reminders"
    SCHEDULER_RECURRING = "/scheduler/recurring"


# Dapr component names
PUBSUB_NAME = "pubsub"
STATESTORE_NAME = "statestore"
SECRETS_STORE_NAME = "kubernetes-secrets"

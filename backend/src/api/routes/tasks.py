"""Tasks REST API endpoints.

Provides CRUD operations for user tasks via REST API.
Supports priority, tags, reminders, recurrence, and event publishing.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.deps import CurrentUserId
from src.api.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
    RecurrenceResponse,
    ReminderResponse,
)
from src.db.session import SessionDep
from src.events.publisher import get_event_publisher
from src.events.schemas import FieldChange
from src.models import (
    Recurrence,
    RecurrenceType,
    Reminder,
    Task,
    TaskPriority,
    TaskStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def _task_to_response(task: Task) -> TaskResponse:
    """Convert a Task model to TaskResponse."""
    reminders = []
    if task.reminders:
        reminders = [
            ReminderResponse(
                id=r.id,
                trigger_at=r.trigger_at,
                fired=r.fired,
                cancelled=r.cancelled,
                created_at=r.created_at,
            )
            for r in task.reminders
        ]

    recurrence = None
    if task.recurrence:
        recurrence = RecurrenceResponse(
            id=task.recurrence.id,
            recurrence_type=task.recurrence.recurrence_type,
            cron_expression=task.recurrence.cron_expression,
            next_occurrence=task.recurrence.next_occurrence,
            active=task.recurrence.active,
            created_at=task.recurrence.created_at,
        )

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        tags=task.tags or [],
        due_date=task.due_date,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        reminders=reminders,
        recurrence=recurrence,
    )


def _calculate_next_occurrence(
    recurrence_type: RecurrenceType,
    cron_expression: Optional[str] = None,
    from_date: Optional[datetime] = None,
) -> datetime:
    """Calculate the next occurrence based on recurrence type."""
    base = from_date or datetime.utcnow()

    if recurrence_type == RecurrenceType.DAILY:
        return base + timedelta(days=1)
    elif recurrence_type == RecurrenceType.WEEKLY:
        return base + timedelta(weeks=1)
    elif recurrence_type == RecurrenceType.CUSTOM and cron_expression:
        try:
            from croniter import croniter
            cron = croniter(cron_expression, base)
            return cron.get_next(datetime)
        except Exception as e:
            logger.warning(f"Failed to parse cron expression: {e}")
            return base + timedelta(days=1)

    return base + timedelta(days=1)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List all tasks",
    description="Get all tasks for the authenticated user with filtering, search, and sorting.",
)
async def list_tasks(
    session: SessionDep,
    # Filters
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    tag: Optional[str] = Query(None, description="Filter by tag (contains)"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    due_before: Optional[datetime] = Query(None, description="Filter tasks due before date"),
    due_after: Optional[datetime] = Query(None, description="Filter tasks due after date"),
    # Sorting
    sort_by: Optional[str] = Query(
        "created_at",
        description="Sort by field: due_date, priority, created_at, title",
    ),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    # Pagination
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> TaskListResponse:
    """List all tasks for the current user with filtering and sorting."""
    query = select(Task).options(selectinload(Task.reminders), selectinload(Task.recurrence))

    # Apply filters
    if status_filter:
        query = query.where(Task.status == status_filter)

    if priority:
        query = query.where(Task.priority == priority)

    if tag:
        # JSONB containment query for tags
        query = query.where(Task.tags.contains([tag]))

    if search:
        # Case-insensitive search in title and description
        search_pattern = f"%{search}%"
        query = query.where(
            (Task.title.ilike(search_pattern)) | (Task.description.ilike(search_pattern))
        )

    if due_before:
        query = query.where(Task.due_date <= due_before)

    if due_after:
        query = query.where(Task.due_date >= due_after)

    # Apply sorting
    sort_column = {
        "due_date": Task.due_date,
        "priority": Task.priority,
        "created_at": Task.created_at,
        "title": Task.title,
        "updated_at": Task.updated_at,
    }.get(sort_by, Task.created_at)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    tasks = result.scalars().all()

    # Get total count (without pagination)
    count_query = select(func.count(Task.id))
    if status_filter:
        count_query = count_query.where(Task.status == status_filter)
    if priority:
        count_query = count_query.where(Task.priority == priority)
    if tag:
        count_query = count_query.where(Task.tags.contains([tag]))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            (Task.title.ilike(search_pattern)) | (Task.description.ilike(search_pattern))
        )
    if due_before:
        count_query = count_query.where(Task.due_date <= due_before)
    if due_after:
        count_query = count_query.where(Task.due_date >= due_after)

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    return TaskListResponse(
        tasks=[_task_to_response(task) for task in tasks],
        total=total,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description="Create a new task for the authenticated user.",
)
async def create_task(
    request: TaskCreateRequest,
    session: SessionDep,
    user_id: CurrentUserId,
    response: Response,
) -> TaskResponse:
    """Create a new task with optional priority, tags, reminders, and recurrence."""
    now = datetime.utcnow()

    task = Task(
        user_id=user_id,
        title=request.title,
        description=request.description,
        status=TaskStatus.PENDING,
        priority=request.priority,
        tags=request.tags or [],
        due_date=request.due_date,
        created_at=now,
        updated_at=now,
    )
    session.add(task)
    await session.flush()

    # Create reminders if provided
    reminders = []
    if request.reminders:
        for reminder_req in request.reminders:
            reminder = Reminder(
                task_id=task.id,
                trigger_at=reminder_req.trigger_at,
            )
            session.add(reminder)
            reminders.append(reminder)
        await session.flush()

    # Create recurrence if provided
    recurrence = None
    if request.recurrence:
        next_occ = _calculate_next_occurrence(
            request.recurrence.recurrence_type,
            request.recurrence.cron_expression,
            request.due_date or now,
        )
        recurrence = Recurrence(
            task_id=task.id,
            recurrence_type=request.recurrence.recurrence_type,
            cron_expression=request.recurrence.cron_expression,
            next_occurrence=next_occ,
        )
        session.add(recurrence)
        await session.flush()

    await session.refresh(task, ["reminders", "recurrence"])

    # Publish TaskCreated event
    publisher = get_event_publisher()
    try:
        event_published = await publisher.publish_task_created(task, reminders, recurrence)
        response.headers["X-Event-Published"] = str(event_published).lower()
    except Exception as e:
        logger.error(f"Failed to publish TaskCreated event: {e}")
        response.headers["X-Event-Published"] = "false"

    return _task_to_response(task)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task",
    description="Get a specific task by ID.",
)
async def get_task(
    task_id: UUID,
    session: SessionDep,
    user_id: CurrentUserId,
) -> TaskResponse:
    """Get a specific task."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id).options(
        selectinload(Task.reminders), selectinload(Task.recurrence)
    )
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    return _task_to_response(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Update a task's fields.",
)
async def update_task(
    task_id: UUID,
    request: TaskUpdateRequest,
    session: SessionDep,
    user_id: CurrentUserId,
    response: Response,
) -> TaskResponse:
    """Update a task with change tracking for events."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id).options(
        selectinload(Task.reminders), selectinload(Task.recurrence)
    )
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    # Track changes for event
    changes = {}

    if request.title is not None and request.title != task.title:
        changes["title"] = FieldChange(old_value=task.title, new_value=request.title)
        task.title = request.title

    if request.description is not None and request.description != task.description:
        changes["description"] = FieldChange(old_value=task.description, new_value=request.description)
        task.description = request.description

    if request.status is not None and request.status != task.status:
        changes["status"] = FieldChange(old_value=task.status.value, new_value=request.status.value)
        task.status = request.status
        if request.status == TaskStatus.COMPLETED and task.completed_at is None:
            task.completed_at = datetime.utcnow()
        elif request.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            task.completed_at = None

    if request.priority is not None and request.priority != task.priority:
        changes["priority"] = FieldChange(old_value=task.priority.value, new_value=request.priority.value)
        task.priority = request.priority

    if request.tags is not None and request.tags != task.tags:
        changes["tags"] = FieldChange(old_value=task.tags, new_value=request.tags)
        task.tags = request.tags

    if request.due_date is not None and request.due_date != task.due_date:
        changes["due_date"] = FieldChange(
            old_value=task.due_date.isoformat() if task.due_date else None,
            new_value=request.due_date.isoformat(),
        )
        task.due_date = request.due_date

    # Update timestamp
    task.updated_at = datetime.utcnow()

    # Handle reminders update (replace existing)
    if request.reminders is not None:
        # Delete existing reminders
        for reminder in task.reminders:
            await session.delete(reminder)

        # Create new reminders
        for reminder_req in request.reminders:
            reminder = Reminder(
                task_id=task.id,
                trigger_at=reminder_req.trigger_at,
            )
            session.add(reminder)
        changes["reminders"] = FieldChange(
            old_value=len(task.reminders or []),
            new_value=len(request.reminders),
        )

    # Handle recurrence update (replace existing)
    if request.recurrence is not None:
        if task.recurrence:
            await session.delete(task.recurrence)

        next_occ = _calculate_next_occurrence(
            request.recurrence.recurrence_type,
            request.recurrence.cron_expression,
            task.due_date or datetime.utcnow(),
        )
        recurrence = Recurrence(
            task_id=task.id,
            recurrence_type=request.recurrence.recurrence_type,
            cron_expression=request.recurrence.cron_expression,
            next_occurrence=next_occ,
        )
        session.add(recurrence)
        changes["recurrence"] = FieldChange(
            old_value=task.recurrence.recurrence_type.value if task.recurrence else None,
            new_value=request.recurrence.recurrence_type.value,
        )

    await session.flush()
    await session.refresh(task, ["reminders", "recurrence"])

    # Publish TaskUpdated event if there are changes
    if changes:
        publisher = get_event_publisher()
        try:
            event_published = await publisher.publish_task_updated(task, changes)
            response.headers["X-Event-Published"] = str(event_published).lower()
        except Exception as e:
            logger.error(f"Failed to publish TaskUpdated event: {e}")
            response.headers["X-Event-Published"] = "false"
    else:
        response.headers["X-Event-Published"] = "false"

    return _task_to_response(task)


@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Complete a task",
    description="Mark a task as completed.",
)
async def complete_task(
    task_id: UUID,
    session: SessionDep,
    user_id: CurrentUserId,
    response: Response,
) -> TaskResponse:
    """Mark a task as completed and emit TaskCompleted event."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id).options(
        selectinload(Task.reminders), selectinload(Task.recurrence)
    )
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    await session.flush()
    await session.refresh(task, ["reminders", "recurrence"])

    # Publish TaskCompleted event
    publisher = get_event_publisher()
    try:
        event_published = await publisher.publish_task_completed(task)
        response.headers["X-Event-Published"] = str(event_published).lower()
    except Exception as e:
        logger.error(f"Failed to publish TaskCompleted event: {e}")
        response.headers["X-Event-Published"] = "false"

    return _task_to_response(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Delete a task permanently.",
)
async def delete_task(
    task_id: UUID,
    session: SessionDep,
    user_id: CurrentUserId,
    response: Response,
) -> None:
    """Delete a task and emit TaskDeleted event."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    task_id_str = str(task.id)
    task_user_id = task.user_id

    await session.delete(task)

    # Publish TaskDeleted event
    publisher = get_event_publisher()
    try:
        event_published = await publisher.publish_task_deleted(task_id_str, task_user_id)
        response.headers["X-Event-Published"] = str(event_published).lower()
    except Exception as e:
        logger.error(f"Failed to publish TaskDeleted event: {e}")
        response.headers["X-Event-Published"] = "false"

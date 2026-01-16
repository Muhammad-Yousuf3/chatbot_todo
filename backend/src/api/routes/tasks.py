"""Tasks REST API endpoints.

Provides CRUD operations for user tasks via REST API.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from src.api.deps import CurrentUserId
from src.api.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from src.db.session import SessionDep
from src.models import Task, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List all tasks",
    description="Get all tasks for the authenticated user.",
)
async def list_tasks(
    session: SessionDep,
    #user_id: CurrentUserId,
    status_filter: TaskStatus | None = None,
) -> TaskListResponse:
    """List all tasks for the current user."""
    query = select(Task)

    if status_filter:
        query = query.where(Task.status == status_filter)

    query = query.order_by(Task.created_at.desc())

    result = await session.execute(query)
    tasks = result.scalars().all()

    return TaskListResponse(
        tasks=[
            TaskResponse(
                id=task.id,
                description=task.description,
                status=task.status,
                due_date=task.due_date,
                created_at=task.created_at,
                completed_at=task.completed_at,
            )
            for task in tasks
        ],
        total=len(tasks),
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
) -> TaskResponse:
    """Create a new task."""
    task = Task(
        user_id=user_id,
        description=request.description,
        status=TaskStatus.PENDING,
        due_date=request.due_date,
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


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
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Update a task's description or status.",
)
async def update_task(
    task_id: UUID,
    request: TaskUpdateRequest,
    session: SessionDep,
    user_id: CurrentUserId,
) -> TaskResponse:
    """Update a task."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    if request.description is not None:
        task.description = request.description

    if request.status is not None:
        task.status = request.status
        if request.status == TaskStatus.COMPLETED and task.completed_at is None:
            task.completed_at = datetime.utcnow()
        elif request.status == TaskStatus.PENDING:
            task.completed_at = None

    if request.due_date is not None:
        task.due_date = request.due_date

    await session.flush()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


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
) -> TaskResponse:
    """Mark a task as completed."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()

    await session.flush()
    await session.refresh(task)

    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


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
) -> None:
    """Delete a task."""
    query = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": "Task not found"}},
        )

    await session.delete(task)

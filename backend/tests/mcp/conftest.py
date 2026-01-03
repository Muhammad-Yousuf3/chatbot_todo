"""Test fixtures for MCP tool testing.

These fixtures provide:
- A mock context for testing tools without the full MCP server
- A test database session for integration testing
- Helper functions for creating test data
"""

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.models.task import Task, TaskStatus


@dataclass
class MockAppContext:
    """Mock application context for testing."""

    engine: MagicMock


@dataclass
class MockRequestContext:
    """Mock request context with lifespan context access."""

    lifespan_context: MockAppContext


@dataclass
class MockContext:
    """Mock MCP context for testing tools.

    This provides the same interface as the real Context object
    that FastMCP passes to tools.
    """

    request_context: MockRequestContext

    # Logging methods (no-op for tests)
    async def info(self, message: str) -> None:
        pass

    async def debug(self, message: str) -> None:
        pass

    async def report_progress(self, progress: float, total: float) -> None:
        pass


# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
def mock_ctx(test_engine) -> MockContext:
    """Create a mock context with test engine for MCP tool testing."""
    app_context = MockAppContext(engine=test_engine)
    request_context = MockRequestContext(lifespan_context=app_context)
    return MockContext(request_context=request_context)


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        id=uuid4(),
        user_id="test-user-1",
        description="Buy groceries",
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
        completed_at=None,
    )


@pytest.fixture
def sample_completed_task() -> Task:
    """Create a sample completed task for testing."""
    now = datetime.utcnow()
    return Task(
        id=uuid4(),
        user_id="test-user-1",
        description="Call mom",
        status=TaskStatus.COMPLETED,
        created_at=now,
        completed_at=now,
    )


async def create_test_task(
    session: AsyncSession,
    user_id: str = "test-user-1",
    description: str = "Test task",
    status: TaskStatus = TaskStatus.PENDING,
    task_id: Optional[UUID] = None,
) -> Task:
    """Helper function to create a task in the test database.

    Args:
        session: The database session
        user_id: The task owner's ID
        description: The task description
        status: The task status
        task_id: Optional specific task ID

    Returns:
        The created Task instance
    """
    now = datetime.utcnow()
    task = Task(
        id=task_id or uuid4(),
        user_id=user_id,
        description=description,
        status=status,
        created_at=now,
        completed_at=now if status == TaskStatus.COMPLETED else None,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

# Quickstart: MCP Task Tools

**Feature Branch**: `002-mcp-task-tools`
**Date**: 2026-01-03

## Prerequisites

- Python 3.11+
- PostgreSQL database (Neon or local)
- MCP SDK (`pip install mcp>=1.25,<2`)
- SQLModel with async support (`pip install sqlmodel[asyncio]`)

## Project Structure

```
backend/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py          # FastMCP server setup
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── add_task.py
│   │   │   ├── list_tasks.py
│   │   │   ├── update_task.py
│   │   │   ├── complete_task.py
│   │   │   └── delete_task.py
│   │   └── schemas.py         # ToolResult, TaskData models
│   ├── models/
│   │   └── task.py            # Task SQLModel
│   └── db/
│       └── engine.py          # Async engine setup
└── tests/
    ├── mcp/
    │   ├── test_add_task.py
    │   ├── test_list_tasks.py
    │   ├── test_update_task.py
    │   ├── test_complete_task.py
    │   └── test_delete_task.py
    └── conftest.py            # Test fixtures
```

## Step 1: Set Up Database Model

```python
# backend/src/models/task.py
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Task(SQLModel, table=True):
    """Todo task item owned by a user."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, max_length=255)
    description: str = Field(max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.PENDING, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)
```

## Step 2: Set Up Response Schemas

```python
# backend/src/mcp_server/schemas.py
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TaskData(BaseModel):
    id: UUID
    description: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ToolResult(BaseModel):
    success: bool
    data: Optional[TaskData | List[TaskData]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
```

## Step 3: Set Up MCP Server

```python
# backend/src/mcp_server/server.py
from contextlib import asynccontextmanager
from typing import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from src.db.engine import DATABASE_URL


@dataclass
class AppContext:
    engine: AsyncEngine


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage database engine lifecycle."""
    engine = create_async_engine(DATABASE_URL)
    try:
        yield AppContext(engine=engine)
    finally:
        await engine.dispose()


mcp = FastMCP("task-tools", lifespan=app_lifespan)

# Import tools to register them
from src.mcp_server.tools import add_task, list_tasks, update_task, complete_task, delete_task
```

## Step 4: Implement a Tool (Example: add_task)

```python
# backend/src/mcp_server/tools/add_task.py
from datetime import datetime
from uuid import uuid4

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.mcp_server.server import mcp, AppContext
from src.mcp_server.schemas import ToolResult, TaskData
from src.models.task import Task, TaskStatus


@mcp.tool()
async def add_task(
    user_id: str,
    description: str,
    ctx: Context[ServerSession, AppContext]
) -> ToolResult:
    """Create a new task for the specified user.

    Args:
        user_id: The authenticated user's ID
        description: Task description (1-1000 characters)

    Returns:
        ToolResult with the created task data
    """
    # Validation
    if not user_id:
        return ToolResult(
            success=False,
            error="user_id is required",
            error_code="VALIDATION_ERROR"
        )

    if not description:
        return ToolResult(
            success=False,
            error="Description cannot be empty",
            error_code="VALIDATION_ERROR"
        )

    if len(description) > 1000:
        return ToolResult(
            success=False,
            error="Description exceeds 1000 characters",
            error_code="VALIDATION_ERROR"
        )

    # Create task
    engine = ctx.request_context.lifespan_context.engine
    async with AsyncSession(engine) as session:
        task = Task(
            id=uuid4(),
            user_id=user_id,
            description=description,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            completed_at=None
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        return ToolResult(
            success=True,
            data=TaskData(
                id=task.id,
                description=task.description,
                status=task.status.value,
                created_at=task.created_at,
                completed_at=task.completed_at
            )
        )
```

## Step 5: Run the MCP Server

```python
# backend/src/mcp_server/__main__.py
from src.mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Step 6: Test a Tool

```python
# backend/tests/mcp/test_add_task.py
import pytest
from uuid import UUID

from src.mcp_server.tools.add_task import add_task
from src.mcp_server.schemas import ToolResult


@pytest.mark.asyncio
async def test_add_task_success(mock_ctx):
    """Test successful task creation."""
    result = await add_task(
        user_id="user-123",
        description="Buy groceries",
        ctx=mock_ctx
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.description == "Buy groceries"
    assert result.data.status == "pending"
    assert isinstance(result.data.id, UUID)


@pytest.mark.asyncio
async def test_add_task_empty_description(mock_ctx):
    """Test validation error for empty description."""
    result = await add_task(
        user_id="user-123",
        description="",
        ctx=mock_ctx
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_add_task_description_too_long(mock_ctx):
    """Test validation error for description exceeding limit."""
    result = await add_task(
        user_id="user-123",
        description="x" * 1001,
        ctx=mock_ctx
    )

    assert result.success is False
    assert result.error_code == "VALIDATION_ERROR"
    assert "1000" in result.error
```

## Running Tests

```bash
# Run all MCP tool tests
pytest backend/tests/mcp/ -v

# Run with coverage
pytest backend/tests/mcp/ --cov=src.mcp_server.tools
```

## Integration with OpenAI Agents SDK

```python
from agents.mcp import MCPServerStdio

# Connect to MCP server
async with MCPServerStdio(
    command="python",
    args=["-m", "src.mcp_server"],
    cwd="/path/to/backend"
) as server:
    # Agent automatically discovers tools
    # Tools are available as: add_task, list_tasks, update_task, complete_task, delete_task
    pass
```

## Key Validation Checklist

- [ ] Each tool validates user_id is non-empty
- [ ] Each tool validates input parameters before database access
- [ ] Ownership is verified before any update/delete/complete operation
- [ ] Idempotent operations (complete_task, delete_task) return success even on re-invocation
- [ ] All responses conform to ToolResult schema
- [ ] No direct database access outside MCP tools

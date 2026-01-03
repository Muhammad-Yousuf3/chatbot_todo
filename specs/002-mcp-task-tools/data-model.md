# Data Model: MCP Task Tools

**Feature Branch**: `002-mcp-task-tools`
**Date**: 2026-01-03
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL                                   │
│  ┌─────────────┐                                                     │
│  │    User     │  (Better Auth - not managed by this spec)          │
│  │─────────────│                                                     │
│  │ id: string  │                                                     │
│  └──────┬──────┘                                                     │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ 1
          │
          ▼ *
┌─────────────────────┐
│        Task         │
│─────────────────────│
│ id: UUID [PK]       │
│ user_id: string [FK]│───── References external User
│ description: text   │
│ status: enum        │
│ created_at: datetime│
│ completed_at: datetime (nullable)
└─────────────────────┘
```

## Entities

### Task

Represents a single todo item owned by a user, managed exclusively via MCP tools.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique task identifier |
| `user_id` | VARCHAR(255) | NOT NULL, INDEX | Reference to Better Auth user ID |
| `description` | VARCHAR(1000) | NOT NULL | Task description text |
| `status` | VARCHAR(20) | NOT NULL, CHECK IN ('pending', 'completed'), DEFAULT 'pending' | Task completion status |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | When task was created |
| `completed_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | When task was completed (null if pending) |

**Indexes**:
- `task_pkey`: PRIMARY KEY on `id`
- `idx_task_user_created`: INDEX on `(user_id, created_at DESC)` for listing

**Validation Rules**:
- `user_id` must be non-empty string
- `description` must be non-empty (length > 0)
- `description` max length 1,000 characters
- `status` must be one of: 'pending', 'completed'
- `completed_at` must be NULL when status is 'pending'
- `completed_at` must be NOT NULL when status is 'completed'

## State Transitions

### Task Status States

```
                        ┌───────────────────┐
  add_task              │                   │
  ─────────────────────►│     PENDING       │
                        │                   │
                        └─────────┬─────────┘
                                  │
                                  │ complete_task
                                  │
                                  ▼
                        ┌───────────────────┐
                        │                   │
                        │    COMPLETED      │
                        │                   │
                        └───────────────────┘
```

**Notes**:
- Tasks are created with status 'pending'
- `complete_task` transitions to 'completed' (idempotent)
- No reverse transition (uncomplete) in this spec
- `delete_task` removes task from any state

### Task Lifecycle

```
  add_task      Validate     Persist     Return
  ─────────────►──────────►───────────►──────────►
       │            │            │           │
       │            │            │           │
   user_id     Check desc    INSERT     TaskResult
   + desc      Check length  in DB      with id
               Check user

  update_task   Validate     Load+Check   Persist    Return
  ─────────────►──────────►────────────►───────────►──────────►
       │            │            │            │           │
       │            │            │            │           │
   task_id     Check desc   Ownership    UPDATE     TaskResult
   + user_id   Check length  verified    in DB
   + new_desc

  complete_task  Validate    Load+Check   Persist    Return
  ─────────────►──────────►────────────►───────────►──────────►
       │            │            │            │           │
       │            │            │            │           │
   task_id     Check UUID   Ownership   UPDATE      TaskResult
   + user_id                verified    status +    (idempotent)
                                        completed_at

  delete_task   Validate     Load+Check   Delete     Return
  ─────────────►──────────►────────────►───────────►──────────►
       │            │            │            │           │
       │            │            │            │           │
   task_id     Check UUID   Ownership    DELETE     TaskResult
   + user_id                (or skip     from DB    (idempotent)
                            if missing)
```

## SQLModel Schema (Reference)

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Task(SQLModel, table=True):
    """Todo task item owned by a user, managed via MCP tools."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, max_length=255)
    description: str = Field(max_length=1000)
    status: TaskStatus = Field(default=TaskStatus.PENDING, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)
```

## MCP Tool Response Models

```python
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TaskData(BaseModel):
    """Task data returned by MCP tools."""
    id: UUID
    description: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ToolResult(BaseModel):
    """Standard response from all MCP task tools."""
    success: bool
    data: Optional[TaskData | List[TaskData]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None  # NOT_FOUND, VALIDATION_ERROR, ACCESS_DENIED


class AddTaskResult(ToolResult):
    """Response from add_task tool."""
    pass  # data contains single TaskData


class ListTasksResult(ToolResult):
    """Response from list_tasks tool."""
    pass  # data contains List[TaskData]


class UpdateTaskResult(ToolResult):
    """Response from update_task tool."""
    pass  # data contains single TaskData


class CompleteTaskResult(ToolResult):
    """Response from complete_task tool."""
    pass  # data contains single TaskData


class DeleteTaskResult(ToolResult):
    """Response from delete_task tool."""
    pass  # data is None on success
```

## Database Migration Notes

1. **UUID Extension**: Ensure `uuid-ossp` extension is enabled in PostgreSQL
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

2. **Table Creation**:
   ```sql
   CREATE TABLE task (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       user_id VARCHAR(255) NOT NULL,
       description VARCHAR(1000) NOT NULL,
       status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed')),
       created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
       completed_at TIMESTAMP WITH TIME ZONE
   );
   ```

3. **Index Creation**:
   ```sql
   CREATE INDEX idx_task_user_created
   ON task (user_id, created_at DESC);
   ```

4. **Constraint for completed_at consistency**:
   ```sql
   ALTER TABLE task
   ADD CONSTRAINT check_completed_at_consistency
   CHECK (
       (status = 'pending' AND completed_at IS NULL) OR
       (status = 'completed' AND completed_at IS NOT NULL)
   );
   ```

## Relationship to Other Entities

### User → Task (1:N)
- One user can have many tasks
- Each task belongs to exactly one user
- User deletion handling: External to this spec (Better Auth manages users)
- No cascade delete defined (tasks may need cleanup policy)

### Task Independence
- Tasks are independent of Conversations (from spec 001)
- Task management is conversation-agnostic
- AI agent may reference tasks in conversation context, but tasks have no FK to conversations

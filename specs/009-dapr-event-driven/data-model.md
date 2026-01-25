# Data Model: Phase V Part 1 - Event-Driven Todo Chatbot

**Branch**: `009-dapr-event-driven` | **Date**: 2026-01-20 | **Plan**: [plan.md](./plan.md)

---

## Overview

This document defines the extended data models required for the event-driven Todo Chatbot. It covers:
1. Extended Task model (priority, tags, relationships)
2. New Reminder entity
3. New Recurrence entity
4. Event payload schemas (CloudEvents)
5. State Store schemas (Dapr)

---

## 1. Core Entities (PostgreSQL)

### 1.1 Task Entity (Extended)

**Table**: `tasks`

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PRIMARY KEY | uuid_generate_v4() | Unique task identifier |
| `user_id` | VARCHAR(255) | NOT NULL, INDEX | - | Owner user ID |
| `title` | VARCHAR(200) | NOT NULL | - | Task title (display name) |
| `description` | TEXT | NULL | NULL | Detailed task description |
| `status` | VARCHAR(20) | NOT NULL | 'pending' | Enum: pending, in_progress, completed |
| `priority` | VARCHAR(10) | NOT NULL | 'medium' | Enum: high, medium, low |
| `tags` | JSONB | NOT NULL | '[]' | Array of tag strings |
| `due_date` | TIMESTAMP | NULL | NULL | Optional deadline |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | NOW() | Last modification timestamp |
| `completed_at` | TIMESTAMP | NULL | NULL | Completion timestamp |

**Indexes**:
- `idx_tasks_user_id` on `user_id`
- `idx_tasks_status` on `status`
- `idx_tasks_priority` on `priority`
- `idx_tasks_due_date` on `due_date`
- `idx_tasks_tags` GIN index on `tags` (for tag search)

**SQLModel Definition**:
```python
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, max_length=255)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    tags: List[str] = Field(default=[], sa_column=Column(JSONB, nullable=False, server_default="[]"))
    due_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    reminders: List["Reminder"] = Relationship(back_populates="task", cascade_delete=True)
    recurrence: Optional["Recurrence"] = Relationship(back_populates="task", cascade_delete=True)

    __table_args__ = (
        Index("idx_tasks_tags", "tags", postgresql_using="gin"),
    )
```

---

### 1.2 Reminder Entity (New)

**Table**: `reminders`

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PRIMARY KEY | uuid_generate_v4() | Unique reminder identifier |
| `task_id` | UUID | NOT NULL, FK(tasks.id) | - | Associated task |
| `trigger_at` | TIMESTAMP | NOT NULL | - | When reminder should fire |
| `fired` | BOOLEAN | NOT NULL | false | Whether reminder was triggered |
| `cancelled` | BOOLEAN | NOT NULL | false | Whether reminder was cancelled |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | Creation timestamp |

**Indexes**:
- `idx_reminders_task_id` on `task_id`
- `idx_reminders_trigger_at` on `trigger_at` (for efficient due reminder queries)
- `idx_reminders_pending` on `(fired, cancelled)` WHERE fired = false AND cancelled = false

**SQLModel Definition**:
```python
class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", index=True)
    trigger_at: datetime = Field(nullable=False)
    fired: bool = Field(default=False)
    cancelled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    task: Optional[Task] = Relationship(back_populates="reminders")
```

---

### 1.3 Recurrence Entity (New)

**Table**: `recurrences`

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PRIMARY KEY | uuid_generate_v4() | Unique recurrence identifier |
| `task_id` | UUID | NOT NULL, FK(tasks.id), UNIQUE | - | Associated task (one-to-one) |
| `recurrence_type` | VARCHAR(20) | NOT NULL | - | Enum: daily, weekly, custom |
| `cron_expression` | VARCHAR(100) | NULL | NULL | Custom cron expression (if type=custom) |
| `next_occurrence` | TIMESTAMP | NULL | NULL | Next scheduled occurrence |
| `active` | BOOLEAN | NOT NULL | true | Whether recurrence is active |
| `created_at` | TIMESTAMP | NOT NULL | NOW() | Creation timestamp |

**Indexes**:
- `idx_recurrences_task_id` on `task_id` (unique)
- `idx_recurrences_next_occurrence` on `next_occurrence`
- `idx_recurrences_active` on `active`

**SQLModel Definition**:
```python
class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

class Recurrence(SQLModel, table=True):
    __tablename__ = "recurrences"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", unique=True, index=True)
    recurrence_type: RecurrenceType = Field(nullable=False)
    cron_expression: Optional[str] = Field(default=None, max_length=100)
    next_occurrence: Optional[datetime] = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    task: Optional[Task] = Relationship(back_populates="recurrence")
```

---

### 1.4 Processed Event Entity (New - Optional)

**Table**: `processed_events`

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | UUID | PRIMARY KEY | uuid_generate_v4() | Record ID |
| `event_id` | VARCHAR(100) | NOT NULL, UNIQUE | - | CloudEvents event ID |
| `event_type` | VARCHAR(100) | NOT NULL | - | Event type string |
| `processed_at` | TIMESTAMP | NOT NULL | NOW() | When event was processed |

> **Note**: This table is optional. Idempotency can also be achieved using Dapr State Store with TTL. Database-backed idempotency provides stronger durability guarantees.

---

## 2. Event Payload Schemas (CloudEvents)

All events follow the CloudEvents v1.0 specification with application-specific data payloads.

### 2.1 Base CloudEvent Envelope

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
from typing import Any

class CloudEvent(BaseModel):
    """CloudEvents v1.0 envelope."""
    specversion: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str  # e.g., "/backend/tasks"
    type: str    # e.g., "com.todo.task.created"
    time: datetime = Field(default_factory=datetime.utcnow)
    datacontenttype: str = "application/json"
    data: Any    # Event-specific payload

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
```

---

### 2.2 TaskCreated Event

**Type**: `com.todo.task.created`
**Source**: `/backend/tasks`
**Topic**: `tasks`

```python
class TaskCreatedData(BaseModel):
    """Payload for TaskCreated event."""
    task_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    status: str  # TaskStatus value
    priority: str  # TaskPriority value
    tags: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime
    reminders: List[ReminderData] = []
    recurrence: Optional[RecurrenceData] = None

class ReminderData(BaseModel):
    """Embedded reminder in task event."""
    reminder_id: str
    trigger_at: datetime

class RecurrenceData(BaseModel):
    """Embedded recurrence in task event."""
    recurrence_id: str
    recurrence_type: str  # daily, weekly, custom
    cron_expression: Optional[str] = None
    next_occurrence: Optional[datetime] = None
```

**Example**:
```json
{
  "specversion": "1.0",
  "id": "evt-abc-123",
  "source": "/backend/tasks",
  "type": "com.todo.task.created",
  "time": "2026-01-20T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "task-xyz-456",
    "user_id": "user-123",
    "title": "Review PR",
    "description": "Review the Dapr integration PR",
    "status": "pending",
    "priority": "high",
    "tags": ["code-review", "dapr"],
    "due_date": "2026-01-21T18:00:00Z",
    "created_at": "2026-01-20T10:30:00Z",
    "reminders": [
      {
        "reminder_id": "rem-001",
        "trigger_at": "2026-01-21T17:00:00Z"
      }
    ],
    "recurrence": null
  }
}
```

---

### 2.3 TaskUpdated Event

**Type**: `com.todo.task.updated`
**Source**: `/backend/tasks`
**Topic**: `tasks`

```python
class FieldChange(BaseModel):
    """Represents a single field change."""
    old_value: Any
    new_value: Any

class TaskUpdatedData(BaseModel):
    """Payload for TaskUpdated event."""
    task_id: str
    user_id: str
    updated_at: datetime
    changes: Dict[str, FieldChange]
```

**Example**:
```json
{
  "specversion": "1.0",
  "id": "evt-def-456",
  "source": "/backend/tasks",
  "type": "com.todo.task.updated",
  "time": "2026-01-20T11:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "task-xyz-456",
    "user_id": "user-123",
    "updated_at": "2026-01-20T11:00:00Z",
    "changes": {
      "priority": {
        "old_value": "high",
        "new_value": "medium"
      },
      "tags": {
        "old_value": ["code-review", "dapr"],
        "new_value": ["code-review", "dapr", "urgent"]
      }
    }
  }
}
```

---

### 2.4 TaskCompleted Event

**Type**: `com.todo.task.completed`
**Source**: `/backend/tasks`
**Topic**: `tasks`

```python
class TaskCompletedData(BaseModel):
    """Payload for TaskCompleted event."""
    task_id: str
    user_id: str
    completed_at: datetime
```

**Example**:
```json
{
  "specversion": "1.0",
  "id": "evt-ghi-789",
  "source": "/backend/tasks",
  "type": "com.todo.task.completed",
  "time": "2026-01-20T14:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "task-xyz-456",
    "user_id": "user-123",
    "completed_at": "2026-01-20T14:00:00Z"
  }
}
```

---

### 2.5 TaskDeleted Event

**Type**: `com.todo.task.deleted`
**Source**: `/backend/tasks`
**Topic**: `tasks`

```python
class TaskDeletedData(BaseModel):
    """Payload for TaskDeleted event."""
    task_id: str
    user_id: str
```

**Example**:
```json
{
  "specversion": "1.0",
  "id": "evt-jkl-012",
  "source": "/backend/tasks",
  "type": "com.todo.task.deleted",
  "time": "2026-01-20T15:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "task-xyz-456",
    "user_id": "user-123"
  }
}
```

---

### 2.6 ReminderTriggered Event

**Type**: `com.todo.reminder.triggered`
**Source**: `/scheduler/reminders`
**Topic**: `notifications`

```python
class ReminderTriggeredData(BaseModel):
    """Payload for ReminderTriggered event."""
    reminder_id: str
    task_id: str
    user_id: str
    task_title: str
    due_date: Optional[datetime] = None
    triggered_at: datetime
```

**Example**:
```json
{
  "specversion": "1.0",
  "id": "evt-mno-345",
  "source": "/scheduler/reminders",
  "type": "com.todo.reminder.triggered",
  "time": "2026-01-21T17:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "reminder_id": "rem-001",
    "task_id": "task-xyz-456",
    "user_id": "user-123",
    "task_title": "Review PR",
    "due_date": "2026-01-21T18:00:00Z",
    "triggered_at": "2026-01-21T17:00:00Z"
  }
}
```

---

### 2.7 RecurringTaskScheduled Event

**Type**: `com.todo.recurring.scheduled`
**Source**: `/scheduler/recurring`
**Topic**: `tasks`

```python
class RecurringTaskScheduledData(BaseModel):
    """Payload for RecurringTaskScheduled event."""
    source_task_id: str  # Original recurring task
    new_task_id: str     # Newly created instance
    user_id: str
    title: str
    recurrence_type: str
    scheduled_for: datetime
```

**Example**:
```json
{
  "specversion": "1.0",
  "id": "evt-pqr-678",
  "source": "/scheduler/recurring",
  "type": "com.todo.recurring.scheduled",
  "time": "2026-01-21T09:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "source_task_id": "task-recurring-001",
    "new_task_id": "task-instance-001",
    "user_id": "user-123",
    "title": "Daily standup notes",
    "recurrence_type": "daily",
    "scheduled_for": "2026-01-21T09:00:00Z"
  }
}
```

---

## 3. State Store Schemas (Dapr)

The Scheduler service uses Dapr State Store (Redis) for managing schedules and reminders.

### 3.1 Recurring Task State

**Key Pattern**: `recurring:{task_id}`

```python
class RecurringTaskState(BaseModel):
    """State stored for recurring tasks."""
    task_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    priority: str
    tags: List[str] = []
    recurrence_type: str  # daily, weekly, custom
    cron_expression: Optional[str] = None
    next_occurrence: datetime
    last_scheduled: Optional[datetime] = None
    created_from_event_id: str  # For idempotency
```

**Example Redis Key-Value**:
```
Key: recurring:task-recurring-001
Value: {
  "task_id": "task-recurring-001",
  "user_id": "user-123",
  "title": "Daily standup notes",
  "description": "Write notes from daily standup",
  "priority": "medium",
  "tags": ["meeting", "daily"],
  "recurrence_type": "daily",
  "cron_expression": null,
  "next_occurrence": "2026-01-22T09:00:00Z",
  "last_scheduled": "2026-01-21T09:00:00Z",
  "created_from_event_id": "evt-abc-123"
}
```

---

### 3.2 Reminder State

**Key Pattern**: `reminder:{reminder_id}`

```python
class ReminderState(BaseModel):
    """State stored for reminders."""
    reminder_id: str
    task_id: str
    user_id: str
    task_title: str
    trigger_at: datetime
    due_date: Optional[datetime] = None
    fired: bool = False
    cancelled: bool = False
    created_from_event_id: str  # For idempotency
```

**Example Redis Key-Value**:
```
Key: reminder:rem-001
Value: {
  "reminder_id": "rem-001",
  "task_id": "task-xyz-456",
  "user_id": "user-123",
  "task_title": "Review PR",
  "trigger_at": "2026-01-21T17:00:00Z",
  "due_date": "2026-01-21T18:00:00Z",
  "fired": false,
  "cancelled": false,
  "created_from_event_id": "evt-abc-123"
}
```

---

### 3.3 Processed Event State (Idempotency)

**Key Pattern**: `processed:{service}:{event_id}`

```python
class ProcessedEventState(BaseModel):
    """State stored for processed events (idempotency)."""
    event_id: str
    event_type: str
    processed_at: datetime
```

**TTL**: 24 hours (automatic cleanup)

**Example Redis Key-Value**:
```
Key: processed:scheduler:evt-abc-123
Value: {
  "event_id": "evt-abc-123",
  "event_type": "com.todo.task.created",
  "processed_at": "2026-01-20T10:30:05Z"
}
TTL: 86400 seconds
```

---

## 4. Entity Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐         ┌─────────────┐                    │
│  │    User     │         │    Task     │                    │
│  │ (external)  │─────────│             │                    │
│  └─────────────┘  1:N    │  - id       │                    │
│                          │  - user_id  │                    │
│                          │  - title    │                    │
│                          │  - status   │                    │
│                          │  - priority │                    │
│                          │  - tags     │                    │
│                          │  - due_date │                    │
│                          └──────┬──────┘                    │
│                                 │                            │
│                    ┌────────────┼────────────┐              │
│                    │            │            │              │
│                    │ 1:N        │ 1:1        │              │
│                    ▼            ▼            │              │
│            ┌─────────────┐  ┌─────────────┐  │              │
│            │  Reminder   │  │ Recurrence  │  │              │
│            │             │  │             │  │              │
│            │ - id        │  │ - id        │  │              │
│            │ - task_id   │  │ - task_id   │  │              │
│            │ - trigger_at│  │ - type      │  │              │
│            │ - fired     │  │ - cron_expr │  │              │
│            │ - cancelled │  │ - next_occ  │  │              │
│            └─────────────┘  └─────────────┘  │              │
│                                              │              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Dapr State Store (Redis)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  recurring:{task_id}  ──────────────────────────────────────│
│    └─ RecurringTaskState                                    │
│                                                              │
│  reminder:{reminder_id}  ───────────────────────────────────│
│    └─ ReminderState                                         │
│                                                              │
│  processed:{service}:{event_id}  ───────────────────────────│
│    └─ ProcessedEventState (TTL: 24h)                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Validation Rules

### 5.1 Task Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| `title` | 1-200 characters | "Title must be between 1 and 200 characters" |
| `description` | 0-2000 characters | "Description must not exceed 2000 characters" |
| `status` | Must be valid enum | "Invalid status value" |
| `priority` | Must be valid enum | "Invalid priority value" |
| `tags` | Max 10 tags, each max 50 chars | "Maximum 10 tags allowed, each up to 50 characters" |
| `due_date` | Must be in future (for new tasks) | "Due date must be in the future" |

### 5.2 Reminder Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| `trigger_at` | Must be before task due_date | "Reminder must be before task due date" |
| `trigger_at` | Must be in future | "Reminder time must be in the future" |
| Per task | Max 5 reminders | "Maximum 5 reminders per task" |

### 5.3 Recurrence Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| `recurrence_type` | Must be valid enum | "Invalid recurrence type" |
| `cron_expression` | Required if type=custom | "Cron expression required for custom recurrence" |
| `cron_expression` | Must be valid cron syntax | "Invalid cron expression" |
| Per task | Only one recurrence | "Task can only have one recurrence schedule" |

---

## 6. State Transitions

### 6.1 Task Status Transitions

```
                    ┌───────────────┐
                    │    PENDING    │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
     ┌────────────────┐          ┌───────────────┐
     │  IN_PROGRESS   │          │   COMPLETED   │
     └───────┬────────┘          └───────────────┘
              │                           ▲
              └───────────────────────────┘

Valid Transitions:
- PENDING → IN_PROGRESS
- PENDING → COMPLETED
- IN_PROGRESS → COMPLETED
- IN_PROGRESS → PENDING (revert)

Invalid Transitions:
- COMPLETED → any (task is final)
```

### 6.2 Reminder State Transitions

```
     ┌───────────────┐
     │    PENDING    │  (fired=false, cancelled=false)
     └───────┬───────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌───────────┐
│  FIRED  │    │ CANCELLED │
└─────────┘    └───────────┘
(fired=true)   (cancelled=true)

Triggers:
- PENDING → FIRED: Cron trigger at trigger_at time
- PENDING → CANCELLED: Task completed or deleted
```

### 6.3 Recurrence State Transitions

```
     ┌───────────────┐
     │    ACTIVE     │  (active=true)
     └───────┬───────┘
             │
             │ (task completed or deleted)
             ▼
     ┌───────────────┐
     │   INACTIVE    │  (active=false)
     └───────────────┘

Active Behavior:
- Cron trigger checks next_occurrence
- If now >= next_occurrence:
  1. Create new task instance
  2. Calculate new next_occurrence
  3. Update state
```

---

## 7. Migration Script

**Migration Name**: `add_task_extensions.py`

```sql
-- Add new columns to tasks table
ALTER TABLE tasks
ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'medium',
ADD COLUMN tags JSONB NOT NULL DEFAULT '[]',
ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT NOW();

-- Create index for tags (GIN for JSONB array queries)
CREATE INDEX idx_tasks_tags ON tasks USING GIN (tags);

-- Create index for priority
CREATE INDEX idx_tasks_priority ON tasks (priority);

-- Create reminders table
CREATE TABLE reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    trigger_at TIMESTAMP NOT NULL,
    fired BOOLEAN NOT NULL DEFAULT false,
    cancelled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reminders_task_id ON reminders (task_id);
CREATE INDEX idx_reminders_trigger_at ON reminders (trigger_at);
CREATE INDEX idx_reminders_pending ON reminders (fired, cancelled) WHERE fired = false AND cancelled = false;

-- Create recurrences table
CREATE TABLE recurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE UNIQUE,
    recurrence_type VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    next_occurrence TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recurrences_task_id ON recurrences (task_id);
CREATE INDEX idx_recurrences_next_occurrence ON recurrences (next_occurrence);
CREATE INDEX idx_recurrences_active ON recurrences (active);
```

---

**Data Model Status**: Complete. Ready for API contract generation.

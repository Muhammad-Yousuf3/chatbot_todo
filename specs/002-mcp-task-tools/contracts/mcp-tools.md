# MCP Tool Contracts: Task Management

**Feature Branch**: `002-mcp-task-tools`
**Date**: 2026-01-03
**MCP SDK Version**: >=1.25,<2

## Overview

This document defines the contracts for all MCP tools that manage todo tasks. These tools are the **only** interface through which AI agents can interact with task data.

## Common Types

### ToolResult (Base Response)

All tools return a structured response conforming to this schema:

```json
{
  "success": boolean,
  "data": object | array | null,
  "error": string | null,
  "error_code": string | null
}
```

**Error Codes**:
| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed (missing/invalid fields) |
| `NOT_FOUND` | Task with given ID does not exist |
| `ACCESS_DENIED` | User does not own the task |
| `DATABASE_ERROR` | Database operation failed |

### TaskData (Task Object)

```json
{
  "id": "uuid-string",
  "description": "string (max 1000 chars)",
  "status": "pending | completed",
  "created_at": "ISO 8601 datetime",
  "completed_at": "ISO 8601 datetime | null"
}
```

---

## Tool: add_task

Creates a new task for the specified user.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "The authenticated user's ID (externally provided)"
    },
    "description": {
      "type": "string",
      "description": "Task description text",
      "minLength": 1,
      "maxLength": 1000
    }
  },
  "required": ["user_id", "description"]
}
```

### Output Schema

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Buy groceries",
    "status": "pending",
    "created_at": "2026-01-03T10:30:00Z",
    "completed_at": null
  },
  "error": null,
  "error_code": null
}
```

### Error Cases

| Condition | Response |
|-----------|----------|
| Empty description | `{"success": false, "error": "Description cannot be empty", "error_code": "VALIDATION_ERROR"}` |
| Description too long | `{"success": false, "error": "Description exceeds 1000 characters", "error_code": "VALIDATION_ERROR"}` |
| Missing user_id | `{"success": false, "error": "user_id is required", "error_code": "VALIDATION_ERROR"}` |

### Behavior

- Creates task with status "pending"
- Sets created_at to current timestamp
- Sets completed_at to null
- Returns the created task with its new ID

---

## Tool: list_tasks

Returns all tasks belonging to the specified user.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "The authenticated user's ID (externally provided)"
    }
  },
  "required": ["user_id"]
}
```

### Output Schema

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "description": "Buy groceries",
      "status": "pending",
      "created_at": "2026-01-03T10:30:00Z",
      "completed_at": null
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "description": "Call mom",
      "status": "completed",
      "created_at": "2026-01-02T08:00:00Z",
      "completed_at": "2026-01-02T14:30:00Z"
    }
  ],
  "error": null,
  "error_code": null
}
```

### Error Cases

| Condition | Response |
|-----------|----------|
| Missing user_id | `{"success": false, "error": "user_id is required", "error_code": "VALIDATION_ERROR"}` |

### Behavior

- Returns all tasks owned by user_id
- Tasks sorted by created_at descending (newest first)
- Returns empty array if user has no tasks (not an error)
- Only returns tasks owned by the specified user

---

## Tool: update_task

Modifies the description of an existing task.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "The authenticated user's ID (externally provided)"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The task ID to update"
    },
    "description": {
      "type": "string",
      "description": "New task description text",
      "minLength": 1,
      "maxLength": 1000
    }
  },
  "required": ["user_id", "task_id", "description"]
}
```

### Output Schema

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Buy groceries and milk",
    "status": "pending",
    "created_at": "2026-01-03T10:30:00Z",
    "completed_at": null
  },
  "error": null,
  "error_code": null
}
```

### Error Cases

| Condition | Response |
|-----------|----------|
| Task not found | `{"success": false, "error": "Task not found", "error_code": "NOT_FOUND"}` |
| User doesn't own task | `{"success": false, "error": "Access denied", "error_code": "ACCESS_DENIED"}` |
| Empty description | `{"success": false, "error": "Description cannot be empty", "error_code": "VALIDATION_ERROR"}` |
| Description too long | `{"success": false, "error": "Description exceeds 1000 characters", "error_code": "VALIDATION_ERROR"}` |
| Invalid task_id format | `{"success": false, "error": "Invalid task_id format", "error_code": "VALIDATION_ERROR"}` |

### Behavior

- Only modifies description field
- Does NOT modify status (use complete_task for that)
- Verifies ownership before update
- Returns the updated task

---

## Tool: complete_task

Marks a task as completed.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "The authenticated user's ID (externally provided)"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The task ID to complete"
    }
  },
  "required": ["user_id", "task_id"]
}
```

### Output Schema

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Buy groceries",
    "status": "completed",
    "created_at": "2026-01-03T10:30:00Z",
    "completed_at": "2026-01-03T15:45:00Z"
  },
  "error": null,
  "error_code": null
}
```

### Error Cases

| Condition | Response |
|-----------|----------|
| Task not found | `{"success": false, "error": "Task not found", "error_code": "NOT_FOUND"}` |
| User doesn't own task | `{"success": false, "error": "Access denied", "error_code": "ACCESS_DENIED"}` |
| Invalid task_id format | `{"success": false, "error": "Invalid task_id format", "error_code": "VALIDATION_ERROR"}` |

### Behavior

- Sets status to "completed"
- Sets completed_at to current timestamp
- **Idempotent**: Completing an already completed task returns success (no error, no duplicate timestamp update)
- Verifies ownership before update
- Returns the completed task

---

## Tool: delete_task

Permanently removes a task.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "The authenticated user's ID (externally provided)"
    },
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "The task ID to delete"
    }
  },
  "required": ["user_id", "task_id"]
}
```

### Output Schema

```json
{
  "success": true,
  "data": null,
  "error": null,
  "error_code": null
}
```

### Error Cases

| Condition | Response |
|-----------|----------|
| User doesn't own task | `{"success": false, "error": "Access denied", "error_code": "ACCESS_DENIED"}` |
| Invalid task_id format | `{"success": false, "error": "Invalid task_id format", "error_code": "VALIDATION_ERROR"}` |

### Behavior

- Permanently deletes the task from database
- **Idempotent**: Deleting a non-existent task returns success (no error)
- Verifies ownership before delete (if task exists)
- Returns success with null data

---

## Security Guarantees

1. **Ownership Enforcement**: Every tool validates that user_id matches the task's owner before any operation
2. **No Direct Database Access**: AI agents cannot bypass MCP tools to access the database
3. **Input Validation**: All inputs are validated before any database operation
4. **Stateless Operations**: Each tool call is independent; no state is maintained between calls
5. **Auditable**: Each tool invocation can be traced with tool name, user_id, task_id, and result

## Implementation Notes

### FastMCP Tool Definition Pattern

```python
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel

mcp = FastMCP("task-tools")

class ToolResult(BaseModel):
    success: bool
    data: dict | list | None = None
    error: str | None = None
    error_code: str | None = None

@mcp.tool()
async def add_task(user_id: str, description: str, ctx: Context) -> ToolResult:
    """Create a new task for the specified user.

    Args:
        user_id: The authenticated user's ID
        description: Task description (1-1000 characters)

    Returns:
        ToolResult with the created task data
    """
    # Implementation
    pass
```

### Database Session Pattern

```python
from sqlmodel.ext.asyncio.session import AsyncSession

async with AsyncSession(engine) as session:
    # All database operations within session
    # Commit on success, rollback on error
```

# API Usage Patterns for UI Enablement

**Feature**: UI Enablement for Intermediate & Advanced Features
**Date**: 2026-01-24

## Overview

This document describes how the frontend will use existing backend API endpoints with extended request payloads. **No API endpoint modifications are required** - the backend already supports all fields. This document serves as a reference for frontend developers implementing the UI components.

---

## Endpoints Used

### 1. GET /api/tasks - List Tasks with Filters and Sorting

**Purpose**: Retrieve filtered and sorted task list

**Query Parameters** (all optional):

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | enum | Filter by pending/completed | `?status=pending` |
| `priority` | enum | Filter by low/medium/high | `?priority=high` |
| `tag` | string | Filter by tag (contains) | `?tag=urgent` |
| `search` | string | Search title/description | `?search=report` |
| `due_before` | datetime | Tasks due before date | `?due_before=2026-02-01T00:00:00Z` |
| `due_after` | datetime | Tasks due after date | `?due_after=2026-01-25T00:00:00Z` |
| `sort_by` | enum | Sort field | `?sort_by=due_date` |
| `sort_order` | enum | Sort order (asc/desc) | `?sort_order=asc` |
| `limit` | integer | Max items (1-1000) | `?limit=50` |
| `offset` | integer | Skip items (pagination) | `?offset=0` |

**Sort Options**:
- `due_date`: Sort by task due date
- `priority`: Sort by priority (high > medium > low)
- `title`: Sort alphabetically by title
- `created_at`: Sort by creation date (default)

**Multiple Filters**: Combine with `&`
```
GET /api/tasks?status=pending&priority=high&sort_by=due_date&sort_order=asc
```

**Response**:
```typescript
{
  "tasks": Task[],  // Array of task objects with all fields
  "total": number   // Total count (for pagination)
}
```

**Frontend Usage**:
```typescript
// In useTasks hook
const queryString = buildQueryString({
  status,
  priority,
  tag,
  sort_by: sortBy,
  sort_order: sortOrder,
});

const { data } = useSWR(`/api/tasks?${queryString}`, fetcher);
```

---

### 2. POST /api/tasks - Create Task with All Fields

**Purpose**: Create new task with priority, tags, description, due date, recurrence, and reminders

**Request Body**:
```typescript
{
  "title": string,                 // Required, 1-200 chars
  "description"?: string | null,    // Optional, max 2000 chars
  "priority"?: "low" | "medium" | "high",  // Optional, default: "medium"
  "tags"?: string[],                // Optional, max 10 tags, each max 50 chars
  "due_date"?: string | null,       // Optional, ISO 8601 datetime
  "reminders"?: [                   // Optional, max 5 reminders
    {
      "trigger_at": string          // ISO 8601 datetime
    }
  ],
  "recurrence"?: {                  // Optional
    "recurrence_type": "daily" | "weekly" | "custom",
    "cron_expression"?: string | null  // Required if type is "custom"
  }
}
```

**Example - Basic Task** (P1 features only):
```json
{
  "title": "Review PR #123",
  "description": "Check implementation and test coverage",
  "priority": "high",
  "tags": ["code-review", "urgent"],
  "due_date": "2026-01-26T17:00:00Z"
}
```

**Example - Task with Recurrence** (P2 features):
```json
{
  "title": "Team standup",
  "priority": "medium",
  "tags": ["meeting"],
  "due_date": "2026-01-27T09:00:00Z",
  "recurrence": {
    "recurrence_type": "weekly"
  }
}
```

**Example - Task with Reminders** (P3 features):
```json
{
  "title": "Submit quarterly report",
  "description": "Include Q4 metrics and projections",
  "priority": "high",
  "due_date": "2026-02-01T17:00:00Z",
  "reminders": [
    { "trigger_at": "2026-02-01T09:00:00Z" },
    { "trigger_at": "2026-01-31T17:00:00Z" }
  ]
}
```

**Example - Custom Recurrence** (advanced):
```json
{
  "title": "Database backup",
  "recurrence": {
    "recurrence_type": "custom",
    "cron_expression": "0 2 * * *"
  }
}
```

**Response** (201 Created):
```typescript
{
  "id": string,
  "title": string,
  "description": string | null,
  "status": "pending",
  "priority": TaskPriority,
  "tags": string[],
  "due_date": string | null,
  "created_at": string,
  "updated_at": string,
  "completed_at": null,
  "reminders": Reminder[],
  "recurrence": Recurrence | null
}
```

**Frontend Usage**:
```typescript
const createTask = async (formState: TaskFormState) => {
  const requestBody = formStateToCreateRequest(formState);
  const response = await apiClient.post('/api/tasks', requestBody);
  return response;
};
```

---

### 3. PATCH /api/tasks/{task_id} - Update Task

**Purpose**: Update existing task fields (all fields optional)

**Request Body** (all fields optional):
```typescript
{
  "title"?: string,
  "description"?: string | null,
  "status"?: "pending" | "completed",
  "priority"?: "low" | "medium" | "high",
  "tags"?: string[],
  "due_date"?: string | null,
  "reminders"?: ReminderCreate[],    // Replaces all existing reminders
  "recurrence"?: RecurrenceCreate    // Replaces existing recurrence
}
```

**Important Notes**:
- **Reminders**: Sending `reminders` array **replaces** all existing reminders (not append)
- **Recurrence**: Sending `recurrence` **replaces** existing recurrence
- To remove reminders: Send `"reminders": []`
- To remove recurrence: Send `"recurrence": null`
- Omitted fields are not modified

**Example - Update Priority Only**:
```json
{
  "priority": "high"
}
```

**Example - Update Tags and Add Reminder**:
```json
{
  "tags": ["urgent", "backend", "api"],
  "reminders": [
    { "trigger_at": "2026-01-25T10:00:00Z" }
  ]
}
```

**Example - Remove Recurrence**:
```json
{
  "recurrence": null
}
```

**Response** (200 OK):
```typescript
{
  // Updated task object with all fields
}
```

**Frontend Usage**:
```typescript
const updateTask = async (taskId: string, updates: Partial<TaskFormState>) => {
  const requestBody = formStateToUpdateRequest(updates);
  const response = await apiClient.patch(`/api/tasks/${taskId}`, requestBody);
  return response;
};
```

---

## Validation Error Handling

### Client-Side Validation (Before API Call)

Validate form state before making API request:

```typescript
const errors = validateTaskForm(formState);
if (Object.keys(errors).length > 0) {
  setFormErrors(errors);
  return; // Don't submit
}
```

### Server-Side Validation (API Errors)

Handle validation errors from backend:

```typescript
try {
  await createTask(formState);
} catch (error) {
  if (error instanceof ApiClientError) {
    // Parse error message and map to form fields
    if (error.status === 422) {
      // Validation error
      setFormErrors({
        // Extract field from error message or use generic error
        title: error.message
      });
    } else if (error.status === 400) {
      // Bad request (e.g., invalid cron expression)
      setFormErrors({
        cron_expression: error.message
      });
    }
  }
}
```

**Common Validation Errors**:

| Error | Status | Field | Message |
|-------|--------|-------|---------|
| Title required | 422 | title | "field required" |
| Title too long | 422 | title | "ensure this value has at most 200 characters" |
| Too many tags | 422 | tags | "Maximum 10 tags allowed" |
| Tag too long | 422 | tags | "Each tag must be 50 characters or less" |
| Too many reminders | 422 | reminders | "Maximum 5 reminders per task" |
| Invalid cron | 400 | cron_expression | "Invalid cron expression" |
| Missing cron for custom | 422 | cron_expression | "cron_expression is required for custom recurrence type" |

---

## DateTime Format Handling

### Frontend → Backend

**Input**: User selects date/time in browser's local timezone via `<input type="datetime-local">`

**Output**: Convert to ISO 8601 UTC string

```typescript
// HTML5 datetime-local gives: "2026-01-26T14:30"
const localDateTime = "2026-01-26T14:30";

// Convert to Date object (interprets as local timezone)
const date = new Date(localDateTime);

// Convert to ISO 8601 UTC string
const isoString = date.toISOString(); // "2026-01-26T19:30:00.000Z"

// Send to API
const requestBody = {
  due_date: isoString
};
```

### Backend → Frontend

**Input**: ISO 8601 UTC string from API

**Output**: Display in user's local timezone

```typescript
// From API: "2026-01-26T19:30:00Z"
const utcDateTime = task.due_date;

// For datetime-local input (requires format: "YYYY-MM-DDTHH:mm")
const date = new Date(utcDateTime);
const localDateTimeString = date.toISOString().slice(0, 16);
// Result: "2026-01-26T14:30" (in user's local timezone)

// For display (formatted)
const displayString = date.toLocaleString('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit'
});
// Result: "Jan 26, 2026, 2:30 PM"
```

---

## Query String Building

### Helper Function

```typescript
/**
 * Build query string from task query params
 * Omits undefined/null values
 */
export function buildTaskQueryString(params: TaskQueryParams): string {
  const searchParams = new URLSearchParams();

  if (params.status) searchParams.append('status', params.status);
  if (params.priority) searchParams.append('priority', params.priority);
  if (params.tag) searchParams.append('tag', params.tag);
  if (params.search) searchParams.append('search', params.search);
  if (params.due_before) searchParams.append('due_before', params.due_before);
  if (params.due_after) searchParams.append('due_after', params.due_after);
  if (params.sort_by) searchParams.append('sort_by', params.sort_by);
  if (params.sort_order) searchParams.append('sort_order', params.sort_order);
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());

  return searchParams.toString();
}

// Usage
const queryString = buildTaskQueryString({
  status: 'pending',
  priority: 'high',
  sort_by: 'due_date',
  sort_order: 'asc'
});
// Result: "status=pending&priority=high&sort_by=due_date&sort_order=asc"
```

---

## Example API Calls

### Create Task with All P1 Features

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Update documentation",
    "description": "Add examples for new API endpoints",
    "priority": "medium",
    "tags": ["docs", "api"],
    "due_date": "2026-01-28T17:00:00Z"
  }'
```

### Get High-Priority Tasks Sorted by Due Date

```bash
curl -X GET "http://localhost:8000/api/tasks?status=pending&priority=high&sort_by=due_date&sort_order=asc" \
  -H "Authorization: Bearer <token>"
```

### Update Task to Add Weekly Recurrence

```bash
curl -X PATCH http://localhost:8000/api/tasks/abc-123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "recurrence": {
      "recurrence_type": "weekly"
    }
  }'
```

---

## SWR Integration Pattern

### Hook Signature Update

```typescript
// Current
function useTasks(status?: TaskStatus)

// New
function useTasks(params?: TaskQueryParams)
```

### Implementation

```typescript
export function useTasks(params: TaskQueryParams = {}) {
  const queryString = buildTaskQueryString(params);
  const key = queryString ? `/api/tasks?${queryString}` : '/api/tasks';

  const { data, error, mutate } = useSWR<TaskListResponse>(
    key,
    (url) => apiClient.getTasks(url)
  );

  return {
    tasks: data?.tasks || [],
    total: data?.total || 0,
    isLoading: !error && !data,
    isError: error,
    mutate
  };
}
```

### Usage in Component

```typescript
const [sortBy, setSortBy] = useState<'due_date' | 'priority'>('created_at');
const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
const [priority, setPriority] = useState<TaskPriority | undefined>();

const { tasks, isLoading } = useTasks({
  status: 'pending',
  priority,
  sort_by: sortBy,
  sort_order: sortOrder
});

// SWR automatically refetches when key (queryString) changes
```

---

## Authorization

All API requests require JWT authentication:

```typescript
// Set token after login
apiClient.setAccessToken(authResponse.access_token);

// Token is automatically included in requests
// Header: Authorization: Bearer <token>
```

---

## Summary

- **No API changes needed** - backend already supports all fields
- Frontend uses existing POST/PATCH/GET endpoints with extended payloads
- All new fields are optional - backward compatible
- Validation happens client-side (for UX) and server-side (for security)
- DateTime values always use ISO 8601 format
- Query parameters enable filtering and sorting without new endpoints

# API Contracts: Midnight AI Glass UI Theme

**Feature**: 011-midnight-glass-ui
**Date**: 2026-01-25
**Status**: N/A (UI-only feature)

## Overview

This feature is a **UI-only enhancement**. No new API endpoints or contract changes are required.

## Existing Contracts (Unchanged)

The following existing API contracts remain **unchanged** and continue to be used by the updated UI:

### Task Endpoints
- `GET /api/tasks` - List tasks with query params
- `POST /api/tasks` - Create task
- `GET /api/tasks/:id` - Get single task
- `PATCH /api/tasks/:id` - Update task
- `POST /api/tasks/:id/complete` - Mark complete
- `DELETE /api/tasks/:id` - Delete task

### Chat Endpoints
- `POST /api/chat` - Send chat message, receive AI response

### Query Parameters (Tasks)
```typescript
interface TaskQueryParams {
  status?: 'pending' | 'completed';
  priority?: 'low' | 'medium' | 'high';
  tag?: string;
  search?: string;
  due_before?: string;  // ISO date
  due_after?: string;   // ISO date
  sort_by?: 'due_date' | 'priority' | 'title' | 'created_at';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}
```

## Why No API Changes

Per the feature specification:
- **FR-009**: System MUST NOT modify any backend API calls, request/response formats, or authentication logic

The UI enhancement:
1. Uses existing task fields (title, description, priority, tags, due_date, reminders, recurrence)
2. Uses existing filter/sort query parameters
3. Uses existing chat message structure
4. Makes no new backend requests

## Frontend API Client

The existing API client at `frontend/lib/api.ts` requires no modifications. All calls continue to work as before with the enhanced UI.

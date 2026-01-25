# Phase 1: Data Model & TypeScript Types

**Feature**: UI Enablement for Intermediate & Advanced Features
**Date**: 2026-01-24

## Overview

This document defines the TypeScript types and interfaces needed for the UI enablement feature. Since this is a frontend-only feature, the data model consists of type extensions to support new request payloads and enhanced component props.

## Type Extensions

### Request Payload Types (NEW)

These types are needed to support creating/updating tasks with reminders and recurrence from the UI.

```typescript
/**
 * Reminder creation payload for task API requests
 */
export interface ReminderCreate {
  trigger_at: string; // ISO 8601 datetime string
}

/**
 * Recurrence configuration payload for task API requests
 */
export interface RecurrenceCreate {
  recurrence_type: RecurrenceType; // 'daily' | 'weekly' | 'custom'
  cron_expression?: string | null; // Required when type is 'custom'
}
```

### Extended Task Request Types (MODIFY)

Update existing `TaskCreateRequest` and `TaskUpdateRequest` to include new fields:

```typescript
/**
 * Task creation request payload (EXTENDED)
 * Existing fields + new reminder and recurrence support
 */
export interface TaskCreateRequest {
  title: string;                     // EXISTING: 1-200 chars (required)
  description?: string | null;        // EXISTING: 0-2000 chars (optional)
  priority?: TaskPriority;            // EXISTING: 'low' | 'medium' | 'high'
  tags?: string[];                    // EXISTING: max 10, each max 50 chars
  due_date?: string | null;           // EXISTING: ISO 8601 datetime
  reminders?: ReminderCreate[];       // NEW: max 5 reminders
  recurrence?: RecurrenceCreate;      // NEW: optional recurrence schedule
}

/**
 * Task update request payload (EXTENDED)
 * All fields optional, includes reminder and recurrence
 */
export interface TaskUpdateRequest {
  title?: string;                     // EXISTING: 1-200 chars
  description?: string | null;        // EXISTING: 0-2000 chars
  status?: TaskStatus;                // EXISTING: 'pending' | 'completed'
  priority?: TaskPriority;            // EXISTING: 'low' | 'medium' | 'high'
  tags?: string[];                    // EXISTING: max 10, each max 50 chars
  due_date?: string | null;           // EXISTING: ISO 8601 datetime
  reminders?: ReminderCreate[];       // NEW: replaces existing reminders
  recurrence?: RecurrenceCreate;      // NEW: replaces existing recurrence
}
```

**Note**: Response types (`Task`, `Reminder`, `Recurrence`) already exist and don't need modification.

---

## Component Props Interfaces

### Form Component Props

```typescript
/**
 * Props for basic task form fields (priority, tags, description)
 */
export interface TaskFormBasicProps {
  priority: TaskPriority;
  onPriorityChange: (priority: TaskPriority) => void;

  tags: string[];
  onTagsChange: (tags: string[]) => void;

  description: string;
  onDescriptionChange: (description: string) => void;

  errors?: {
    priority?: string;
    tags?: string;
    description?: string;
  };
}

/**
 * Props for advanced task form fields (recurrence, reminders)
 */
export interface TaskFormAdvancedProps {
  recurrence: RecurrenceCreate | null;
  onRecurrenceChange: (recurrence: RecurrenceCreate | null) => void;

  reminders: ReminderCreate[];
  onRemindersChange: (reminders: ReminderCreate[]) => void;

  errors?: {
    recurrence?: string;
    reminders?: string;
  };
}

/**
 * Props for date-time picker component
 */
export interface DateTimePickerProps {
  value: string | null;              // ISO 8601 string or null
  onChange: (value: string | null) => void;
  label: string;
  withTime?: boolean;                // If true, show time input (default: true)
  min?: string;                      // Minimum date/time (optional)
  max?: string;                      // Maximum date/time (optional)
  required?: boolean;
  error?: string;
}

/**
 * Props for tag input component
 */
export interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  maxTags?: number;                  // Default: 10
  maxTagLength?: number;             // Default: 50
  placeholder?: string;
  error?: string;
}

/**
 * Props for recurrence selector component
 */
export interface RecurrenceSelectorProps {
  value: RecurrenceCreate | null;
  onChange: (value: RecurrenceCreate | null) => void;
  error?: string;
}

/**
 * Props for reminder list component
 */
export interface ReminderListProps {
  reminders: ReminderCreate[];
  onChange: (reminders: ReminderCreate[]) => void;
  maxReminders?: number;             // Default: 5
  minDateTime?: string;              // Minimum allowed reminder time (optional)
  error?: string;
}

/**
 * Props for sort controls component
 */
export interface SortControlsProps {
  sortBy: 'due_date' | 'priority' | 'title' | 'created_at';
  sortOrder: 'asc' | 'desc';
  onSortByChange: (sortBy: SortControlsProps['sortBy']) => void;
  onSortOrderChange: (sortOrder: 'asc' | 'desc') => void;
}

/**
 * Props for filter panel component
 */
export interface FilterPanelProps {
  selectedPriorities: TaskPriority[];
  onPrioritiesChange: (priorities: TaskPriority[]) => void;

  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;

  availableTags: string[];           // All tags used across tasks

  onClearFilters: () => void;
}
```

---

## Validation Error Types

```typescript
/**
 * Validation errors for task form
 * Maps field names to error messages
 */
export interface TaskFormErrors {
  title?: string;
  description?: string;
  priority?: string;
  tags?: string;
  due_date?: string;
  reminders?: string;
  recurrence?: string;
  cron_expression?: string;
}
```

---

## Query Parameter Types

```typescript
/**
 * Query parameters for task list API
 * Used by useTasks hook and API client
 */
export interface TaskQueryParams {
  status?: TaskStatus;               // Filter by status
  priority?: TaskPriority;           // Filter by priority
  tag?: string;                      // Filter by tag (contains match)
  search?: string;                   // Search in title/description
  due_before?: string;               // ISO 8601 datetime
  due_after?: string;                // ISO 8601 datetime
  sort_by?: 'due_date' | 'priority' | 'title' | 'created_at';
  sort_order?: 'asc' | 'desc';
  limit?: number;                    // Max items (1-1000, default 100)
  offset?: number;                   // Skip items (pagination)
}
```

---

## Validation Constants

```typescript
/**
 * Validation limits matching backend constraints
 */
export const VALIDATION_LIMITS = {
  TITLE_MIN_LENGTH: 1,
  TITLE_MAX_LENGTH: 200,
  DESCRIPTION_MAX_LENGTH: 2000,
  MAX_TAGS: 10,
  MAX_TAG_LENGTH: 50,
  MAX_REMINDERS: 5,
} as const;
```

---

## Helper Types

```typescript
/**
 * Form state for task creation/editing
 * Combines all form fields into single state object
 */
export interface TaskFormState {
  // Basic fields
  title: string;
  description: string;
  priority: TaskPriority;
  tags: string[];
  due_date: string | null;

  // Advanced fields
  recurrence: RecurrenceCreate | null;
  reminders: ReminderCreate[];
}

/**
 * Initial empty form state
 */
export const INITIAL_TASK_FORM_STATE: TaskFormState = {
  title: '',
  description: '',
  priority: 'medium',
  tags: [],
  due_date: null,
  recurrence: null,
  reminders: [],
};

/**
 * Convert Task to TaskFormState (for editing)
 */
export function taskToFormState(task: Task): TaskFormState {
  return {
    title: task.title,
    description: task.description || '',
    priority: task.priority,
    tags: task.tags,
    due_date: task.due_date,
    recurrence: task.recurrence ? {
      recurrence_type: task.recurrence.recurrence_type,
      cron_expression: task.recurrence.cron_expression,
    } : null,
    reminders: task.reminders.map(r => ({
      trigger_at: r.trigger_at,
    })),
  };
}

/**
 * Convert TaskFormState to TaskCreateRequest
 */
export function formStateToCreateRequest(state: TaskFormState): TaskCreateRequest {
  return {
    title: state.title.trim(),
    description: state.description.trim() || null,
    priority: state.priority,
    tags: state.tags,
    due_date: state.due_date,
    reminders: state.reminders,
    recurrence: state.recurrence,
  };
}

/**
 * Convert partial TaskFormState to TaskUpdateRequest
 */
export function formStateToUpdateRequest(state: Partial<TaskFormState>): TaskUpdateRequest {
  const request: TaskUpdateRequest = {};

  if (state.title !== undefined) request.title = state.title.trim();
  if (state.description !== undefined) request.description = state.description.trim() || null;
  if (state.priority !== undefined) request.priority = state.priority;
  if (state.tags !== undefined) request.tags = state.tags;
  if (state.due_date !== undefined) request.due_date = state.due_date;
  if (state.reminders !== undefined) request.reminders = state.reminders;
  if (state.recurrence !== undefined) request.recurrence = state.recurrence;

  return request;
}
```

---

## Entity Relationships

```
TaskFormState
├── Basic Fields (P1)
│   ├── title: string
│   ├── description: string
│   ├── priority: TaskPriority
│   ├── tags: string[]
│   └── due_date: string | null
└── Advanced Fields (P2/P3)
    ├── recurrence: RecurrenceCreate | null
    │   ├── recurrence_type: RecurrenceType
    │   └── cron_expression: string | null
    └── reminders: ReminderCreate[]
        └── trigger_at: string

TaskCreateRequest / TaskUpdateRequest
├── Same structure as TaskFormState
└── Sent to POST /api/tasks or PATCH /api/tasks/{id}

TaskResponse (existing, no changes)
├── id: string
├── Basic Fields (same as form)
└── Advanced Fields (nested objects)
    ├── recurrence: Recurrence | null
    │   ├── id: string
    │   ├── recurrence_type: RecurrenceType
    │   ├── cron_expression: string | null
    │   ├── next_occurrence: string | null
    │   ├── active: boolean
    │   └── created_at: string
    └── reminders: Reminder[]
        ├── id: string
        ├── trigger_at: string
        ├── fired: boolean
        ├── cancelled: boolean
        └── created_at: string
```

---

## Validation Rules

### Client-Side Validation

Implemented in `lib/utils.ts`:

```typescript
/**
 * Validate task form state
 * Returns validation errors or empty object if valid
 */
export function validateTaskForm(state: TaskFormState): TaskFormErrors {
  const errors: TaskFormErrors = {};

  // Title validation
  if (!state.title.trim()) {
    errors.title = 'Title is required';
  } else if (state.title.length > VALIDATION_LIMITS.TITLE_MAX_LENGTH) {
    errors.title = `Title must be ${VALIDATION_LIMITS.TITLE_MAX_LENGTH} characters or less`;
  }

  // Description validation
  if (state.description.length > VALIDATION_LIMITS.DESCRIPTION_MAX_LENGTH) {
    errors.description = `Description must be ${VALIDATION_LIMITS.DESCRIPTION_MAX_LENGTH} characters or less`;
  }

  // Tags validation
  if (state.tags.length > VALIDATION_LIMITS.MAX_TAGS) {
    errors.tags = `Maximum ${VALIDATION_LIMITS.MAX_TAGS} tags allowed`;
  }
  const invalidTag = state.tags.find(tag => tag.length > VALIDATION_LIMITS.MAX_TAG_LENGTH);
  if (invalidTag) {
    errors.tags = `Each tag must be ${VALIDATION_LIMITS.MAX_TAG_LENGTH} characters or less`;
  }

  // Reminders validation
  if (state.reminders.length > VALIDATION_LIMITS.MAX_REMINDERS) {
    errors.reminders = `Maximum ${VALIDATION_LIMITS.MAX_REMINDERS} reminders allowed`;
  }

  // Recurrence validation
  if (state.recurrence) {
    if (state.recurrence.recurrence_type === 'custom' && !state.recurrence.cron_expression) {
      errors.cron_expression = 'Cron expression is required for custom recurrence';
    }
  }

  return errors;
}
```

---

## Type Location Summary

| Type/Interface | File | Purpose |
|----------------|------|---------|
| `ReminderCreate` | `types/index.ts` | Request payload for creating reminders |
| `RecurrenceCreate` | `types/index.ts` | Request payload for recurrence config |
| `TaskCreateRequest` (extended) | `types/index.ts` | Extended with reminders and recurrence |
| `TaskUpdateRequest` (extended) | `types/index.ts` | Extended with reminders and recurrence |
| `TaskQueryParams` | `types/index.ts` | Query params for task list API |
| `TaskFormState` | `types/index.ts` | Internal form state management |
| `TaskFormErrors` | `types/index.ts` | Validation error mapping |
| Component props interfaces | `types/index.ts` or component files | Props for form components |
| `VALIDATION_LIMITS` | `lib/utils.ts` | Validation constants |
| Helper functions | `lib/utils.ts` | Form conversion and validation |

---

## Migration Notes

**Existing Code Impact**:
- `types/index.ts`: Add new types, extend existing request types
- `lib/api.ts`: Update `createTask` and `updateTask` method signatures to accept new fields
- `hooks/useTasks.ts`: Accept `TaskQueryParams` instead of just `status`
- No breaking changes: all new fields are optional in request types

**Backward Compatibility**:
- All new fields are optional in `TaskCreateRequest` and `TaskUpdateRequest`
- Existing code that creates tasks without reminders/recurrence continues to work
- Backend already supports these fields, so no API version changes needed

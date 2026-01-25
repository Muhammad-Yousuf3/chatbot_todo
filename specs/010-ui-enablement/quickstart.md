# Quickstart Guide: UI Enablement Development

**Feature**: UI Enablement for Intermediate & Advanced Features
**Branch**: `010-ui-enablement`
**Date**: 2026-01-24

## Overview

This guide helps developers get started implementing the UI enablement feature. Follow these steps to set up your environment, understand the codebase, and begin development.

---

## Prerequisites

- Node.js 20+ and npm
- TypeScript 5.6+ knowledge
- React 18+ and Next.js 14+ familiarity
- Existing backend running at `http://localhost:8000`
- Valid JWT token for API authentication

---

## Quick Start

### 1. Switch to Feature Branch

```bash
git checkout 010-ui-enablement
```

### 2. Install Dependencies (if not already installed)

```bash
cd frontend
npm install
```

All dependencies are already in `package.json`:
- React 18.3.1
- Next.js 14.2.21
- SWR 2.2.5 (data fetching)
- Tailwind CSS 3.4.17 (styling)
- TypeScript 5.6.3

### 3. Start Development Server

```bash
npm run dev
```

Frontend runs at `http://localhost:3000`

### 4. Ensure Backend is Running

```bash
cd backend
uvicorn src.main:app --reload
```

Backend runs at `http://localhost:8000`

### 5. Test Existing Functionality

- Navigate to `/tasks` page
- Create a basic task (title + due date only)
- Verify task appears in list
- This confirms baseline is working before adding features

---

## Development Workflow

### Phase 1: Type Extensions (Start Here)

**File**: `frontend/types/index.ts`

1. Add new request types:
   - `ReminderCreate`
   - `RecurrenceCreate`

2. Extend existing types:
   - `TaskCreateRequest` (add `reminders?`, `recurrence?`)
   - `TaskUpdateRequest` (add `reminders?`, `recurrence?`)

3. Add component prop interfaces (copy from `specs/010-ui-enablement/data-model.md`)

4. Add validation constants to `frontend/lib/utils.ts`

**Test**: TypeScript compilation should pass with no errors
```bash
npm run build
```

---

### Phase 2: Basic Form Components (P1 Features)

Build in this order:

#### 2.1 Tag Input Component

**File**: `frontend/components/tasks/TagInput.tsx`

**Features**:
- Add tag on Enter or comma
- Show tags as removable chips
- Validate max 10 tags, each max 50 chars
- Display validation errors

**Test**:
- Add tags by typing and pressing Enter
- Remove tags with X button
- Try to add 11th tag (should show error)
- Try to add 51-character tag (should show error)

#### 2.2 Priority Selector

**File**: `frontend/app/tasks/page.tsx` (inline in form)

**Features**:
- Dropdown or radio buttons for low/medium/high
- Default: medium
- Visual preview (color coding)

**Test**:
- Select each priority option
- Verify default is medium

#### 2.3 Description Textarea

**File**: `frontend/app/tasks/page.tsx` (inline in form)

**Features**:
- Multi-line textarea
- Character counter (2000 max)
- Auto-resize or scrollbar

**Test**:
- Type multi-line text
- Paste long text (>2000 chars)
- Verify character counter updates
- Verify validation error at 2001 chars

---

### Phase 3: Task Display Enhancements

**File**: `frontend/app/tasks/page.tsx` (TaskItem component)

Add display for new fields:
- Priority badge (high = red, low = gray)
- Tag chips
- Description text (truncate if long)

**Test**:
- Create task with all P1 fields via chatbot
- Verify task displays correctly in list

---

### Phase 4: Sort and Filter Controls (P1)

#### 4.1 Sort Controls Component

**File**: `frontend/components/tasks/SortControls.tsx`

**Features**:
- Dropdown: due_date, priority, title, created_at
- Toggle: ascending/descending

**Test**:
- Sort by each option
- Toggle order
- Verify tasks reorder correctly

#### 4.2 Filter Panel Component

**File**: `frontend/components/tasks/FilterPanel.tsx`

**Features**:
- Checkboxes for priorities (high, medium, low)
- Tag filter (dropdown of available tags)
- Clear filters button

**Test**:
- Filter by priority
- Filter by tag
- Combine filters
- Clear all filters

---

### Phase 5: Date-Time Picker (P2)

**File**: `frontend/components/tasks/DateTimePicker.tsx`

**Features**:
- HTML5 `<input type="datetime-local">`
- Convert to/from ISO 8601
- Optional time component

**Test**:
- Select date and time
- Verify ISO string sent to API
- Edit existing task with due date
- Verify time displays correctly in local timezone

---

### Phase 6: Advanced Form Components (P2/P3)

#### 6.1 Recurrence Selector

**File**: `frontend/components/tasks/RecurrenceSelector.tsx`

**Features**:
- Radio buttons: none, daily, weekly, custom
- Cron expression input (shown only for custom)
- Help text with examples

**Test**:
- Select daily recurrence
- Select weekly recurrence
- Select custom, enter cron expression
- Verify validation error if custom selected without cron

#### 6.2 Reminder List Component

**File**: `frontend/components/tasks/ReminderList.tsx`

**Features**:
- List of reminder times
- Add reminder button (datetime picker)
- Remove reminder button
- Max 5 reminders validation

**Test**:
- Add multiple reminders
- Remove reminder
- Try to add 6th reminder (should error)

---

### Phase 7: Integration

**Files**:
- `frontend/lib/api.ts`
- `frontend/hooks/useTasks.ts`

1. Update API client methods to include new fields
2. Update useTasks hook to accept query params
3. Wire form state to API calls

**Test**:
- Create task with all fields via UI
- Verify API request payload in Network tab
- Verify task saved correctly in database
- Edit task, verify updates work
- Verify sort/filter query params in API calls

---

## Testing Checklist

### Manual Testing

- [ ] Create task with priority, tags, description
- [ ] Edit task to change priority
- [ ] Add/remove tags from task
- [ ] Filter tasks by priority
- [ ] Filter tasks by tag
- [ ] Sort tasks by due date (asc/desc)
- [ ] Sort tasks by priority (asc/desc)
- [ ] Create task with due date and time
- [ ] Create task with daily recurrence
- [ ] Create task with weekly recurrence
- [ ] Create task with custom cron recurrence
- [ ] Add multiple reminders to task
- [ ] Remove reminder from task
- [ ] Verify validation errors display correctly
- [ ] Verify existing tasks (created via chatbot) display correctly
- [ ] Verify no regression in basic task creation
- [ ] Verify no console errors

### Browser Testing

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Accessibility

- [ ] Keyboard navigation works for all form fields
- [ ] Focus indicators visible
- [ ] Form labels associated with inputs
- [ ] Error messages announced (test with screen reader if possible)

---

## Common Issues & Solutions

### Issue: TypeScript errors for new types

**Solution**: Ensure all new types are exported from `types/index.ts`

### Issue: API returns 422 validation error

**Solution**: Check request payload format matches API schema. Verify:
- Field names are snake_case (e.g., `due_date` not `dueDate`)
- DateTime values are ISO 8601 strings
- Tags is an array, not comma-separated string

### Issue: Sort/filter not working

**Solution**: Check SWR cache key includes query params. Debug with:
```typescript
console.log('SWR key:', key);
```

### Issue: Date picker shows wrong timezone

**Solution**: Use `toISOString().slice(0, 16)` when setting input value

### Issue: Reminders not saving

**Solution**: Check reminders array format matches `ReminderCreate[]` type

---

## File Structure Reference

```
frontend/
├── app/tasks/page.tsx               # Main tasks page (modify)
├── components/tasks/                # New components directory
│   ├── TagInput.tsx                 # Tag chip input
│   ├── DateTimePicker.tsx           # Date+time picker
│   ├── RecurrenceSelector.tsx       # Recurrence config
│   ├── ReminderList.tsx             # Reminder management
│   ├── SortControls.tsx             # Sort dropdown
│   └── FilterPanel.tsx              # Filter checkboxes
├── hooks/useTasks.ts                # Update for query params
├── lib/api.ts                       # Update API methods
├── lib/utils.ts                     # Add validation helpers
└── types/index.ts                   # Add new types
```

---

## Component Dependencies

```
TasksPage
├── TaskForm (existing, inline)
│   ├── TagInput (new)
│   ├── DateTimePicker (new)
│   ├── RecurrenceSelector (new)
│   └── ReminderList (new)
├── SortControls (new)
├── FilterPanel (new)
└── TaskList (existing, inline)
    └── TaskItem (existing, enhance)
```

---

## API Client Usage

### Creating a Task

```typescript
import { apiClient } from '@/lib/api';
import type { TaskCreateRequest } from '@/types';

const createTask = async (formState: TaskFormState) => {
  const request: TaskCreateRequest = {
    title: formState.title.trim(),
    description: formState.description.trim() || null,
    priority: formState.priority,
    tags: formState.tags,
    due_date: formState.due_date,
    reminders: formState.reminders,
    recurrence: formState.recurrence,
  };

  try {
    const task = await apiClient.post<TaskResponse>('/api/tasks', request);
    console.log('Task created:', task);
    // Refresh task list
    mutate();
  } catch (error) {
    console.error('Failed to create task:', error);
    // Handle error
  }
};
```

### Fetching with Filters

```typescript
import { useTasks } from '@/hooks/useTasks';

const { tasks, isLoading } = useTasks({
  status: 'pending',
  priority: 'high',
  sort_by: 'due_date',
  sort_order: 'asc',
});
```

---

## Debugging Tips

1. **Check Network Tab**: Verify API request/response in browser DevTools
2. **React DevTools**: Inspect component state and props
3. **Console Logging**: Add logs to track state changes
4. **SWR DevTools**: Install SWR DevTools for cache inspection
5. **TypeScript Errors**: Run `tsc --noEmit` to catch type errors

---

## Next Steps After Implementation

1. Run full manual testing checklist
2. Test in all supported browsers
3. Fix any bugs found
4. Create pull request
5. Request code review
6. Merge to main branch

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [SWR Documentation](https://swr.vercel.app/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [MDN HTML5 Input Types](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/datetime-local)
- [Crontab Guru](https://crontab.guru/) (cron expression helper)
- [Feature Specification](./spec.md)
- [API Usage Patterns](./contracts/api-extensions.md)
- [Data Model](./data-model.md)

---

## Support

For questions or issues:
1. Check this quickstart guide
2. Review specification documents in `specs/010-ui-enablement/`
3. Check existing similar components in codebase
4. Ask team for help if stuck

Happy coding! 🚀

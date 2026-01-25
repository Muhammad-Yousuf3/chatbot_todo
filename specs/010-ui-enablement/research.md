# Phase 0: Research & Technical Decisions

**Feature**: UI Enablement for Intermediate & Advanced Features
**Date**: 2026-01-24

## Research Questions & Answers

### Q1: HTML5 Date-Time Input vs Custom Picker Component

**Decision**: Use native HTML5 `<input type="datetime-local">` for date-time picker

**Rationale**:
- Native browser support in all target browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Automatically handles timezone conversion and displays in user's local time
- Consistent UX with browser's native date/time picker
- Zero additional dependencies or bundle size
- Accessibility built-in (keyboard navigation, screen reader support)
- Mobile-friendly (shows native mobile date/time pickers)

**Alternatives Considered**:
- **react-datepicker**: Popular library but adds ~50KB to bundle, requires additional styling, more complex API
- **@mui/x-date-pickers**: Material-UI date pickers - heavy dependency (~200KB), requires @mui/material peer dependency
- **Custom implementation**: Unnecessary complexity for standard date/time selection

**Implementation Notes**:
- Format datetime value as ISO 8601 string (YYYY-MM-DDTHH:mm) for input value
- Convert to full ISO string with seconds when sending to API (YYYY-MM-DDTHH:mm:ss)
- Handle empty time (date-only) by using type="date" fallback or allowing null time component

---

### Q2: Tag Input Pattern (Comma-Separated vs Chip Input)

**Decision**: Implement custom chip input component with visual tag badges and remove buttons

**Rationale**:
- Better UX than plain comma-separated text input (users can see tags as distinct entities)
- Clear visual feedback for validation errors (tag too long, too many tags)
- Easy tag removal with X button on each chip
- Prevents confusion about separators (comma vs space vs semicolon)
- Matches existing tag display pattern in task list (already shows tags as chips)

**Alternatives Considered**:
- **Comma-separated text input**: Simple but error-prone, no visual feedback, harder to edit individual tags
- **Third-party library (react-tag-input, react-select)**: Adds dependencies, may not match design system, overkill for simple use case

**Implementation Pattern**:
```typescript
// State: tags as array of strings
const [tags, setTags] = useState<string[]>([]);
const [inputValue, setInputValue] = useState('');

// Add tag on Enter or comma
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    const tag = inputValue.trim();
    if (tag && !tags.includes(tag)) {
      if (tags.length < 10 && tag.length <= 50) {
        setTags([...tags, tag]);
        setInputValue('');
      } else {
        // Show validation error
      }
    }
  }
};

// Remove tag
const removeTag = (index: number) => {
  setTags(tags.filter((_, i) => i !== index));
};
```

---

### Q3: Recurrence Custom Cron Input UX

**Decision**: Provide text input with help text and examples; no visual cron builder

**Rationale**:
- Custom recurrence is advanced feature (P2 priority), used by minority of users
- Cron expression validation handled by backend (frontend just passes string)
- Visual cron builders are complex and add significant bundle size
- Help text with common examples (e.g., "0 9 * * 1,3,5 = Mon/Wed/Fri at 9am") provides sufficient guidance
- Users who need custom cron already understand the syntax or can look it up

**Alternatives Considered**:
- **react-cron-generator**: Visual cron builder - adds 100KB+, complex UI, may confuse non-technical users
- **Embedded cron documentation**: Too verbose, breaks form flow
- **External link to cron documentation**: Better than embedding, but still requires context switch

**Implementation Notes**:
- Show cron input only when "custom" recurrence type selected (progressive disclosure)
- Display placeholder: "e.g., 0 9 * * 1,3,5 (Mon/Wed/Fri at 9am)"
- On validation error from API, show error message with hint to check syntax
- Consider adding link to crontab.guru for advanced users

---

### Q4: Sort and Filter State Management

**Decision**: Use React component state with URL query params sync (optional/future enhancement)

**Rationale**:
- Simple component state (`useState`) sufficient for session-based sort/filter
- SWR hook can accept dynamic parameters, refetching when sort/filter changes
- URL sync not required for MVP but enables shareable filtered views (future enhancement)
- Spec explicitly states "Filter Persistence: Sort and filter states are session-based (reset on page reload)"

**Implementation Pattern**:
```typescript
const [sortBy, setSortBy] = useState<'due_date' | 'priority' | 'title' | 'created_at'>('created_at');
const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
const [priorityFilters, setPriorityFilters] = useState<TaskPriority[]>([]);
const [tagFilter, setTagFilter] = useState<string | null>(null);

// Pass to SWR hook
const { tasks } = useTasks({
  status,
  sortBy,
  sortOrder,
  priority: priorityFilters,
  tag: tagFilter
});
```

**Alternatives Considered**:
- **URL query params (useSearchParams)**: Better for sharing/bookmarking but adds complexity; deferred to future enhancement
- **Global state (Zustand, Redux)**: Overkill for page-level filter state
- **localStorage**: Adds persistence not required by spec

---

### Q5: Form Validation Strategy (Client vs Server)

**Decision**: Implement client-side validation mirroring backend rules + handle server validation errors gracefully

**Rationale**:
- Client-side validation provides immediate feedback (<300ms per spec)
- Prevents unnecessary API calls for invalid data
- Server validation is source of truth (defense in depth)
- Must handle API validation errors for edge cases (concurrent updates, backend rule changes)

**Validation Rules to Mirror**:
- Title: 1-200 characters (required)
- Description: 0-2000 characters (optional)
- Tags: max 10 tags, each max 50 characters
- Reminders: max 5 per task
- Cron expression: required when recurrence type is "custom" (basic presence check, backend validates syntax)

**Error Display Pattern**:
```typescript
interface ValidationErrors {
  title?: string;
  description?: string;
  tags?: string;
  reminders?: string;
  cron_expression?: string;
}

const [errors, setErrors] = useState<ValidationErrors>({});

// Client validation
const validateForm = (): boolean => {
  const newErrors: ValidationErrors = {};
  if (!title.trim()) newErrors.title = 'Title is required';
  if (title.length > 200) newErrors.title = 'Title must be 200 characters or less';
  if (description && description.length > 2000) newErrors.description = 'Description must be 2000 characters or less';
  if (tags.length > 10) newErrors.tags = 'Maximum 10 tags allowed';
  if (tags.some(t => t.length > 50)) newErrors.tags = 'Each tag must be 50 characters or less';
  // ... more validations

  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

// Server error handling
try {
  await createTask(taskData);
} catch (error) {
  if (error instanceof ApiClientError) {
    // Parse backend validation errors and display
    setErrors({ title: error.message });
  }
}
```

---

### Q6: Reminder UI/UX Without Notification Delivery

**Decision**: Show reminders with "Scheduled" status label and clear help text explaining no notifications

**Rationale**:
- Spec explicitly states: "System MUST NOT display any notifications or alerts when reminder trigger times pass"
- Users need to understand reminders are saved but not delivered (avoid misleading expectations)
- Prepares data layer for future notification implementation
- Help text example: "Reminders are saved for future use. Notification delivery coming soon."

**Display Pattern**:
- Reminder count badge: "2 reminders"
- Status label: "Scheduled" (not "Active" or "Pending" which imply action)
- Help icon with tooltip explaining limitation
- List reminder times in task details with clock icon

**Alternatives Considered**:
- **Hide reminders entirely**: Removes useful feature preparation and user testing opportunity
- **Implement browser notifications**: Out of scope per spec
- **Mock notifications**: Misleading, creates bad user experience

---

## Best Practices Research

### React Hook Form Patterns for Complex Forms

**Pattern**: Controlled components with React hooks, no form library

**Justification**:
- React Hook Form adds ~25KB, beneficial for very complex forms with many fields
- Our form has ~10 fields total, manageable with useState
- Some fields (tags, reminders) require custom logic that form libraries complicate
- Existing codebase doesn't use React Hook Form, consistency is valuable

**Approach**:
- Use individual `useState` hooks for each form field
- Group related state (basic fields vs advanced fields) for progressive disclosure
- Extract reusable validation logic to `lib/utils.ts`

---

### Progressive Disclosure for Advanced Features

**Pattern**: Collapsible "Advanced Options" section for recurrence and reminders

**Justification**:
- P1 features (priority, tags, description, sort, filter) should be immediately visible
- P2/P3 features (recurrence, reminders) less frequently used, can be hidden initially
- Reduces cognitive load and form intimidation for basic task creation
- Matches common UX pattern (e.g., GitHub issue forms, Jira task creation)

**Implementation**:
```typescript
const [showAdvanced, setShowAdvanced] = useState(false);

// Button to toggle advanced section
<button onClick={() => setShowAdvanced(!showAdvanced)}>
  {showAdvanced ? 'Hide' : 'Show'} Advanced Options
</button>

{showAdvanced && (
  <div>
    <RecurrenceSelector />
    <ReminderList />
  </div>
)}
```

---

### TypeScript Type Safety for API Requests

**Pattern**: Extend existing types, create helper types for request payloads

**Justification**:
- Existing `Task` type has all response fields
- Need `ReminderCreate` and `RecurrenceCreate` types for request payloads
- Type guards help validate data before API calls

**Type Additions Needed**:
```typescript
// types/index.ts additions
export interface ReminderCreate {
  trigger_at: string; // ISO 8601 datetime
}

export interface RecurrenceCreate {
  recurrence_type: RecurrenceType;
  cron_expression?: string | null;
}

// Extend TaskCreateRequest
export interface TaskCreateRequest {
  title: string;
  description?: string | null;
  priority?: TaskPriority;
  tags?: string[];
  due_date?: string | null;
  reminders?: ReminderCreate[];  // NEW
  recurrence?: RecurrenceCreate; // NEW
}

// Extend TaskUpdateRequest similarly
```

---

## Technology Integration Notes

### SWR Data Fetching with Dynamic Parameters

**Current Pattern**:
```typescript
const { tasks, isLoading } = useTasks(status);
```

**Enhanced Pattern**:
```typescript
interface TaskQueryParams {
  status?: TaskStatus;
  priority?: TaskPriority;
  tag?: string;
  sort_by?: 'due_date' | 'priority' | 'title' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

const { tasks, isLoading } = useTasks(params);
```

**SWR Key Generation**:
- Serialize params to query string for stable cache key
- SWR will auto-refetch when params change

---

### Tailwind CSS Utility Classes for New Components

**Patterns to Reuse**:
- Form inputs: `px-4 py-2.5 border border-slate-300 dark:border-dark-600 rounded-lg`
- Badges/chips: `px-2 py-0.5 text-xs rounded-full`
- Error text: `text-sm text-error-700 dark:text-error-400`
- Buttons: Use existing Button component variants

**Color Palette** (from spec):
- High priority: `text-error-500 dark:text-error-400` (red)
- Medium priority: neutral (no special color)
- Low priority: `text-slate-600 dark:text-slate-400` (gray)

---

## Decision Summary

| Decision Point | Choice | Key Reason |
|----------------|--------|------------|
| Date-time picker | HTML5 native input | Zero dependencies, browser support, accessibility |
| Tag input | Custom chip component | Better UX, visual feedback, matches existing design |
| Cron input | Text with help text | Advanced feature, backend validates, no heavy library |
| Sort/filter state | Component state + SWR | Simple, session-based per spec |
| Validation | Client + server | Immediate feedback + defense in depth |
| Reminder display | "Scheduled" label + help text | Clear expectation setting, no misleading UI |
| Form library | No library, React hooks | Simple form, consistency with existing code |
| Advanced features | Progressive disclosure | Reduces form complexity for basic use cases |
| Type safety | Extend existing types | Maintains type safety, minimal additions |

---

## Open Questions Resolved

All technical decisions have been made. No remaining clarifications needed. Ready to proceed to Phase 1 (Design & Contracts).

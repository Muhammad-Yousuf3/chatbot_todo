# Feature Specification: UI Enablement for Intermediate & Advanced Features

**Feature Branch**: `010-ui-enablement`
**Created**: 2026-01-24
**Status**: Draft
**Input**: User description: "Phase V - UI Enablement for Intermediate and Advanced Features"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Task with Priority and Tags Manually (Priority: P1)

As a user, I want to create tasks directly from the UI with priority levels and tags so that I can organize my work without needing to use the chatbot for every task.

**Why this priority**: This is the most fundamental improvement - users currently cannot set priority or tags when manually creating tasks, forcing them to use the chatbot or leave tasks unorganized.

**Independent Test**: Can be fully tested by creating a task through the UI form with priority set to "high" and tags "urgent, work" and verifying the task displays correctly with these attributes.

**Acceptance Scenarios**:

1. **Given** I am on the /tasks page, **When** I click to create a new task and select priority "high" and add tags "urgent" and "work", **Then** the task is created with high priority badge and both tags displayed
2. **Given** I have created a task with default priority (medium), **When** I edit the task and change priority to "low", **Then** the task updates and displays with low priority indicator
3. **Given** I am creating a task, **When** I add more than 10 tags, **Then** I see a validation error preventing submission
4. **Given** I am creating a task, **When** I add a tag longer than 50 characters, **Then** I see a validation error for that tag

---

### User Story 2 - Add Detailed Description to Tasks (Priority: P1)

As a user, I want to add multi-line descriptions to tasks when creating or editing them so that I can capture all necessary details and context.

**Why this priority**: Descriptions are essential for task clarity. Currently users can only see descriptions created via chatbot but cannot add/edit them manually.

**Independent Test**: Can be fully tested by creating a task with a multi-line description containing 500 characters and verifying it saves and displays correctly in the task list.

**Acceptance Scenarios**:

1. **Given** I am creating a new task, **When** I enter a multi-line description with formatting and special characters, **Then** the description is saved and displays correctly
2. **Given** I have a task with no description, **When** I edit it and add a description, **Then** the description appears on the task card
3. **Given** I am entering a description, **When** I exceed 2000 characters, **Then** I see a character counter warning and cannot submit
4. **Given** I have a task with a description, **When** I edit and remove the description, **Then** the task updates without a description field showing

---

### User Story 3 - Sort and Filter Tasks (Priority: P1)

As a user, I want to sort tasks by due date, priority, or title and filter by priority and tags so that I can quickly find the tasks that matter most.

**Why this priority**: With many tasks, users need sorting and filtering to manage their workload effectively. Backend supports this but UI doesn't expose it.

**Independent Test**: Can be fully tested by creating 10 tasks with varying priorities and due dates, then using sort/filter controls to verify only high-priority tasks show up when filtered, or tasks appear in due-date order when sorted.

**Acceptance Scenarios**:

1. **Given** I have 20 tasks with mixed priorities, **When** I filter by "high priority", **Then** only high priority tasks are displayed
2. **Given** I have tasks tagged "work" and "personal", **When** I filter by tag "work", **Then** only work-tagged tasks appear
3. **Given** I have tasks with various due dates, **When** I sort by "due date ascending", **Then** tasks appear with soonest due dates first
4. **Given** I have applied filters for priority and tag, **When** I clear filters, **Then** all tasks are displayed again
5. **Given** I have sorted tasks by priority descending, **When** I switch to sort by title alphabetically, **Then** tasks reorder alphabetically

---

### User Story 4 - Set Due Date with Time (Priority: P2)

As a user, I want to set both date and time for task due dates so that I can schedule tasks more precisely than just "by end of day".

**Why this priority**: Time precision improves task scheduling but is less critical than basic organization features. Current UI only supports date selection.

**Independent Test**: Can be fully tested by creating a task with due date "2026-02-01 14:30" and verifying it saves correctly and displays with the specific time.

**Acceptance Scenarios**:

1. **Given** I am creating a task, **When** I set due date to "2026-02-01" and time to "14:30", **Then** the task saves with due date "2026-02-01T14:30:00"
2. **Given** I have a task with due date but no time, **When** I edit to add a specific time, **Then** the time is added to the existing date
3. **Given** I am setting a due date, **When** I select a date in the past, **Then** the system allows it (past dates may be intentional for tracking overdue items)
4. **Given** I have a task with a due date and time, **When** the current time passes the due time, **Then** the task displays as overdue with time information

---

### User Story 5 - Configure Recurring Tasks (Priority: P2)

As a user, I want to set up recurring tasks (daily, weekly, or custom schedule) directly in the UI so that I don't need to use the chatbot for routine task automation.

**Why this priority**: Recurring tasks are powerful for routine work but not critical for basic task management. Backend infrastructure is ready.

**Independent Test**: Can be fully tested by creating a task with "weekly" recurrence, verifying it saves with recurrence indicator, and confirming the scheduler service can process it (check database/logs, no UI verification of next instance creation needed).

**Acceptance Scenarios**:

1. **Given** I am creating a task, **When** I select recurrence type "daily", **Then** the task is created with daily recurrence schedule
2. **Given** I am creating a task, **When** I select recurrence type "weekly", **Then** the task is created with weekly recurrence schedule
3. **Given** I am creating a task, **When** I select recurrence type "custom" and provide cron expression "0 9 * * 1,3,5", **Then** the task is created with custom recurrence
4. **Given** I select "custom" recurrence, **When** I don't provide a cron expression, **Then** I see a validation error
5. **Given** I have a task with recurrence, **When** I view the task, **Then** I see a recurrence indicator showing the schedule type
6. **Given** I am editing a task with recurrence, **When** I remove the recurrence, **Then** the task becomes a one-time task

---

### User Story 6 - Add Reminders to Tasks (Priority: P3)

As a user, I want to add one or more reminder times to tasks so that the system can notify me before tasks are due, even though actual notification delivery is not implemented yet.

**Why this priority**: Reminders enhance task management but require notification delivery (out of scope) to be fully useful. This enables the data layer for future notification features.

**Independent Test**: Can be fully tested by creating a task with 2 reminders at different times and verifying they are saved to the database and displayed in the UI as "Scheduled" status.

**Acceptance Scenarios**:

1. **Given** I am creating a task with due date "2026-02-01 17:00", **When** I add reminders for "2026-02-01 09:00" and "2026-01-31 17:00", **Then** both reminders are saved and displayed
2. **Given** I am adding a reminder, **When** I set reminder time after the due date, **Then** I see a validation warning but can still save (user may have reasons)
3. **Given** I have a task, **When** I add more than 5 reminders, **Then** I see a validation error preventing the 6th reminder
4. **Given** I have a task with reminders, **When** I view the task, **Then** I see reminder count and status (e.g., "2 reminders - Scheduled")
5. **Given** I am editing a task with reminders, **When** I remove a reminder, **Then** the reminder count updates and removed reminder is deleted
6. **Given** A reminder trigger time has passed, **When** I view the task, **Then** the UI does NOT show any notification (notification delivery is out of scope)

---

### Edge Cases

- **What happens when a user edits a task to remove all tags?** The task should update with an empty tags array and no tag badges should display.
- **How does the system handle concurrent edits?** Last write wins (existing API behavior) - no optimistic locking implemented.
- **What happens if a user enters an invalid cron expression for custom recurrence?** The API will reject it with a validation error (backend handles cron validation).
- **How are tasks with multiple filters (priority AND tag) handled?** Filters are combined with AND logic - task must match all active filters.
- **What happens when sorting by priority with tasks of mixed priorities?** High > Medium > Low order for ascending, reversed for descending.
- **What happens to reminders when a task's due date is removed?** Reminders remain (they have independent trigger times) - user must manually remove if desired.
- **How are overdue tasks with recurring schedules displayed?** The overdue instance shows as overdue; scheduler creates next instance per schedule regardless.

## Requirements *(mandatory)*

### Functional Requirements

#### Task Creation Form Enhancements

- **FR-001**: System MUST provide a priority selector with options: low, medium, high (default: medium)
- **FR-002**: System MUST provide a tags input field that accepts multiple tags (comma-separated or chip-style entry)
- **FR-003**: System MUST provide a multi-line text area for task description (max 2000 characters)
- **FR-004**: System MUST provide a date-time picker for due date selection (supporting both date and optional time)
- **FR-005**: System MUST validate tags to enforce maximum 10 tags per task and 50 characters per tag
- **FR-006**: System MUST display character count for description field showing remaining characters

#### Task Editing

- **FR-007**: Users MUST be able to edit all task fields (title, description, priority, tags, due date, recurrence, reminders) through inline or modal editing
- **FR-008**: System MUST preserve existing values when editing a task (pre-populate form with current values)
- **FR-009**: System MUST allow removal of optional fields (description, tags, due date, recurrence, reminders) by clearing the input

#### Recurrence Configuration

- **FR-010**: System MUST provide a recurrence selector with options: none, daily, weekly, custom
- **FR-011**: System MUST show a cron expression input field when "custom" recurrence type is selected
- **FR-012**: System MUST validate that cron expression is provided when custom recurrence type is selected
- **FR-013**: System MUST display recurrence information on task cards showing recurrence type

#### Reminder Management

- **FR-014**: System MUST provide an interface to add multiple reminders to a task (max 5 reminders)
- **FR-015**: Each reminder MUST have a date-time picker for trigger time selection
- **FR-016**: System MUST display reminder count and scheduled status on task cards (e.g., "3 reminders - Scheduled")
- **FR-017**: System MUST allow users to remove individual reminders from a task
- **FR-018**: System MUST NOT display any notifications or alerts when reminder trigger times pass (notification delivery is out of scope)

#### Sorting Functionality

- **FR-019**: System MUST provide sort options: due date, priority, title, created date
- **FR-020**: System MUST provide sort order toggle: ascending and descending
- **FR-021**: System MUST maintain sort state when tasks are updated or new tasks are added
- **FR-022**: System MUST use the following sort orders:
  - Priority: high > medium > low (ascending), reversed for descending
  - Due date: earliest to latest (ascending), reversed for descending
  - Title: alphabetical A-Z (ascending), reversed for descending
  - Created date: oldest to newest (ascending), reversed for descending

#### Filtering Functionality

- **FR-023**: System MUST provide filter by priority with checkboxes for: high, medium, low
- **FR-024**: System MUST provide filter by tag with tag selection (show all used tags)
- **FR-025**: System MUST maintain existing status filter (all, pending, completed)
- **FR-026**: System MUST combine multiple filters with AND logic (task must match all active filters)
- **FR-027**: System MUST provide a "Clear Filters" action to reset all filters
- **FR-028**: System MUST display active filter count or indicator when filters are applied

#### Data Validation

- **FR-029**: System MUST prevent submission when validation fails and display clear error messages
- **FR-030**: System MUST validate all fields according to existing API constraints:
  - Title: 1-200 characters (required)
  - Description: 0-2000 characters (optional)
  - Tags: max 10 tags, each max 50 characters
  - Reminders: max 5 per task
  - Cron expression: required for custom recurrence type

#### Display Requirements

- **FR-031**: Task cards MUST display all task attributes: title, description, priority badge, tag chips, due date, recurrence indicator, reminder count
- **FR-032**: Priority MUST be visually differentiated with color coding:
  - High: red/error color
  - Medium: neutral (or no special color)
  - Low: gray/muted color
- **FR-033**: Tags MUST be displayed as colored chips/badges
- **FR-034**: Recurrence indicator MUST show recurrence type (daily, weekly, custom)
- **FR-035**: Due date display MUST show both date and time when time is set
- **FR-036**: Overdue tasks MUST be visually highlighted

### Key Entities *(include if feature involves data)*

- **Task**: User's todo item with title, description, priority, tags, due date, status, timestamps, optional recurrence, and optional reminders
  - Attributes: id, user_id, title, description, status, priority, tags[], due_date, created_at, updated_at, completed_at
  - Relationships: has many Reminders, has one Recurrence (optional)

- **Reminder**: Scheduled notification trigger time associated with a task
  - Attributes: id, task_id, trigger_at, fired, cancelled, created_at
  - Relationships: belongs to Task

- **Recurrence**: Schedule definition for automatically creating recurring task instances
  - Attributes: id, task_id, recurrence_type, cron_expression (for custom), next_occurrence, active, created_at
  - Relationships: belongs to Task

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a fully-configured task (with priority, tags, description, due date) in under 60 seconds
- **SC-002**: All task attributes (priority, tags, description, recurrence, reminders) are visible in the task list without additional clicks
- **SC-003**: Users can find specific tasks using filters in under 10 seconds (filter by priority and tag)
- **SC-004**: Sorting tasks by any available field (due date, priority, title, created date) reorders the list within 500ms
- **SC-005**: 100% of tasks created through the UI with all fields populate correctly in the database matching API schema
- **SC-006**: Zero regression - all existing UI functionality (create basic task, complete, delete, status filter) continues to work without errors
- **SC-007**: Form validation prevents invalid submissions with clear error messages visible within 200ms of validation trigger
- **SC-008**: Users can successfully configure recurring tasks (daily, weekly, custom) through the UI and verify recurrence is saved in the database

## Assumptions *(optional)*

1. **API Stability**: The existing task API endpoints (`POST /api/tasks`, `PATCH /api/tasks/{id}`, `GET /api/tasks`) accept all fields defined in the API schemas without modification
2. **Authentication**: Current JWT authentication mechanism continues to work and provides user_id for task ownership
3. **Browser Support**: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+) with JavaScript enabled
4. **Date/Time Format**: ISO 8601 format is used for all datetime fields (YYYY-MM-DDTHH:mm:ss)
5. **Timezone Handling**: All times are stored and displayed in UTC; local timezone conversion is handled by browser's date picker
6. **Cron Expression Validation**: Backend performs cron expression validation; UI does not need to validate cron syntax
7. **Scheduler Service**: The Scheduler service is running and will process recurrence and reminders; UI only needs to save the configuration
8. **No Notification UI**: Even though reminders are saved and processed by backend, the UI will not display any notifications, alerts, or delivery confirmations
9. **Filter Persistence**: Sort and filter states are session-based (reset on page reload) unless explicitly implemented otherwise
10. **Existing Data Migration**: Tasks created before this feature will display correctly even though they may lack some new fields (priority defaults to medium, empty tags/description)

## Dependencies *(optional)*

### Internal Dependencies

- **Backend API**: Existing task API must support all fields in TaskCreateRequest and TaskUpdateRequest schemas
- **Database Schema**: Task, Reminder, and Recurrence tables must exist with defined fields
- **Frontend API Client**: TypeScript types must be updated to include all task fields (priority, tags, description, recurrence, reminders)
- **UI Component Library**: Need date-time picker, tag input, dropdown/select components

### External Dependencies

- **None**: This feature is entirely self-contained in the frontend using existing backend infrastructure

## Out of Scope *(optional)*

- ❌ **Notification Delivery**: No browser notifications, email, SMS, or push alerts when reminders trigger
- ❌ **Backend Changes**: No API endpoint modifications, no database schema changes, no business logic changes
- ❌ **Chatbot Updates**: No changes to AI agent behavior or MCP tools
- ❌ **Event Publishing Changes**: No modifications to Dapr/Kafka event publishing logic
- ❌ **Real-time Updates**: No WebSocket or server-sent events for live task updates
- ❌ **Collaborative Features**: No multi-user editing, task sharing, or comments
- ❌ **Advanced Recurrence**: No RRULE support beyond the existing daily/weekly/custom types
- ❌ **Reminder Snoozing**: No ability to snooze or reschedule reminders
- ❌ **Filter Persistence**: Saved filter/sort preferences across sessions
- ❌ **Bulk Operations**: No bulk edit, bulk delete, or bulk status change
- ❌ **Task Templates**: No saved task templates or quick-add presets
- ❌ **Calendar View**: No calendar or timeline visualization
- ❌ **Mobile-Specific UI**: Responsive design follows existing patterns but no mobile app
- ❌ **Accessibility Audit**: No comprehensive WCAG compliance review (follow existing patterns)
- ❌ **Performance Optimization**: No virtual scrolling or pagination UI improvements beyond existing implementation

## Constraints *(optional)*

1. **Frontend-Only Changes**: All modifications must be confined to the frontend codebase (React/Next.js components, hooks, utilities)
2. **API Contract Compliance**: UI must use existing API request/response schemas without modification
3. **No Schema Changes**: Cannot add, remove, or modify database fields or API contracts
4. **Existing Component Patterns**: Must follow established UI component patterns and design system
5. **No Breaking Changes**: Existing functionality must continue to work; this is purely additive
6. **Validation Alignment**: Frontend validation must match backend validation rules exactly (tag limits, character limits, required fields)
7. **Data Format Compliance**: All datetime values must be sent in ISO 8601 format as expected by the API
8. **Tag Storage**: Tags must be sent as an array of strings matching backend expectations
9. **Recurrence Structure**: Recurrence data must match RecurrenceCreate schema structure
10. **Reminder Structure**: Reminders must be sent as an array of ReminderCreate objects with trigger_at datetime

## Open Questions *(optional)*

None - all requirements are clear based on existing API contracts and user stories.

## Risks & Mitigations *(optional)*

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| UI validation out of sync with API validation causing submission errors | Medium | Medium | Mirror backend validation rules in frontend; handle API validation errors gracefully with clear messages |
| Complex form with many fields overwhelming users | Low | Low | Use progressive disclosure (e.g., advanced options in expandable section); provide sensible defaults |
| Cron expression input confusing for non-technical users | Low | Medium | Provide help text with examples; validate on blur; consider cron builder UI in future iteration |
| Performance degradation with large task lists and complex filtering | Low | Low | Use existing pagination; optimize filter logic with memoization; defer optimization until needed |
| Reminder UI misleading users into expecting notifications | Medium | High | Clearly label as "Scheduled" (not "Active" or "Sending"); add help text explaining notifications are not delivered |
| Date-time picker timezone confusion | Low | Medium | Show timezone indicator; use browser's local timezone in picker; store UTC in backend as designed |
| Accessibility issues with new form components | Low | Low | Follow existing component patterns; ensure keyboard navigation and screen reader support |

## Security & Privacy Considerations *(optional)*

- **Input Sanitization**: Description and tag inputs must be sanitized to prevent XSS attacks (follow existing input handling patterns)
- **Authorization**: Task operations must continue to enforce user ownership (existing JWT middleware)
- **Data Validation**: Client-side validation is for UX only; backend validation is source of truth
- **No PII in Tags**: Users should not be encouraged to put sensitive personal information in tags (no validation for this, user responsibility)

## Non-Functional Requirements *(optional)*

### Performance

- Form submission (create/update task) should complete within 2 seconds under normal network conditions
- Sorting and filtering operations should feel instant (<500ms to re-render task list)
- Character counters and validation feedback should be real-time (as user types, debounced to ~300ms)

### Usability

- Form fields should have clear labels and placeholder text
- Validation errors should appear inline near the relevant field
- Current sort and filter state should be visually indicated
- Multi-line description field should auto-expand or show scrollbar appropriately

### Reliability

- Form should handle API errors gracefully without losing user input
- Optimistic UI updates (task appears in list immediately, rolls back on error)
- Loading states should be shown during async operations

### Maintainability

- Component structure should be modular (separate form, filter, sort components)
- TypeScript types should be updated to match API schemas
- Validation logic should be reusable across create/edit forms

## Glossary *(optional)*

- **Priority**: Importance level of a task (high, medium, low)
- **Tag**: Short label/keyword for categorizing tasks (e.g., "work", "urgent")
- **Recurrence**: Schedule for automatically recreating a task (daily, weekly, or custom cron)
- **Reminder**: Scheduled trigger time for future notification (notification delivery out of scope for this phase)
- **Cron Expression**: Unix cron syntax for defining custom schedules (e.g., "0 9 * * 1-5" = weekdays at 9am)
- **Due Date**: Target completion date/time for a task
- **Status**: Current state of a task (pending, in_progress, completed)
- **Chip**: UI component showing a tag as a colored badge/pill with remove option

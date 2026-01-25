# Tasks: UI Enablement for Intermediate & Advanced Features

**Input**: Design documents from `/specs/010-ui-enablement/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Manual testing only (no automated test suite in frontend per plan.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions

This is a web application with frontend-only modifications:
- Frontend: `frontend/` directory
- All changes confined to frontend code (TypeScript, React, Next.js)
- No backend, database, or API modifications

---

## Phase 1: Setup (Type System & Validation Foundation)

**Purpose**: TypeScript types and validation infrastructure that all user stories depend on

- [x] T001 Add ReminderCreate and RecurrenceCreate types to frontend/types/index.ts
- [x] T002 [P] Extend TaskCreateRequest interface with reminders and recurrence fields in frontend/types/index.ts
- [x] T003 [P] Extend TaskUpdateRequest interface with reminders and recurrence fields in frontend/types/index.ts
- [x] T004 [P] Add TaskQueryParams interface for sort/filter in frontend/types/index.ts
- [x] T005 [P] Add VALIDATION_LIMITS constants to frontend/lib/utils.ts
- [x] T006 [P] Add validateTaskForm function to frontend/lib/utils.ts
- [x] T007 [P] Add helper functions (taskToFormState, formStateToCreateRequest, formStateToUpdateRequest) to frontend/types/index.ts

**Checkpoint**: ✅ Type system ready - all components can reference proper types

---

## Phase 2: Foundational (API Client & Data Hooks)

**Purpose**: Core API integration that MUST be complete before ANY user story UI can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Update createTask method in frontend/lib/api.ts to include reminders and recurrence in request payload
- [x] T009 [P] Update updateTask method in frontend/lib/api.ts to include reminders and recurrence in request payload
- [x] T010 Update useTasks hook signature in frontend/hooks/useTasks.ts to accept TaskQueryParams instead of just status
- [x] T011 Implement buildTaskQueryString helper function in frontend/hooks/useTasks.ts or frontend/lib/utils.ts
- [x] T012 Update SWR cache key generation in frontend/hooks/useTasks.ts to include query params

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create Task with Priority and Tags Manually (Priority: P1) 🎯 MVP

**Goal**: Enable users to create tasks with priority levels and tags directly from the UI

**Independent Test**: Create a task through the UI form with priority set to "high" and tags "urgent, work" and verify the task displays correctly with these attributes

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create TagInput component in frontend/components/tasks/TagInput.tsx with chip display and add/remove functionality
- [ ] T014 [P] [US1] Add priority selector (dropdown or radio buttons) to task creation form in frontend/app/tasks/page.tsx
- [ ] T015 [US1] Integrate TagInput component into task creation form in frontend/app/tasks/page.tsx
- [ ] T016 [US1] Add client-side validation for tags (max 10, each max 50 chars) in task form
- [ ] T017 [US1] Add client-side validation for title (1-200 chars) in task form
- [ ] T018 [US1] Update handleCreateTask function to include priority and tags in API request
- [ ] T019 [US1] Add priority badge display to TaskItem component with color coding (high=red, low=gray)
- [ ] T020 [US1] Add tag chips display to TaskItem component
- [ ] T021 [US1] Add error display for validation failures in task form
- [ ] T022 [US1] Test task creation with priority and tags and verify API request payload

**Checkpoint**: At this point, User Story 1 should be fully functional - users can create and view tasks with priority and tags

---

## Phase 4: User Story 2 - Add Detailed Description to Tasks (Priority: P1)

**Goal**: Enable users to add multi-line descriptions when creating or editing tasks

**Independent Test**: Create a task with a multi-line description containing 500 characters and verify it saves and displays correctly in the task list

### Implementation for User Story 2

- [ ] T023 [P] [US2] Add description textarea to task creation form in frontend/app/tasks/page.tsx
- [ ] T024 [P] [US2] Add character counter display (2000 max) for description field
- [ ] T025 [US2] Add client-side validation for description (max 2000 chars)
- [ ] T026 [US2] Update handleCreateTask to include description in API request
- [ ] T027 [US2] Add description display to TaskItem component (with truncation or expand/collapse)
- [ ] T028 [US2] Add description field to edit task functionality
- [ ] T029 [US2] Test task creation and editing with descriptions including special characters and line breaks

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can create tasks with all P1 basic fields

---

## Phase 5: User Story 3 - Sort and Filter Tasks (Priority: P1)

**Goal**: Enable users to sort tasks by due date, priority, or title and filter by priority and tags

**Independent Test**: Create 10 tasks with varying priorities and due dates, then use sort/filter controls to verify only high-priority tasks show up when filtered, or tasks appear in due-date order when sorted

### Implementation for User Story 3

- [ ] T030 [P] [US3] Create SortControls component in frontend/components/tasks/SortControls.tsx with dropdown for sort field and order toggle
- [ ] T031 [P] [US3] Create FilterPanel component in frontend/components/tasks/FilterPanel.tsx with priority checkboxes and tag filter
- [ ] T032 [US3] Add sort state management (sortBy, sortOrder) to tasks page component
- [ ] T033 [US3] Add filter state management (priorityFilters, tagFilter) to tasks page component
- [ ] T034 [US3] Integrate SortControls component into tasks page header
- [ ] T035 [US3] Integrate FilterPanel component into tasks page sidebar or header
- [ ] T036 [US3] Pass sort/filter params to useTasks hook and verify SWR refetching
- [ ] T037 [US3] Add "Clear Filters" button functionality
- [ ] T038 [US3] Add active filter count indicator in UI
- [ ] T039 [US3] Extract unique tags from tasks for tag filter dropdown
- [ ] T040 [US3] Test sorting by each field (due_date, priority, title, created_at) in both orders
- [ ] T041 [US3] Test filtering by priority and tag combinations
- [ ] T042 [US3] Verify filter persistence during task creation/updates (SWR cache invalidation)

**Checkpoint**: All P1 user stories (1, 2, 3) should now be independently functional - basic task management is complete

---

## Phase 6: User Story 4 - Set Due Date with Time (Priority: P2)

**Goal**: Enable users to set both date and time for task due dates for precise scheduling

**Independent Test**: Create a task with due date "2026-02-01 14:30" and verify it saves correctly and displays with the specific time

### Implementation for User Story 4

- [ ] T043 [P] [US4] Create DateTimePicker component in frontend/components/tasks/DateTimePicker.tsx using HTML5 datetime-local input
- [ ] T044 [P] [US4] Add datetime conversion helpers (ISO 8601 to datetime-local format and vice versa) to frontend/lib/utils.ts
- [ ] T045 [US4] Replace existing date input with DateTimePicker component in task creation form
- [ ] T046 [US4] Update due date display in TaskItem to show time when present
- [ ] T047 [US4] Add timezone indicator to datetime picker (optional)
- [ ] T048 [US4] Update handleCreateTask to convert datetime-local value to ISO 8601 string
- [ ] T049 [US4] Add edit functionality for due date with time
- [ ] T050 [US4] Test task creation with date and time and verify API payload format
- [ ] T051 [US4] Test due date display with time component in task list
- [ ] T052 [US4] Test overdue task display when time has passed

**Checkpoint**: User Story 4 should work independently - users can set precise due date/time

---

## Phase 7: User Story 5 - Configure Recurring Tasks (Priority: P2)

**Goal**: Enable users to set up recurring tasks (daily, weekly, or custom schedule) directly in the UI

**Independent Test**: Create a task with "weekly" recurrence, verify it saves with recurrence indicator, and confirm the scheduler service can process it

### Implementation for User Story 5

- [ ] T053 [P] [US5] Create RecurrenceSelector component in frontend/components/tasks/RecurrenceSelector.tsx with radio buttons for none/daily/weekly/custom
- [ ] T054 [P] [US5] Add cron expression input field (shown only when custom selected) to RecurrenceSelector component
- [ ] T055 [P] [US5] Add help text with cron expression examples to RecurrenceSelector component
- [ ] T056 [US5] Add RecurrenceSelector to task creation form within collapsible "Advanced Options" section
- [ ] T057 [US5] Add recurrence state management to task form
- [ ] T058 [US5] Add client-side validation: cron expression required when recurrence type is "custom"
- [ ] T059 [US5] Update handleCreateTask to include recurrence in API request
- [ ] T060 [US5] Add recurrence indicator display to TaskItem component (icon + recurrence type)
- [ ] T061 [US5] Add edit functionality for recurrence
- [ ] T062 [US5] Add remove recurrence functionality (set to null)
- [ ] T063 [US5] Test task creation with daily recurrence
- [ ] T064 [US5] Test task creation with weekly recurrence
- [ ] T065 [US5] Test task creation with custom cron expression
- [ ] T066 [US5] Test validation error when custom selected without cron expression
- [ ] T067 [US5] Verify recurrence data in database (check via API response or database query)

**Checkpoint**: User Story 5 should work independently - users can configure recurring tasks

---

## Phase 8: User Story 6 - Add Reminders to Tasks (Priority: P3)

**Goal**: Enable users to add one or more reminder times to tasks (data layer for future notifications)

**Independent Test**: Create a task with 2 reminders at different times and verify they are saved to the database and displayed in the UI as "Scheduled" status

### Implementation for User Story 6

- [ ] T068 [P] [US6] Create ReminderList component in frontend/components/tasks/ReminderList.tsx with list of reminder times and add/remove buttons
- [ ] T069 [P] [US6] Add datetime picker for each reminder in ReminderList component
- [ ] T070 [P] [US6] Add "Add Reminder" button with validation (max 5 reminders)
- [ ] T071 [P] [US6] Add help text explaining reminders are scheduled but not delivered
- [ ] T072 [US6] Add ReminderList to task creation form within "Advanced Options" section
- [ ] T073 [US6] Add reminders state management to task form
- [ ] T074 [US6] Add client-side validation: max 5 reminders per task
- [ ] T075 [US6] Add optional validation warning when reminder time is after due date
- [ ] T076 [US6] Update handleCreateTask to include reminders in API request
- [ ] T077 [US6] Add reminder count and "Scheduled" status display to TaskItem component
- [ ] T078 [US6] Add edit functionality for reminders (add/remove)
- [ ] T079 [US6] Test task creation with multiple reminders
- [ ] T080 [US6] Test reminder validation (max 5)
- [ ] T081 [US6] Verify reminders are saved to database (check via API response)
- [ ] T082 [US6] Verify NO notification is displayed when reminder time passes (per spec)

**Checkpoint**: All user stories (1-6) should now be independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: UX improvements, error handling, and final integration testing

- [ ] T083 [P] Add loading states to task creation/update operations
- [ ] T084 [P] Add optimistic UI updates for task creation (show in list immediately, rollback on error)
- [ ] T085 [P] Implement error recovery for failed API calls (retry, user feedback)
- [ ] T086 [P] Add success notifications for task operations (toast or inline message)
- [ ] T087 [P] Add form reset functionality after successful task creation
- [ ] T088 [P] Improve mobile responsiveness of new components (TagInput, DateTimePicker, etc.)
- [ ] T089 [P] Add keyboard shortcuts for common operations (Enter to submit, Esc to cancel)
- [ ] T090 [P] Add accessibility attributes (ARIA labels, roles) to new components
- [ ] T091 Add "Advanced Options" collapsible section for recurrence and reminders
- [ ] T092 Implement progressive disclosure pattern (show/hide advanced options)
- [ ] T093 Add form state persistence during edit mode (pre-populate with existing values)
- [ ] T094 Add clear visual distinction between basic and advanced form fields
- [ ] T095 Verify browser compatibility testing (Chrome, Firefox, Safari, Edge)
- [ ] T096 Perform full regression testing (ensure existing task creation/editing still works)
- [ ] T097 Test all validation error messages display correctly
- [ ] T098 Test edge cases (empty tags array, null values, concurrent edits)
- [ ] T099 Verify no console errors in production build
- [ ] T100 Final end-to-end testing: create task with all fields, edit, filter, sort, delete

**Checkpoint**: Feature complete and polished - ready for production

---

## Dependencies & Execution Order

### User Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3-9 (User Stories + Polish)
                                                ↓
                        ┌──────────────────────────────────────┐
                        │                                      │
                    Phase 3 ──→ Phase 4 ──→ Phase 5          │
                    (US1: P1)   (US2: P1)   (US3: P1)        │
                        │           │           │             │
                        └───────────┴───────────┴──→ MVP READY
                                                     ↓
                                    Phase 6 ──→ Phase 7 ──→ Phase 8 ──→ Phase 9
                                    (US4: P2)   (US5: P2)   (US6: P3)   (Polish)
```

### Dependencies Between User Stories

- **US1 (Priority & Tags)**: No dependencies - can be implemented first
- **US2 (Description)**: No dependencies - can be implemented in parallel with US1
- **US3 (Sort & Filter)**: Depends on US1 and US2 for full testing (needs tasks with varied attributes)
- **US4 (Due Date/Time)**: Independent - enhances existing due date feature
- **US5 (Recurrence)**: Independent - uses advanced options section
- **US6 (Reminders)**: Independent - uses advanced options section, may share UI patterns with US5

### Parallel Execution Opportunities

**After Phase 2 completion, these can run in parallel:**

- **Team A**: Implement US1 (T013-T022)
- **Team B**: Implement US2 (T023-T029)
- **Team C**: Implement US4 (T043-T052)

**After US1 and US2 complete:**

- **Team A**: Implement US3 (T030-T042)
- **Team B**: Implement US5 (T053-T067)
- **Team C**: Implement US6 (T068-T082)

**Maximum parallelization:**
- Up to 3 teams can work simultaneously on independent user stories
- Each user story is a complete vertical slice (types → components → integration → testing)

---

## Implementation Strategy

### Minimum Viable Product (MVP)

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5 (P1 User Stories only)

This delivers core task organization features:
- Create tasks with priority and tags
- Add detailed descriptions
- Sort and filter tasks

**MVP Test**: User can organize their work without using the chatbot

### Incremental Delivery Plan

1. **Sprint 1**: Setup + Foundational + US1 (T001-T022)
   - Deliverable: Create tasks with priority and tags

2. **Sprint 2**: US2 + US3 (T023-T042)
   - Deliverable: Add descriptions, sort and filter

3. **Sprint 3**: US4 (T043-T052)
   - Deliverable: Precise due date/time scheduling

4. **Sprint 4**: US5 + US6 (T053-T082)
   - Deliverable: Advanced features (recurrence and reminders)

5. **Sprint 5**: Polish (T083-T100)
   - Deliverable: Production-ready with full UX polish

### Independent Deliverables

Each user story can be delivered independently:
- **US1**: Ship priority and tags without descriptions or filters
- **US2**: Ship descriptions without other features
- **US3**: Ship sort/filter when US1 and US2 are complete
- **US4-6**: Ship any P2/P3 feature independently

---

## Task Summary

**Total Tasks**: 100
**Setup Tasks**: 7 (T001-T007)
**Foundational Tasks**: 5 (T008-T012)
**User Story Tasks**:
- US1 (P1): 10 tasks (T013-T022)
- US2 (P1): 7 tasks (T023-T029)
- US3 (P1): 13 tasks (T030-T042)
- US4 (P2): 10 tasks (T043-T052)
- US5 (P2): 15 tasks (T053-T067)
- US6 (P3): 15 tasks (T068-T082)
**Polish Tasks**: 18 (T083-T100)

**Parallel Tasks**: 41 tasks marked with [P] can run in parallel with other [P] tasks
**Sequential Tasks**: 59 tasks have dependencies or modify the same files

**MVP Task Count**: 37 tasks (T001-T042) - Essential P1 features only

---

## Format Validation

✅ All 100 tasks follow checklist format: `- [ ] [ID] [P?] [Story?] Description`
✅ All user story tasks include [US#] label
✅ All tasks include specific file paths
✅ Dependencies clearly documented
✅ Independent test criteria defined for each user story
✅ Parallel execution opportunities identified

**Ready for Implementation**: Run `/sp.implement` to begin executing tasks in order

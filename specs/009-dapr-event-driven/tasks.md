# Tasks: Phase V Part 1 - Cloud-Native Event-Driven Todo Chatbot

**Branch**: `009-dapr-event-driven` | **Date**: 2026-01-20
**Input**: Design documents from `/specs/009-dapr-event-driven/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6, SETUP, FOUND, INFRA, POLISH)
- Include exact file paths in descriptions

## Path Conventions (from plan.md)

- **Backend**: `backend/src/` (existing service)
- **Scheduler**: `scheduler/src/` (new service)
- **Helm**: `helm/todo-chatbot/templates/`
- **Tests**: `backend/tests/`, `scheduler/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [x] T001 [SETUP] Add `dapr-client>=1.12.0` to backend/pyproject.toml dependencies
- [x] T002 [P] [SETUP] Create scheduler/ directory structure per plan.md project structure
- [x] T003 [P] [SETUP] Initialize scheduler/pyproject.toml with FastAPI, dapr-client, pydantic dependencies
- [x] T004 [P] [SETUP] Create scheduler/Dockerfile based on backend/Dockerfile pattern
- [x] T005 [SETUP] Create scheduler/src/main.py with FastAPI app skeleton and health endpoints

**Checkpoint**: Both services have dependencies configured. Scheduler has basic runnable structure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### 2A: Database Schema Extensions

- [x] T006 [FOUND] Add TaskPriority enum to backend/src/models/enums.py (high, medium, low)
- [x] T007 [FOUND] Add RecurrenceType enum to backend/src/models/enums.py (daily, weekly, custom)
- [x] T008 [FOUND] Extend Task model in backend/src/models/task.py with priority, tags (JSONB), updated_at fields
- [x] T009 [P] [FOUND] Create Reminder model in backend/src/models/reminder.py per data-model.md Section 1.2
- [x] T010 [P] [FOUND] Create Recurrence model in backend/src/models/recurrence.py per data-model.md Section 1.3
- [x] T011 [FOUND] Add Task relationships to Reminder and Recurrence with cascade_delete in backend/src/models/task.py
- [x] T012 [FOUND] Create Alembic migration script for task extensions (priority, tags, updated_at columns)
- [x] T013 [FOUND] Create Alembic migration script for reminders table with indexes
- [x] T014 [FOUND] Create Alembic migration script for recurrences table with indexes
- [x] T015 [FOUND] Run migrations and verify database schema matches data-model.md

### 2B: Event Infrastructure (Backend)

- [x] T016 [FOUND] Create backend/src/events/ directory structure
- [x] T017 [FOUND] Create CloudEvent Pydantic model in backend/src/events/schemas.py per data-model.md Section 2.1
- [x] T018 [P] [FOUND] Create TaskCreatedData schema in backend/src/events/schemas.py per data-model.md Section 2.2
- [x] T019 [P] [FOUND] Create TaskUpdatedData and FieldChange schemas in backend/src/events/schemas.py per data-model.md Section 2.3
- [x] T020 [P] [FOUND] Create TaskCompletedData schema in backend/src/events/schemas.py per data-model.md Section 2.4
- [x] T021 [P] [FOUND] Create TaskDeletedData schema in backend/src/events/schemas.py per data-model.md Section 2.5
- [x] T022 [FOUND] Create event constants in backend/src/events/constants.py (topic names, event type strings)

### 2C: Dapr Client Integration (Backend)

- [x] T023 [FOUND] Create backend/src/dapr/ directory structure
- [x] T024 [FOUND] Create DaprClient wrapper in backend/src/dapr/client.py with graceful fallback for non-Dapr mode
- [x] T025 [FOUND] Create secrets retrieval helper in backend/src/dapr/secrets.py for JWT_SECRET and DATABASE_URL
- [x] T026 [FOUND] Create event publisher in backend/src/events/publisher.py using DaprClient for Pub/Sub
- [x] T027 [FOUND] Update backend/src/main.py to initialize DaprClient on startup (with fallback)

### 2D: API Schema Extensions (Backend)

- [x] T028 [FOUND] Extend TaskCreateRequest schema in backend/src/api/schemas/tasks.py with priority, tags, reminders, recurrence fields
- [x] T029 [FOUND] Extend TaskUpdateRequest schema in backend/src/api/schemas/tasks.py with priority, tags, reminders, recurrence fields
- [x] T030 [FOUND] Extend TaskResponse schema in backend/src/api/schemas/tasks.py with priority, tags, reminders, recurrence, updated_at
- [x] T031 [P] [FOUND] Create ReminderCreate and ReminderResponse schemas in backend/src/api/schemas/reminders.py
- [x] T032 [P] [FOUND] Create RecurrenceCreate and RecurrenceResponse schemas in backend/src/api/schemas/recurrence.py

### 2E: Scheduler Service Core

- [x] T033 [FOUND] Create ReminderTriggeredData schema in scheduler/src/events/schemas.py per data-model.md Section 2.6
- [x] T034 [P] [FOUND] Create RecurringTaskScheduledData schema in scheduler/src/events/schemas.py per data-model.md Section 2.7
- [x] T035 [P] [FOUND] Create RecurringTaskState schema in scheduler/src/state/schemas.py per data-model.md Section 3.1
- [x] T036 [P] [FOUND] Create ReminderState schema in scheduler/src/state/schemas.py per data-model.md Section 3.2
- [x] T037 [FOUND] Create Dapr state store operations in scheduler/src/dapr/state.py (get, save, delete with key patterns)
- [x] T038 [FOUND] Create event publisher in scheduler/src/dapr/publisher.py for notifications and tasks topics
- [x] T039 [FOUND] Configure /dapr/subscribe endpoint in scheduler/src/main.py returning subscription config

**Checkpoint**: Foundation ready - All models, schemas, Dapr integration in place. User story implementation can now begin.

---

## Phase 3: User Story 1 - Task Priority Management (Priority: P1) 🎯 MVP

**Goal**: Allow users to organize tasks by importance (high/medium/low priority)

**Independent Test**: Create tasks with different priorities, verify they display and filter correctly

### Implementation for User Story 1

- [x] T040 [US1] Update POST /api/tasks route in backend/src/api/routes/tasks.py to accept and persist priority field
- [x] T041 [US1] Update PATCH /api/tasks/{id} route in backend/src/api/routes/tasks.py to update priority field
- [x] T042 [US1] Add priority filter parameter to GET /api/tasks route in backend/src/api/routes/tasks.py
- [x] T043 [US1] Update MCP add_task tool in backend/src/mcp_server/tools/add_task.py to accept priority parameter
- [x] T044 [US1] Update MCP update_task tool in backend/src/mcp_server/tools/update_task.py to accept priority parameter
- [x] T045 [US1] Add TaskCreated event emission after task creation in backend/src/api/routes/tasks.py
- [x] T046 [US1] Add TaskUpdated event emission (with priority change tracking) after task update in backend/src/api/routes/tasks.py

**Acceptance Criteria**:
- [x] AC1: Task can be created with priority (high/medium/low), defaults to medium
- [x] AC2: GET /api/tasks?priority=high returns only high-priority tasks
- [x] AC3: TaskCreated event includes priority field
- [x] AC4: TaskUpdated event tracks priority changes with old/new values

**Checkpoint**: Priority management fully functional. Can create, update, and filter tasks by priority.

---

## Phase 4: User Story 2 - Tag-Based Organization (Priority: P1)

**Goal**: Allow users to categorize tasks with tags for flexible organization

**Independent Test**: Add tags to tasks, filter and search by tag

### Implementation for User Story 2

- [x] T047 [US2] Update POST /api/tasks route in backend/src/api/routes/tasks.py to accept and persist tags array
- [x] T048 [US2] Update PATCH /api/tasks/{id} route in backend/src/api/routes/tasks.py to update tags array
- [x] T049 [US2] Add tag filter parameter to GET /api/tasks route in backend/src/api/routes/tasks.py (use PostgreSQL JSONB containment)
- [x] T050 [US2] Update MCP add_task tool in backend/src/mcp_server/tools/add_task.py to accept tags parameter
- [x] T051 [US2] Update MCP update_task tool in backend/src/mcp_server/tools/update_task.py to accept tags parameter
- [x] T052 [US2] Add tags validation (max 10 tags, each max 50 chars) in backend/src/api/schemas/tasks.py
- [x] T053 [US2] Update TaskCreated event payload to include tags array
- [x] T054 [US2] Update TaskUpdated event to track tags changes with old/new values

**Acceptance Criteria**:
- [x] AC1: Task can be created with tags array (e.g., ["work", "urgent"])
- [x] AC2: GET /api/tasks?tag=work returns tasks containing that tag
- [x] AC3: Tags limited to 10 per task, 50 chars each
- [x] AC4: TaskCreated/TaskUpdated events include tags

**Checkpoint**: Tag-based organization fully functional. Can create, update, and filter tasks by tags.

---

## Phase 5: User Story 3 - Task Search and Filtering (Priority: P1)

**Goal**: Allow users to quickly find specific tasks among many

**Independent Test**: Create multiple tasks, use search and filter to locate specific ones

### Implementation for User Story 3

- [x] T055 [US3] Add search parameter to GET /api/tasks route for keyword search in title/description (PostgreSQL ILIKE)
- [x] T056 [US3] Add status filter parameter to GET /api/tasks route (pending, in_progress, completed)
- [x] T057 [US3] Add due_before and due_after filter parameters to GET /api/tasks route
- [x] T058 [US3] Add sort_by parameter to GET /api/tasks route (due_date, priority, created_at, title)
- [x] T059 [US3] Add sort_order parameter to GET /api/tasks route (asc, desc)
- [x] T060 [US3] Combine all filters in backend/src/api/routes/tasks.py with SQLAlchemy query building
- [x] T061 [US3] Update MCP list_tasks tool in backend/src/mcp_server/tools/list_tasks.py to support search and filter parameters

**Acceptance Criteria**:
- [x] AC1: GET /api/tasks?search=review returns tasks with "review" in title or description
- [x] AC2: GET /api/tasks?status=pending returns only pending tasks
- [x] AC3: GET /api/tasks?sort_by=due_date&sort_order=asc returns tasks sorted by due date
- [x] AC4: Filters can be combined (e.g., ?priority=high&status=pending&tag=urgent)

**Checkpoint**: Search and filtering fully functional. Users can find tasks quickly.

---

## Phase 6: User Story 4 - Recurring Task Scheduling (Priority: P2)

**Goal**: Allow tasks that automatically recreate on a schedule (daily, weekly, custom)

**Independent Test**: Create recurring task, wait for cron trigger, verify new task instance created

### Implementation for User Story 4

- [x] T062 [US4] Update POST /api/tasks route to accept recurrence object (recurrence_type, cron_expression)
- [x] T063 [US4] Create Recurrence record in database when task has recurrence in backend/src/api/routes/tasks.py
- [x] T064 [US4] Calculate next_occurrence based on recurrence_type (daily=+1day, weekly=+7days, custom=cron)
- [x] T065 [US4] Include recurrence data in TaskCreated event payload
- [x] T066 [US4] Create /events/tasks subscription endpoint in scheduler/src/api/subscriptions.py
- [x] T067 [US4] Handle TaskCreated event in scheduler: extract recurrence, save to State Store (key: recurring:{task_id})
- [x] T068 [US4] Create /triggers/recurring endpoint in scheduler/src/api/triggers.py
- [x] T069 [US4] Implement recurring task check: query State Store for due recurring tasks in scheduler/src/services/recurring.py
- [x] T070 [US4] Publish RecurringTaskScheduled event when recurring task is due
- [x] T071 [US4] Create /events/tasks subscription endpoint in backend/src/api/routes/events.py for RecurringTaskScheduled
- [x] T072 [US4] Handle RecurringTaskScheduled event in backend: create new task instance in PostgreSQL
- [x] T073 [US4] Update next_occurrence in State Store after scheduling in scheduler/src/services/recurring.py
- [x] T074 [US4] Handle TaskDeleted event in scheduler: remove recurring schedule from State Store
- [x] T075 [US4] Add idempotency check using event ID in scheduler to prevent duplicate processing

**Acceptance Criteria**:
- [ ] AC1: Task with daily recurrence creates new instance each day
- [ ] AC2: Task with weekly recurrence creates new instance each week
- [ ] AC3: Task with custom cron expression follows the schedule
- [ ] AC4: Completing individual task instance does not stop recurrence
- [ ] AC5: Deleting source task stops recurrence

**Checkpoint**: Recurring tasks fully functional. Tasks automatically recreate on schedule.

---

## Phase 7: User Story 5 - Due Date Reminders (Priority: P2)

**Goal**: Allow notifications before tasks are due to avoid missing deadlines

**Independent Test**: Create task with reminder, wait for trigger time, verify ReminderTriggered event

### Implementation for User Story 5

- [x] T076 [US5] Update POST /api/tasks route to accept reminders array (trigger_at timestamps)
- [x] T077 [US5] Create Reminder records in database when task has reminders in backend/src/api/routes/tasks.py
- [x] T078 [US5] Validate reminder trigger_at is in future and before due_date
- [x] T079 [US5] Include reminders data in TaskCreated event payload
- [x] T080 [US5] Handle TaskCreated event in scheduler: extract reminders, save each to State Store (key: reminder:{reminder_id})
- [x] T081 [US5] Create /triggers/reminders endpoint in scheduler/src/api/triggers.py
- [x] T082 [US5] Implement reminder check: query State Store for due reminders (trigger_at <= now, fired=false, cancelled=false)
- [x] T083 [US5] Publish ReminderTriggered event to notifications topic when reminder is due
- [x] T084 [US5] Mark reminder as fired in State Store after publishing event
- [x] T085 [US5] Create /events/notifications subscription endpoint in backend/src/api/routes/events.py
- [x] T086 [US5] Handle ReminderTriggered event in backend: update Reminder.fired=true in PostgreSQL
- [x] T087 [US5] Handle TaskCompleted event in scheduler: cancel pending reminders (set cancelled=true in State Store)
- [x] T088 [US5] Handle TaskDeleted event in scheduler: remove all reminders from State Store
- [x] T089 [US5] Add idempotency check using event ID for reminder processing

**Acceptance Criteria**:
- [ ] AC1: Reminder triggers at configured time (within 2 minutes accuracy)
- [ ] AC2: Multiple reminders per task trigger independently
- [ ] AC3: Completing task cancels pending reminders
- [ ] AC4: Deleting task removes all associated reminders

**Checkpoint**: Reminders fully functional. Users get notified before tasks are due.

---

## Phase 8: User Story 6 - Event-Driven Task Lifecycle (Priority: P2)

**Goal**: Ensure all task state changes emit events for decoupled processing

**Independent Test**: Perform task operations, verify corresponding events in message broker

### Implementation for User Story 6

- [x] T090 [US6] Add TaskCompleted event emission in POST /api/tasks/{id}/complete route
- [x] T091 [US6] Add TaskDeleted event emission in DELETE /api/tasks/{id} route
- [x] T092 [US6] Emit TaskCreated event from MCP add_task tool after successful operation
- [x] T093 [US6] Emit TaskUpdated event from MCP update_task tool after successful operation
- [x] T094 [US6] Emit TaskCompleted event from MCP complete_task tool after successful operation
- [x] T095 [US6] Emit TaskDeleted event from MCP delete_task tool after successful operation
- [x] T096 [US6] Handle TaskUpdated event in scheduler: update recurrence/reminders if changed
- [x] T097 [US6] Handle TaskCompleted event in scheduler: deactivate recurrence if needed
- [x] T098 [US6] Add X-Event-Published header to API responses indicating event status
- [x] T099 [US6] Create processed_events idempotency table (optional) per data-model.md Section 1.4

**Acceptance Criteria**:
- [ ] AC1: TaskCreated event published within 1 second of task creation
- [ ] AC2: TaskUpdated event published with changed fields tracked
- [ ] AC3: TaskCompleted event published when task marked complete
- [ ] AC4: TaskDeleted event published when task deleted
- [ ] AC5: Events are idempotent (duplicate events don't cause duplicate actions)

**Checkpoint**: Full event-driven lifecycle implemented. All task changes propagate via events.

---

## Phase 9: Infrastructure - Local Kubernetes Deployment (Minikube + Dapr)

**Purpose**: Deploy complete event-driven system on Minikube with all Dapr components

### 9A: Redis Infrastructure

- [x] T100 [INFRA] Create helm/todo-chatbot/templates/redis/deployment.yaml for Redis server
- [x] T101 [P] [INFRA] Create helm/todo-chatbot/templates/redis/service.yaml (ClusterIP on port 6379)

### 9B: Dapr Components

- [x] T102 [INFRA] Create helm/todo-chatbot/templates/dapr-components/pubsub.yaml (pubsub.redis) per plan.md
- [x] T103 [P] [INFRA] Create helm/todo-chatbot/templates/dapr-components/statestore.yaml (state.redis) per plan.md
- [x] T104 [P] [INFRA] Create helm/todo-chatbot/templates/dapr-components/secrets.yaml (secretstores.kubernetes)
- [x] T105 [P] [INFRA] Create helm/todo-chatbot/templates/dapr-components/bindings.yaml with recurring-task-trigger and reminder-check-trigger cron bindings

### 9C: Service Deployments

- [x] T106 [INFRA] Update helm/todo-chatbot/templates/backend/deployment.yaml with Dapr annotations (dapr.io/enabled, app-id, app-port)
- [x] T107 [P] [INFRA] Create helm/todo-chatbot/templates/scheduler/deployment.yaml with Dapr annotations
- [x] T108 [P] [INFRA] Create helm/todo-chatbot/templates/scheduler/service.yaml (ClusterIP on port 8001)

### 9D: Configuration

- [x] T109 [INFRA] Update helm/todo-chatbot/values.yaml with scheduler and redis configuration sections
- [x] T110 [INFRA] Update helm/todo-chatbot/values-local.yaml with local Minikube-specific overrides
- [x] T111 [INFRA] Create Kubernetes Secret manifest or document kubectl command for app-secrets (jwt-secret, database-url)

### 9E: Deployment Validation

- [ ] T112 [INFRA] Verify Minikube setup: `minikube start --cpus=4 --memory=8192`
- [ ] T113 [INFRA] Verify Dapr installation: `dapr init -k --wait` and `dapr status -k`
- [ ] T114 [INFRA] Build Docker images: `docker build -t todo-backend:local ./backend` and `docker build -t todo-scheduler:local ./scheduler`
- [ ] T115 [INFRA] Deploy with Helm: `helm install todo-chatbot ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml -n todo-app`
- [ ] T116 [INFRA] Verify all pods Running with 2/2 containers (app + Dapr sidecar)
- [ ] T117 [INFRA] Verify Dapr components loaded: `dapr components -n todo-app`

**Checkpoint**: Full system deployed on Minikube with all Dapr building blocks operational.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T118 [POLISH] Update backend/src/api/routes/tasks.py docstrings with event publishing documentation
- [x] T119 [P] [POLISH] Add structured logging for event publishing in backend (success/failure/latency)
- [x] T120 [P] [POLISH] Add structured logging for event subscription handling in scheduler
- [x] T121 [POLISH] Add health check for Dapr sidecar connectivity in backend/src/api/routes/health.py
- [x] T122 [P] [POLISH] Add health check for Dapr sidecar connectivity in scheduler/src/main.py
- [x] T123 [POLISH] Add readiness probe checking State Store connectivity in scheduler
- [x] T124 [POLISH] Run quickstart.md validation end-to-end per specs/009-dapr-event-driven/quickstart.md
- [x] T125 [POLISH] Document troubleshooting steps in quickstart.md for common deployment issues
- [ ] T126 [POLISH] Verify all acceptance scenarios from spec.md Section 4 pass

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ───────────────────────────────┐
                                               │
Phase 2: Foundational (2A→2B→2C→2D→2E) ───────┤ BLOCKS ALL USER STORIES
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    USER STORIES (Can run in parallel)            │
├──────────────────────────────────────────────────────────────────┤
│  Phase 3: US1 Priority (P1) ─────────────────────────────────┐   │
│  Phase 4: US2 Tags (P1) ─────────────────────────────────────┤   │
│  Phase 5: US3 Search (P1) ───────────────────────────────────┤   │
│                                                               │   │
│  Phase 6: US4 Recurring (P2) ────────────────────────────────┤   │
│  Phase 7: US5 Reminders (P2) ────────────────────────────────┤   │
│  Phase 8: US6 Event Lifecycle (P2) ──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                                               │
Phase 9: Infrastructure (depends on US4-US6)  ─┤
                                               │
Phase 10: Polish (depends on all above) ───────┘
```

### User Story Dependencies

| Story | Can Start After | Dependencies on Other Stories |
|-------|-----------------|-------------------------------|
| US1 (Priority) | Phase 2 complete | None - fully independent |
| US2 (Tags) | Phase 2 complete | None - fully independent |
| US3 (Search) | Phase 2 complete | Uses priority/tags from US1/US2 but can test independently |
| US4 (Recurring) | Phase 2 complete | Requires Scheduler (built in Phase 2E) |
| US5 (Reminders) | Phase 2 complete | Requires Scheduler (built in Phase 2E) |
| US6 (Events) | Phase 2 complete | Coordinates with US4/US5 for full event flow |
| Infrastructure | US4, US5, US6 | Needs all services ready for deployment |

### Task Dependencies Within Phases

**Phase 2 (Foundational)**:
- 2A (Schema): T006→T007→T008→T011, T009/T010 parallel, T012→T013→T014→T015
- 2B (Events): T016→T017→(T018-T021 parallel)→T022
- 2C (Dapr): T023→T024→T025→T026→T027
- 2D (Schemas): T028→T029→T030, T031/T032 parallel
- 2E (Scheduler): T033/T034/T035/T036 parallel→T037→T038→T039

**Phase 6 (US4 Recurring)**:
- T062→T063→T064→T065 (Backend setup)
- T066→T067 (Scheduler subscription)
- T068→T069→T070→T073 (Scheduler trigger)
- T071→T072 (Backend subscription)
- T074, T075 (Cleanup handlers)

**Phase 7 (US5 Reminders)**:
- T076→T077→T078→T079 (Backend setup)
- T080 (Scheduler subscription)
- T081→T082→T083→T084 (Scheduler trigger)
- T085→T086 (Backend subscription)
- T087, T088, T089 (Cleanup handlers)

### Parallel Opportunities

**Same phase, different files:**
- T002, T003, T004 (Setup - different files)
- T009, T010 (Models - different files)
- T018, T019, T020, T021 (Event schemas - same file but independent sections)
- T031, T032 (API schemas - different files)
- T033, T034, T035, T036 (Scheduler schemas - different files)
- T100, T101 (Redis manifests)
- T102, T103, T104, T105 (Dapr components - different files)
- T106, T107, T108 (Deployment manifests - different files)

**Across user stories (after Phase 2):**
- US1, US2, US3 can all proceed in parallel (P1 priority, independent features)
- US4, US5 can proceed in parallel (both use Scheduler but different features)

---

## Parallel Example: P1 User Stories

```bash
# After Phase 2 is complete, launch all P1 stories in parallel:

# Developer A: User Story 1 (Priority)
T040 → T041 → T042 → T043 → T044 → T045 → T046

# Developer B: User Story 2 (Tags)
T047 → T048 → T049 → T050 → T051 → T052 → T053 → T054

# Developer C: User Story 3 (Search)
T055 → T056 → T057 → T058 → T059 → T060 → T061
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: US1 Priority → **VALIDATE**
4. Complete Phase 4: US2 Tags → **VALIDATE**
5. Complete Phase 5: US3 Search → **VALIDATE**
6. **MVP COMPLETE**: Core task management with priority, tags, search

### Full Feature (Add P2 Stories)

7. Complete Phase 6: US4 Recurring
8. Complete Phase 7: US5 Reminders
9. Complete Phase 8: US6 Event Lifecycle
10. Complete Phase 9: Infrastructure (Minikube deployment)
11. Complete Phase 10: Polish

### Incremental Validation

After each user story:
1. Run manual acceptance tests
2. Verify events in Redis Streams (for event-emitting tasks)
3. Check Dapr Dashboard for component health
4. Commit and tag milestone

---

## Success Criteria Summary

| Metric | Target | Validation |
|--------|--------|------------|
| Task CRUD latency | < 3 seconds | Manual timing |
| Search latency (1000 tasks) | < 2 seconds | Manual timing |
| Recurring task accuracy | Within 2 minutes | Wait for cron trigger |
| Reminder accuracy | Within 2 minutes | Wait for reminder time |
| Event publishing latency | < 1 second | Check Redis timestamps |
| Pod startup | All Running in 5 min | `kubectl get pods -w` |
| Dapr components | All loaded | `dapr components -n todo-app` |

---

## Notes

- [P] tasks can run in parallel (different files, no dependencies)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

**Task Count**: 126 tasks total
- Setup: 5 tasks
- Foundational: 34 tasks
- US1 Priority: 7 tasks
- US2 Tags: 8 tasks
- US3 Search: 7 tasks
- US4 Recurring: 14 tasks
- US5 Reminders: 14 tasks
- US6 Events: 10 tasks
- Infrastructure: 18 tasks
- Polish: 9 tasks

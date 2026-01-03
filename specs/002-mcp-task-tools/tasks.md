# Tasks: MCP Task Tools

**Input**: Design documents from `/specs/002-mcp-task-tools/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per testing strategy in plan.md (unit + integration tests for each tool)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`
- Paths shown below follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and MCP server structure

- [x] T001 Create MCP server directory structure: `backend/src/mcp_server/`, `backend/src/mcp_server/tools/`, `backend/src/models/`, `backend/src/db/`
- [x] T002 Add MCP SDK dependency `mcp>=1.25,<2` to `backend/pyproject.toml` or `backend/requirements.txt`
- [x] T003 [P] Create `backend/src/mcp_server/__init__.py` with package exports
- [x] T004 [P] Create `backend/src/mcp_server/tools/__init__.py` with tool imports
- [x] T005 [P] Create `backend/src/models/__init__.py` with model exports
- [x] T006 [P] Create `backend/src/db/__init__.py` with database exports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Create Task SQLModel entity in `backend/src/models/task.py` per data-model.md (TaskStatus enum, Task model with id, user_id, description, status, created_at, completed_at)
- [x] T008 Create async database engine setup in `backend/src/db/engine.py` with environment-based DATABASE_URL
- [x] T009 Create ToolResult and TaskData Pydantic schemas in `backend/src/mcp_server/schemas.py` per contracts/mcp-tools.md
- [x] T010 Create FastMCP server with lifespan context in `backend/src/mcp_server/server.py` (app_lifespan, mcp instance, AppContext dataclass)
- [x] T011 Create MCP test fixtures in `backend/tests/mcp/conftest.py` (mock_ctx fixture, test database session)
- [x] T012 Create `backend/src/mcp_server/__main__.py` entry point for running MCP server via `python -m src.mcp_server`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - AI Agent Creates a Task (Priority: P1)

**Goal**: Enable AI agents to create new tasks for authenticated users via `add_task` MCP tool

**Independent Test**: Invoke `add_task` with valid user_id and description, verify task created with correct ownership and pending status

### Tests for User Story 1

- [x] T013 [P] [US1] Create unit test for add_task tool in `backend/tests/mcp/test_add_task.py` (test success, empty description, description too long, missing user_id)

### Implementation for User Story 1

- [x] T014 [US1] Implement `add_task` MCP tool in `backend/src/mcp_server/tools/add_task.py` per contracts/mcp-tools.md (validate user_id, validate description length, create Task with pending status, return TaskData)
- [x] T015 [US1] Register add_task tool in `backend/src/mcp_server/tools/__init__.py`
- [x] T016 [US1] Import add_task in `backend/src/mcp_server/server.py` to register with FastMCP

**Checkpoint**: User Story 1 complete - AI agents can now create tasks

---

## Phase 4: User Story 2 - AI Agent Lists User Tasks (Priority: P1)

**Goal**: Enable AI agents to retrieve all tasks for an authenticated user via `list_tasks` MCP tool

**Independent Test**: Create tasks for user, invoke `list_tasks`, verify all user's tasks returned sorted by created_at descending

### Tests for User Story 2

- [x] T017 [P] [US2] Create unit test for list_tasks tool in `backend/tests/mcp/test_list_tasks.py` (test with tasks, empty list, user isolation)

### Implementation for User Story 2

- [x] T018 [US2] Implement `list_tasks` MCP tool in `backend/src/mcp_server/tools/list_tasks.py` per contracts/mcp-tools.md (validate user_id, query tasks by user_id, sort by created_at DESC, return List[TaskData])
- [x] T019 [US2] Register list_tasks tool in `backend/src/mcp_server/tools/__init__.py`
- [x] T020 [US2] Import list_tasks in `backend/src/mcp_server/server.py` to register with FastMCP

**Checkpoint**: User Stories 1 + 2 complete - AI agents can create and list tasks (core read/write)

---

## Phase 5: User Story 3 - AI Agent Updates a Task (Priority: P2)

**Goal**: Enable AI agents to modify task descriptions via `update_task` MCP tool

**Independent Test**: Create task, invoke `update_task` with new description, verify description updated and other fields unchanged

### Tests for User Story 3

- [x] T021 [P] [US3] Create unit test for update_task tool in `backend/tests/mcp/test_update_task.py` (test success, not found, access denied, validation errors)

### Implementation for User Story 3

- [x] T022 [US3] Implement `update_task` MCP tool in `backend/src/mcp_server/tools/update_task.py` per contracts/mcp-tools.md (validate inputs, load task, verify ownership, update description only, return TaskData)
- [x] T023 [US3] Register update_task tool in `backend/src/mcp_server/tools/__init__.py`
- [x] T024 [US3] Import update_task in `backend/src/mcp_server/server.py` to register with FastMCP

**Checkpoint**: User Stories 1-3 complete - AI agents can create, list, and update tasks

---

## Phase 6: User Story 4 - AI Agent Completes a Task (Priority: P2)

**Goal**: Enable AI agents to mark tasks as completed via `complete_task` MCP tool

**Independent Test**: Create pending task, invoke `complete_task`, verify status changed to completed and completed_at set

### Tests for User Story 4

- [x] T025 [P] [US4] Create unit test for complete_task tool in `backend/tests/mcp/test_complete_task.py` (test success, idempotent completion, not found, access denied)

### Implementation for User Story 4

- [x] T026 [US4] Implement `complete_task` MCP tool in `backend/src/mcp_server/tools/complete_task.py` per contracts/mcp-tools.md (validate inputs, load task, verify ownership, set status=completed + completed_at, idempotent if already completed, return TaskData)
- [x] T027 [US4] Register complete_task tool in `backend/src/mcp_server/tools/__init__.py`
- [x] T028 [US4] Import complete_task in `backend/src/mcp_server/server.py` to register with FastMCP

**Checkpoint**: User Stories 1-4 complete - AI agents can create, list, update, and complete tasks

---

## Phase 7: User Story 5 - AI Agent Deletes a Task (Priority: P3)

**Goal**: Enable AI agents to permanently remove tasks via `delete_task` MCP tool

**Independent Test**: Create task, invoke `delete_task`, verify task no longer exists in list_tasks

### Tests for User Story 5

- [x] T029 [P] [US5] Create unit test for delete_task tool in `backend/tests/mcp/test_delete_task.py` (test success, idempotent deletion, access denied)

### Implementation for User Story 5

- [x] T030 [US5] Implement `delete_task` MCP tool in `backend/src/mcp_server/tools/delete_task.py` per contracts/mcp-tools.md (validate inputs, check ownership if exists, delete task, idempotent for missing tasks, return success with null data)
- [x] T031 [US5] Register delete_task tool in `backend/src/mcp_server/tools/__init__.py`
- [x] T032 [US5] Import delete_task in `backend/src/mcp_server/server.py` to register with FastMCP

**Checkpoint**: All 5 user stories complete - full CRUD via MCP tools

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, ownership validation, and documentation

- [ ] T033 Create ownership isolation integration test in `backend/tests/integration/test_mcp_ownership.py` (verify User A cannot access/modify/delete User B's tasks)
- [ ] T034 Add logging to MCP server in `backend/src/mcp_server/server.py` (log tool invocations with user_id, tool name, result)
- [x] T035 Run all tests and verify all 5 tools work correctly: `pytest backend/tests/mcp/ -v`
- [ ] T036 Validate against quickstart.md: manually test add_task → list_tasks → update_task → complete_task → delete_task flow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (both P1)
  - US3 and US4 can proceed in parallel (both P2)
  - US5 can proceed after US1+US2 (P3)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Priority | Dependencies | Can Parallel With |
|-------|----------|--------------|-------------------|
| US1 (add_task) | P1 | Foundational only | US2 |
| US2 (list_tasks) | P1 | Foundational only | US1 |
| US3 (update_task) | P2 | Foundational only | US4 |
| US4 (complete_task) | P2 | Foundational only | US3 |
| US5 (delete_task) | P3 | Foundational only | None (lowest priority) |

### Within Each User Story

- Tests FIRST (write and ensure they fail before implementation)
- Implement tool in `tools/` directory
- Register in `tools/__init__.py`
- Import in `server.py`

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004, T005, T006 can run in parallel (different `__init__.py` files)

**Phase 2 (Foundational)**: T007 and T008 can run in parallel (models vs db)

**User Stories**: After Foundational completes:
- US1 + US2 in parallel (both P1, independent tools)
- US3 + US4 in parallel (both P2, independent tools)
- All test tasks marked [P] can run in parallel with other user story tests

---

## Parallel Execution Examples

### Example 1: Parallel Setup (Phase 1)

```bash
# Launch all init files in parallel:
Task T003: Create backend/src/mcp_server/__init__.py
Task T004: Create backend/src/mcp_server/tools/__init__.py
Task T005: Create backend/src/models/__init__.py
Task T006: Create backend/src/db/__init__.py
```

### Example 2: Parallel P1 User Stories (US1 + US2)

```bash
# After Foundational (Phase 2) completes, launch in parallel:

# Developer A - User Story 1:
Task T013: Create test_add_task.py
Task T014: Implement add_task tool
Task T015-T016: Register tool

# Developer B - User Story 2:
Task T017: Create test_list_tasks.py
Task T018: Implement list_tasks tool
Task T019-T020: Register tool
```

### Example 3: Parallel P2 User Stories (US3 + US4)

```bash
# After P1 stories complete, launch in parallel:

# Developer A - User Story 3:
Task T021: Create test_update_task.py
Task T022: Implement update_task tool
Task T023-T024: Register tool

# Developer B - User Story 4:
Task T025: Create test_complete_task.py
Task T026: Implement complete_task tool
Task T027-T028: Register tool
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (add_task)
4. Complete Phase 4: User Story 2 (list_tasks)
5. **STOP and VALIDATE**: Test create + list flow independently
6. Deploy/demo if ready - AI can now add and view tasks

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (add_task) → Test → **Minimal MVP** (can create tasks)
3. Add US2 (list_tasks) → Test → **Read MVP** (can create + list)
4. Add US3 (update_task) → Test → Can modify tasks
5. Add US4 (complete_task) → Test → Can complete tasks
6. Add US5 (delete_task) → Test → **Full CRUD** (all 5 tools working)
7. Polish phase → Integration tests, logging, validation

### Suggested MVP Scope

**Minimum**: Phase 1 + Phase 2 + Phase 3 (US1: add_task only)
- AI agents can create tasks
- Tests verify ownership and validation

**Recommended MVP**: Phase 1 + Phase 2 + Phase 3 + Phase 4 (US1 + US2)
- AI agents can create and list tasks
- Core read/write functionality complete
- 2 of 5 tools working

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 36 |
| Setup Tasks | 6 |
| Foundational Tasks | 6 |
| US1 Tasks | 4 |
| US2 Tasks | 4 |
| US3 Tasks | 4 |
| US4 Tasks | 4 |
| US5 Tasks | 4 |
| Polish Tasks | 4 |
| Parallel Opportunities | 15 tasks marked [P] |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- All 5 MCP tools (add_task, list_tasks, update_task, complete_task, delete_task) covered
- Ownership enforcement tested in integration phase
- Commit after each task or logical group

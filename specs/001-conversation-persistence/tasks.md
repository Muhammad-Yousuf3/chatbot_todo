# Tasks: Conversation Persistence & Stateless Chat Contract

**Input**: Design documents from `/specs/001-conversation-persistence/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are NOT explicitly requested in the spec. Test tasks are included as optional guidance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`
- Paths follow the structure defined in plan.md

---

## Phase 1: Setup

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend directory structure per plan.md (`backend/src/`, `backend/tests/`)
- [x] T002 Initialize Python project with pyproject.toml including FastAPI, SQLModel, Pydantic, uvicorn, pytest
- [x] T003 [P] Create .env.example with DATABASE_URL placeholder in `backend/`
- [x] T004 [P] Create .gitignore for Python project in `backend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create database session management in `backend/src/db/session.py`
- [x] T006 Create MessageRole enum in `backend/src/models/__init__.py`
- [x] T007 [P] Create Conversation SQLModel in `backend/src/models/conversation.py`
- [x] T008 [P] Create Message SQLModel in `backend/src/models/message.py`
- [x] T009 Create error response schemas in `backend/src/api/schemas/error.py`
- [x] T010 Create auth dependency stub (get_current_user_id) in `backend/src/api/deps.py`
- [x] T011 Create FastAPI app entry point in `backend/src/main.py`
- [x] T012 Create database initialization script in `backend/src/db/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Send Message in New Conversation (Priority: P1)

**Goal**: User sends first message, system creates conversation and persists message

**Independent Test**: Send POST /api/chat without conversation_id, verify conversation created and message persisted

### Implementation for User Story 1

- [x] T013 [US1] Create SendMessageRequest schema in `backend/src/api/schemas/chat.py`
- [x] T014 [US1] Create Message response schema in `backend/src/api/schemas/chat.py`
- [x] T015 [US1] Create SendMessageResponse schema in `backend/src/api/schemas/chat.py`
- [x] T016 [US1] Implement create_conversation function in `backend/src/services/chat_service.py`
- [x] T017 [US1] Implement create_message function in `backend/src/services/chat_service.py`
- [x] T018 [US1] Implement generate_conversation_title function in `backend/src/services/chat_service.py`
- [x] T019 [US1] Create POST /api/chat endpoint (new conversation flow) in `backend/src/api/routes/chat.py`
- [x] T020 [US1] Register chat router in `backend/src/main.py`
- [x] T021 [US1] Add message content validation (non-empty, max 32000 chars) in `backend/src/api/schemas/chat.py`

**Checkpoint**: User Story 1 complete - can create new conversations with first message

---

## Phase 4: User Story 2 - Continue Existing Conversation (Priority: P1)

**Goal**: User sends message to existing conversation, system loads history and appends

**Independent Test**: Create conversation (US1), then POST /api/chat with conversation_id, verify message appended and history returned

### Implementation for User Story 2

- [x] T022 [US2] Implement get_conversation_by_id function in `backend/src/services/chat_service.py`
- [x] T023 [US2] Implement verify_conversation_ownership function in `backend/src/services/chat_service.py`
- [x] T024 [US2] Implement get_conversation_messages function in `backend/src/services/chat_service.py`
- [x] T025 [US2] Implement update_conversation_timestamp function in `backend/src/services/chat_service.py`
- [x] T026 [US2] Extend POST /api/chat to handle existing conversation flow in `backend/src/api/routes/chat.py`
- [x] T027 [US2] Add conversation_id UUID validation in `backend/src/api/routes/chat.py`
- [x] T028 [US2] Add 404 error handling for missing conversation in `backend/src/api/routes/chat.py`
- [x] T029 [US2] Add 403 error handling for ownership violation in `backend/src/api/routes/chat.py`

**Checkpoint**: User Stories 1 AND 2 complete - full chat send/continue flow working

---

## Phase 5: User Story 3 - Retrieve Conversation History (Priority: P2)

**Goal**: Retrieve full conversation with all messages in chronological order

**Independent Test**: GET /api/conversations/{id} returns conversation with ordered messages

### Implementation for User Story 3

- [x] T030 [US3] Create Conversation response schema in `backend/src/api/schemas/conversations.py`
- [x] T031 [US3] Create ConversationDetailResponse schema in `backend/src/api/schemas/conversations.py`
- [x] T032 [US3] Create GET /api/conversations/{conversation_id} endpoint in `backend/src/api/routes/conversations.py`
- [x] T033 [US3] Register conversations router in `backend/src/main.py`
- [x] T034 [US3] Add 400 error handling for invalid UUID format in `backend/src/api/routes/conversations.py`

**Checkpoint**: User Story 3 complete - can retrieve full conversation history

---

## Phase 6: User Story 4 - List User Conversations (Priority: P3)

**Goal**: List all conversations for authenticated user, ordered by recent activity

**Independent Test**: GET /api/conversations returns list of user's conversations with metadata

### Implementation for User Story 4

- [x] T035 [US4] Create ConversationSummary schema in `backend/src/api/schemas/conversations.py`
- [x] T036 [US4] Create ConversationListResponse schema in `backend/src/api/schemas/conversations.py`
- [x] T037 [US4] Implement list_user_conversations function in `backend/src/services/chat_service.py`
- [x] T038 [US4] Implement get_conversation_message_count function in `backend/src/services/chat_service.py`
- [x] T039 [US4] Create GET /api/conversations endpoint with pagination in `backend/src/api/routes/conversations.py`
- [x] T040 [US4] Add limit/offset query parameters (default 20, max 100) in `backend/src/api/routes/conversations.py`

**Checkpoint**: All user stories complete - full conversation persistence API working

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Add comprehensive docstrings to all service functions in `backend/src/services/chat_service.py`
- [ ] T042 [P] Add request/response logging middleware in `backend/src/main.py`
- [ ] T043 Create pytest conftest with database fixtures in `backend/tests/conftest.py`
- [ ] T044 [P] Create integration test for new conversation flow in `backend/tests/integration/test_chat.py`
- [ ] T045 [P] Create integration test for continue conversation in `backend/tests/integration/test_chat.py`
- [ ] T046 [P] Create integration test for conversation history in `backend/tests/integration/test_conversations.py`
- [ ] T047 [P] Create integration test for list conversations in `backend/tests/integration/test_conversations.py`
- [ ] T048 Run quickstart.md validation manually

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (shares chat endpoint)
- **User Story 3 (Phase 5)**: Depends on Foundational (can run parallel to US1/US2)
- **User Story 4 (Phase 6)**: Depends on Foundational (can run parallel to US1/US2/US3)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundational → can start immediately after Phase 2
- **User Story 2 (P1)**: Foundational + US1 → extends the same endpoint
- **User Story 3 (P2)**: Foundational only → independent of US1/US2
- **User Story 4 (P3)**: Foundational only → independent of US1/US2/US3

### Within Each User Story

- Schemas before services
- Services before routes
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks T003, T004 can run in parallel
- Foundational tasks T007, T008 (models) can run in parallel
- User Stories 3 and 4 can run in parallel with each other
- All Polish phase tests (T044-T047) can run in parallel

---

## Parallel Execution Examples

### Phase 2: Foundational Models

```bash
# Launch model creation in parallel:
Task: "Create Conversation SQLModel in backend/src/models/conversation.py"
Task: "Create Message SQLModel in backend/src/models/message.py"
```

### Phase 5+6: User Stories 3 & 4 (can run in parallel)

```bash
# If team capacity allows, these stories are independent:
Developer A: User Story 3 (T030-T034)
Developer B: User Story 4 (T035-T040)
```

### Phase 7: Integration Tests

```bash
# All tests can run in parallel:
Task: "Integration test for new conversation flow"
Task: "Integration test for continue conversation"
Task: "Integration test for conversation history"
Task: "Integration test for list conversations"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test sending first message creates conversation
5. Deploy/demo if ready - this alone is a working increment

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Multi-turn chat working
4. Add User Story 3 → Test independently → History retrieval working
5. Add User Story 4 → Test independently → Conversation list working
6. Polish phase → Full test coverage and documentation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 2 (sequential, same endpoint)
   - Developer B: User Story 3 (independent)
   - Developer C: User Story 4 (independent)
3. Merge and run integration tests

---

## Task Summary

| Phase | Tasks | Parallel Opportunities |
|-------|-------|----------------------|
| Setup | 4 | 2 tasks parallel |
| Foundational | 8 | 2 tasks parallel (models) |
| User Story 1 | 9 | Sequential (single endpoint) |
| User Story 2 | 8 | Sequential (extends US1) |
| User Story 3 | 5 | Can run parallel to US4 |
| User Story 4 | 6 | Can run parallel to US3 |
| Polish | 8 | 4 tests parallel |
| **Total** | **48** | |

### Tasks per User Story

- US1: 9 tasks (T013-T021)
- US2: 8 tasks (T022-T029)
- US3: 5 tasks (T030-T034)
- US4: 6 tasks (T035-T040)

### Suggested MVP Scope

**Minimum**: Phase 1 + Phase 2 + Phase 3 (User Story 1) = 21 tasks
- This delivers: Create new conversation with first message
- Validates: Full stateless persistence flow

**Recommended MVP**: Add Phase 4 (User Story 2) = 29 tasks
- This delivers: Complete chat send/continue flow
- Validates: Multi-turn conversation support

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests in Phase 7 are optional but recommended for quality assurance

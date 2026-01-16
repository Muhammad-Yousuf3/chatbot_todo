# Tasks: LLM-Driven Agent Runtime (Gemini-Backed)

**Input**: Design documents from `/specs/005-llm-agent-runtime/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests included per spec.md Testing Strategy section. Mock LLM for deterministic tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`
- Based on plan.md structure: new `llm_runtime` module under `backend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Install google-genai dependency via `uv add google-genai` in backend/
- [x] T002 [P] Create llm_runtime module structure: `backend/src/llm_runtime/__init__.py`
- [x] T003 [P] Create test directory structure: `backend/tests/llm_runtime/__init__.py`
- [x] T004 [P] Add LLM configuration to environment: update `.env.example` with GEMINI_API_KEY, GEMINI_MODEL

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Error Types & Schemas

- [x] T005 [P] Create LLM error types in `backend/src/llm_runtime/errors.py`: LLMError, RateLimitError, TimeoutError, InvalidResponseError, ToolNotFoundError
- [x] T006 [P] Create LLM schemas in `backend/src/llm_runtime/schemas.py`: LLMMessage, FunctionCall, FunctionResponse, LLMRequest, LLMResponse, ToolDeclaration, TokenUsage

### Constitution (System Prompt)

- [x] T007 Create constitution file in `backend/src/llm_runtime/constitution.md` with behavioral rules, tool whitelist, response guidelines

### Test Mocks

- [x] T008 [P] Create mock LLM adapter in `backend/tests/llm_runtime/mocks.py`: MockLLMAdapter with configurable responses
- [x] T009 [P] Create test fixtures in `backend/tests/llm_runtime/conftest.py`: mock adapter, sample contexts, tool declarations

### GeminiAdapter (LLM Communication)

- [x] T010 Implement GeminiAdapter in `backend/src/llm_runtime/adapter.py`: __init__, generate, get_tool_declarations, message conversion, error handling

### ToolExecutor (MCP Bridge)

- [x] T011 Implement ToolExecutor in `backend/src/llm_runtime/executor.py`: TOOL_REGISTRY, execute, get_available_tools, get_tool_declarations, user_id injection

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - LLM Decides to Invoke Tool (Priority: P1) 🎯 MVP

**Goal**: User sends natural language requesting task operation; LLM invokes appropriate MCP tool and returns helpful response

**Independent Test**: Send "remind me to buy groceries tomorrow" → verify `add_task` MCP tool invoked with correct params → confirmation response returned

### Unit Tests for User Story 1

- [x] T012 [P] [US1] Create test for tool invocation flow in `backend/tests/llm_runtime/test_engine.py`: test_invoke_add_task, test_invoke_list_tasks, test_invoke_complete_task
- [x] T013 [P] [US1] Create test for tool execution in `backend/tests/llm_runtime/test_executor.py`: test_execute_add_task, test_execute_list_tasks, test_user_id_injection

### Implementation for User Story 1

- [x] T014 [US1] Implement LLMAgentEngine core in `backend/src/llm_runtime/engine.py`: __init__, _build_messages_from_context, _invoke_llm, _execute_tool_calls
- [x] T015 [US1] Implement process_message in `backend/src/llm_runtime/engine.py`: main entry point matching DecisionContext → AgentDecision contract
- [x] T016 [US1] Add decision mapping in `backend/src/llm_runtime/engine.py`: _map_llm_response_to_decision for INVOKE_TOOL type
- [x] T017 [US1] Export public API in `backend/src/llm_runtime/__init__.py`: LLMAgentEngine, GeminiAdapter, ToolExecutor

**Checkpoint**: User Story 1 complete - can invoke MCP tools via LLM decisions ✅

---

## Phase 4: User Story 2 - LLM Responds Directly Without Tools (Priority: P1)

**Goal**: User sends message not requiring task operations (greeting, general question); LLM responds directly without invoking tools

**Independent Test**: Send "hello, how are you?" → verify no MCP tools invoked → LLM provides friendly response

### Unit Tests for User Story 2

- [x] T018 [P] [US2] Create test for direct response in `backend/tests/llm_runtime/test_engine.py`: test_greeting_no_tools, test_capability_question_no_tools, test_off_topic_no_tools

### Implementation for User Story 2

- [x] T019 [US2] Add RESPOND_ONLY decision handling in `backend/src/llm_runtime/engine.py`: extend _map_llm_response_to_decision for text-only responses
- [x] T020 [US2] Add constitution guidance for non-task messages in `backend/src/llm_runtime/constitution.md`: clarify when NOT to use tools

**Checkpoint**: User Stories 1 & 2 complete - core decision types working (tool invocation + direct response) ✅

---

## Phase 5: User Story 3 - LLM Requests Clarification (Priority: P2)

**Goal**: User sends ambiguous message; LLM asks clarifying question before proceeding

**Independent Test**: Send "groceries" alone → verify LLM asks clarification about intended action

### Unit Tests for User Story 3

- [x] T021 [P] [US3] Create test for clarification in `backend/tests/llm_runtime/test_engine.py`: test_ambiguous_single_word, test_multiple_possible_intents, test_missing_context_reference

### Implementation for User Story 3

- [x] T022 [US3] Add ASK_CLARIFICATION decision handling in `backend/src/llm_runtime/engine.py`: detect question patterns in LLM response
- [x] T023 [US3] Add constitution guidance for ambiguity in `backend/src/llm_runtime/constitution.md`: instruct LLM to ask ONE clarifying question when intent unclear

**Checkpoint**: User Story 3 complete - LLM handles ambiguous input gracefully ✅

---

## Phase 6: User Story 4 - Observability Logging (Priority: P2)

**Goal**: All agent decisions logged with full context for audit and debugging via Spec 004 observability layer

**Independent Test**: Process any message → verify DecisionLog and ToolInvocationLog records created with correct categories

### Unit Tests for User Story 4

- [x] T024 [P] [US4] Create test for logging integration in `backend/tests/llm_runtime/test_engine.py`: test_decision_log_on_tool_invoke, test_decision_log_on_respond, test_tool_invocation_log

### Implementation for User Story 4

- [x] T025 [US4] Integrate logging_service in `backend/src/llm_runtime/engine.py`: import and call write_decision_log, write_tool_invocation_log (via chat.py integration)
- [x] T026 [US4] Add outcome category mapping in `backend/src/llm_runtime/engine.py`: SUCCESS:TASK_COMPLETED, SUCCESS:RESPONSE_GIVEN, AMBIGUITY:UNCLEAR_INTENT, ERROR:*, REFUSAL:* (via chat.py)
- [x] T027 [US4] Add duration tracking in `backend/src/llm_runtime/engine.py`: measure LLM call time, tool execution time

**Checkpoint**: User Story 4 complete - full observability for all decisions ✅

---

## Phase 7: User Story 5 - Safety and Refusal Handling (Priority: P2)

**Goal**: LLM politely refuses out-of-scope requests and explains limitations

**Independent Test**: Send "what's the weather?" → verify polite refusal explaining task-only capabilities

### Unit Tests for User Story 5

- [x] T028 [P] [US5] Create test for refusal handling in `backend/tests/llm_runtime/test_engine.py`: test_out_of_scope_request, test_rate_limit_handling, test_unknown_tool_rejected

### Implementation for User Story 5

- [x] T029 [US5] Add refusal detection in `backend/src/llm_runtime/engine.py`: pattern detection for refusal responses
- [x] T030 [US5] Add rate limit handling in `backend/src/llm_runtime/adapter.py`: catch RateLimitError, return graceful response
- [x] T031 [US5] Add tool whitelist enforcement in `backend/src/llm_runtime/executor.py`: validate tool_name against ALLOWED_TOOLS, raise ToolNotFoundError
- [x] T032 [US5] Add constitution safety rules in `backend/src/llm_runtime/constitution.md`: instructions for politely declining off-topic requests

**Checkpoint**: User Story 5 complete - safe operation with clear boundaries ✅

---

## Phase 8: User Story 6 - Multi-Turn Tool Execution (Priority: P3)

**Goal**: Complex requests requiring multiple tool calls; LLM orchestrates sequence, feeding results back

**Independent Test**: Send "show my tasks and then mark the first one complete" → verify sequential tool execution

### Unit Tests for User Story 6

- [x] T033 [P] [US6] Create test for multi-turn in `backend/tests/llm_runtime/test_engine.py`: test_sequential_tool_calls, test_tool_result_fed_back, test_max_iteration_limit

### Implementation for User Story 6

- [x] T034 [US6] Implement tool loop in `backend/src/llm_runtime/engine.py`: _tool_execution_loop with iteration counter, result accumulation
- [x] T035 [US6] Add tool result messaging in `backend/src/llm_runtime/engine.py`: append FunctionResponse to messages, re-invoke LLM
- [x] T036 [US6] Add max iteration enforcement in `backend/src/llm_runtime/engine.py`: MAX_ITERATIONS=5, graceful termination with helpful message
- [x] T037 [US6] Add tool failure recovery in `backend/src/llm_runtime/engine.py`: surface tool errors to LLM for recovery attempt

**Checkpoint**: User Story 6 complete - complex multi-tool orchestration working ✅

---

## Phase 9: API Integration

**Purpose**: Integrate LLMAgentEngine into existing chat route

- [x] T038 Integrate LLMAgentEngine in `backend/src/api/routes/chat.py`: replace AgentDecisionEngine with LLMAgentEngine initialization
- [x] T039 Add constitution loader in `backend/src/api/routes/chat.py`: helper function to load constitution.md
- [x] T040 Add LLM config loading in `backend/src/api/routes/chat.py`: read GEMINI_API_KEY from environment, configure adapter
- [x] T041 Create integration test in `backend/tests/llm_runtime/test_integration.py`: end-to-end test with mock adapter, real MCP tools

**Checkpoint**: LLM runtime integrated into API - full end-to-end flow working ✅

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T042 [P] Add error fallback responses in `backend/src/llm_runtime/engine.py`: user-friendly messages for LLM failures, timeouts, rate limits
- [x] T043 [P] Add request validation in `backend/src/llm_runtime/engine.py`: validate DecisionContext, handle missing user_id
- [x] T044 [P] Add logging/debugging helpers in `backend/src/llm_runtime/engine.py`: log LLM requests/responses at debug level
- [x] T045 Run all tests via `uv run pytest backend/tests/llm_runtime/ -v` (37 tests passing)
- [ ] T046 Validate quickstart.md scenarios manually (requires GEMINI_API_KEY)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 & US2 can proceed in parallel (both P1)
  - US3, US4, US5 can proceed in parallel after US1+US2 (all P2)
  - US6 can start after Foundational but benefits from US1 completion (P3)
- **API Integration (Phase 9)**: Depends on at least US1+US2 completion
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Shares engine with US1, independent test
- **User Story 3 (P2)**: Can start after Foundational - Independent of US1/US2
- **User Story 4 (P2)**: Can start after Foundational - Adds logging to existing engine
- **User Story 5 (P2)**: Can start after Foundational - Adds safety layer
- **User Story 6 (P3)**: Benefits from US1 (tool invocation) being complete first

### Within Each User Story

- Tests should be written first and fail before implementation
- Schema/model tasks before service tasks
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T005-T006, T008-T009)
- Once Foundational completes, US1 and US2 can start in parallel
- Tests within each user story marked [P] can run in parallel
- US3, US4, US5 can all proceed in parallel after Foundational

---

## Parallel Example: Foundational Phase

```bash
# Launch schema + error tasks in parallel:
Task T005: "Create LLM error types in backend/src/llm_runtime/errors.py"
Task T006: "Create LLM schemas in backend/src/llm_runtime/schemas.py"

# Launch mock + fixture tasks in parallel:
Task T008: "Create mock LLM adapter in backend/tests/llm_runtime/mocks.py"
Task T009: "Create test fixtures in backend/tests/llm_runtime/conftest.py"
```

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all US1 tests together:
Task T012: "Create test for tool invocation flow in backend/tests/llm_runtime/test_engine.py"
Task T013: "Create test for tool execution in backend/tests/llm_runtime/test_executor.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (tool invocation)
4. Complete Phase 4: User Story 2 (direct response)
5. **STOP and VALIDATE**: Test both stories independently
6. Complete Phase 9: API Integration
7. Deploy/demo if ready - this is the MVP!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 2 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 (clarification) → Test → Enhanced UX
4. Add User Story 4 (logging) → Test → Full observability
5. Add User Story 5 (safety) → Test → Production-ready safety
6. Add User Story 6 (multi-turn) → Test → Advanced capability

### Suggested MVP Scope

**Minimum Viable Product**: Phases 1-4 + Phase 9 (API Integration)
- Setup + Foundational + US1 + US2 + API Integration
- Users can: invoke tools via natural language, get direct responses for non-task messages
- Total tasks: ~23 tasks (T001-T020 + T038-T041)

---

## Summary

| Phase | User Story | Priority | Task Count | Key Deliverable |
|-------|------------|----------|------------|-----------------|
| 1 | Setup | - | 4 | Project structure |
| 2 | Foundational | - | 7 | Schemas, adapter, executor |
| 3 | US1: Tool Invoke | P1 | 6 | Core LLM→Tool flow |
| 4 | US2: Direct Response | P1 | 3 | Non-tool responses |
| 5 | US3: Clarification | P2 | 3 | Ambiguity handling |
| 6 | US4: Observability | P2 | 4 | Logging integration |
| 7 | US5: Safety | P2 | 5 | Refusal handling |
| 8 | US6: Multi-Turn | P3 | 5 | Tool loops |
| 9 | API Integration | - | 4 | Chat route integration |
| 10 | Polish | - | 5 | Error handling, validation |
| **Total** | | | **46** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

  # Tasks: Agent Evaluation, Safety & Observability

  **Input**: Design documents from `/specs/004-agent-observability/`
  **Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/observability-api.md

  **Tests**: Tests included per spec requirements for validation and quality assurance.

  **Organization**: Tasks grouped by user story priority (P1 → P2 → P3) for incremental delivery.

  ## Format: `[ID] [P?] [Story] Description`

  - **[P]**: Can run in parallel (different files, no dependencies)
  - **[Story]**: Which user story this task belongs to (US1, US2, etc.)
  - Include exact file paths in descriptions

  ## Path Conventions

  - **Web app**: `backend/src/`, `backend/tests/`
  - All observability code in `backend/src/observability/`
  - All tests in `backend/tests/observability/`

  ---

  ## Phase 1: Setup (Shared Infrastructure)

  **Purpose**: Project initialization and observability module structure

  - [x] T001 Add aiosqlite dependency to backend/pyproject.toml
  - [x] T002 Create observability module structure in backend/src/observability/__init__.py
  - [x] T003 [P] Create data directory for logs at backend/data/.gitkeep
  - [x] T004 [P] Create test directory structure at backend/tests/observability/__init__.py
  - [x] T005 [P] Create test fixtures directory at backend/tests/observability/fixtures/

  ---

  ## Phase 2: Foundational (Blocking Prerequisites)

  **Purpose**: Core infrastructure that MUST be complete before ANY user story

  **CRITICAL**: No user story work can begin until this phase is complete

  - [x] T006 Implement SQLite database connection manager in backend/src/observability/database.py
  - [x] T007 Define OutcomeCategory enum and validation in backend/src/observability/categories.py
  - [x] T008 [P] Create ErrorCode enum in backend/src/observability/categories.py
  - [x] T009 Create DecisionLog model with all fields per data-model.md in backend/src/observability/models.py
  - [x] T010 Create ToolInvocationLog model with foreign key to DecisionLog in backend/src/observability/models.py
  - [x] T011 Implement database table creation on startup in backend/src/observability/database.py
  - [x] T012 Create test conftest with SQLite fixtures in backend/tests/observability/conftest.py

  **Checkpoint**: Foundation ready - user story implementation can begin

  ---

  ## Phase 3: User Story 1 - Reviewer Audits Agent Decision Trail (Priority: P1) - MVP

  **Goal**: Enable reviewers to examine logs and understand exactly what the agent did for any interaction

  **Independent Test**: Run user interactions, then query logs by conversation_id to verify complete decision trace is captured

  ### Implementation for User Story 1

  - [x] T013 [US1] Implement write_decision_log in backend/src/observability/logging_service.py
  - [x] T014 [US1] Implement write_tool_invocation_log in backend/src/observability/logging_service.py
  - [x] T015 [US1] Implement get_decision_trace (decision + tools) in backend/src/observability/query_service.py
  - [x] T016 [US1] Implement query_decisions with conversation_id filter in backend/src/observability/query_service.py
  - [x] T017 [US1] Add logging hook in chat route process_message in backend/src/api/routes/chat.py
  - [x] T018 [US1] Add tool invocation logging hook in agent engine in backend/src/api/routes/chat.py
  - [x] T019 [US1] Write test for complete decision trace capture in backend/tests/observability/test_logging.py
  - [x] T020 [US1] Write test for conversation query in backend/tests/observability/test_queries.py

  **Checkpoint**: User Story 1 complete - reviewers can audit full decision trail

  ---

  ## Phase 4: User Story 2 - Engineer Diagnoses Agent Failure (Priority: P1)

  **Goal**: Enable engineers to identify root cause of failures from logs alone

  **Independent Test**: Trigger failure scenarios, query logs, verify failure point is identifiable

  ### Implementation for User Story 2

  - [x] T021 [US2] Add error_code and error_message logging to tool invocations in backend/src/observability/logging_service.py
  - [x] T022 [US2] Add duration_ms tracking to all log entries in backend/src/observability/logging_service.py
  - [x] T023 [US2] Implement query_decisions with outcome_category filter in backend/src/observability/query_service.py
  - [x] T024 [US2] Add exception handling in logging hooks to capture failures in backend/src/api/routes/chat.py
  - [x] T025 [US2] Write test for tool failure logging in backend/tests/observability/test_logging.py
  - [x] T026 [US2] Write test for error query filtering in backend/tests/observability/test_queries.py

  **Checkpoint**: User Story 2 complete - engineers can diagnose failures from logs

  ---

  ## Phase 5: User Story 3 - System Categorizes Errors and Refusals (Priority: P1)

  **Goal**: Automatically categorize all outcomes into SUCCESS/ERROR/REFUSAL/AMBIGUITY with subcategories

  **Independent Test**: Trigger various error types, verify each is logged with correct category:subcategory

  ### Implementation for User Story 3

  - [x] T027 [US3] Implement outcome_category assignment logic for SUCCESS cases in backend/src/observability/categories.py
  - [x] T028 [US3] Implement outcome_category assignment for ERROR cases with subcategories in backend/src/observability/categories.py
  - [x] T029 [US3] Implement outcome_category assignment for REFUSAL cases in backend/src/observability/categories.py
  - [x] T030 [US3] Implement outcome_category assignment for AMBIGUITY cases in backend/src/observability/categories.py
  - [x] T031 [US3] Integrate category assignment into decision logging flow in backend/src/observability/logging_service.py
  - [x] T032 [US3] Write test for each outcome category assignment in backend/tests/observability/test_categories.py

  **Checkpoint**: User Stories 1, 2, 3 complete - core P1 logging functionality delivered

  ---

  ## Phase 6: User Story 4 - Reviewer Detects Behavioral Drift (Priority: P2)

  **Goal**: Enable comparison of agent behavior across time periods to detect drift from baseline

  **Independent Test**: Create baseline, run new sessions, compare patterns to detect >10% deviation

  ### Implementation for User Story 4

  - [x] T033 [US4] Create BaselineSnapshot model in backend/src/observability/models.py
  - [x] T034 [US4] Implement intent distribution calculation from logs in backend/src/observability/query_service.py
  - [x] T035 [US4] Implement tool frequency calculation from logs in backend/src/observability/query_service.py
  - [x] T036 [US4] Implement create_baseline in backend/src/observability/baseline_service.py
  - [x] T037 [US4] Implement compare_to_baseline with drift threshold in backend/src/observability/baseline_service.py
  - [x] T038 [US4] Implement DriftReport generation with flagged metrics in backend/src/observability/baseline_service.py
  - [x] T039 [US4] Write test for baseline creation in backend/tests/observability/test_baseline.py
  - [x] T040 [US4] Write test for drift detection at 10% threshold in backend/tests/observability/test_baseline.py

  **Checkpoint**: User Story 4 complete - drift detection operational

  ---

  ## Phase 7: User Story 5 - Demo Reviewer Validates System Behavior (Priority: P2)

  **Goal**: Enable demo reviewers to see session summaries and verify agent behavior without technical knowledge

  **Independent Test**: Run demo session, generate summary, verify non-technical reviewer can understand key metrics

  ### Implementation for User Story 5

  - [x] T041 [US5] Implement get_metrics_summary in backend/src/observability/query_service.py
  - [x] T042 [US5] Implement success_rate calculation in backend/src/observability/query_service.py
  - [x] T043 [US5] Implement error_breakdown aggregation in backend/src/observability/query_service.py
  - [x] T044 [US5] Implement avg_duration calculations in backend/src/observability/query_service.py
  - [x] T045 [US5] Implement export_logs for offline analysis in backend/src/observability/query_service.py
  - [x] T046 [US5] Write test for metrics summary in backend/tests/observability/test_queries.py
  - [x] T047 [US5] Write test for log export in backend/tests/observability/test_queries.py

  **Checkpoint**: User Story 5 complete - demo review capability delivered

  ---

  ## Phase 8: User Story 6 - Engineer Runs Automated Validation (Priority: P3)

  **Goal**: Enable automated comparison of agent behavior against defined expectations for CI/CD

  **Independent Test**: Run validation against known-good baseline, verify pass/fail report is accurate

  ### Implementation for User Story 6

  - [x] T048 [US6] Create ValidationReport model in backend/src/observability/models.py
  - [x] T049 [US6] Create TestCase schema in backend/src/observability/validation_service.py
  - [x] T050 [US6] Implement load_fixtures from YAML in backend/src/observability/validation_service.py
  - [x] T051 [US6] Implement run_validation test execution in backend/src/observability/validation_service.py
  - [x] T052 [US6] Implement pass/fail comparison logic in backend/src/observability/validation_service.py
  - [x] T053 [US6] Implement ValidationReport JSON generation in backend/src/observability/validation_service.py
  - [x] T054 [US6] Create sample test fixtures file in backend/tests/observability/fixtures/agent_behaviors.yaml
  - [x] T055 [US6] Write test for fixture loading in backend/tests/observability/test_validation.py
  - [x] T056 [US6] Write test for validation execution in backend/tests/observability/test_validation.py

  **Checkpoint**: User Story 6 complete - automated validation ready for CI/CD

  ---

  ## Phase 9: Polish & Cross-Cutting Concerns

  **Purpose**: Improvements that affect multiple user stories

  - [x] T057 [P] Add 30-day retention cleanup function in backend/src/observability/database.py
  - [x] T058 [P] Add query pagination for large result sets in backend/src/observability/query_service.py
  - [x] T059 [P] Add concurrent write handling verification in backend/tests/observability/test_logging.py
  - [x] T060 [P] Add performance test for 10k entry query in backend/tests/observability/test_queries.py
  - [x] T061 Update module exports in backend/src/observability/__init__.py
  - [x] T062 Run quickstart.md validation scenarios manually

  ---

  ## Dependencies & Execution Order

  ### Phase Dependencies

  - **Setup (Phase 1)**: No dependencies - can start immediately
  - **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
  - **US1, US2, US3 (Phases 3-5)**: All depend on Foundational (Phase 2)
    - US1 should complete first (core logging infrastructure)
    - US2 and US3 can proceed after US1 (extend logging)
  - **US4, US5 (Phases 6-7)**: Depend on US1-US3 (need logs to analyze)
  - **US6 (Phase 8)**: Can proceed after US1-US3 (validation needs logging)
  - **Polish (Phase 9)**: Depends on all desired user stories being complete

  ### User Story Dependencies

  | Story | Depends On | Can Parallel With |
  |-------|-----------|-------------------|
  | US1 (P1) | Phase 2 | - (must complete first for others) |
  | US2 (P1) | US1 | US3 |
  | US3 (P1) | US1 | US2 |
  | US4 (P2) | US1, US2, US3 | US5 |
  | US5 (P2) | US1, US2, US3 | US4 |
  | US6 (P3) | US1, US2, US3 | US4, US5 |

  ### Within Each User Story

  - Models before services
  - Services before integration hooks
  - Core implementation before tests
  - Tests validate the story is complete

  ### Parallel Opportunities

  - T003, T004, T005: Directory setup
  - T007, T008: Enum definitions
  - T021-T024: Error tracking enhancements
  - T027-T030: Category assignment logic
  - T033-T035: Baseline/metrics calculations
  - T041-T045: Summary calculations
  - T057-T060: Polish tasks

  ---

  ## Parallel Example: Phase 3 (User Story 1)

  ```bash
  # After T012 (conftest) completes:
  # These can run in parallel once foundation is ready:
  Task T013: "Implement write_decision_log"
  Task T014: "Implement write_tool_invocation_log"

  # After T013, T014 complete:
  Task T015: "Implement get_decision_trace"
  Task T016: "Implement query_decisions"

  # After services complete:
  Task T17, T18: "Add logging hooks" (parallel - different files)

  # After hooks:
  Task T19, T20: "Write tests" (parallel - different test files)
  ```

  ---

  ## Implementation Strategy

  ### MVP First (User Story 1 Only)

  1. Complete Phase 1: Setup (T001-T005)
  2. Complete Phase 2: Foundational (T006-T012)
  3. Complete Phase 3: User Story 1 (T013-T020)
  4. **STOP and VALIDATE**: Can reviewer see complete decision trace?
  5. Deploy/demo if ready - basic logging works!

  ### P1 Complete (User Stories 1-3)

  1. MVP (above)
  2. Add User Story 2 (T021-T026) → Test failure diagnosis
  3. Add User Story 3 (T027-T032) → Test categorization
  4. **STOP and VALIDATE**: All P1 requirements met?
  5. Full logging with categorization delivered

  ### Full Feature

  1. P1 Complete (above)
  2. Add User Story 4 (T033-T040) → Drift detection
  3. Add User Story 5 (T041-T047) → Demo review
  4. Add User Story 6 (T048-T056) → Automated validation
  5. Complete Polish (T057-T062)
  6. Feature complete per spec

  ---

  ## Summary

  | Phase | Tasks | User Story | Priority |
  |-------|-------|------------|----------|
  | 1 | T001-T005 (5) | Setup | - |
  | 2 | T006-T012 (7) | Foundational | Blocking |
  | 3 | T013-T020 (8) | US1: Audit Trail | P1 MVP |
  | 4 | T021-T026 (6) | US2: Failure Diagnosis | P1 |
  | 5 | T027-T032 (6) | US3: Categorization | P1 |
  | 6 | T033-T040 (8) | US4: Drift Detection | P2 |
  | 7 | T041-T047 (7) | US5: Demo Review | P2 |
  | 8 | T048-T056 (9) | US6: Automation | P3 |
  | 9 | T057-T062 (6) | Polish | - |
  | **Total** | **62 tasks** | **6 stories** | |

  ---

  ## Notes

  - [P] tasks = different files, no dependencies
  - [Story] label maps task to specific user story for traceability
  - Each user story is independently testable after completion
  - Commit after each task or logical group
  - Stop at any checkpoint to validate story independently
  - All observability code is additive - no modifications to Spec 001, 002, 003 code behavior

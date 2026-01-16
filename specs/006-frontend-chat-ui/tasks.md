# Tasks: Frontend Agent Review & Chat UI

**Input**: Design documents from `/specs/006-frontend-chat-ui/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/frontend-api.md (complete)

**Tests**: Not explicitly requested in specification. Skipped per template guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `frontend/` directory (Next.js app)
- **Backend addition**: `backend/src/api/routes/` for observability endpoints

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Next.js configuration

- [x] T001 Create Next.js 14+ project with TypeScript and Tailwind CSS in frontend/ directory
- [x] T002 Install dependencies: @openai/chatkit-react, swr in frontend/package.json
- [x] T003 [P] Configure environment variables in frontend/.env.local (NEXT_PUBLIC_API_URL)
- [x] T004 [P] Configure Tailwind with custom color palette in frontend/tailwind.config.ts
- [x] T005 [P] Create TypeScript types from data-model.md in frontend/types/index.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create API client class with fetch wrapper in frontend/lib/api.ts
- [x] T007 [P] Create SWR fetcher with error handling in frontend/lib/fetcher.ts
- [x] T008 [P] Create utility functions (formatDate, cn) in frontend/lib/utils.ts
- [x] T009 Create AuthContext provider with localStorage session in frontend/contexts/AuthContext.tsx
- [x] T010 [P] Create ErrorBoundary component in frontend/components/ui/ErrorBoundary.tsx
- [x] T011 [P] Create Button component with variants in frontend/components/ui/Button.tsx
- [x] T012 [P] Create Card component in frontend/components/ui/Card.tsx
- [x] T013 [P] Create Skeleton loader component in frontend/components/ui/Skeleton.tsx
- [x] T014 Create root layout with providers in frontend/app/layout.tsx
- [x] T015 [P] Create Header component with navigation in frontend/components/layout/Header.tsx
- [x] T016 [P] Create Footer component with GitHub link in frontend/components/layout/Footer.tsx
- [x] T017 [P] Create Container component for max-width centering in frontend/components/layout/Container.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Chat with AI Agent (Priority: P1) MVP

**Goal**: Users can send messages to the AI agent and receive responses in a clean chat interface

**Independent Test**: User opens /chat, sends "Add a task to buy groceries", sees agent response with confirmation

### Implementation for User Story 1

- [x] T018 [US1] Create useAuth hook wrapping AuthContext in frontend/hooks/useAuth.ts
- [x] T019 [US1] Create chat page with ChatKit integration in frontend/app/chat/page.tsx
- [x] T020 [US1] Create ChatContainer component with custom backend adapter in frontend/components/chat/ChatContainer.tsx
- [x] T021 [US1] Implement sendMessage API call in frontend/lib/api.ts (add method to ApiClient)
- [x] T022 [US1] Add loading/thinking indicator to ChatContainer in frontend/components/chat/ChatContainer.tsx
- [x] T023 [US1] Implement error handling with retry for chat in frontend/components/chat/ChatContainer.tsx
- [x] T024 [US1] Add message history display with auto-scroll in frontend/components/chat/ChatContainer.tsx
- [x] T025 [US1] Style chat bubbles for user vs assistant in frontend/components/chat/ChatContainer.tsx
- [x] T026 [US1] Add collapsible tool invocation display (collapsed by default) in frontend/components/chat/ChatContainer.tsx

**Checkpoint**: User Story 1 complete - chat interface fully functional

---

## Phase 4: User Story 2 - Navigate and Understand (Priority: P1)

**Goal**: Users land on homepage, understand the product in seconds, click CTA to start chatting

**Independent Test**: User lands on /, reads hero text, clicks "Start Chatting", arrives at /chat (or /login)

### Implementation for User Story 2

- [x] T027 [US2] Create landing page with Hero section in frontend/app/page.tsx
- [x] T028 [US2] Add headline, description, and CTA button to landing page in frontend/app/page.tsx
- [x] T029 [US2] Implement CTA navigation logic (to /chat or /login based on auth) in frontend/app/page.tsx
- [x] T030 [US2] Add responsive styling for landing page (mobile-first) in frontend/app/page.tsx
- [x] T031 [US2] Configure Footer with GitHub link, project name, hackathon attribution in frontend/components/layout/Footer.tsx

**Checkpoint**: User Story 2 complete - landing page explains product clearly

---

## Phase 5: User Story 4 - Authenticate and Access (Priority: P2)

**Goal**: Users log in with email/password to access protected pages

**Independent Test**: User enters email/password on /login, clicks submit, redirected to /chat with session active

**Note**: Ordered before US3 because Dashboard requires authentication context

### Implementation for User Story 4

- [x] T032 [US4] Create login page with form in frontend/app/login/page.tsx
- [x] T033 [US4] Implement form validation (email format, non-empty password) in frontend/app/login/page.tsx
- [x] T034 [US4] Implement mock login logic (accept any credentials, generate UUID) in frontend/contexts/AuthContext.tsx
- [x] T035 [US4] Add inline error display for login failures in frontend/app/login/page.tsx
- [x] T036 [US4] Implement redirect to /chat on successful login in frontend/app/login/page.tsx
- [x] T037 [US4] Create ProtectedRoute wrapper component in frontend/components/auth/ProtectedRoute.tsx
- [x] T038 [US4] Apply ProtectedRoute to /chat page in frontend/app/chat/page.tsx
- [x] T039 [US4] Implement logout functionality in Header navigation in frontend/components/layout/Header.tsx

**Checkpoint**: User Story 4 complete - authentication flow works end-to-end

---

## Phase 6: Backend Observability Endpoints (Dependency for US3/US5)

**Goal**: Expose observability query service via REST endpoints

**Independent Test**: curl GET /api/observability/metrics returns JSON with success_rate

**Note**: This is backend work that blocks Dashboard and Traces features

### Implementation for Observability API

- [x] T040 Create observability router in backend/src/api/routes/observability.py
- [x] T041 Implement GET /api/observability/decisions endpoint in backend/src/api/routes/observability.py
- [x] T042 Implement GET /api/observability/decisions/{id}/trace endpoint in backend/src/api/routes/observability.py
- [x] T043 Implement GET /api/observability/metrics endpoint in backend/src/api/routes/observability.py
- [x] T044 Register observability router in backend/src/main.py
- [x] T045 Add Pydantic response schemas for observability in backend/src/api/schemas/observability.py

**Checkpoint**: Backend observability API ready - Dashboard can now fetch real data

---

## Phase 7: User Story 3 - View Agent Dashboard (Priority: P2)

**Goal**: Judges/reviewers see metrics cards showing agent performance at a glance

**Independent Test**: User opens /dashboard, sees cards with total decisions, success rate, tool usage

### Implementation for User Story 3

- [x] T046 [US3] Create useMetrics hook with SWR in frontend/hooks/useMetrics.ts
- [x] T047 [US3] Create dashboard page layout in frontend/app/dashboard/page.tsx
- [x] T048 [P] [US3] Create MetricsCard component in frontend/components/dashboard/MetricsCard.tsx
- [x] T049 [P] [US3] Create SuccessRateGauge component in frontend/components/dashboard/SuccessRateGauge.tsx
- [x] T050 [P] [US3] Create ToolUsageList component in frontend/components/dashboard/ToolUsageList.tsx
- [x] T051 [P] [US3] Create IntentDistribution component in frontend/components/dashboard/IntentDistribution.tsx
- [x] T052 [US3] Integrate metrics components into dashboard page in frontend/app/dashboard/page.tsx
- [x] T053 [US3] Add skeleton loaders for dashboard cards in frontend/app/dashboard/page.tsx
- [x] T054 [US3] Add empty state message when no data in frontend/app/dashboard/page.tsx
- [x] T055 [US3] Apply ProtectedRoute to /dashboard page in frontend/app/dashboard/page.tsx

**Checkpoint**: User Story 3 complete - dashboard displays real metrics

---

## Phase 8: User Story 5 - Explore Decision Traces (Priority: P3)

**Goal**: Technical reviewers can see timeline of agent decisions and expand to view tool call details

**Independent Test**: User opens /dashboard/traces, selects conversation, sees timeline, expands decision node to view tool params

### Implementation for User Story 5

- [x] T056 [US5] Create useDecisions hook with SWR in frontend/hooks/useDecisions.ts
- [x] T057 [US5] Create traces page layout in frontend/app/dashboard/traces/page.tsx
- [x] T058 [P] [US5] Create DecisionTimeline component in frontend/components/trace/DecisionTimeline.tsx
- [x] T059 [P] [US5] Create DecisionNode component (expandable) in frontend/components/trace/DecisionNode.tsx
- [x] T060 [P] [US5] Create ToolInvocationCard component in frontend/components/trace/ToolInvocationCard.tsx
- [x] T061 [US5] Implement conversation selector dropdown in frontend/app/dashboard/traces/page.tsx
- [x] T062 [US5] Integrate trace components into traces page in frontend/app/dashboard/traces/page.tsx
- [x] T063 [US5] Add expand/collapse behavior for decision nodes in frontend/components/trace/DecisionNode.tsx
- [x] T064 [US5] Style success vs failure tool invocations with colors in frontend/components/trace/ToolInvocationCard.tsx
- [x] T065 [US5] Add skeleton loaders for trace timeline in frontend/app/dashboard/traces/page.tsx
- [x] T066 [US5] Apply ProtectedRoute to /dashboard/traces page in frontend/app/dashboard/traces/page.tsx

**Checkpoint**: User Story 5 complete - technical reviewers can inspect agent decisions

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T067 [P] Verify responsive design at 320px viewport width across all pages
- [x] T068 [P] Verify responsive design at 1920px viewport width across all pages
- [x] T069 Add keyboard navigation support to all interactive elements
- [x] T070 [P] Ensure color contrast meets WCAG 2.1 AA (4.5:1 ratio)
- [x] T071 Remove all console.log statements and ensure zero console errors
- [x] T072 Add error boundary wrapping to all page components
- [x] T073 [P] Add aria-labels to icon buttons in Header/Footer
- [x] T074 Verify page load time under 2 seconds on broadband
- [x] T075 Run full demo rehearsal: landing → login → chat → dashboard → traces
- [x] T076 Fix any issues discovered during demo rehearsal (fixed snake_case property names, added Suspense boundary)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-5 (US1, US2, US4)**: Depend on Phase 2 - can run in parallel after foundation
- **Phase 6 (Backend)**: No frontend dependencies - can run in parallel with Phase 3-5
- **Phase 7 (US3)**: Depends on Phase 6 (observability API)
- **Phase 8 (US5)**: Depends on Phase 6 (observability API) and Phase 7 (dashboard shell)
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

| Story | Depends On | Can Run After |
|-------|------------|---------------|
| US1 (Chat) | Foundational | Phase 2 complete |
| US2 (Landing) | Foundational | Phase 2 complete |
| US4 (Auth) | Foundational | Phase 2 complete |
| US3 (Dashboard) | Backend API | Phase 6 complete |
| US5 (Traces) | Backend API + Dashboard | Phase 7 complete |

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T003, T004, T005 can run in parallel

**Within Foundational (Phase 2)**:
- T007, T008 can run in parallel
- T010, T011, T012, T013 can run in parallel
- T015, T016, T017 can run in parallel

**After Foundational**:
- US1, US2, US4 can all start in parallel (different page files)
- Backend Phase 6 can run in parallel with frontend US1/US2/US4

**Within US3 (Dashboard)**:
- T048, T049, T050, T051 can run in parallel (different component files)

**Within US5 (Traces)**:
- T058, T059, T060 can run in parallel (different component files)

---

## Parallel Execution Examples

### Example 1: Frontend Foundation (Phase 2)

```bash
# Launch in parallel - different files, no dependencies:
Task: "Create SWR fetcher with error handling in frontend/lib/fetcher.ts"
Task: "Create utility functions in frontend/lib/utils.ts"
Task: "Create ErrorBoundary component in frontend/components/ui/ErrorBoundary.tsx"
Task: "Create Button component in frontend/components/ui/Button.tsx"
Task: "Create Card component in frontend/components/ui/Card.tsx"
Task: "Create Skeleton component in frontend/components/ui/Skeleton.tsx"
```

### Example 2: After Foundational - Three Parallel Tracks

```bash
# Track A (US1 - Chat):
Task: "Create chat page with ChatKit integration in frontend/app/chat/page.tsx"

# Track B (US2 - Landing):
Task: "Create landing page with Hero section in frontend/app/page.tsx"

# Track C (US4 - Auth):
Task: "Create login page with form in frontend/app/login/page.tsx"

# Track D (Backend - parallel with frontend):
Task: "Create observability router in backend/src/api/routes/observability.py"
```

### Example 3: Dashboard Components (Phase 7)

```bash
# Launch all dashboard components in parallel:
Task: "Create MetricsCard component in frontend/components/dashboard/MetricsCard.tsx"
Task: "Create SuccessRateGauge component in frontend/components/dashboard/SuccessRateGauge.tsx"
Task: "Create ToolUsageList component in frontend/components/dashboard/ToolUsageList.tsx"
Task: "Create IntentDistribution component in frontend/components/dashboard/IntentDistribution.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Chat) - **Core MVP**
4. Complete Phase 4: User Story 2 (Landing)
5. **STOP and VALIDATE**: Demo chat functionality with landing page
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Chat) + US2 (Landing) → **MVP Demo Ready**
3. Add US4 (Auth) → Multi-user capability
4. Add Backend API (Phase 6) → Observability ready
5. Add US3 (Dashboard) → Metrics for judges
6. Add US5 (Traces) → Technical depth for reviewers
7. Polish → Demo-ready quality

### Hackathon Fast Track

For maximum velocity with single developer:

1. Phase 1 + 2: Setup + Foundation (2 hours)
2. Phase 3: Chat MVP (2 hours)
3. Phase 4: Landing page (30 min)
4. Phase 5: Auth (1 hour)
5. Phase 6: Backend API (1 hour)
6. Phase 7: Dashboard (1.5 hours)
7. Phase 8: Traces (1.5 hours)
8. Phase 9: Polish (1 hour)

**Total Estimate**: ~10 hours focused work

---

## Task Summary

| Category | Count |
|----------|-------|
| Setup (Phase 1) | 5 |
| Foundational (Phase 2) | 12 |
| US1 - Chat (Phase 3) | 9 |
| US2 - Landing (Phase 4) | 5 |
| US4 - Auth (Phase 5) | 8 |
| Backend API (Phase 6) | 6 |
| US3 - Dashboard (Phase 7) | 10 |
| US5 - Traces (Phase 8) | 11 |
| Polish (Phase 9) | 10 |
| **Total** | **76** |

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Backend Phase 6 is critical path for Dashboard/Traces features
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests not included per specification - add later if needed

# Tasks: Midnight AI Glass UI Theme

**Input**: Design documents from `/specs/011-midnight-glass-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - manual visual testing only as per spec.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/` directory only (no backend changes per FR-009)
- All paths relative to repository root

---

## Phase 1: Setup (Design System Foundation)

**Purpose**: Establish Midnight AI Glass design tokens and utilities that ALL user stories depend on

- [x] T001 Update Tailwind color palette with Midnight colors (dark-900:#0B0F1A, dark-800:#12182B, dark-700:#1A2235, dark-600:#232D42) in `frontend/tailwind.config.ts`
- [x] T002 Update Tailwind primary colors for accent gradient (primary-400:#5B8CFF, primary-500:#7B6CF6, primary-600:#8B5CF6) in `frontend/tailwind.config.ts`
- [x] T003 Update Tailwind semantic colors (success-500:#22C55E, warning-500:#FACC15, error-500:#EF4444) in `frontend/tailwind.config.ts`
- [x] T004 Add custom box shadows (glow-accent, glass) in `frontend/tailwind.config.ts`
- [x] T005 Add typing-bounce keyframe animation in `frontend/tailwind.config.ts`
- [x] T006 Update CSS variables for dark mode (--background, --card, --foreground) in `frontend/app/globals.css`
- [x] T007 Add .glass utility class (semi-transparent bg, backdrop-blur, border) in `frontend/app/globals.css`
- [x] T008 Add .glass-subtle utility class (less prominent glass effect) in `frontend/app/globals.css`
- [x] T009 Add .input-glass utility class (form input glass styling with focus glow) in `frontend/app/globals.css`
- [x] T010 Add .typing-dot animation class (bouncing dots for typing indicator) in `frontend/app/globals.css`
- [x] T011 Update scrollbar colors for dark theme in `frontend/app/globals.css`
- [x] T012 Update gradient text utility for accent colors in `frontend/app/globals.css`

**Checkpoint**: Design system tokens ready - component work can begin ✅

---

## Phase 2: Foundational (Core UI Components)

**Purpose**: Update base UI components with glass styling - MUST complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T013 Force dark mode by default in `frontend/app/layout.tsx` (add dark class to html element)
- [x] T014 Update ThemeContext to default to dark mode and always apply dark class in `frontend/contexts/ThemeContext.tsx`
- [x] T015 [P] Add glass variant to Card component with semi-transparent bg, backdrop-blur, border glow in `frontend/components/ui/Card.tsx`
- [x] T016 [P] Add hover prop to Card component for lift + glow effect (translateY, shadow) in `frontend/components/ui/Card.tsx`
- [x] T017 [P] Update Button primary variant to use accent gradient background in `frontend/components/ui/Button.tsx`
- [x] T018 [P] Update Button focus ring to use accent color in `frontend/components/ui/Button.tsx`
- [x] T019 [P] Add subtle glow on hover for primary Button variant in `frontend/components/ui/Button.tsx`
- [x] T020 [P] Apply glass effect to Toast container in `frontend/components/ui/Toast.tsx`
- [x] T021 [P] Update Toast success/error/info colors to Midnight palette in `frontend/components/ui/Toast.tsx`
- [x] T022 [P] Update Skeleton background to Midnight surface color in `frontend/components/ui/Skeleton.tsx`
- [x] T023 [P] Update Skeleton pulse animation colors in `frontend/components/ui/Skeleton.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel ✅

---

## Phase 3: User Story 1 - Visual Task Management with Glass Cards (Priority: P1) 🎯 MVP

**Goal**: Transform task list items into elegant floating glass cards displaying all metadata

**Independent Test**: Load task list page, verify glass card styling, hover animations, and proper display of title, description, priority badge, tags, due date, reminders, and recurrence

### Implementation for User Story 1

- [x] T024 [US1] Wrap task items in Card variant="glass" with hover prop in `frontend/app/tasks/page.tsx`
- [x] T025 [US1] Display task title with primary text styling in `frontend/app/tasks/page.tsx`
- [x] T026 [US1] Display description preview with secondary text, truncated to 2-3 lines in `frontend/app/tasks/page.tsx`
- [x] T027 [US1] Create PriorityBadge component with color coding (High:#EF4444, Medium:#FACC15, Low:#22C55E) in `frontend/app/tasks/page.tsx`
- [x] T028 [US1] Update tag chip styling with accent gradient background and white text in `frontend/components/tasks/TagInput.tsx`
- [x] T029 [US1] Add "+N more" indicator when task has more than 3-4 tags in `frontend/app/tasks/page.tsx`
- [x] T030 [US1] Color-code due date display (overdue:red, today:warning, upcoming:default) in `frontend/app/tasks/page.tsx`
- [x] T031 [US1] Add hover effect to task cards (translateY:-2px, glow shadow) in `frontend/app/tasks/page.tsx`
- [x] T032 [US1] Style completion checkbox with accent color in `frontend/app/tasks/page.tsx`
- [x] T033 [US1] Add tooltip for truncated task titles in `frontend/app/tasks/page.tsx`

**Checkpoint**: User Story 1 complete - task cards display as glass panels with all metadata visible ✅

---

## Phase 4: User Story 2 - Enhanced Task Creation Form (Priority: P1)

**Goal**: Apply glass styling to task creation/editing forms with all input fields

**Independent Test**: Open task creation form, fill all fields, verify glass panel styling, input focus effects, and successful task creation

### Implementation for User Story 2

- [x] T034 [US2] Wrap task creation form in glass panel container in `frontend/app/tasks/page.tsx`
- [x] T035 [US2] Apply input-glass class to title input field in `frontend/app/tasks/page.tsx`
- [x] T036 [US2] Apply input-glass class to description textarea in `frontend/app/tasks/page.tsx`
- [x] T037 [US2] Update priority selector buttons with gradient accent for selected state in `frontend/app/tasks/page.tsx`
- [x] T038 [US2] Style unselected priority buttons with surface glass background in `frontend/app/tasks/page.tsx`
- [x] T039 [US2] Apply input-glass styling to DateTimePicker component in `frontend/components/tasks/DateTimePicker.tsx`
- [x] T040 [US2] Update TagInput with glass-styled input field in `frontend/components/tasks/TagInput.tsx`
- [x] T041 [US2] Style tag chips in form with accent gradient and removable X button in `frontend/components/tasks/TagInput.tsx`
- [x] T042 [US2] Apply glass styling to RecurrenceSelector buttons in `frontend/components/tasks/RecurrenceSelector.tsx`
- [x] T043 [US2] Apply glass styling to ReminderList inputs in `frontend/components/tasks/ReminderList.tsx`
- [x] T044 [US2] Ensure all inputs show accent glow ring on focus with 150-250ms transition in `frontend/app/tasks/page.tsx`

**Checkpoint**: User Story 2 complete - forms have glass aesthetic with styled inputs ✅

---

## Phase 5: User Story 3 - Glass Chat Interface (Priority: P2)

**Goal**: Transform chat interface with glass panel, styled message bubbles, and typing indicator

**Independent Test**: Open chat, send messages, verify glass panel, user vs AI bubble styling, and typing indicator animation

### Implementation for User Story 3

- [x] T045 [US3] Apply glass effect to chat container panel in `frontend/components/chat/ChatContainer.tsx`
- [x] T046 [US3] Style user message bubbles with accent gradient, right-aligned, rounded corners (more on right) in `frontend/components/chat/ChatContainer.tsx`
- [x] T047 [US3] Style AI message bubbles with surface glass background, left-aligned, rounded corners (more on left) in `frontend/components/chat/ChatContainer.tsx`
- [x] T048 [US3] Update message timestamps to secondary text color with reduced opacity in `frontend/components/chat/ChatContainer.tsx`
- [x] T049 [US3] Create TypingIndicator component with 3 bouncing dots animation in `frontend/components/chat/ChatContainer.tsx`
- [x] T050 [US3] Show TypingIndicator when AI response is pending (isPending state) in `frontend/components/chat/ChatContainer.tsx`
- [x] T051 [US3] Apply input-glass styling to chat textarea in `frontend/components/chat/ChatContainer.tsx`
- [x] T052 [US3] Style send button with accent color in `frontend/components/chat/ChatContainer.tsx`
- [x] T053 [US3] Add focus glow effect to chat input area in `frontend/components/chat/ChatContainer.tsx`

**Checkpoint**: User Story 3 complete - chat interface has glass panel with styled bubbles and typing indicator ✅

---

## Phase 6: User Story 4 - Filter and Sort Controls (Priority: P2)

**Goal**: Apply glass styling to filter panel and sort controls matching the theme

**Independent Test**: Use filter dropdowns and sort controls, verify glass styling and functional filtering/sorting

### Implementation for User Story 4

- [x] T054 [US4] Apply glass panel background to FilterPanel container in `frontend/components/tasks/FilterPanel.tsx`
- [x] T055 [US4] Style radio buttons/checkboxes with accent color in `frontend/components/tasks/FilterPanel.tsx`
- [x] T056 [US4] Apply glass styling to dropdown select elements in `frontend/components/tasks/FilterPanel.tsx`
- [x] T057 [US4] Style active filter option with gradient accent highlight in `frontend/components/tasks/FilterPanel.tsx`
- [x] T058 [US4] Update active filter count badge with gradient accent styling in `frontend/components/tasks/FilterPanel.tsx`
- [x] T059 [US4] Apply glass styling to SortControls dropdown in `frontend/components/tasks/SortControls.tsx`
- [x] T060 [US4] Style sort direction toggle with accent highlight on active state in `frontend/components/tasks/SortControls.tsx`
- [x] T061 [US4] Ensure smooth 150-250ms transitions on filter/sort interactions in `frontend/components/tasks/FilterPanel.tsx`

**Checkpoint**: User Story 4 complete - filter and sort controls integrated with glass theme ✅

---

## Phase 7: User Story 5 - Reminder and Recurrence Display (Priority: P3)

**Goal**: Display reminder and recurrence metadata on task cards with clear status indicators

**Independent Test**: Create tasks with reminders/recurrence, verify status indicators appear correctly on cards

### Implementation for User Story 5

- [x] T062 [US5] Add reminder indicator (bell icon) when task has reminders in `frontend/app/tasks/page.tsx`
- [x] T063 [US5] Add reminder count badge when multiple reminders exist in `frontend/app/tasks/page.tsx`
- [x] T064 [US5] Add tooltip "N reminders scheduled" for reminder indicator in `frontend/app/tasks/page.tsx`
- [x] T065 [US5] Add recurrence label "Recurring: daily" for daily recurrence in `frontend/app/tasks/page.tsx`
- [x] T066 [US5] Add recurrence label "Recurring: weekly" for weekly recurrence in `frontend/app/tasks/page.tsx`
- [x] T067 [US5] Add recurrence label "Recurring: custom" for custom recurrence in `frontend/app/tasks/page.tsx`
- [x] T068 [US5] Style reminder/recurrence indicators in secondary text color in `frontend/app/tasks/page.tsx`

**Checkpoint**: User Story 5 complete - reminder and recurrence metadata visible on task cards ✅

---

## Phase 8: Header & Layout

**Purpose**: Apply glass styling to navigation header

- [x] T069 Apply glass effect to Header bar in `frontend/components/layout/Header.tsx`
- [x] T070 Update logo/branding with accent color in `frontend/components/layout/Header.tsx`
- [x] T071 Add hover effects to navigation links in `frontend/components/layout/Header.tsx`
- [x] T072 Apply glass panel styling to mobile menu in `frontend/components/layout/Header.tsx`

**Checkpoint**: Header integrates with glass theme ✅

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Responsive testing, contrast validation, and regression testing

- [ ] T073 Test responsive layout at 375px (mobile) viewport and fix any issues
- [ ] T074 Test responsive layout at 768px (tablet) viewport and fix any issues
- [ ] T075 Test responsive layout at 1024px (desktop) viewport and fix any issues
- [ ] T076 Test responsive layout at 1920px (large desktop) viewport and fix any issues
- [ ] T077 Validate text contrast ratios meet WCAG AA (4.5:1 minimum) across all components
- [ ] T078 Verify focus states are visible for keyboard navigation
- [ ] T079 Verify hover animations run at 60fps (check for jank)
- [ ] T080 Ensure GPU-accelerated properties (transform, opacity) used for animations
- [ ] T081 Functional regression: Create task with all fields
- [ ] T082 Functional regression: Edit task
- [ ] T083 Functional regression: Complete/uncomplete task
- [ ] T084 Functional regression: Delete task
- [ ] T085 Functional regression: Filter by priority, tags, status
- [ ] T086 Functional regression: Sort by all fields
- [ ] T087 Functional regression: Send chat message and receive AI response
- [ ] T088 Functional regression: Login/logout flow
- [ ] T089 Verify zero console errors in Chrome, Firefox, Safari, Edge

**Checkpoint**: All polish tasks complete - UI ready for demo and portfolio review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **Phases 3-7 (User Stories)**: All depend on Phase 2 completion
  - User stories can proceed in parallel (if team capacity allows)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 8 (Header)**: Can run after Phase 2, parallel with user stories
- **Phase 9 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 - Shares TagInput with US1 but independently testable
- **User Story 3 (P2)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 5 (P3)**: Can start after Phase 2 - Shares task card with US1 but independently testable

### Within Each Phase

- Tasks marked [P] can run in parallel (different files)
- Tasks without [P] should be executed sequentially
- Core styling before integration

### Parallel Opportunities

**Phase 1 (Sequential - same files)**:
- T001-T005: All modify tailwind.config.ts (sequential)
- T006-T012: All modify globals.css (sequential)

**Phase 2 (Parallel opportunities)**:
- T013-T014: Sequential (layout depends on context)
- T015-T023: All [P] - different component files

**User Stories (Each can run in parallel with others)**:
- US1 and US2 share TagInput.tsx - coordinate T028/T040-T041
- US3 is fully independent (ChatContainer.tsx)
- US4 is fully independent (FilterPanel.tsx, SortControls.tsx)
- US5 shares tasks/page.tsx with US1 - coordinate T062-T068

---

## Parallel Example: Phase 2 Components

```bash
# Launch all component updates together (after T013-T014):
Task: "T015 [P] Add glass variant to Card component"
Task: "T017 [P] Update Button primary variant"
Task: "T020 [P] Apply glass effect to Toast"
Task: "T022 [P] Update Skeleton background"
```

## Parallel Example: User Stories After Foundation

```bash
# With multiple developers after Phase 2:
Developer A: User Story 1 (T024-T033) → Task Cards
Developer B: User Story 3 (T045-T053) → Chat Interface
Developer C: User Story 4 (T054-T061) → Filters
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (design tokens)
2. Complete Phase 2: Foundational (core components)
3. Complete Phase 3: User Story 1 (glass task cards)
4. Complete Phase 4: User Story 2 (glass forms)
5. **STOP and VALIDATE**: Test task list and creation independently
6. Deploy/demo if ready - this is the MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (task cards)
3. Add User Story 2 → Test independently → Demo (forms)
4. Add User Story 3 → Test independently → Demo (chat)
5. Add User Story 4 → Test independently → Demo (filters)
6. Add User Story 5 → Test independently → Demo (metadata)
7. Complete Header + Polish → Full release

### Suggested MVP Scope

**Minimum Viable Product**: Phases 1-4 (Setup + Foundational + US1 + US2)
- Establishes design system
- Delivers glass task cards
- Delivers glass forms
- ~44 tasks, covers the two P1 stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No backend changes (FR-009) - all tasks are frontend-only
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Test manually in Chrome, Firefox, Safari, Edge

# Implementation Plan: UI Enablement for Intermediate & Advanced Features

**Branch**: `010-ui-enablement` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-ui-enablement/spec.md`

## Summary

Enable manual UI access to all existing task features (priority, tags, description, due date with time, recurrence, reminders, sorting, and filtering) in the `/tasks` page without modifying backend APIs or database schema. This is a frontend-only enhancement that exposes capabilities already supported by the backend through improved form controls and task display.

**Technical Approach**: Extend existing React/Next.js components with enhanced form inputs, validation, and display components while maintaining TypeScript type safety and SWR-based data fetching patterns.

## Technical Context

**Language/Version**: TypeScript 5.6.3, React 18.3.1, Next.js 14.2.21
**Primary Dependencies**: Next.js, React, SWR 2.2.5, Tailwind CSS 3.4.17, clsx 2.1.1
**Storage**: N/A (frontend only, uses existing backend REST API)
**Testing**: Manual testing (no automated test suite in frontend currently)
**Target Platform**: Modern web browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
**Project Type**: Web application (frontend-only modifications)
**Performance Goals**: Form submission <2s, sort/filter operations <500ms, real-time validation <300ms
**Constraints**: Frontend-only changes, no API modifications, use existing TypeScript types, match backend validation exactly
**Scale/Scope**: ~5 new form components, ~3 enhanced display components, update 1 main page component

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Spec-Driven Development ✅ PASS
- Feature follows: specify (`/sp.specify` complete) → plan (current) → tasks → implement sequence
- Specification defines behavior and contracts, not implementation
- This plan focuses on architecture and decisions, not tasks
- Tasks will be generated via `/sp.tasks` after plan approval

### Principle II: Stateless Backend Architecture ✅ PASS (N/A)
- No backend changes planned
- Frontend remains stateless client making REST API calls
- No state stored beyond browser session/localStorage (existing pattern)

### Principle III: Clear Responsibility Boundaries ✅ PASS
- Frontend-only changes maintain layer separation:
  - UI components: user interaction and presentation
  - API client: HTTP requests to backend (no modifications)
  - Backend: unchanged (existing validation and persistence)
- No violation of layer boundaries

### Principle IV: AI Safety Through Controlled Tool Usage ✅ PASS (N/A)
- No AI agent modifications
- MCP tools unchanged
- This feature is purely UI enhancement

### Principle V: Simplicity Over Cleverness ✅ PASS
- Uses existing component patterns (Card, Button, Input)
- No custom state management libraries (uses React hooks + SWR)
- Minimal abstractions: reusable form components where needed, inline for one-off cases
- No premature optimization or complex architectures

### Principle VI: Deterministic, Debuggable Behavior ✅ PASS
- All form logic is explicit and client-side
- Validation rules mirror backend (testable)
- Clear error messages from both frontend validation and API responses
- State changes traceable through React DevTools

**Constitution Check Result**: ✅ ALL GATES PASS - No violations, proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/010-ui-enablement/
├── spec.md                      # Feature specification
├── plan.md                      # This file
├── research.md                  # Phase 0 output (component research)
├── data-model.md                # Phase 1 output (TypeScript type extensions)
├── quickstart.md                # Phase 1 output (development guide)
├── contracts/                   # Phase 1 output
│   └── api-extensions.md        # Document API usage patterns for new fields
└── checklists/
    └── requirements.md          # Specification quality checklist (complete)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   └── tasks/
│       └── page.tsx             # MODIFY: Main tasks page with enhanced form and filters
├── components/
│   ├── tasks/                   # NEW: Task-specific components
│   │   ├── TaskFormBasic.tsx    # NEW: Priority, tags, description fields
│   │   ├── TaskFormAdvanced.tsx # NEW: Recurrence, reminders (collapsible section)
│   │   ├── DateTimePicker.tsx   # NEW: Date + optional time input
│   │   ├── TagInput.tsx         # NEW: Multi-tag chip input
│   │   ├── RecurrenceSelector.tsx # NEW: Recurrence type + cron expression
│   │   ├── ReminderList.tsx     # NEW: Manage multiple reminders
│   │   ├── SortControls.tsx     # NEW: Sort dropdown and order toggle
│   │   └── FilterPanel.tsx      # NEW: Priority and tag filter checkboxes
│   ├── ui/
│   │   ├── Button.tsx           # EXISTING: reuse
│   │   ├── Card.tsx             # EXISTING: reuse
│   │   └── Input.tsx            # EXISTING: may extend for validation display
│   └── layout/
│       └── Container.tsx        # EXISTING: reuse
├── hooks/
│   └── useTasks.ts              # MODIFY: Add sort/filter params, update create/update signatures
├── lib/
│   ├── api.ts                   # MODIFY: Add reminder/recurrence to task create/update methods
│   └── utils.ts                 # MODIFY: Add validation helpers (tag length, count)
├── types/
│   └── index.ts                 # MODIFY: Add ReminderCreate, RecurrenceCreate request types
└── package.json                 # NO CHANGE: All dependencies already present
```

**Structure Decision**: Web application (frontend only). All modifications are within the `frontend/` directory. No backend, database, or infrastructure changes. Reuses existing Next.js App Router structure, component organization, and utility patterns.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. All principles are satisfied.

---

## Phase 0: Research & Decisions

**Status**: ✅ Complete
**Output**: [research.md](./research.md)

### Key Decisions Made

1. **Date-Time Input**: Use HTML5 native `<input type="datetime-local">` (zero dependencies, built-in accessibility)
2. **Tag Input Pattern**: Custom chip component with visual badges (better UX than comma-separated text)
3. **Cron Expression Input**: Simple text input with help text (no complex builder library)
4. **Sort/Filter State**: React component state with SWR dynamic parameters (session-based per spec)
5. **Validation Strategy**: Client-side validation for UX + server validation as source of truth
6. **Reminder Display**: "Scheduled" label with clear help text explaining no notification delivery
7. **Form Library**: No external form library, use React hooks (form is simple, consistency with existing code)
8. **Advanced Features**: Progressive disclosure in collapsible section (reduces cognitive load)

### Technologies Confirmed

- TypeScript 5.6.3, React 18.3.1, Next.js 14.2.21
- SWR 2.2.5 for data fetching
- Tailwind CSS 3.4.17 for styling
- No additional dependencies required

**Rationale**: All decisions prioritize simplicity, zero additional dependencies, and alignment with existing codebase patterns.

---

## Phase 1: Design & Contracts

**Status**: ✅ Complete
**Outputs**:
- [data-model.md](./data-model.md) - TypeScript type extensions
- [contracts/api-extensions.md](./contracts/api-extensions.md) - API usage patterns
- [quickstart.md](./quickstart.md) - Developer guide

### Data Model Summary

**New Types**:
- `ReminderCreate`: Request payload for reminders
- `RecurrenceCreate`: Request payload for recurrence config
- Extended `TaskCreateRequest` and `TaskUpdateRequest` with optional `reminders` and `recurrence` fields

**Component Props**: 8 new component prop interfaces defined for reusable components

**Validation**: Client-side validation helpers mirroring backend constraints

### API Contract Summary

**Endpoints Used** (no modifications):
- `GET /api/tasks` with query params for filter/sort
- `POST /api/tasks` with extended request body
- `PATCH /api/tasks/{id}` for updates

**Key Patterns**:
- DateTime handling: ISO 8601 UTC strings
- Query string building for dynamic filters
- SWR cache key generation based on query params

### Architecture Decisions

1. **Component Structure**:
   - Reusable components in `components/tasks/` directory
   - Main page component coordinates state
   - Progressive disclosure for advanced features

2. **State Management**:
   - React hooks (`useState`) for form state
   - SWR for server state and caching
   - No global state library needed

3. **Validation**:
   - Constants in `lib/utils.ts`: `VALIDATION_LIMITS`
   - Helper function: `validateTaskForm()`
   - Inline validation in components
   - Server errors mapped to form fields

4. **Type Safety**:
   - All API payloads typed
   - Helper functions for state conversion
   - Strict TypeScript compilation

---

## Implementation Approach

### Component Development Order (Prioritized)

**Phase A - P1 Features (Essential)**:
1. Type extensions (`types/index.ts`)
2. Validation helpers (`lib/utils.ts`)
3. API client updates (`lib/api.ts`)
4. useTasks hook enhancements (`hooks/useTasks.ts`)
5. TagInput component (`components/tasks/TagInput.tsx`)
6. Inline form fields: priority selector, description textarea
7. TaskItem display enhancements (priority badge, tags)
8. SortControls component (`components/tasks/SortControls.tsx`)
9. FilterPanel component (`components/tasks/FilterPanel.tsx`)

**Phase B - P2 Features (Enhanced)**:
10. DateTimePicker component (`components/tasks/DateTimePicker.tsx`)
11. RecurrenceSelector component (`components/tasks/RecurrenceSelector.tsx`)
12. Form integration for due date with time
13. Form integration for recurrence

**Phase C - P3 Features (Future-Ready)**:
14. ReminderList component (`components/tasks/ReminderList.tsx`)
15. Form integration for reminders
16. Help text and "Scheduled" status display

### Testing Strategy

**Manual Testing**:
- Create tasks with all field combinations
- Edit existing tasks
- Verify sort/filter operations
- Test validation error display
- Browser compatibility testing (Chrome, Firefox, Safari, Edge)

**Integration Testing**:
- Verify API request payloads match schema
- Confirm SWR refetching on filter changes
- Test error handling (network errors, validation errors)

**Regression Testing**:
- Ensure basic task creation still works
- Verify chatbot-created tasks display correctly
- Check existing UI functionality (complete, delete)

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Client validation out of sync with server | Mirror exact backend validation rules; test error handling |
| Complex form overwhelming users | Use progressive disclosure; defaults for all optional fields |
| Timezone confusion in date picker | Show timezone indicator; use browser local timezone |
| SWR cache staleness | Use SWR mutate after create/update operations |
| Performance with many tasks | Use existing pagination; optimize filter logic with memoization |
| Accessibility issues | Follow existing component patterns; test keyboard navigation |

---

## Success Criteria (from Spec)

Implementation will be considered complete when:

- ✅ Users can create fully-configured task (priority, tags, description, due date) in <60s
- ✅ All task attributes visible in task list without additional clicks
- ✅ Filtering by priority/tag works in <10s
- ✅ Sorting operations complete in <500ms
- ✅ 100% of UI-created tasks populate correctly in database
- ✅ Zero regression in existing functionality
- ✅ Form validation provides feedback in <200ms
- ✅ Recurring tasks configurable through UI and save correctly

---

## Next Steps

**Ready for Task Breakdown**: Run `/sp.tasks` to generate ordered implementation tasks

The planning phase is complete with:
- ✅ Constitution check passed (all 6 principles)
- ✅ Research decisions documented
- ✅ Data model defined
- ✅ API contracts documented
- ✅ Component architecture designed
- ✅ Development guide created
- ✅ Agent context updated

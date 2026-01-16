# Implementation Plan: Frontend Agent Review & Chat UI

**Branch**: `006-frontend-chat-ui` | **Date**: 2026-01-09 | **Spec**: `specs/006-frontend-chat-ui/spec.md`
**Input**: Feature specification from `/specs/006-frontend-chat-ui/spec.md`

---

## Summary

Build a hackathon-ready frontend for the AI Todo Agent using Next.js 14+, OpenAI ChatKit, and Tailwind CSS. The frontend provides three core experiences: a chat interface for conversational task management, a metrics dashboard for judges to assess agent performance, and a decision trace viewer for technical reviewers. Integration with the existing FastAPI backend requires creating new observability REST endpoints.

---

## Technical Context

**Language/Version**: TypeScript 5.x, React 18+, Node.js 20+
**Primary Dependencies**: Next.js 14+, @openai/chatkit-react, Tailwind CSS 3.4+, SWR
**Storage**: N/A (stateless frontend, all data from backend)
**Testing**: Vitest for unit tests, MSW for API mocking, Playwright for E2E (optional)
**Target Platform**: Web (desktop, tablet, mobile responsive)
**Project Type**: Web application (separate frontend directory)
**Performance Goals**: Page load <2s, chat response display <500ms after backend response
**Constraints**: Mobile-first responsive design, zero console errors, WCAG 2.1 AA accessibility
**Scale/Scope**: 5 pages (landing, login, chat, dashboard, traces), ~30 components

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | PASS | Full spec exists, plan follows, tasks will be generated |
| II. Stateless Backend Architecture | PASS | Frontend is stateless, uses backend APIs |
| III. Clear Responsibility Boundaries | PASS | Frontend handles UI only, backend owns business logic |
| IV. AI Safety Through Controlled Tool Usage | N/A | Frontend doesn't interact with AI directly |
| V. Simplicity Over Cleverness | PASS | React Context over Redux, SWR over React Query |
| VI. Deterministic, Debuggable Behavior | PASS | Clear state management, explicit error handling |

**Technical Constraints Check**:
| Constraint | Status | Evidence |
|------------|--------|----------|
| Frontend Chat UI: OpenAI ChatKit | PASS | Using @openai/chatkit-react |
| Backend Framework: FastAPI | N/A | Backend already exists |
| No direct database access from UI | PASS | All data via REST APIs |
| No hardcoded secrets | PASS | Environment variables only |

---

## Project Structure

### Documentation (this feature)

```text
specs/006-frontend-chat-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output (complete)
├── data-model.md        # Phase 1 output (complete)
├── api-integration.md   # Existing integration spec
├── ui-layout.md         # Existing layout spec
├── quickstart.md        # Phase 1 output (complete)
├── contracts/
│   └── frontend-api.md  # Phase 1 output (complete)
└── tasks.md             # Phase 2 output (via /sp.tasks)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Landing page (Hero + CTA)
│   ├── login/
│   │   └── page.tsx         # Mock authentication page
│   ├── chat/
│   │   └── page.tsx         # ChatKit integration
│   └── dashboard/
│       ├── page.tsx         # Metrics cards
│       └── traces/
│           └── page.tsx     # Decision trace viewer
├── components/
│   ├── ui/                  # Shared UI primitives
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Skeleton.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── Toast.tsx
│   ├── layout/              # Layout components
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── Container.tsx
│   ├── chat/                # Chat-specific components
│   │   └── ChatContainer.tsx
│   ├── dashboard/           # Dashboard components
│   │   ├── MetricsCard.tsx
│   │   ├── SuccessRateGauge.tsx
│   │   ├── ToolUsageList.tsx
│   │   └── IntentDistribution.tsx
│   └── trace/               # Trace viewer components
│       ├── DecisionTimeline.tsx
│       ├── DecisionNode.tsx
│       └── ToolInvocationCard.tsx
├── lib/
│   ├── api.ts               # API client class
│   ├── fetcher.ts           # SWR fetcher
│   └── utils.ts             # Utility functions
├── hooks/
│   ├── useAuth.ts           # Authentication hook
│   ├── useConversations.ts  # Conversations data hook
│   ├── useDecisions.ts      # Decisions data hook
│   └── useMetrics.ts        # Metrics data hook
├── contexts/
│   └── AuthContext.tsx      # Auth provider
├── types/
│   └── index.ts             # TypeScript types
├── .env.local               # Environment variables
├── tailwind.config.ts       # Tailwind configuration
├── next.config.js           # Next.js configuration
└── package.json

backend/
└── src/
    └── api/
        └── routes/
            └── observability.py  # NEW: REST endpoints for observability
```

**Structure Decision**: Web application structure with separate `frontend/` directory. Backend already exists in `backend/`. New backend file needed: `observability.py` route handler.

---

## Architecture Decisions

### ADR-006-001: Framework Selection - Next.js 14+

**Context**: Need React-based framework for chat UI with good DX and deployment story.

**Options Considered**:
1. Create React App - Simple, familiar
2. Vite + React - Fast, modern
3. Next.js 14+ App Router - SSR, routing, Vercel deployment

**Decision**: Next.js 14+ with App Router

**Rationale**:
- Built-in file-based routing eliminates react-router setup
- Server Components reduce client bundle size for landing/dashboard
- Static generation for landing page improves initial load
- One-click Vercel deployment (hackathon time pressure)
- App Router is current best practice

**Trade-offs Accepted**:
- Slightly more complex than plain React
- `"use client"` directive needed for ChatKit components

---

### ADR-006-002: Chat UI - OpenAI ChatKit

**Context**: Constitution mandates OpenAI ChatKit. Need production-ready chat components.

**Decision**: Use @openai/chatkit-react

**Implementation Notes**:
- ChatKit requires custom backend adapter (not using OpenAI hosted)
- Tool call visualization built-in (collapsed by default)
- May need custom message renderer for our response format

---

### ADR-006-003: State Management - React Context

**Context**: Need global state for auth and UI preferences.

**Options Considered**:
1. Redux - Powerful but overkill
2. Zustand - Lightweight but another dependency
3. React Context - Built-in, sufficient for scope

**Decision**: React Context for auth state only. SWR handles server state.

**Rationale**:
- Auth is the only truly global client state
- SWR handles data fetching with caching
- ChatKit manages chat state internally
- Simplest solution that works

---

### ADR-006-004: Data Fetching - SWR

**Context**: Need efficient data fetching with caching for dashboard/traces.

**Decision**: SWR with custom fetcher

**Configuration**:
- Conversations: 30s cache, invalidate on send
- Metrics: 60s cache, auto-refresh
- Traces: On-demand, no refresh

---

### ADR-006-005: Authentication - Mock Auth for MVP

**Context**: Real auth adds complexity, hackathon time is limited.

**Decision**: Mock authentication with localStorage session

**Implementation**:
- Login accepts any email/password
- Generate UUID as user_id
- Store in localStorage
- Pass via X-User-Id header
- Backend must have AUTH_MODE=mock

**Future Migration Path**:
- Replace with Better Auth (per constitution)
- JWT tokens in httpOnly cookies
- Authorization header instead of X-User-Id

---

## Backend Dependency

**BLOCKING**: Frontend dashboard and trace viewer require new backend endpoints.

The observability query service exists (`LogQueryService`) but has no REST exposure.

**Required Backend Work** (can run in parallel with frontend shell):

Create `backend/src/api/routes/observability.py`:

```python
@router.get("/api/observability/decisions")
async def query_decisions(...) -> QueryResult

@router.get("/api/observability/decisions/{id}/trace")
async def get_decision_trace(...) -> DecisionTrace

@router.get("/api/observability/metrics")
async def get_metrics_summary(...) -> MetricsSummary
```

**Estimated Effort**: 1-2 hours
**Can Block**: Dashboard page, Trace viewer page
**Does Not Block**: Landing, Login, Chat (core MVP)

---

## Implementation Phases

### Phase 1: Project Setup & App Shell
- Create Next.js project with TypeScript + Tailwind
- Configure environment variables
- Implement root layout with Header/Footer
- Create placeholder pages
- Set up API client and SWR

### Phase 2: Authentication & Landing
- Implement AuthContext with localStorage
- Create Login page with form
- Create Landing page with Hero + CTA
- Protected route wrapper

### Phase 3: Chat Interface (MVP Core)
- Integrate ChatKit with custom adapter
- Connect to /api/chat endpoint
- Handle conversation creation/continuation
- Loading states and error handling

### Phase 4: Backend Observability Endpoints
- Create observability.py route handler
- Expose query_decisions, get_decision_trace, get_metrics_summary
- Test endpoints with curl/Postman

### Phase 5: Dashboard
- Implement metrics cards (total decisions, success rate)
- Error breakdown display
- Tool usage statistics
- Intent distribution
- Loading skeletons and empty states

### Phase 6: Decision Trace Viewer
- Conversation selector
- Decision timeline component
- Expandable decision nodes
- Tool invocation details
- Success/failure indicators

### Phase 7: Polish & Testing
- Responsive design verification (320px - 1920px)
- Error state testing
- Accessibility audit (keyboard nav, contrast)
- Demo rehearsal
- Zero console errors

---

## Testing Strategy

### Unit Tests (Vitest)
- Components render without crashing
- Hooks return expected state
- API client handles errors

### Integration Tests (MSW)
- Login flow with mock backend
- Chat send/receive cycle
- Dashboard data loading
- Error scenarios

### Manual Testing Checklist
- [ ] Login with any email/password
- [ ] Send chat message, receive response
- [ ] View conversation history
- [ ] Dashboard metrics load correctly
- [ ] Trace viewer shows decision details
- [ ] Mobile responsive at 320px
- [ ] Keyboard navigation works
- [ ] No console errors in production build

### Demo Validation
- [ ] Cold start: Judge opens app, understands purpose in 10s
- [ ] Happy path: Send task request, see agent response
- [ ] Dashboard: Metrics explain agent behavior
- [ ] Traces: Technical reviewer can inspect decisions
- [ ] Error resilience: Backend restart during demo

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| ChatKit API doesn't match our backend format | High | Research ChatKit adapter pattern early; fallback to custom chat UI |
| Observability endpoints delayed | Medium | Build dashboard UI with mock data first |
| Performance on mobile | Medium | Test early, use skeleton loaders, lazy load heavy components |
| Demo crashes | High | Error boundaries everywhere, graceful degradation |

---

## Success Criteria (from Spec)

- [ ] SC-001: Message send/receive within 5 seconds
- [ ] SC-002: Page load under 2 seconds
- [ ] SC-003: Zero UI crashes on error states
- [ ] SC-004: Dashboard matches backend data
- [ ] SC-005: 100% keyboard accessible
- [ ] SC-006: Renders 320px to 1920px
- [ ] SC-007: Purpose clear in 10 seconds
- [ ] SC-008: Traces viewable without documentation

---

## Milestones

| Phase | Deliverable | Dependencies |
|-------|-------------|--------------|
| 1 | App shell + routing | None |
| 2 | Landing + Login | Phase 1 |
| 3 | Chat interface | Phase 2, Backend running |
| 4 | Backend observability endpoints | Backend codebase |
| 5 | Dashboard | Phase 1, Phase 4 |
| 6 | Decision traces | Phase 5 |
| 7 | Polish + testing | All phases |

---

## Next Steps

1. Run `/sp.tasks` to generate executable task list
2. Begin Phase 1: Project setup
3. Parallel track: Create backend observability endpoints

---

## Complexity Tracking

No constitution violations requiring justification. Architecture is straightforward:
- Single frontend project
- Standard Next.js patterns
- React Context (not Redux)
- Built-in OpenAI ChatKit (not custom)

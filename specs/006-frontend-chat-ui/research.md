# Research & Technology Notes

**Feature**: 006-frontend-chat-ui
**Purpose**: Document technology decisions, library research, and integration considerations
**Status**: Complete

---

## Research Questions Resolved

| Question | Resolution | Source |
|----------|------------|--------|
| Observability REST endpoints exist? | No - need to create in backend | Backend code inspection |
| Mock auth with X-User-Id header? | Yes - backend supports when AUTH_MODE=mock | Backend deps.py |
| ChatKit UI compatibility with Next.js? | Yes - use `@openai/chatkit-react` | OpenAI docs |
| WebSockets for real-time? | No - poll/refresh sufficient for MVP | Scope decision |

---

## Technology Stack Decision

### Framework: Next.js 14+ (App Router)

**Decision**: Next.js over plain React

**Rationale**:
- Built-in file-based routing (no react-router setup)
- Server-side rendering improves initial load time (critical for hackathon demo)
- Easy deployment to Vercel (one-click deploy)
- App Router with React Server Components for efficient data fetching
- Built-in API routes if needed for BFF pattern

**Trade-offs Accepted**:
- Slightly more complex than plain Create React App
- Learning curve for App Router patterns
- Some Chatkit UI components need `"use client"` directive

---

## Key Libraries

### 1. OpenAI ChatKit (`@openai/chatkit-react`)

**Purpose**: Production-ready chat interface components

**Features**:
- Deep UI customization with existing design systems
- Built-in response streaming support
- Tool and workflow visualization for agentic actions
- Rich interactive widgets within chat
- Attachment handling (file/image upload)
- Thread and message management
- Source annotations for transparency

**Integration Pattern**:
```javascript
import { useChatKit, ChatKit } from '@openai/chatkit-react';

function ChatPage({ clientToken }) {
  const { control } = useChatKit({
    api: { url: process.env.NEXT_PUBLIC_API_URL }
  });

  return (
    <ChatKit
      control={control}
      className="h-full w-full"
    />
  );
}
```

**Customization Options**:
- Widget nodes: `Widgets.Box`, `Widgets.Button`, `Widgets.Card`, etc.
- Styling: `Alignment`, `Spacing`, `ThemeColor` namespaces
- Tool call visualization built-in

**Decision**: Use ChatKit for chat interface (constitution specifies "OpenAI ChatKit")

---

### 2. Tailwind CSS v3.4+

**Purpose**: Utility-first CSS framework

**Configuration**:
- Enable dark mode support (class-based)
- Custom color palette for brand consistency
- Typography plugin for readable text
- Animate plugin for subtle transitions

**Custom Theme Colors**:
```
slate: text and backgrounds
blue/teal: primary accent (CTA buttons)
green: success states
red: error states
gray: neutral borders and shadows
```

**Decision**: Tailwind CSS (matches tech constraints in constitution)

---

### 3. Data Fetching: SWR

**Options Evaluated**:

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| SWR | Simple, caching, revalidation | Another dependency | **Selected** |
| React Query | Powerful, devtools | Overkill for scope | Skip |
| Native fetch | No deps | Manual caching | For simple cases |

**Decision**: SWR for data fetching with caching and revalidation

**Usage Pattern**:
```javascript
import useSWR from 'swr';

function useConversations() {
  return useSWR('/api/conversations', fetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 30000
  });
}
```

---

### 4. State Management: React Context

**Options Evaluated**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| React Context | Built-in, simple | Prop drilling for deep trees | **Selected** |
| Zustand | Lightweight | Another dependency | Skip |
| Redux | Scalable | Massive overkill | Definitely skip |

**Decision**: React Context for auth state and global UI state

**Contexts Needed**:
- `AuthContext`: User session, login status
- `ChatContext`: Active conversation state (handled by ChatKit)

---

## Backend API Integration

### Existing Endpoints (Confirmed from Backend)

#### Chat API (`/api/chat`)
- POST: Send message, get response
- Creates conversation if `conversation_id` omitted
- Returns full message history

#### Conversations API (`/api/conversations`)
- GET: List user's conversations (paginated)
- GET `/{id}`: Get conversation with messages

### Missing Endpoints (Need Backend Work)

The observability query service exists (`LogQueryService`) but has **no REST exposure**:

```
GET /api/observability/decisions       → query_decisions()
GET /api/observability/decisions/{id}  → get_decision_trace()
GET /api/observability/metrics         → get_metrics_summary()
```

**Action Required**: Create `backend/src/api/routes/observability.py` exposing these endpoints.

---

## Authentication Strategy

### For Hackathon MVP (Selected)

**Approach**: Mock authentication

1. Login form accepts any email/password
2. Backend configured with `AUTH_MODE=mock`
3. User ID passed via `X-User-Id` header (or `X-User-ID`)
4. Session stored in localStorage

**Benefits**:
- Eliminates auth complexity for hackathon
- Focus on core AI features
- Easy to demo without account creation

**Implementation**:
```typescript
// api client
const headers = {
  'Content-Type': 'application/json',
  ...(userId ? { 'X-User-Id': userId } : {})
};
```

### For Production (Future, Not in Scope)
- OAuth2 with Google/GitHub
- JWT tokens with refresh
- Secure httpOnly cookies
- Better Auth integration (per constitution)

---

## Performance Considerations

### Initial Load
- Use Next.js static generation for landing page
- Lazy load dashboard components
- Skeleton loaders for perceived performance

### Chat Performance
- ChatKit handles virtualized scrolling internally
- Optimistic UI updates for sent messages
- Debounced input for typing indicators

### Image/Asset Optimization
- Use Next.js Image component
- WebP format for any graphics
- Inline SVGs for icons

---

## Accessibility Requirements

### WCAG 2.1 Level AA
- Minimum contrast ratio 4.5:1 for text
- Focus indicators on all interactive elements
- Keyboard navigation for entire app
- Screen reader labels for icons
- Skip links for main content

### Chat-Specific
- Live region announcements for new messages
- Clear role labels for user vs. agent
- Expandable sections use proper ARIA

---

## Testing Strategy

### Unit Tests (Vitest)
- Component rendering tests
- Hook logic tests
- Utility function tests

### Integration Tests
- API mocking with MSW
- Full page interaction flows
- Error state handling

### E2E Tests (Optional for Hackathon)
- Playwright for critical paths
- Login -> Chat -> Send message flow

---

## Deployment

### Recommended: Vercel

**Reasons**:
- One-click Next.js deployment
- Automatic preview deploys for PRs
- Edge caching and CDN
- Environment variable management

**Configuration**:
```
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_AUTH_ENABLED=false
```

### Alternative: Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

---

## Architecture Diagram

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                      FRONTEND (Next.js)                      │
                    │                                                               │
                    │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐ │
                    │  │  Landing Page │  │   Chat Page   │  │   Dashboard Page  │ │
                    │  │   (Static)    │  │  (ChatKit UI) │  │  (Metrics/Trace)  │ │
                    │  └───────────────┘  └───────────────┘  └───────────────────┘ │
                    │           │                 │                    │           │
                    │           └─────────────────┼────────────────────┘           │
                    │                             │                                 │
                    │                    ┌────────▼────────┐                       │
                    │                    │   API Client    │                       │
                    │                    │   (SWR + Fetch) │                       │
                    │                    └────────┬────────┘                       │
                    └────────────────────────────┬────────────────────────────────┘
                                                 │
                                                 │ HTTP/REST
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                                          │
│                                                                                         │
│  ┌────────────────────┐  ┌────────────────────┐  ┌─────────────────────────────────┐   │
│  │  /api/chat         │  │  /api/conversations│  │  /api/observability            │   │
│  │  Send messages     │  │  List/Get convos   │  │  Metrics, Traces, Decisions     │   │
│  └────────┬───────────┘  └────────────────────┘  └─────────────────────────────────┘   │
│           │                                                                             │
│           ▼                                                                             │
│  ┌────────────────────┐                         ┌─────────────────────────────────┐    │
│  │  LLM Agent Engine  │─────────────────────────│  Observability Layer            │    │
│  │  (Gemini-powered)  │         logs            │  (SQLite - logs.db)             │    │
│  └────────┬───────────┘                         └─────────────────────────────────┘    │
│           │                                                                             │
│           ▼                                                                             │
│  ┌────────────────────┐                                                                 │
│  │    MCP Tools       │                                                                 │
│  │  (Task operations) │                                                                 │
│  └────────┬───────────┘                                                                 │
│           │                                                                             │
│           ▼                                                                             │
│  ┌────────────────────┐                                                                 │
│  │  PostgreSQL (Neon) │                                                                 │
│  │  Conversations,    │                                                                 │
│  │  Messages, Tasks   │                                                                 │
│  └────────────────────┘                                                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Decision Log Summary

| Decision | Choice | Alternatives Rejected | Rationale |
|----------|--------|----------------------|-----------|
| Framework | Next.js 14+ | Create React App | SSR, routing, Vercel deployment |
| Chat UI | OpenAI ChatKit | Custom components, react-chat-ui | Constitution mandate, production-ready |
| Styling | Tailwind CSS | MUI, Chakra, styled-components | Utility-first, matches constitution |
| Data Fetching | SWR | React Query, native fetch | Balance of features vs complexity |
| State | React Context | Zustand, Redux | Sufficient for scope, no extra deps |
| Auth (MVP) | Mock auth | Full OAuth | Hackathon time constraints |
| Deployment | Vercel | Docker, Railway | Best Next.js support |

---

## Sources

- [OpenAI ChatKit Documentation](https://platform.openai.com/docs/guides/chatkit)
- [ChatKit.js GitHub](https://github.com/openai/chatkit-js)
- [ChatKit.js API Reference](https://openai.github.io/chatkit-js/)
- Backend code inspection: `backend/src/api/routes/chat.py`
- Backend code inspection: `backend/src/observability/query_service.py`

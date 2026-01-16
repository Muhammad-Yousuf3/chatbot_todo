# UI Layout Specification

**Feature**: 006-frontend-chat-ui
**Purpose**: Define page layouts, component hierarchy, and visual structure

---

## Page Layouts

### 1. Landing Page (`/`)

```
┌──────────────────────────────────────────────────────────┐
│                        HEADER                            │
│  [Logo]                           [Login] [Dashboard]    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                                                          │
│                      HERO SECTION                        │
│                                                          │
│              ┌─────────────────────────┐                 │
│              │   AI Task Assistant     │                 │
│              │                         │                 │
│              │  Manage your tasks with │                 │
│              │  natural conversation   │                 │
│              │                         │                 │
│              │   [ Start Chatting ]    │                 │
│              └─────────────────────────┘                 │
│                                                          │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                        FOOTER                            │
│  AI Todo Agent  •  Built for Hackathon  •  [GitHub]     │
└──────────────────────────────────────────────────────────┘
```

**Layout Notes**:
- Centered content with max-width container (1200px)
- Hero section vertically centered on viewport
- Minimal navigation - only essential links
- Footer always visible at bottom

---

### 2. Login Page (`/login`)

```
┌──────────────────────────────────────────────────────────┐
│                        HEADER                            │
│  [Logo]                                     [← Back]     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                                                          │
│                  ┌─────────────────────┐                 │
│                  │      LOGIN          │                 │
│                  │                     │                 │
│                  │  ┌───────────────┐  │                 │
│                  │  │ Email         │  │                 │
│                  │  └───────────────┘  │                 │
│                  │                     │                 │
│                  │  ┌───────────────┐  │                 │
│                  │  │ Password      │  │                 │
│                  │  └───────────────┘  │                 │
│                  │                     │                 │
│                  │  [    Log In     ]  │                 │
│                  │                     │                 │
│                  │  (inline errors)    │                 │
│                  └─────────────────────┘                 │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                        FOOTER                            │
└──────────────────────────────────────────────────────────┘
```

**Layout Notes**:
- Form card centered vertically and horizontally
- Large, accessible input fields (min 48px height)
- Inline error messages below inputs (not alerts)
- No "remember me" or "forgot password" for MVP

---

### 3. Chat Page (`/chat`)

```
┌──────────────────────────────────────────────────────────┐
│                        HEADER                            │
│  [Logo]  [New Chat]              [Dashboard]  [Logout]   │
├───────────────┬──────────────────────────────────────────┤
│               │                                          │
│  CONVERSATION │          CHAT AREA                       │
│     LIST      │                                          │
│               │  ┌────────────────────────────────────┐  │
│  ┌─────────┐  │  │ [User bubble]                      │  │
│  │ Conv 1  │  │  │                                    │  │
│  └─────────┘  │  │ [Agent bubble]                     │  │
│  ┌─────────┐  │  │   └─[Tool call - collapsed]        │  │
│  │ Conv 2  │  │  │                                    │  │
│  └─────────┘  │  │ [User bubble]                      │  │
│  ┌─────────┐  │  │                                    │  │
│  │ Conv 3  │  │  │ [Typing indicator...]              │  │
│  └─────────┘  │  │                                    │  │
│               │  └────────────────────────────────────┘  │
│               │  ┌────────────────────────────────────┐  │
│               │  │ Type a message...           [Send] │  │
│               │  └────────────────────────────────────┘  │
├───────────────┴──────────────────────────────────────────┤
│                        FOOTER                            │
└──────────────────────────────────────────────────────────┘
```

**Layout Notes**:
- Sidebar for conversation list (collapsible on mobile)
- Chat area takes remaining width
- Message input fixed at bottom of chat area
- Auto-scroll to bottom on new messages
- Smooth scroll when viewing history

**Mobile Layout** (< 768px):
- Conversation list becomes slide-out drawer
- Full-width chat area
- Hamburger menu for navigation

---

### 4. Dashboard Page (`/dashboard`)

```
┌──────────────────────────────────────────────────────────┐
│                        HEADER                            │
│  [Logo]  [Chat]                  [Trace Viewer] [Logout] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  DASHBOARD                                               │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐                  │
│  │ Total          │  │ Success Rate   │                  │
│  │ Conversations  │  │                │                  │
│  │    147         │  │    94.2%       │                  │
│  └────────────────┘  └────────────────┘                  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │             OUTCOME CATEGORIES                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │  │
│  │  │ SUCCESS  │ │ ERROR    │ │ AMBIG    │ │ REFUSE │ │  │
│  │  │   89%    │ │   5%     │ │   4%     │ │   2%   │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │               TOOL USAGE                            │  │
│  │  add_task: ████████████  45                        │  │
│  │  list_tasks: ████████  32                          │  │
│  │  complete_task: █████  21                          │  │
│  │  update_task: ███  12                              │  │
│  │  delete_task: █  5                                 │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                        FOOTER                            │
└──────────────────────────────────────────────────────────┘
```

**Layout Notes**:
- Grid layout for metric cards (2 cols desktop, 1 col mobile)
- Simple bar chart for tool usage (no complex charting library needed)
- Outcome categories as colored percentage cards
- All cards show skeleton loaders during data fetch

---

### 5. Decision Trace Viewer (`/trace/{conversation_id}`)

```
┌──────────────────────────────────────────────────────────┐
│                        HEADER                            │
│  [← Back to Chat]                           [Dashboard]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  DECISION TRACE: "Buy groceries conversation"            │
│                                                          │
│  ●───────────────────────────────────────────────────●   │
│  │                                                   │   │
│  ▼                                                   │   │
│  ┌────────────────────────────────────────────────┐  │   │
│  │ Decision 1: INVOKE_TOOL                        │  │   │
│  │ Message: "Add a task to buy groceries"         │  │   │
│  │ Duration: 245ms                                │  │   │
│  │ [▼ Expand]                                     │  │   │
│  │   Tool: add_task                               │  │   │
│  │   Params: {"description": "buy groceries"}     │  │   │
│  │   Result: ✓ Success                            │  │   │
│  └────────────────────────────────────────────────┘  │   │
│  │                                                   │   │
│  ▼                                                   │   │
│  ┌────────────────────────────────────────────────┐  │   │
│  │ Decision 2: RESPOND_ONLY                       │  │   │
│  │ Message: "What else should I add?"             │  │   │
│  │ Duration: 123ms                                │  │   │
│  │ [▼ Expand]                                     │  │   │
│  │   Response: "I've added 'buy groceries'..."    │  │   │
│  └────────────────────────────────────────────────┘  │   │
│  │                                                   │   │
│  ●───────────────────────────────────────────────────●   │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                        FOOTER                            │
└──────────────────────────────────────────────────────────┘
```

**Layout Notes**:
- Vertical timeline with connecting lines
- Each decision node is expandable/collapsible
- Color coding: green for success, red for errors
- Show tool parameters as formatted JSON
- Chronological order (oldest first)

---

## Component Hierarchy

```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── NavLinks
│   │   └── UserMenu
│   ├── Main (page content)
│   └── Footer
│       ├── ProjectName
│       ├── HackathonBadge
│       └── GitHubLink
│
├── Pages
│   ├── LandingPage
│   │   └── HeroSection
│   │       ├── Headline
│   │       ├── Description
│   │       └── CTAButton
│   │
│   ├── LoginPage
│   │   └── LoginForm
│   │       ├── EmailInput
│   │       ├── PasswordInput
│   │       ├── SubmitButton
│   │       └── InlineError
│   │
│   ├── ChatPage
│   │   ├── ConversationSidebar
│   │   │   └── ConversationItem[]
│   │   └── ChatArea
│   │       ├── MessageList
│   │       │   └── MessageBubble[]
│   │       │       └── ToolCallCollapsible
│   │       ├── TypingIndicator
│   │       └── MessageInput
│   │
│   ├── DashboardPage
│   │   ├── MetricCard[]
│   │   ├── OutcomeCategoryGrid
│   │   └── ToolUsageChart
│   │
│   └── TraceViewerPage
│       └── DecisionTimeline
│           └── DecisionNode[]
│               ├── DecisionHeader
│               └── ToolCallDetails
│
└── Shared
    ├── LoadingSkeleton
    ├── ErrorMessage
    ├── EmptyState
    └── Button
```

---

## Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| Mobile | < 640px | Single column, hamburger nav, drawer sidebar |
| Tablet | 640-1024px | Collapsible sidebar, 2-col grid on dashboard |
| Desktop | > 1024px | Full sidebar, 3-4 col grid on dashboard |

---

## Z-Index Layers

| Layer | Z-Index | Usage |
|-------|---------|-------|
| Base content | 0 | Page content |
| Sticky header | 10 | Fixed navigation |
| Sidebar overlay | 20 | Mobile drawer backdrop |
| Sidebar drawer | 30 | Mobile sidebar |
| Modal/Dialog | 40 | Confirmations, alerts |
| Toast notifications | 50 | Error/success messages |

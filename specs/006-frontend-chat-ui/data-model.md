# Frontend Data Model

**Feature**: 006-frontend-chat-ui
**Purpose**: Define TypeScript types for frontend data entities
**Status**: Complete

---

## Core Types

### Authentication

```typescript
/**
 * Authenticated user session stored in localStorage.
 * For hackathon MVP, this is mock authentication.
 */
interface UserSession {
  /** Unique user identifier (UUID format) */
  userId: string;
  /** User's email address */
  email: string;
  /** Display name (derived from email) */
  displayName: string;
  /** ISO timestamp when session was created */
  createdAt: string;
}

/**
 * Authentication context state.
 */
interface AuthState {
  /** Current user session, null if not logged in */
  user: UserSession | null;
  /** Whether auth state is being loaded */
  isLoading: boolean;
  /** Whether user is authenticated */
  isAuthenticated: boolean;
}
```

---

### Chat Entities

```typescript
/**
 * A chat conversation containing messages.
 * Maps to backend Conversation model.
 */
interface Conversation {
  /** Unique identifier (UUID) */
  id: string;
  /** Auto-generated title from first message */
  title: string;
  /** ISO timestamp of creation */
  createdAt: string;
  /** ISO timestamp of last update */
  updatedAt: string;
}

/**
 * Summary of a conversation for list views.
 * Lighter than full Conversation to reduce payload.
 */
interface ConversationSummary {
  /** Unique identifier (UUID) */
  id: string;
  /** Conversation title */
  title: string;
  /** ISO timestamp of last activity */
  updatedAt: string;
  /** Total number of messages in conversation */
  messageCount: number;
}

/**
 * Message role enum matching backend MessageRole.
 */
type MessageRole = 'user' | 'assistant' | 'system';

/**
 * A single message in a conversation.
 * Maps to backend Message model.
 */
interface Message {
  /** Unique identifier (UUID) */
  id: string;
  /** Who sent the message */
  role: MessageRole;
  /** Message text content */
  content: string;
  /** ISO timestamp of creation */
  createdAt: string;
}

/**
 * Message displayed in chat UI with additional UI state.
 */
interface ChatMessage extends Message {
  /** Whether message is currently being sent (optimistic UI) */
  isPending?: boolean;
  /** Whether message send failed */
  hasError?: boolean;
  /** Error message if send failed */
  errorMessage?: string;
}
```

---

### Observability Entities

```typescript
/**
 * A record of a single agent decision.
 * Used in dashboard and decision trace viewer.
 */
interface DecisionLog {
  /** Unique decision identifier */
  decisionId: string;
  /** Associated conversation ID */
  conversationId: string;
  /** User who triggered the decision */
  userId: string;
  /** Original user message */
  message: string;
  /** Classified intent type (e.g., CREATE_TASK, LIST_TASKS) */
  intentType: string;
  /** Confidence score for intent classification (0-1) */
  confidence: number | null;
  /** Type of decision made */
  decisionType: string;
  /** Outcome category (e.g., SUCCESS:TASK_COMPLETED) */
  outcomeCategory: string;
  /** Agent's response text */
  responseText: string | null;
  /** ISO timestamp of decision */
  createdAt: string;
  /** Processing duration in milliseconds */
  durationMs: number;
}

/**
 * A record of a tool invocation within a decision.
 */
interface ToolInvocationLog {
  /** Name of the MCP tool invoked */
  toolName: string;
  /** Parameters passed to the tool */
  parameters: Record<string, unknown>;
  /** Tool execution result (if successful) */
  result: Record<string, unknown> | null;
  /** Whether tool execution succeeded */
  success: boolean;
  /** Error code if failed */
  errorCode: string | null;
  /** Error message if failed */
  errorMessage: string | null;
  /** Tool execution duration in milliseconds */
  durationMs: number;
  /** ISO timestamp of invocation */
  invokedAt: string;
  /** Order of invocation within decision */
  sequence: number;
}

/**
 * Complete trace of a decision including all tool invocations.
 * Used in decision trace viewer.
 */
interface DecisionTrace {
  /** The decision record */
  decision: DecisionLog;
  /** Ordered list of tool invocations */
  toolInvocations: ToolInvocationLog[];
}

/**
 * Aggregated metrics for dashboard display.
 */
interface MetricsSummary {
  /** Total number of decisions in period */
  totalDecisions: number;
  /** Success rate (0.0 - 1.0) */
  successRate: number;
  /** Count of errors by category */
  errorBreakdown: Record<string, number>;
  /** Average decision processing time (ms) */
  avgDecisionDurationMs: number;
  /** Average tool execution time (ms) */
  avgToolDurationMs: number;
  /** Distribution of intent types */
  intentDistribution: Record<string, number>;
  /** Count of each tool used */
  toolUsage: Record<string, number>;
}

/**
 * Generic paginated query result.
 */
interface QueryResult<T> {
  /** List of items */
  items: T[];
  /** Total count matching query */
  total: number;
  /** Whether more items exist */
  hasMore: boolean;
}
```

---

### API Request/Response Types

```typescript
/**
 * Request to send a chat message.
 */
interface SendMessageRequest {
  /** Existing conversation ID, or null to create new */
  conversationId: string | null;
  /** Message content (1-32000 chars) */
  content: string;
}

/**
 * Response after sending a message.
 */
interface SendMessageResponse {
  /** Conversation ID (new or existing) */
  conversationId: string;
  /** The assistant's reply */
  message: Message;
  /** Full conversation history */
  messages: Message[];
}

/**
 * Response for listing conversations.
 */
interface ConversationListResponse {
  /** List of conversation summaries */
  conversations: ConversationSummary[];
  /** Total count of conversations */
  total: number;
  /** Limit used for this request */
  limit: number;
  /** Offset used for this request */
  offset: number;
}

/**
 * Response for getting conversation detail.
 */
interface ConversationDetailResponse {
  /** Full conversation data */
  conversation: Conversation;
  /** All messages in chronological order */
  messages: Message[];
}

/**
 * Query parameters for decisions endpoint.
 */
interface DecisionQueryParams {
  /** Filter by conversation */
  conversationId?: string;
  /** Filter by user */
  userId?: string;
  /** Filter after timestamp (ISO) */
  startTime?: string;
  /** Filter before timestamp (ISO) */
  endTime?: string;
  /** Filter by decision type */
  decisionType?: string;
  /** Filter by outcome category */
  outcomeCategory?: string;
  /** Max results (default 100, max 1000) */
  limit?: number;
  /** Pagination offset */
  offset?: number;
}

/**
 * Query parameters for metrics endpoint.
 */
interface MetricsQueryParams {
  /** Start of analysis period (ISO) - required */
  startTime: string;
  /** End of analysis period (ISO) - defaults to now */
  endTime?: string;
  /** Filter by user */
  userId?: string;
}
```

---

### Error Types

```typescript
/**
 * API error codes matching backend.
 */
type ErrorCode =
  | 'INVALID_ID_FORMAT'
  | 'CONVERSATION_NOT_FOUND'
  | 'ACCESS_DENIED'
  | 'VALIDATION_ERROR'
  | 'SERVICE_UNAVAILABLE'
  | 'DECISION_NOT_FOUND';

/**
 * API error response structure.
 */
interface ApiError {
  error: {
    code: ErrorCode;
    message: string;
  };
}

/**
 * Frontend error state for UI display.
 */
interface ErrorState {
  /** Error code for programmatic handling */
  code: ErrorCode | 'NETWORK_ERROR' | 'TIMEOUT' | 'UNKNOWN';
  /** User-friendly error message */
  message: string;
  /** Whether error is retryable */
  isRetryable: boolean;
}
```

---

### UI State Types

```typescript
/**
 * Chat page UI state.
 */
interface ChatPageState {
  /** Active conversation ID, null if new conversation */
  activeConversationId: string | null;
  /** Current input text */
  inputValue: string;
  /** Whether a message is being sent */
  isSending: boolean;
  /** Whether conversation history is loading */
  isLoadingHistory: boolean;
  /** Current error state */
  error: ErrorState | null;
}

/**
 * Dashboard page UI state.
 */
interface DashboardPageState {
  /** Selected time range for metrics */
  timeRange: 'hour' | 'day' | 'week' | 'month';
  /** Whether metrics are loading */
  isLoading: boolean;
  /** Current error state */
  error: ErrorState | null;
}

/**
 * Decision trace viewer UI state.
 */
interface TraceViewerState {
  /** Selected conversation ID */
  selectedConversationId: string | null;
  /** Selected decision ID for expanded view */
  expandedDecisionId: string | null;
  /** Whether trace is loading */
  isLoading: boolean;
  /** Current error state */
  error: ErrorState | null;
}

/**
 * Tool invocation expansion state in trace viewer.
 */
interface ToolExpansionState {
  /** Map of tool sequence number to expanded state */
  [sequence: number]: boolean;
}
```

---

## Entity Relationships

```
UserSession
    │
    └── owns many ──▶ Conversation
                         │
                         └── contains many ──▶ Message
                                                  │
                                                  │ (observability layer)
                                                  ▼
                                             DecisionLog
                                                  │
                                                  └── has many ──▶ ToolInvocationLog
```

---

## Validation Rules

| Entity | Field | Rule |
|--------|-------|------|
| SendMessageRequest | content | 1-32000 characters, not empty |
| UserSession | userId | Valid UUID format |
| UserSession | email | Valid email format |
| DecisionQueryParams | limit | 1-1000 |
| DecisionQueryParams | offset | >= 0 |
| MetricsQueryParams | startTime | Valid ISO 8601 timestamp |

---

## State Transitions

### ChatMessage States

```
[Initial] ──send──▶ [Pending] ──success──▶ [Confirmed]
                        │
                        └──failure──▶ [Error] ──retry──▶ [Pending]
```

### DecisionLog Outcome Categories

```
SUCCESS:TASK_COMPLETED   - Tool executed successfully
SUCCESS:CLARIFIED        - Clarification resolved
AMBIGUITY:NEEDS_CLARIFICATION - Agent requested clarification
REFUSAL:OUT_OF_SCOPE     - Request outside agent capabilities
ERROR:TOOL_INVOCATION    - Tool execution failed
ERROR:POLICY_VIOLATION   - Request violated policy
```

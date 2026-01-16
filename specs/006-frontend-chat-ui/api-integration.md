# API Integration Specification

**Feature**: 006-frontend-chat-ui
**Purpose**: Define frontend data contracts and backend API integration points

---

## API Endpoints Consumed

### Chat API

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/api/chat` | POST | Send a chat message | `SendMessageRequest` | `SendMessageResponse` |

### Conversations API

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/api/conversations` | GET | List user conversations | Query: `limit`, `offset` | `ConversationListResponse` |
| `/api/conversations/{id}` | GET | Get conversation with messages | Path: `conversation_id` | `ConversationDetailResponse` |

### Observability API (for Dashboard & Trace Viewer)

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/api/observability/decisions` | GET | Query decision logs | Query filters | `QueryResult<DecisionLog>` |
| `/api/observability/decisions/{id}/trace` | GET | Get decision trace | Path: `decision_id` | `DecisionTrace` |
| `/api/observability/metrics` | GET | Get metrics summary | Query: `start_time`, `end_time` | `MetricsSummary` |

---

## Frontend Data Contracts

### Chat Types

```
SendMessageRequest {
  conversation_id: UUID | null  // null to create new conversation
  content: string               // message text (1-32000 chars)
}

SendMessageResponse {
  conversation_id: UUID
  message: MessageResponse      // the assistant's reply
  messages: MessageResponse[]   // full conversation history
}

MessageResponse {
  id: UUID
  role: "user" | "assistant"
  content: string
  created_at: ISO8601 datetime
}
```

### Conversation Types

```
ConversationListResponse {
  conversations: ConversationSummary[]
  total: number
  limit: number
  offset: number
}

ConversationSummary {
  id: UUID
  title: string
  updated_at: ISO8601 datetime
  message_count: number
}

ConversationDetailResponse {
  conversation: ConversationResponse
  messages: MessageResponse[]
}

ConversationResponse {
  id: UUID
  title: string
  created_at: ISO8601 datetime
  updated_at: ISO8601 datetime
}
```

### Observability Types

```
DecisionLog {
  decision_id: UUID
  conversation_id: string
  user_id: string
  message: string
  intent_type: string
  confidence: number
  decision_type: string
  outcome_category: string
  response_text: string
  created_at: ISO8601 datetime
  duration_ms: number
}

ToolInvocationLog {
  tool_name: string
  parameters: object
  result: object | null
  success: boolean
  error_code: string | null
  error_message: string | null
  duration_ms: number
  invoked_at: ISO8601 datetime
  sequence: number
}

DecisionTrace {
  decision: DecisionLog
  tool_invocations: ToolInvocationLog[]
}

MetricsSummary {
  total_decisions: number
  success_rate: number           // 0.0 - 1.0
  error_breakdown: Record<string, number>
  avg_decision_duration_ms: number
  avg_tool_duration_ms: number
  intent_distribution: Record<string, number>
  tool_usage: Record<string, number>
}

QueryResult<T> {
  items: T[]
  total: number
  has_more: boolean
}
```

---

## Error Handling Strategy

### Network Failures

| Scenario | Frontend Behavior |
|----------|-------------------|
| Backend unreachable | Show "Unable to connect to server. Check your connection." with retry button |
| Request timeout (>10s) | Show "Request timed out. Please try again." with retry button |
| 5xx server error | Show "Something went wrong on our end. Please try again later." |

### Invalid Responses

| Scenario | Frontend Behavior |
|----------|-------------------|
| Malformed JSON | Log to console, show generic error message |
| Missing required fields | Use defaults where safe, log warning |
| Unexpected status code | Show status-appropriate error message |

### Authentication Errors

| Status Code | Frontend Behavior |
|-------------|-------------------|
| 401 Unauthorized | Clear session, redirect to login with "Session expired" message |
| 403 Forbidden | Show "You don't have access to this resource" |

### Validation Errors

| Status Code | Frontend Behavior |
|-------------|-------------------|
| 400 Bad Request | Display inline validation errors from response body |
| 422 Unprocessable Entity | Display field-level errors from response body |

---

## Loading States

Every async action MUST have a loading state:

| Action | Loading UI |
|--------|------------|
| Sending chat message | Thinking indicator in chat, disabled send button |
| Loading conversations | Skeleton list items |
| Loading conversation detail | Skeleton message bubbles |
| Loading dashboard metrics | Skeleton cards with pulse animation |
| Loading decision trace | Skeleton timeline nodes |

---

## Environment Configuration

```
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API base URL
NEXT_PUBLIC_AUTH_ENABLED=true              # Enable/disable authentication
```

**Rules**:
- All API URLs MUST be constructed from `NEXT_PUBLIC_API_URL`
- Never hardcode localhost or production URLs in code
- Frontend MUST fail gracefully if environment variables are missing

---

## Request Headers

All authenticated requests MUST include:

```
Authorization: Bearer <session_token>
Content-Type: application/json
```

For mock authentication (hackathon mode):
- User ID can be passed via `X-User-Id` header
- Backend accepts this when `AUTH_MODE=mock` environment variable is set

---

## API Response Caching

| Endpoint | Cache Strategy |
|----------|----------------|
| `/api/conversations` | Cache for 30s, invalidate on new message |
| `/api/conversations/{id}` | Cache for 10s, invalidate on new message |
| `/api/observability/metrics` | Cache for 60s |
| `/api/chat` | Never cache |

---

## Retry Policy

| Request Type | Retry Count | Backoff |
|--------------|-------------|---------|
| GET requests | 3 | Exponential (1s, 2s, 4s) |
| POST requests | 1 | Immediate |

**Important**: Never retry POST `/api/chat` automatically to prevent duplicate messages.

# Frontend API Contract

**Feature**: 006-frontend-chat-ui
**Purpose**: Define API client contracts and integration patterns
**Version**: 1.0.0

---

## API Base Configuration

```typescript
// Environment-based configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === 'true';
```

---

## Authentication Headers

All API requests must include appropriate headers:

```typescript
interface RequestHeaders {
  'Content-Type': 'application/json';
  // For mock auth mode (hackathon)
  'X-User-Id'?: string;
  // For production auth (future)
  'Authorization'?: `Bearer ${string}`;
}

function getHeaders(userId?: string): RequestHeaders {
  const headers: RequestHeaders = {
    'Content-Type': 'application/json',
  };

  if (userId) {
    headers['X-User-Id'] = userId;
  }

  return headers;
}
```

---

## API Endpoints

### Chat Endpoints

#### POST /api/chat - Send Message

Send a chat message and get agent response.

**Request**:
```typescript
interface SendMessageRequest {
  conversation_id?: string;  // UUID, omit for new conversation
  content: string;           // 1-32000 chars
}
```

**Response (200)**:
```typescript
interface SendMessageResponse {
  conversation_id: string;   // UUID
  message: {
    id: string;              // UUID
    role: 'user' | 'assistant';
    content: string;
    created_at: string;      // ISO timestamp
  };
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
  }>;
}
```

**Errors**:
| Status | Code | Cause |
|--------|------|-------|
| 400 | INVALID_ID_FORMAT | Malformed conversation_id |
| 403 | ACCESS_DENIED | Not conversation owner |
| 404 | CONVERSATION_NOT_FOUND | Conversation doesn't exist |
| 422 | VALIDATION_ERROR | Empty content |

---

### Conversation Endpoints

#### GET /api/conversations - List Conversations

List user's conversations.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 20 | Max results (1-100) |
| offset | int | 0 | Pagination offset |

**Response (200)**:
```typescript
interface ConversationListResponse {
  conversations: Array<{
    id: string;
    title: string;
    updated_at: string;
    message_count: number;
  }>;
  total: number;
  limit: number;
  offset: number;
}
```

---

#### GET /api/conversations/{id} - Get Conversation

Get conversation with all messages.

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| id | UUID | Conversation ID |

**Response (200)**:
```typescript
interface ConversationDetailResponse {
  conversation: {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
  };
  messages: Array<{
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    created_at: string;
  }>;
}
```

**Errors**:
| Status | Code | Cause |
|--------|------|-------|
| 400 | INVALID_ID_FORMAT | Malformed UUID |
| 403 | ACCESS_DENIED | Not owner |
| 404 | CONVERSATION_NOT_FOUND | Doesn't exist |

---

### Observability Endpoints

> **Note**: These endpoints need to be created in backend. See `backend/src/api/routes/observability.py`.

#### GET /api/observability/decisions - Query Decisions

Query decision logs with filters.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| conversation_id | string | - | Filter by conversation |
| user_id | string | - | Filter by user |
| start_time | ISO string | - | Filter after timestamp |
| end_time | ISO string | - | Filter before timestamp |
| decision_type | string | - | Filter by type |
| outcome_category | string | - | Filter by outcome |
| limit | int | 100 | Max results (1-1000) |
| offset | int | 0 | Pagination offset |

**Response (200)**:
```typescript
interface DecisionQueryResponse {
  items: Array<{
    decision_id: string;
    conversation_id: string;
    user_id: string;
    message: string;
    intent_type: string;
    confidence: number | null;
    decision_type: string;
    outcome_category: string;
    response_text: string | null;
    created_at: string;
    duration_ms: number;
  }>;
  total: number;
  has_more: boolean;
}
```

---

#### GET /api/observability/decisions/{id}/trace - Get Decision Trace

Get complete decision trace with tool invocations.

**Path Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| id | UUID | Decision ID |

**Response (200)**:
```typescript
interface DecisionTraceResponse {
  decision: {
    decision_id: string;
    conversation_id: string;
    user_id: string;
    message: string;
    intent_type: string;
    confidence: number | null;
    decision_type: string;
    outcome_category: string;
    response_text: string | null;
    created_at: string;
    duration_ms: number;
  };
  tool_invocations: Array<{
    tool_name: string;
    parameters: Record<string, unknown>;
    result: Record<string, unknown> | null;
    success: boolean;
    error_code: string | null;
    error_message: string | null;
    duration_ms: number;
    invoked_at: string;
    sequence: number;
  }>;
}
```

**Errors**:
| Status | Code | Cause |
|--------|------|-------|
| 404 | DECISION_NOT_FOUND | Decision doesn't exist |

---

#### GET /api/observability/metrics - Get Metrics Summary

Get aggregated metrics for a time period.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| start_time | ISO string | **required** | Start of period |
| end_time | ISO string | now | End of period |
| user_id | string | - | Filter by user |

**Response (200)**:
```typescript
interface MetricsSummaryResponse {
  total_decisions: number;
  success_rate: number;           // 0.0 - 1.0
  error_breakdown: Record<string, number>;
  avg_decision_duration_ms: number;
  avg_tool_duration_ms: number;
  intent_distribution: Record<string, number>;
  tool_usage: Record<string, number>;
}
```

---

## Error Response Format

All error responses follow this structure:

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
```

---

## API Client Implementation

### Base Fetcher

```typescript
class ApiClient {
  private baseUrl: string;
  private userId: string | null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.userId = null;
  }

  setUserId(userId: string | null) {
    this.userId = userId;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers = getHeaders(this.userId || undefined);

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(response.status, error);
    }

    return response.json();
  }

  // Chat
  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Conversations
  async listConversations(limit = 20, offset = 0): Promise<ConversationListResponse> {
    return this.request(`/api/conversations?limit=${limit}&offset=${offset}`);
  }

  async getConversation(id: string): Promise<ConversationDetailResponse> {
    return this.request(`/api/conversations/${id}`);
  }

  // Observability
  async queryDecisions(params: DecisionQueryParams): Promise<DecisionQueryResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    });
    return this.request(`/api/observability/decisions?${searchParams}`);
  }

  async getDecisionTrace(id: string): Promise<DecisionTraceResponse> {
    return this.request(`/api/observability/decisions/${id}/trace`);
  }

  async getMetrics(params: MetricsQueryParams): Promise<MetricsSummaryResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set('start_time', params.startTime);
    if (params.endTime) searchParams.set('end_time', params.endTime);
    if (params.userId) searchParams.set('user_id', params.userId);
    return this.request(`/api/observability/metrics?${searchParams}`);
  }
}
```

---

## SWR Hooks

```typescript
import useSWR from 'swr';

// Conversations
export function useConversations(limit = 20, offset = 0) {
  return useSWR<ConversationListResponse>(
    `/api/conversations?limit=${limit}&offset=${offset}`,
    fetcher,
    { revalidateOnFocus: false }
  );
}

export function useConversation(id: string | null) {
  return useSWR<ConversationDetailResponse>(
    id ? `/api/conversations/${id}` : null,
    fetcher
  );
}

// Observability
export function useDecisions(params: DecisionQueryParams) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) searchParams.set(key, String(value));
  });

  return useSWR<DecisionQueryResponse>(
    `/api/observability/decisions?${searchParams}`,
    fetcher,
    { refreshInterval: 30000 }
  );
}

export function useDecisionTrace(decisionId: string | null) {
  return useSWR<DecisionTraceResponse>(
    decisionId ? `/api/observability/decisions/${decisionId}/trace` : null,
    fetcher
  );
}

export function useMetrics(startTime: string, endTime?: string) {
  const params = new URLSearchParams({ start_time: startTime });
  if (endTime) params.set('end_time', endTime);

  return useSWR<MetricsSummaryResponse>(
    `/api/observability/metrics?${params}`,
    fetcher,
    { refreshInterval: 60000 }
  );
}
```

---

## Caching Strategy

| Endpoint | Cache TTL | Invalidation |
|----------|-----------|--------------|
| /api/conversations | 30s | On new message |
| /api/conversations/{id} | 10s | On new message |
| /api/observability/metrics | 60s | None |
| /api/observability/decisions | 30s | None |
| /api/chat | Never | N/A (POST) |

---

## Retry Policy

| Request Type | Retry Count | Backoff |
|--------------|-------------|---------|
| GET requests | 3 | Exponential (1s, 2s, 4s) |
| POST /api/chat | 0 | No retry (prevent duplicates) |

---

## Request Timeout

All requests have a 10-second timeout. Longer timeouts for:
- POST /api/chat: 30 seconds (agent processing time)

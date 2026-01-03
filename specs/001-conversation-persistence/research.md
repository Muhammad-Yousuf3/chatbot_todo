# Research: Conversation Persistence & Stateless Chat Contract

**Feature Branch**: `001-conversation-persistence`
**Date**: 2026-01-02
**Status**: Complete

## Research Summary

This document captures research findings for implementing stateless conversation persistence
with FastAPI, SQLModel, and PostgreSQL.

---

## Decision 1: Conversation Identification Strategy

### Question
How should conversations be identified and managed per user?

### Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | One active conversation per user | Simpler implementation, fewer queries | Limits multi-threaded conversations, less flexible |
| B | Multiple conversations per user (conversation_id) | Flexible, future-proof, clean boundaries | Slightly more complex queries |

### Decision
**Option B: Multiple conversations per user**

### Rationale
- Aligns with FR-005 (unique conversation identifiers) and FR-011 (list all conversations)
- Enables future features like topic-based conversations or conversation history browsing
- UUID-based conversation IDs provide collision-free identification across distributed systems
- Standard pattern in chat applications (ChatGPT, Slack, etc.)

### Implementation Notes
- Use UUID v4 for conversation IDs (standard, collision-resistant)
- Client passes `conversation_id` to continue existing conversation
- Omitting `conversation_id` triggers new conversation creation (lazy creation)

---

## Decision 2: Message Ordering Mechanism

### Question
How should messages within a conversation be ordered?

### Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | Timestamp-based ordering | Simple, human-readable, standard | Edge case with identical timestamps |
| B | Auto-increment sequence per conversation | Strong guarantees, deterministic | More schema complexity, harder to merge |

### Decision
**Option A: Timestamp-based ordering with database guarantees**

### Rationale
- PostgreSQL `TIMESTAMP WITH TIME ZONE` provides microsecond precision
- Combined with database-assigned `created_at` using `DEFAULT NOW()`, ordering is reliable
- For tie-breaking edge cases: secondary sort by message ID (UUID, lexicographically stable)
- Simpler schema aligns with Principle V (Simplicity Over Cleverness)
- Standard practice in stateless chat systems

### Implementation Notes
- All timestamps assigned server-side (not client-provided) per edge case handling in spec
- Query: `ORDER BY created_at ASC, id ASC` for deterministic ordering
- Index on `(conversation_id, created_at)` for efficient history retrieval

---

## Decision 3: Conversation Lifecycle

### Question
Should conversations be created explicitly or lazily on first message?

### Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | Lazy creation on first message | Cleaner UX, simpler API, fewer round trips | Conversation metadata must be created atomically with first message |
| B | Explicit conversation creation | More control, separate concerns | More API complexity, worse UX |

### Decision
**Option A: Lazy creation on first message**

### Rationale
- Single endpoint (`POST /api/chat`) handles both new and existing conversations
- Aligns with FR-001 (create conversation when no existing reference)
- Reduces API surface area (Principle V: Simplicity)
- Transaction ensures atomicity: conversation + message created together or not at all

### Implementation Notes
- If `conversation_id` is omitted or invalid → create new conversation
- If `conversation_id` is valid → append to existing
- Conversation title auto-generated from first message (truncated, can be updated later)

---

## Decision 4: SQLModel Relationship Pattern

### Question
How should SQLModel relationships be structured for Conversation ↔ Message?

### Research Findings

SQLModel (built on SQLAlchemy) supports relationship patterns:

```python
# Parent model
class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True)  # FK to Better Auth user
    title: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    messages: list["Message"] = Relationship(back_populates="conversation")

# Child model
class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=20)  # "user" | "assistant" | "system"
    content: str = Field(max_length=32000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: Conversation = Relationship(back_populates="messages")
```

### Decision
Use SQLModel `Relationship` with explicit foreign keys and lazy loading.

### Rationale
- Explicit FK constraints ensure referential integrity at database level
- Lazy loading prevents N+1 queries when loading conversation without messages
- Eager loading available via `selectinload` when messages are needed
- Index on `conversation_id` enables efficient message retrieval

---

## Decision 5: Stateless Request Lifecycle

### Question
What is the exact sequence of database operations for a chat request?

### Research Findings

Standard stateless chat flow:

```
1. Receive request (user_id, content, optional conversation_id)
2. Validate input (non-empty content, valid format)
3. Begin database transaction
4. If conversation_id:
   - Load conversation (verify ownership)
   - If not found or not owned → error
   Else:
   - Create new conversation
5. Load message history (ordered by timestamp)
6. Persist user message
7. [Future: Pass to AI agent for response generation]
8. Persist assistant message (if any)
9. Update conversation.updated_at
10. Commit transaction
11. Return response with conversation_id and messages
```

### Decision
Implement the above lifecycle with single transaction boundary.

### Rationale
- Single transaction ensures atomicity (FR-002: persist before response)
- Loading history inside transaction provides consistent read
- Supports future AI agent integration without architectural changes
- Ownership check at step 4 enforces FR-012

---

## Decision 6: Error Handling Strategy

### Question
How should errors be structured for API consumers?

### Research Findings

FastAPI standard patterns:
- Use HTTP status codes correctly (400, 401, 403, 404, 422, 500)
- Return structured error responses with `detail` field
- Use Pydantic for request validation (automatic 422 responses)

### Decision
Structured error responses with clear codes and messages.

### Error Taxonomy

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|------------|---------|
| Invalid conversation ID format | 400 | `INVALID_ID_FORMAT` | "Conversation ID must be a valid UUID" |
| Conversation not found | 404 | `CONVERSATION_NOT_FOUND` | "Conversation does not exist" |
| Not conversation owner | 403 | `ACCESS_DENIED` | "You do not have access to this conversation" |
| Empty message content | 422 | `VALIDATION_ERROR` | "Message content cannot be empty" |
| Message too long | 422 | `VALIDATION_ERROR` | "Message exceeds maximum length of 32000 characters" |
| Database unavailable | 503 | `SERVICE_UNAVAILABLE` | "Service temporarily unavailable" |

### Rationale
- Consistent error format simplifies client error handling
- Specific error codes enable programmatic handling
- Human-readable messages support debugging

---

## Decision 7: Index Strategy

### Question
What database indexes are needed for efficient queries?

### Research Findings

Query patterns from spec requirements:
1. Get conversation by ID (ownership check): `WHERE id = ? AND user_id = ?`
2. List user conversations: `WHERE user_id = ? ORDER BY updated_at DESC`
3. Get messages for conversation: `WHERE conversation_id = ? ORDER BY created_at ASC`

### Decision
Create the following indexes:

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| conversation | pk | `id` | Primary lookup |
| conversation | idx_user_conversations | `user_id, updated_at DESC` | List user conversations |
| message | pk | `id` | Primary lookup |
| message | idx_conversation_messages | `conversation_id, created_at ASC` | Get message history |

### Rationale
- Composite indexes cover the exact query patterns
- Descending order on `updated_at` optimizes "most recent first" listing
- Ascending order on `created_at` optimizes chronological message retrieval

---

## Validation Against Constitution

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Spec-Driven Development | ✅ | Spec completed before plan |
| II. Stateless Backend | ✅ | No in-memory state, all from DB |
| III. Clear Boundaries | ✅ | API layer handles requests, DB handles persistence |
| IV. AI Safety | ✅ | This spec has no AI logic (deferred to later spec) |
| V. Simplicity | ✅ | Minimal schema, standard patterns |
| VI. Deterministic | ✅ | Timestamp ordering, transaction guarantees |

---

## Open Items for Future Specs

1. **AI Agent Integration**: How assistant messages are generated (deferred to AI agent spec)
2. **MCP Tool Integration**: How AI accesses conversations via tools (deferred to MCP spec)
3. **Pagination**: Large conversation history pagination (implement if needed)
4. **Conversation Archive/Delete**: Lifecycle management beyond create/read (out of scope per spec)

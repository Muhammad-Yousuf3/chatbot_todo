# Implementation Plan: Conversation Persistence & Stateless Chat Contract

**Branch**: `001-conversation-persistence` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-conversation-persistence/spec.md`

## Summary

Implement a stateless conversation persistence layer for the AI-powered Todo chatbot.
The system will store and retrieve conversations and messages from PostgreSQL, enabling
any server instance to process chat requests without in-memory state. This provides
the foundation for AI agent integration in later specifications.

**Primary Requirements**:
- Create and persist conversations with unique identifiers
- Store messages with role, content, and timestamp
- Load complete conversation history on each request
- Enforce user ownership of conversations
- Maintain message ordering via timestamps

**Technical Approach**:
- FastAPI endpoints for chat and conversation management
- SQLModel entities for Conversation and Message
- PostgreSQL (Neon) for persistence
- UUID-based identifiers for global uniqueness
- Lazy conversation creation on first message

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLModel, Pydantic, uvicorn
**Storage**: PostgreSQL (Neon) with SQLModel ORM
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux server (containerized)
**Project Type**: Web application (backend API)
**Performance Goals**: <500ms for conversation history retrieval (up to 100 messages)
**Constraints**: Full statelessness, no in-memory caching, sync with DB before response
**Scale/Scope**: 100 concurrent users, ~1000 conversations, ~10,000 messages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification |
|-----------|--------|--------------|
| I. Spec-Driven Development | ✅ PASS | Spec completed and approved before planning |
| II. Stateless Backend | ✅ PASS | All state persisted in DB, no in-memory caching |
| III. Clear Boundaries | ✅ PASS | API handles requests, DB handles persistence, no AI in this spec |
| IV. AI Safety | ✅ PASS | This spec has no AI logic (deferred to later spec) |
| V. Simplicity | ✅ PASS | 2 entities, 3 endpoints, standard REST patterns |
| VI. Deterministic | ✅ PASS | Timestamp ordering, transaction guarantees, consistent reads |

**Technical Constraints Compliance**:

| Constraint | Status | Notes |
|------------|--------|-------|
| FastAPI | ✅ | Using for all endpoints |
| SQLModel | ✅ | Using for data models |
| PostgreSQL (Neon) | ✅ | Primary datastore |
| Better Auth | ✅ | JWT validation assumed, user_id from token |
| No direct DB from AI | ✅ | N/A - no AI in this spec |
| No in-memory state | ✅ | All data loaded fresh per request |

## Project Structure

### Documentation (this feature)

```text
specs/001-conversation-persistence/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Research findings and decisions
├── data-model.md        # Entity definitions
├── quickstart.md        # Usage examples
├── contracts/
│   └── openapi.yaml     # API contract
├── checklists/
│   └── requirements.md  # Quality validation
└── tasks.md             # (Created by /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py    # Conversation SQLModel
│   │   └── message.py         # Message SQLModel
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py    # Chat business logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py        # POST /api/chat
│   │   │   └── conversations.py # GET /api/conversations
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py        # Request/response schemas
│   │   │   └── error.py       # Error response schemas
│   │   └── deps.py            # Dependencies (DB session, auth)
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py         # Database session management
│   └── main.py                # FastAPI app entry
└── tests/
    ├── conftest.py            # Test fixtures
    ├── integration/
    │   ├── test_chat.py       # Chat endpoint tests
    │   └── test_conversations.py
    └── unit/
        ├── test_models.py     # Model validation tests
        └── test_services.py   # Service logic tests
```

**Structure Decision**: Web application structure with `backend/` directory.
This aligns with future frontend integration (OpenAI ChatKit) and keeps
backend code isolated for independent testing and deployment.

## Architecture Overview

### Stateless Chat Request Flow

```
┌────────┐     ┌─────────────────────────────────────────────────────┐     ┌────────────┐
│ Client │     │                    FastAPI Backend                   │     │ PostgreSQL │
└────┬───┘     └─────────────────────────────────────────────────────┘     └─────┬──────┘
     │                                                                            │
     │  POST /api/chat                                                            │
     │  {conversation_id?, content}                                               │
     ├──────────────────────────►│                                                │
     │                           │  1. Validate JWT (Better Auth)                 │
     │                           │  2. Validate request body                      │
     │                           │                                                │
     │                           │  3. BEGIN TRANSACTION                          │
     │                           ├───────────────────────────────────────────────►│
     │                           │                                                │
     │                           │  4a. If conversation_id:                       │
     │                           │      Load conversation (verify owner)          │
     │                           │  4b. Else:                                     │
     │                           │      Create new conversation                   │
     │                           │◄───────────────────────────────────────────────┤
     │                           │                                                │
     │                           │  5. Load message history                       │
     │                           │◄───────────────────────────────────────────────┤
     │                           │                                                │
     │                           │  6. Insert user message                        │
     │                           ├───────────────────────────────────────────────►│
     │                           │                                                │
     │                           │  7. Update conversation.updated_at             │
     │                           ├───────────────────────────────────────────────►│
     │                           │                                                │
     │                           │  8. COMMIT TRANSACTION                         │
     │                           ├───────────────────────────────────────────────►│
     │                           │                                                │
     │  Response:                │                                                │
     │  {conversation_id,        │                                                │
     │   message, messages[]}    │                                                │
     │◄──────────────────────────┤                                                │
     │                           │                                                │
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Conversation ID Strategy | Multiple per user (UUID) | Flexible, future-proof, clean boundaries |
| Message Ordering | Timestamp-based | Simple, standard, sufficient with server-assigned timestamps |
| Conversation Creation | Lazy (on first message) | Better UX, fewer round trips, simpler API |
| Error Handling | Structured codes | Consistent format, programmatic handling |

See [research.md](./research.md) for full decision documentation.

## Complexity Tracking

> **No constitution violations to justify.** All gates passed.

## Extension Points

This spec provides extension points for future specifications:

1. **AI Agent Integration** (Future Spec)
   - After step 6, pass message history to AI agent
   - Agent generates response
   - Insert assistant message before commit

2. **MCP Tool Integration** (Future Spec)
   - AI agent calls MCP tools during response generation
   - Tools have access to conversation context
   - Tool results included in response

3. **Task Management** (Future Spec)
   - MCP tools for create/list/update/complete/delete todos
   - Tasks linked to user via same user_id

The current design requires no changes to support these extensions.

## Testing Strategy

### Integration Tests

| Test Case | Validates |
|-----------|-----------|
| New conversation creation | FR-001, FR-005, SC-001 |
| Continue existing conversation | FR-002, FR-003, SC-005 |
| Message ordering | FR-007, SC-007 |
| Ownership enforcement | FR-012, SC-006 |
| Statelessness (server restart) | FR-004, SC-001, SC-005 |
| Concurrent users | SC-003 |

### Unit Tests

| Test Case | Validates |
|-----------|-----------|
| Message validation (empty) | FR-013 |
| Message validation (too long) | FR-013 |
| Conversation title generation | FR-014 |
| Role enum validation | FR-009 |

## Artifacts Generated

- [x] `research.md` - Research findings and decisions
- [x] `data-model.md` - Entity definitions (Conversation, Message)
- [x] `contracts/openapi.yaml` - API contract
- [x] `quickstart.md` - Usage examples
- [ ] `tasks.md` - Created by `/sp.tasks` command

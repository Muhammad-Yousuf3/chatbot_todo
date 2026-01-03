# Implementation Plan: MCP Task Tools

**Branch**: `002-mcp-task-tools` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification for MCP tools enabling AI-controlled task management

## Summary

Implement five MCP tools (`add_task`, `list_tasks`, `update_task`, `complete_task`, `delete_task`) using the FastMCP high-level API that allow AI agents to manage todo tasks without direct database access. Tools enforce user ownership, validate inputs, and return structured responses. The MCP server is embedded within the FastAPI backend process and uses SQLModel for database operations.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, MCP SDK (>=1.25,<2), SQLModel, Pydantic
**Storage**: PostgreSQL (Neon) via SQLModel with async engine
**Testing**: pytest with pytest-asyncio
**Target Platform**: Linux server (containerized backend)
**Project Type**: Web application (backend component)
**Performance Goals**: Tool responses within 500ms for single CRUD operations
**Constraints**: Stateless tools, ownership enforcement per tool, no direct AI database access
**Scale/Scope**: Supports same user scale as conversation persistence (100 concurrent users)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | PASS | Following specify → plan → tasks → implement sequence |
| II. Stateless Backend | PASS | All tools are stateless; no memory between invocations |
| III. Clear Responsibility Boundaries | PASS | MCP Tools layer handles database operations only |
| IV. AI Safety Through Controlled Tool Usage | PASS | AI agents access tasks only via MCP tools; ownership enforced per tool |
| V. Simplicity Over Cleverness | PASS | One tool per action; no complex abstractions |
| VI. Deterministic, Debuggable Behavior | PASS | Structured responses; idempotent operations; traceable invocations |

**Technical Constraints Alignment**:

| Layer | Constitution | This Plan |
|-------|--------------|-----------|
| Backend Framework | FastAPI | FastAPI (MCP server embedded) |
| Database ORM | SQLModel | SQLModel (async) |
| Database | PostgreSQL (Neon) | PostgreSQL (Neon) |
| Tool Interface | Official MCP SDK | FastMCP (part of mcp>=1.25,<2) |

## Project Structure

### Documentation (this feature)

```text
specs/002-mcp-task-tools/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # MCP SDK research and decisions
├── data-model.md        # Task entity model
├── quickstart.md        # Implementation guide
├── contracts/
│   └── mcp-tools.md     # Tool input/output contracts
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py              # FastMCP server with lifespan
│   │   ├── schemas.py             # ToolResult, TaskData models
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── add_task.py        # FR-001, FR-010
│   │       ├── list_tasks.py      # FR-002, FR-011
│   │       ├── update_task.py     # FR-003, FR-012
│   │       ├── complete_task.py   # FR-004, FR-013
│   │       └── delete_task.py     # FR-005, FR-014
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py                # Task SQLModel
│   └── db/
│       ├── __init__.py
│       └── engine.py              # Async engine setup
└── tests/
    ├── mcp/
    │   ├── conftest.py            # MCP test fixtures
    │   ├── test_add_task.py
    │   ├── test_list_tasks.py
    │   ├── test_update_task.py
    │   ├── test_complete_task.py
    │   └── test_delete_task.py
    └── integration/
        └── test_mcp_ownership.py  # Cross-user isolation tests
```

**Structure Decision**: Backend-only feature. MCP server is embedded in the existing `backend/` directory structure. Tools are organized in a dedicated `mcp_server/tools/` module for clear separation from API endpoints.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      AI Agent (OpenAI Agents SDK)                 │
│                                                                  │
│  - Receives user intent from chat                               │
│  - Selects appropriate MCP tool                                  │
│  - Passes user_id explicitly to tools                           │
│  - Processes structured ToolResult responses                     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ MCP Protocol (STDIO or SSE)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    MCP Server (FastMCP)                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  add_task    │  │  list_tasks  │  │ update_task  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │complete_task │  │ delete_task  │                             │
│  └──────────────┘  └──────────────┘                             │
│                                                                  │
│  - Validates inputs                                              │
│  - Enforces ownership (user_id check)                           │
│  - Manages database session lifecycle                            │
│  - Returns structured ToolResult                                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ SQLModel (async)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PostgreSQL (Neon)                             │
│                                                                  │
│  ┌──────────────┐                                               │
│  │    task      │  id, user_id, description, status,            │
│  │              │  created_at, completed_at                     │
│  └──────────────┘                                               │
└──────────────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

### ADR-001: Embedded MCP Server

**Decision**: Embed MCP server within FastAPI backend process

**Rationale**:
- Simpler deployment for hackathon scope
- Shared database connection pool
- Single process reduces operational complexity

**Trade-offs**:
- Less isolation than separate service
- Cannot scale MCP independently

**Alternatives Rejected**:
- Separate MCP microservice: Too much operational complexity for scope

### ADR-002: One Tool Per Action

**Decision**: Create separate tools for each action (add, list, update, complete, delete)

**Rationale**:
- Clear, auditable contracts per operation
- Independent testing
- AI agents select precise action

**Trade-offs**:
- More tool definitions to maintain
- Slightly more code duplication

**Alternatives Rejected**:
- Generic mutation tool: Higher ambiguity, harder to audit

### ADR-003: Ownership Enforcement in Tools

**Decision**: Enforce user ownership inside each MCP tool

**Rationale**:
- Tools are the security boundary per constitution
- Prevents bypass if agent layer is compromised
- Each tool self-contained for testing

**Trade-offs**:
- Repeated ownership checks in each tool

**Alternatives Rejected**:
- Enforce in agent layer: Higher security risk

### ADR-004: Structured Error Responses

**Decision**: Return structured `ToolResult` with error codes

**Rationale**:
- AI agents can interpret error types programmatically
- Consistent response format
- Clear separation of success/error paths

**Implementation**:
```python
class ToolResult(BaseModel):
    success: bool
    data: Optional[dict | list] = None
    error: Optional[str] = None
    error_code: Optional[str] = None  # VALIDATION_ERROR, NOT_FOUND, ACCESS_DENIED
```

## Testing Strategy

| Category | Scope | Approach |
|----------|-------|----------|
| Unit | Each tool function | Mock database, test validation and logic |
| Integration | Tool → Database | Real database, test CRUD operations |
| Contract | Input/Output schemas | Validate against contracts/mcp-tools.md |
| Ownership | Cross-user isolation | Verify user A cannot access user B's tasks |
| Idempotency | complete_task, delete_task | Verify repeated calls succeed |

## Complexity Tracking

No violations requiring justification. The design follows all constitution principles.

## Artifacts Generated

| Artifact | Path | Purpose |
|----------|------|---------|
| Research | research.md | MCP SDK patterns and decisions |
| Data Model | data-model.md | Task entity definition |
| Contracts | contracts/mcp-tools.md | Tool input/output specifications |
| Quickstart | quickstart.md | Implementation guide |

## Next Steps

Run `/sp.tasks` to generate the ordered task list for implementation.

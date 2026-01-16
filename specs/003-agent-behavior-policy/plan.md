# Implementation Plan: Agent Behavior & Tool Invocation Policy

**Branch**: `003-agent-behavior-policy` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-agent-behavior-policy/spec.md`

## Summary

Implement a deterministic agent decision engine that interprets user messages, classifies intents, and invokes MCP tools for task management. The agent is stateless, auditable, and enforces strict behavioral boundaries - it can ONLY perform task operations through MCP tools defined in Spec 002.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: OpenAI Agents SDK, MCP SDK (>=1.25,<2), Pydantic
**Storage**: PostgreSQL (Neon) via SQLModel - accessed ONLY through MCP tools
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (same as backend)
**Project Type**: Web application (backend extension)
**Performance Goals**: <500ms response time for intent classification
**Constraints**: Agent MUST be stateless; NO direct database access
**Scale/Scope**: Single-tenant per conversation, sequential message processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | PASS | This plan follows approved spec.md |
| II. Stateless Backend | PASS | Agent is stateless; context passed per request |
| III. Clear Responsibility Boundaries | PASS | Agent → Tool Orchestration only; MCP → DB only |
| IV. AI Safety Through Controlled Tool Usage | PASS | Agent invokes ONLY MCP tools, no direct DB |
| V. Simplicity Over Cleverness | PASS | Rule-based decisions with LLM classification fallback |
| VI. Deterministic, Debuggable Behavior | PASS | Same input → same output; full audit trail |

**Post-Design Re-Check**: All principles validated. Architecture maintains clear boundaries.

## Project Structure

### Documentation (this feature)

```text
specs/003-agent-behavior-policy/
├── plan.md              # This file
├── research.md          # Agent patterns research
├── data-model.md        # Intent, Decision, Audit entities
├── quickstart.md        # Usage examples
├── contracts/
│   └── agent-interface.md  # Decision engine interface contract
└── tasks.md             # Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── agent/                    # NEW: Agent decision engine
│   │   ├── __init__.py
│   │   ├── engine.py             # AgentDecisionEngine main class
│   │   ├── intent.py             # Intent classification logic
│   │   ├── resolver.py           # Task reference resolution
│   │   ├── policy.py             # Decision rules and guardrails
│   │   ├── responses.py          # Response templates
│   │   └── schemas.py            # Pydantic models for agent types
│   ├── mcp_server/               # Existing: MCP tools (Spec 002)
│   │   └── tools/
│   ├── models/                   # Existing: Database models
│   └── api/
│       └── routes/
│           └── chat.py           # Update to use agent engine
└── tests/
    └── agent/                    # NEW: Agent tests
        ├── conftest.py           # Test fixtures
        ├── test_intent.py        # Intent classification tests
        ├── test_resolver.py      # Task resolution tests
        ├── test_policy.py        # Decision policy tests
        └── test_engine.py        # Integration tests
```

**Structure Decision**: Extend existing backend with `agent/` module. Agent orchestrates MCP tools via established tool interfaces.

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           REQUEST BOUNDARY                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Message ─────► API Route (chat.py)                                │
│                           │                                              │
│                           ▼                                              │
│                  ┌─────────────────────┐                                │
│                  │  Build Decision     │ ◄──── Conversation History     │
│                  │     Context         │       (from Spec 001)          │
│                  └─────────┬───────────┘                                │
│                            │                                             │
│                            ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  AGENT DECISION ENGINE                            │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │  1. Check Pending Confirmation                             │  │   │
│  │  │  2. Classify Intent (LLM + Schema Validation)              │  │   │
│  │  │  3. Apply Decision Rules (policy.py)                       │  │   │
│  │  │  4. Generate Tool Calls OR Response                        │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────┬───────────────────────────────────┘   │
│                                 │                                        │
│              ┌──────────────────┼──────────────────┐                    │
│              │                  │                  │                    │
│              ▼                  ▼                  ▼                    │
│         Tool Calls        Response Only      Clarification              │
│              │                  │                  │                    │
│              ▼                  │                  │                    │
│  ┌───────────────────┐         │                  │                    │
│  │   MCP TOOL LAYER  │         │                  │                    │
│  │   (Spec 002)      │         │                  │                    │
│  │   ┌───────────┐   │         │                  │                    │
│  │   │ add_task  │   │         │                  │                    │
│  │   │ list_tasks│   │         │                  │                    │
│  │   │ update    │   │         │                  │                    │
│  │   │ complete  │   │         │                  │                    │
│  │   │ delete    │   │         │                  │                    │
│  │   └───────────┘   │         │                  │                    │
│  └─────────┬─────────┘         │                  │                    │
│            │                   │                  │                    │
│            ▼                   │                  │                    │
│  ┌───────────────────┐         │                  │                    │
│  │    DATABASE       │         │                  │                    │
│  │   (PostgreSQL)    │         │                  │                    │
│  └───────────────────┘         │                  │                    │
│                                │                  │                    │
│              └─────────────────┴──────────────────┘                    │
│                                │                                        │
│                                ▼                                        │
│                        Build Response                                   │
│                                │                                        │
│                                ▼                                        │
│                    ┌──────────────────┐                                │
│                    │  Audit Log       │ ──► ToolInvocationRecord       │
│                    └──────────────────┘                                │
│                                │                                        │
├────────────────────────────────┼────────────────────────────────────────┤
│                           RESPONSE                                       │
└────────────────────────────────┴────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | May NOT Do |
|-----------|---------------|------------|
| API Route | Request handling, auth context | Business logic |
| Agent Engine | Intent classification, tool orchestration | Direct DB access |
| Policy | Decision rules, guardrails | Tool execution |
| MCP Tools | Database operations (Spec 002) | Intent classification |
| Database | Data persistence | Business logic |

## Key Design Decisions

### 1. Intent Classification Strategy

**Decision**: LLM-based classification with strict schema validation

**Rationale**: Natural language variation ("remind me", "I gotta remember", "add task") requires LLM understanding. Strict schema validation ensures deterministic output categories.

**Implementation**:
```python
class UserIntent(BaseModel):
    intent_type: IntentType  # Enum: CREATE_TASK, LIST_TASKS, etc.
    confidence: float | None
    extracted_params: dict | None

# LLM classifies → Pydantic validates → only valid intents proceed
```

### 2. Tool Invocation Control

**Decision**: Agent proposes → Policy validates → Tool executes

**Rationale**: Extra validation layer prevents accidental mutations and enables audit.

**Flow**:
1. Agent determines intent requires tool
2. Policy checks: is this allowed? requires confirmation?
3. If approved, tool executes
4. Result logged to audit trail

### 3. Ambiguous Input Handling

**Decision**: Always ask clarification, never guess

**Rationale**: Safety over convenience. Wrong actions destroy user trust.

**Examples**:
- "groceries" (create or complete?) → Ask
- "the task" (which one?) → List and ask
- "delete everything" (really?) → Confirm explicitly

### 4. Destructive Action Confirmation

**Decision**: Two-step confirmation for DELETE only

**Rationale**: Delete is irreversible. Complete/update can be reverted.

| Action | Confirmation | Rationale |
|--------|-------------|-----------|
| add_task | No | Non-destructive |
| list_tasks | No | Read-only |
| update_task | No | Reversible |
| complete_task | No | Idempotent |
| delete_task | **Yes** | Irreversible |

### 5. Ordering Guarantees

**Decision**: Read-before-write, sequential execution

**Rules**:
- `list_tasks` MUST precede `complete_task`, `update_task`, `delete_task`
- No parallel tool calls
- One tool completes before next starts

## Testing Strategy

### Test Categories

| Category | Purpose | Coverage |
|----------|---------|----------|
| Unit: Intent | Test classification accuracy | 95% of patterns |
| Unit: Resolver | Test task reference matching | All match types |
| Unit: Policy | Test decision rules | All rules |
| Integration | Test full engine flow | All user stories |
| Determinism | Verify reproducibility | 100% identical output |
| Negative | Test rejection of bad input | All edge cases |
| Security | Test prompt injection resistance | Common attacks |

### Key Test Scenarios

1. **Determinism Test**: Same input + context → identical output (run 10x)
2. **Safety Test**: No mutation without tool call
3. **Isolation Test**: No tool call for general chat
4. **Confirmation Test**: Delete requires explicit "yes"
5. **Prompt Injection Test**: Malicious input → safe handling

### Test Data

```python
# Intent classification test cases
TEST_INTENTS = [
    ("remind me to buy groceries", IntentType.CREATE_TASK, {"description": "buy groceries"}),
    ("what are my tasks?", IntentType.LIST_TASKS, None),
    ("I finished the groceries", IntentType.COMPLETE_TASK, {"task_reference": "groceries"}),
    ("hello", IntentType.GENERAL_CHAT, None),
    ("groceries", IntentType.AMBIGUOUS, {"possible_intents": [...]}),
]
```

## Complexity Tracking

No violations requiring justification. Architecture follows constitution principles.

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Spec 001: Conversation Persistence | Required | Implemented |
| Spec 002: MCP Task Tools | Required | Implemented |
| OpenAI Agents SDK | New | To be added |
| Better Auth | Required | External (auth context) |

## Artifacts Generated

| Artifact | Path | Status |
|----------|------|--------|
| research.md | specs/003-agent-behavior-policy/research.md | Complete |
| data-model.md | specs/003-agent-behavior-policy/data-model.md | Complete |
| agent-interface.md | specs/003-agent-behavior-policy/contracts/agent-interface.md | Complete |
| quickstart.md | specs/003-agent-behavior-policy/quickstart.md | Complete |
| plan.md | specs/003-agent-behavior-policy/plan.md | This file |

## Next Steps

Run `/sp.tasks` to decompose this plan into ordered, executable implementation tasks.

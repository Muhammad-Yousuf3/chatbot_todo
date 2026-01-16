# Implementation Plan: Agent Evaluation, Safety & Observability

**Branch**: `004-agent-observability` | **Date**: 2026-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-agent-observability/spec.md`

## Summary

Implement a comprehensive observability layer that logs all agent decisions and tool invocations, enabling full auditability, failure diagnosis, error categorization, and behavioral drift detection. The layer is **additive only** - it observes and records without modifying agent behavior (Spec 003), MCP tools (Spec 002), or persistence (Spec 001). Logs are stored in SQLite for query support without external service dependencies.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: OpenAI Agents SDK, MCP SDK (>=1.25,<2), Pydantic, SQLite (via aiosqlite)
**Storage**: SQLite (logs.db) - separate from PostgreSQL tasks database
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (same as backend)
**Project Type**: Web application (backend extension)
**Performance Goals**: Log writes <10ms; queries <2s for 10k entries (SC-008)
**Constraints**: No external monitoring services; no UI dashboards; logs only
**Scale/Scope**: 30-day retention, concurrent write support, offline analysis

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Development | PASS | This plan follows approved spec.md |
| II. Stateless Backend | PASS | Logging is append-only, no request-spanning state |
| III. Clear Responsibility Boundaries | PASS | Observability is isolated layer, doesn't affect agent/tools |
| IV. AI Safety Through Controlled Tool Usage | PASS | No new tools; logging observes existing tool calls |
| V. Simplicity Over Cleverness | PASS | SQLite + JSON logs; no ML drift detection |
| VI. Deterministic, Debuggable Behavior | PASS | Every decision logged; full reconstruction possible |

**Post-Design Re-Check**: All principles validated. Observability layer is strictly additive and non-invasive.

## Project Structure

### Documentation (this feature)

```text
specs/004-agent-observability/
├── plan.md              # This file
├── research.md          # Logging format, granularity, drift detection research
├── data-model.md        # DecisionLog, ToolInvocationLog, Baseline entities
├── quickstart.md        # Usage examples for logging and review
├── contracts/
│   └── observability-api.md  # Internal service interfaces
└── tasks.md             # Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── observability/            # NEW: Observability layer
│   │   ├── __init__.py
│   │   ├── models.py             # SQLite models for logs
│   │   ├── logging_service.py    # Decision and tool logging
│   │   ├── query_service.py      # Log queries and metrics
│   │   ├── baseline_service.py   # Baseline management
│   │   ├── validation_service.py # Automated validation
│   │   ├── categories.py         # Outcome category taxonomy
│   │   └── database.py           # SQLite connection management
│   ├── agent/                    # Existing: Agent engine (Spec 003)
│   │   └── engine.py             # UPDATE: Add logging hooks
│   ├── mcp_server/               # Existing: MCP tools (Spec 002)
│   └── api/
│       └── routes/
│           └── chat.py           # UPDATE: Add decision logging
├── data/
│   └── logs.db                   # NEW: SQLite log database
└── tests/
    └── observability/            # NEW: Observability tests
        ├── conftest.py           # Test fixtures
        ├── test_logging.py       # Logging service tests
        ├── test_queries.py       # Query service tests
        ├── test_baseline.py      # Baseline management tests
        ├── test_validation.py    # Validation service tests
        └── fixtures/
            └── agent_behaviors.yaml  # Test case fixtures
```

**Structure Decision**: Add `observability/` module alongside existing `agent/` module. Minimal changes to existing code - only add logging hooks in chat.py and engine.py.

## Architecture

### End-to-End Observable Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REQUEST BOUNDARY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Input ────► [LOG: Incoming Message]                                   │
│       │                                                                      │
│       ▼                                                                      │
│  Conversation Load (Spec 001)                                               │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AGENT DECISION ENGINE (Spec 003)                   │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │   │
│  │  │ Intent          │───►│ Decision        │───►│ Tool Call OR    │  │   │
│  │  │ Classification  │    │ Rules           │    │ Response        │  │   │
│  │  │ [LOG: Intent]   │    │ [LOG: Decision] │    │                 │  │   │
│  │  └─────────────────┘    └─────────────────┘    └────────┬────────┘  │   │
│  │                                                          │           │   │
│  └──────────────────────────────────────────────────────────┼───────────┘   │
│                                                              │               │
│            ┌─────────────────┬───────────────────────────────┘               │
│            │                 │                                               │
│            ▼                 ▼                                               │
│       Tool Call         Response Only                                        │
│            │                 │                                               │
│            ▼                 │                                               │
│  ┌─────────────────┐        │                                               │
│  │   MCP TOOLS     │        │                                               │
│  │  (Spec 002)     │        │                                               │
│  │ [LOG: Request]  │        │                                               │
│  │ [LOG: Response] │        │                                               │
│  └────────┬────────┘        │                                               │
│           │                  │                                               │
│           ▼                  │                                               │
│      Persistence             │                                               │
│      (Spec 001)              │                                               │
│           │                  │                                               │
│           └──────────────────┴─────────► Final Response                     │
│                                               │                              │
│                                               ▼                              │
│                              [LOG: Outcome Category + Duration]              │
│                                               │                              │
├───────────────────────────────────────────────┼──────────────────────────────┤
│                           STRUCTURED LOGS                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         OBSERVABILITY LAYER                           │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ DecisionLog │  │ToolInvocLog │  │  Baseline   │  │ Validation  │  │   │
│  │  │   (Write)   │  │   (Write)   │  │  Snapshot   │  │   Report    │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │   │
│  │         │                │                │                │         │   │
│  │         └────────────────┴────────────────┴────────────────┘         │   │
│  │                                   │                                   │   │
│  │                                   ▼                                   │   │
│  │                          SQLite (logs.db)                            │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Logging Points (Explicit)

| Point | When | What is Logged |
|-------|------|----------------|
| 1. Incoming Intent | After message received | user_id, conversation_id, message, timestamp |
| 2. Intent Classification | After LLM classification | intent_type, confidence, extracted_params |
| 3. Decision Outcome | After policy rules | decision_type (INVOKE_TOOL, RESPOND_ONLY, etc.) |
| 4. Tool Request | Before MCP call | tool_name, parameters, sequence |
| 5. Tool Response | After MCP returns | result, success/failure, duration_ms |
| 6. Error/Refusal | On exception or policy rejection | error_code, error_message, category |
| 7. Final Outcome | After response generated | outcome_category, total_duration_ms |

### Component Responsibilities

| Component | Responsibility | May NOT Do |
|-----------|---------------|------------|
| LoggingService | Write decision and tool logs | Query logs, manage baselines |
| QueryService | Read logs, compute metrics | Write logs, modify data |
| BaselineService | Create/compare baselines | Execute agent actions |
| ValidationService | Run tests, generate reports | Modify agent behavior |
| Observability DB | Store logs (SQLite) | Store tasks (PostgreSQL) |

### Separation from Existing Specs

| Layer | Spec | This Spec (004) |
|-------|------|-----------------|
| Agent Logic | 003 | NO CHANGE - only observe |
| Tool Execution | 002 | NO CHANGE - only observe |
| Persistence | 001 | NO CHANGE - uses separate DB |

## Key Design Decisions

### 1. Logging Format

**Decision**: Structured JSON logs stored in SQLite

**Rationale**:
- FR-013 requires structured, queryable format
- FR-014 requires query by multiple dimensions
- JSON enables schema evolution without migrations
- SQLite provides SQL queries without external dependencies

**Implementation**:
```python
class DecisionLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    decision_id: UUID = Field(index=True)
    conversation_id: str = Field(index=True)
    user_id: str = Field(index=True)
    message: str = Field(max_length=4000)
    intent_type: str
    confidence: float | None
    extracted_params: dict = Field(default={}, sa_column=Column(JSON))
    decision_type: str
    outcome_category: str = Field(index=True)  # "CATEGORY:SUBCATEGORY"
    response_text: str | None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    duration_ms: int
```

### 2. Log Granularity

**Decision**: Decision-level granularity with hierarchical structure

**Rationale**:
- SC-001 requires 100% decision logging
- SC-002 requires 5-minute reconstruction capability
- SC-003 requires root cause identification from logs

**Levels**:
1. **Decision Log**: One entry per user message (parent)
2. **Tool Invocation Logs**: Multiple entries per decision (children)
3. **Metrics Summary**: Aggregated on query (derived)

### 3. Drift Detection Strategy

**Decision**: Rule-based assertions with stored baselines

**Rationale**:
- No ML training per constraints
- SC-005 requires 10% deviation flagging
- Manual review + automated comparison

**Implementation**:
```python
class DriftReport:
    baseline_id: UUID
    intent_drift: dict[str, float]  # {intent: percentage_delta}
    tool_drift: dict[str, float]    # {tool: percentage_delta}
    max_drift: float
    drift_exceeded: bool  # True if max_drift > 0.10
```

### 4. Error Classification Taxonomy

**Decision**: Two-level taxonomy (Category:Subcategory)

**Categories**:
| Category | Subcategories |
|----------|---------------|
| SUCCESS | TASK_COMPLETED, RESPONSE_GIVEN, CLARIFICATION_ANSWERED |
| ERROR | USER_INPUT, INTENT_CLASSIFICATION, TOOL_INVOCATION, RESPONSE_GENERATION |
| REFUSAL | OUT_OF_SCOPE, MISSING_PERMISSION, RATE_LIMITED |
| AMBIGUITY | UNCLEAR_INTENT, MULTIPLE_MATCHES, MISSING_CONTEXT |

**Rationale**:
- FR-009 through FR-012 define these categories
- Two levels enable both aggregate metrics and detailed diagnosis
- String format "CAT:SUB" enables prefix queries

### 5. Observability Boundaries

**MUST Log**:
- User message content (required for audit per FR-001)
- Intent classification and confidence (FR-002)
- Decision type and outcome category (FR-003, FR-009)
- Tool names, parameters, results (FR-005, FR-006)
- Timestamps and durations (performance analysis)
- Error codes and messages (FR-007)

**MUST NOT Log**:
- Authentication tokens
- Session cookies
- Database credentials
- Full stack traces in production (summary only)
- Internal model weights or prompts

**MUST Redact for Export**:
- User IDs (hash or anonymize for external sharing)

## Integration Points

### Where Logging Hooks Are Added

1. **chat.py:process_message()** - Entry point
   - Before: Generate decision_id, capture start time
   - After: Write DecisionLog with outcome

2. **engine.py:AgentDecisionEngine.process()** - Intent/decision
   - After intent classification: Log intent result
   - After decision rules: Log decision type

3. **engine.py:_invoke_tool()** - Tool execution (if exists)
   - Before: Log tool request
   - After: Log tool response with duration

### Minimal Code Changes

```python
# chat.py - Add logging wrapper
from src.observability import LoggingService

async def process_message(request: ChatRequest) -> ChatResponse:
    decision_id = uuid4()
    start_time = datetime.utcnow()

    try:
        # Existing agent processing...
        result = await engine.process(request)
        outcome = "SUCCESS:TASK_COMPLETED" if result.tool_used else "SUCCESS:RESPONSE_GIVEN"
    except AgentError as e:
        outcome = f"ERROR:{e.category}"
        raise
    finally:
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        await logging_service.write_decision_log(
            decision_id=decision_id,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            message=request.message,
            intent=engine.last_intent,
            decision=engine.last_decision,
            outcome_category=outcome,
            duration_ms=int(duration_ms)
        )
```

## Testing Strategy

### Test Categories

| Category | Purpose | Coverage |
|----------|---------|----------|
| Unit: Logging | Verify write operations | All log fields |
| Unit: Queries | Verify read operations | All query patterns |
| Unit: Baseline | Verify drift detection | Threshold scenarios |
| Unit: Validation | Verify test runner | Pass/fail states |
| Integration | Full logging flow | End-to-end recording |
| Performance | Query timing | <2s for 10k entries |

### Key Test Scenarios

1. **Complete Trace Test**: User message → logs contain intent, decision, tools, outcome
2. **Tool Correlation Test**: Each tool invocation links to parent decision
3. **Error Categorization Test**: Different failure modes → correct categories
4. **Drift Detection Test**: 15% deviation → drift_exceeded=True
5. **Retention Test**: 31-day-old logs → automatically deleted
6. **Concurrent Write Test**: Multiple simultaneous writes → no data loss

### Test Fixtures

```yaml
# tests/observability/fixtures/agent_behaviors.yaml
tests:
  - test_id: TC001
    input: "remind me to buy groceries"
    expected_intent: CREATE_TASK
    expected_tool: add_task
    expected_outcome: SUCCESS

  - test_id: TC002
    input: "what are my tasks"
    expected_intent: LIST_TASKS
    expected_tool: list_tasks
    expected_outcome: SUCCESS

  - test_id: TC003
    input: "groceries"
    expected_intent: AMBIGUOUS
    expected_tool: null
    expected_outcome: AMBIGUITY

  - test_id: TC004
    input: "what's the weather"
    expected_intent: GENERAL_CHAT
    expected_tool: null
    expected_outcome: REFUSAL:OUT_OF_SCOPE
```

## Complexity Tracking

No violations requiring justification. Architecture follows constitution principles:
- No new external services
- No modifications to existing specs
- Simple SQLite storage
- Minimal integration hooks

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Spec 001: Conversation Persistence | Required | Implemented |
| Spec 002: MCP Task Tools | Required | Implemented |
| Spec 003: Agent Behavior Policy | Required | Implemented |
| aiosqlite | New | To be added |
| SQLite | System | Available |

## Artifacts Generated

| Artifact | Path | Status |
|----------|------|--------|
| research.md | specs/004-agent-observability/research.md | Complete |
| data-model.md | specs/004-agent-observability/data-model.md | Complete |
| observability-api.md | specs/004-agent-observability/contracts/observability-api.md | Complete |
| quickstart.md | specs/004-agent-observability/quickstart.md | Complete |
| plan.md | specs/004-agent-observability/plan.md | This file |

## Next Steps

Run `/sp.tasks` to decompose this plan into ordered, executable implementation tasks.

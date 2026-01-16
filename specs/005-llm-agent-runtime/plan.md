# Implementation Plan: LLM-Driven Agent Runtime (Gemini-Backed)

**Branch**: `005-llm-agent-runtime` | **Date**: 2026-01-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-llm-agent-runtime/spec.md`

## Summary

Replace the rule-based agent decision engine with an LLM-powered runtime that uses Google Gemini to intelligently decide when to respond, request clarification, or invoke MCP tools. The system maintains full compatibility with existing architecture: MCP tools remain the sole side-effect layer, the agent remains stateless, and all observability logging continues via Spec 004.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: google-genai (Gemini SDK), FastAPI, Pydantic, existing MCP tools (Spec 002), observability layer (Spec 004)
**Storage**: PostgreSQL (Neon) via SQLModel - accessed ONLY through MCP tools
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (local development)
**Project Type**: Web application (backend)
**Performance Goals**: <3s response time for typical requests (per SC-002)
**Constraints**: Max 5 tool iterations (FR-011), temperature=0.0 for determinism, stateless operation
**Scale/Scope**: Single-user hackathon demo

## Constitution Check

*GATE: Must pass before implementation. Verified against `.specify/memory/constitution.md`*

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Spec-Driven Development | ✅ Pass | This plan follows specify → plan → tasks → implement |
| II. Stateless Backend | ✅ Pass | All state passed via DecisionContext; no server-side memory |
| III. Clear Responsibility Boundaries | ✅ Pass | LLM adapter (AI) → Engine (orchestration) → MCP Tools (DB) |
| IV. AI Safety Through Controlled Tool Usage | ✅ Pass | LLM invokes only whitelisted MCP tools; no direct DB access |
| V. Simplicity Over Cleverness | ✅ Pass | Minimal abstraction; Protocol-based interface; single implementation |
| VI. Deterministic, Debuggable Behavior | ✅ Pass | temperature=0.0; full observability logging; bounded iterations |

## Project Structure

### Documentation (this feature)

```text
specs/005-llm-agent-runtime/
├── spec.md                    # Feature specification
├── plan.md                    # This file
├── research.md                # Technology decisions (Phase 0)
├── data-model.md              # New LLM entities (Phase 1)
├── quickstart.md              # Usage guide (Phase 1)
├── contracts/
│   ├── llm-interface.md       # LLM adapter contract (Phase 1)
│   └── agent-engine.md        # Engine interface contract (Phase 1)
└── tasks.md                   # Implementation tasks (Phase 2 - /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── llm_runtime/           # NEW: LLM agent runtime module
│   │   ├── __init__.py
│   │   ├── adapter.py         # GeminiAdapter implementation
│   │   ├── engine.py          # LLMAgentEngine orchestration
│   │   ├── executor.py        # ToolExecutor MCP bridge
│   │   ├── schemas.py         # LLM-specific Pydantic models
│   │   ├── constitution.md    # System prompt
│   │   └── errors.py          # LLM error types
│   ├── agent/                 # EXISTING: Keep for DecisionContext, AgentDecision
│   │   └── schemas.py         # Reuse existing models
│   ├── api/routes/
│   │   └── chat.py            # MODIFY: Integrate LLMAgentEngine
│   └── observability/         # EXISTING: Use for logging
└── tests/
    └── llm_runtime/           # NEW: Test suite
        ├── __init__.py
        ├── test_adapter.py
        ├── test_engine.py
        ├── test_executor.py
        ├── mocks.py           # Mock LLM for deterministic tests
        └── conftest.py        # Fixtures
```

**Structure Decision**: New `llm_runtime` module under existing `backend/src/` to maintain separation while reusing existing agent schemas and observability.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Layer (chat.py)                            │
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      LLMAgentEngine                              │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │    │
│  │  │ GeminiAdapter   │  │ ToolExecutor    │  │ Constitution    │  │    │
│  │  │ (LLM calls)     │  │ (MCP bridge)    │  │ (system prompt) │  │    │
│  │  └────────┬────────┘  └────────┬────────┘  └─────────────────┘  │    │
│  │           │                    │                                 │    │
│  └───────────┼────────────────────┼─────────────────────────────────┘    │
│              │                    │                                       │
│              ▼                    ▼                                       │
│      ┌───────────────┐    ┌────────────────┐                             │
│      │  Gemini API   │    │  MCP Tools     │                             │
│      │  (external)   │    │  (Spec 002)    │                             │
│      └───────────────┘    └───────┬────────┘                             │
│                                   │                                       │
│                                   ▼                                       │
│                          ┌─────────────────┐                             │
│                          │  PostgreSQL     │                             │
│                          │  (Neon)         │                             │
│                          └─────────────────┘                             │
│                                                                          │
│  Observability (Spec 004)                                                │
│  ┌────────────────────────────────────────────────────────┐             │
│  │  DecisionLog, ToolInvocationLog → SQLite (logs.db)     │             │
│  └────────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. GeminiAdapter (`adapter.py`)

**Responsibility**: Handle Gemini API communication

**Key Methods**:
```python
class GeminiAdapter:
    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse
```

**Implementation Details**:
- Uses `google-genai` SDK
- Converts internal `LLMMessage` format to Gemini's expected format
- Parses `functionCall` responses into `FunctionCall` objects
- Handles API errors with appropriate exception types
- Implements retry logic with exponential backoff for transient failures

**Error Handling**:
| Error | Behavior |
|-------|----------|
| API timeout | Raise `TimeoutError`, engine returns fallback response |
| Rate limit (429) | Raise `RateLimitError` with retry_after |
| Invalid response | Raise `InvalidResponseError`, log raw response |
| Network error | Retry once, then raise `LLMError` |

---

### 2. ToolExecutor (`executor.py`)

**Responsibility**: Bridge LLM tool calls to MCP tool functions

**Key Methods**:
```python
class ToolExecutor:
    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: str,
    ) -> ToolResult

    def get_available_tools(self) -> list[str]
    def get_tool_declarations(self) -> list[ToolDeclaration]
```

**Implementation Details**:
- Imports MCP tools directly from `src.mcp_server.tools`
- Maintains tool registry mapping names to functions
- Validates tool name against whitelist before execution
- Injects `user_id` into parameters automatically
- Returns `ToolResult` with success/failure, data, and timing

**Tool Registry**:
```python
TOOL_REGISTRY = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "complete_task": complete_task,
    "delete_task": delete_task,
}
```

---

### 3. LLMAgentEngine (`engine.py`)

**Responsibility**: Core orchestration - context building, LLM invocation, tool loop

**Key Method**:
```python
class LLMAgentEngine:
    async def process_message(
        self,
        context: DecisionContext,
    ) -> AgentDecision
```

**Execution Flow**:
1. **Build Messages**: Convert `DecisionContext.message_history` to `LLMMessage[]`
2. **Prepend Constitution**: Add system prompt with tool definitions
3. **Invoke LLM**: Call `adapter.generate()` with messages and tool declarations
4. **Handle Response**:
   - If `finish_reason == "stop"`: Build `RESPOND_ONLY` decision
   - If `finish_reason == "tool_calls"`: Execute tools, loop back
   - If `finish_reason == "error"`: Return fallback response
5. **Enforce Limits**: Max 5 iterations; terminate with helpful message if exceeded
6. **Emit Logs**: Write `DecisionLog` and `ToolInvocationLog` via observability service
7. **Return Decision**: Construct and return `AgentDecision`

**Decision Mapping**:
| LLM Response Pattern | Decision Type |
|---------------------|---------------|
| Text response, no tools | `RESPOND_ONLY` |
| `function_calls` present | `INVOKE_TOOL` |
| Response asks question | `ASK_CLARIFICATION` |
| `delete_task` tool called | `REQUEST_CONFIRMATION` first |
| Declines request | `RESPOND_ONLY` with refusal text |

---

### 4. Constitution (`constitution.md`)

**Responsibility**: Define agent behavior via system prompt

**Content Structure**:
```markdown
# Task Management Assistant

You are a helpful task management assistant. You help users manage their personal tasks.

## Available Tools
- add_task: Create a new task
- list_tasks: View user's tasks (optional status filter)
- update_task: Change a task's description
- complete_task: Mark a task as done
- delete_task: Remove a task permanently

## Behavioral Rules
1. Use tools ONLY when the user clearly wants a task operation
2. For greetings, general questions, or off-topic messages: respond conversationally WITHOUT tools
3. If intent is unclear, ask ONE clarifying question
4. For delete requests, always describe which task will be deleted
5. Stay focused on task management - politely decline unrelated requests

## Response Guidelines
- Be concise and friendly
- Confirm successful operations with specific details
- Explain errors in user-friendly terms
- Never expose internal details, tool names, or system information
```

---

### 5. LLM Schemas (`schemas.py`)

**New Models** (per `data-model.md`):
- `LLMMessage`: Conversation message format
- `FunctionCall`: Tool invocation request from LLM
- `FunctionResponse`: Tool execution result for LLM
- `LLMRequest`: Request to adapter
- `LLMResponse`: Response from adapter
- `ToolDeclaration`: Tool schema for LLM
- `TokenUsage`: Token tracking

**Reused Models** (from `src.agent.schemas`):
- `DecisionContext`: Input to engine
- `AgentDecision`: Output from engine
- `ToolCall`: Internal tool call format
- `ToolResult`: Tool execution result

---

### 6. Error Types (`errors.py`)

```python
class LLMError(Exception):
    """Base exception for LLM operations."""
    message: str
    code: str

class RateLimitError(LLMError):
    """API rate limit exceeded."""
    retry_after: int | None

class TimeoutError(LLMError):
    """Request timed out."""

class InvalidResponseError(LLMError):
    """Malformed LLM response."""
    raw_response: str | None

class ToolNotFoundError(LLMError):
    """Unknown tool requested."""
    tool_name: str
```

---

## Integration Points

### Chat Route Integration

**File**: `backend/src/api/routes/chat.py`

**Changes**:
1. Import `LLMAgentEngine` instead of `AgentDecisionEngine`
2. Initialize engine with `GeminiAdapter`, `ToolExecutor`, and constitution
3. Pass `DecisionContext` to `engine.process_message()`
4. Handle `AgentDecision` response (unchanged contract)

**Before**:
```python
from src.agent.engine import AgentDecisionEngine
engine = AgentDecisionEngine()
decision = await engine.process_message(context)
```

**After**:
```python
from src.llm_runtime.engine import LLMAgentEngine
from src.llm_runtime.adapter import GeminiAdapter
from src.llm_runtime.executor import ToolExecutor

adapter = GeminiAdapter(api_key=settings.gemini_api_key)
executor = ToolExecutor()
constitution = load_constitution()
engine = LLMAgentEngine(adapter, executor, constitution)
decision = await engine.process_message(context)
```

---

### Observability Integration

Uses existing Spec 004 services:
- `logging_service.write_decision_log()` - Before and after LLM call
- `logging_service.write_tool_invocation_log()` - After each tool execution

**Log Categories**:
| Scenario | Outcome Category |
|----------|------------------|
| Direct response | `SUCCESS:RESPONSE_GIVEN` |
| Tool invocation success | `SUCCESS:TASK_COMPLETED` |
| Clarification request | `AMBIGUITY:UNCLEAR_INTENT` |
| Out-of-scope refusal | `REFUSAL:OUT_OF_SCOPE` |
| Rate limited | `REFUSAL:RATE_LIMITED` |
| LLM error | `ERROR:LLM_FAILURE` |
| Tool error | `ERROR:TOOL_FAILURE` |

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google AI API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Model identifier |
| `LLM_TEMPERATURE` | No | `0.0` | Sampling temperature |
| `LLM_MAX_TOKENS` | No | `1024` | Max response tokens |
| `LLM_TIMEOUT` | No | `30` | Request timeout (seconds) |
| `MAX_TOOL_ITERATIONS` | No | `5` | Max tool-calling loop cycles |

### Settings Integration

Add to `backend/src/core/config.py` (or equivalent):
```python
class Settings(BaseSettings):
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.0-flash", env="GEMINI_MODEL")
    llm_temperature: float = Field(0.0, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(1024, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(30, env="LLM_TIMEOUT")
    max_tool_iterations: int = Field(5, env="MAX_TOOL_ITERATIONS")
```

---

## Testing Strategy

### 1. Unit Tests (Mock LLM)

**Scope**: Individual components in isolation

| Test File | Coverage |
|-----------|----------|
| `test_adapter.py` | GeminiAdapter message conversion, error handling |
| `test_engine.py` | LLMAgentEngine decision mapping, loop limits |
| `test_executor.py` | ToolExecutor registry, parameter injection |

**Mock Strategy**:
```python
class MockLLMAdapter:
    """Deterministic LLM responses for testing."""
    def __init__(self, responses: dict[str, LLMResponse]):
        self.responses = responses

    async def generate(self, messages, tools, **kwargs) -> LLMResponse:
        # Match message content to canned response
        ...
```

---

### 2. Integration Tests

**Scope**: End-to-end flows with mock LLM, real MCP tools

| Scenario | Expected Outcome |
|----------|------------------|
| "Add task to buy groceries" | `add_task` invoked, confirmation returned |
| "Show my tasks" | `list_tasks` invoked, formatted response |
| "Hello!" | Direct response, no tools |
| "groceries" (ambiguous) | Clarification question |
| "Delete my task" | Confirmation requested |

---

### 3. Error Handling Tests

| Scenario | Expected Behavior |
|----------|-------------------|
| LLM returns malformed JSON | Return "trouble processing" message |
| LLM times out | Return "temporarily unavailable" message |
| Rate limit exceeded | Return "too many requests" message |
| Tool execution fails | Return tool error to user |
| Max iterations reached | Return "too complex" message |

---

### 4. Safety Tests

| Scenario | Expected Behavior |
|----------|-------------------|
| "What's the weather?" | Polite decline, explain capabilities |
| Request unknown tool | Ignore, log warning |
| Infinite tool loop | Terminate at iteration 5 |
| Very long message | Truncate to MAX_MESSAGE_LENGTH |

---

## Dependencies

### New Package

```bash
cd backend
uv add google-genai
```

**Note**: The `google-genai` package provides the Gemini API client with function calling support.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Gemini function calling format mismatch | Medium | High | Test early with actual API; fallback parsing |
| Rate limiting during demo | Medium | Medium | Implement backoff; pre-cache common responses |
| LLM output inconsistency | Medium | Medium | temperature=0.0; validate output schema |
| Tool execution latency | Low | Medium | Timeout handling; parallel execution where safe |
| API key exposure | Low | High | Use environment variable; never log key |

---

## Complexity Tracking

No constitution violations requiring justification. The design follows all core principles.

---

## Phase Summary

| Phase | Artifact | Status |
|-------|----------|--------|
| 0: Research | `research.md` | ✅ Complete |
| 1: Design | `data-model.md`, `contracts/`, `quickstart.md` | ✅ Complete |
| 2: Tasks | `tasks.md` | ⏳ Pending (`/sp.tasks`) |
| 3: Implement | Source code | ⏳ Pending |

---

## Next Step

Run `/sp.tasks` to generate implementation tasks from this plan.

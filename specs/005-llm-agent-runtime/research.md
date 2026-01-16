# Research: LLM-Driven Agent Runtime (Gemini-Backed)

**Feature**: 005-llm-agent-runtime
**Date**: 2026-01-04
**Status**: Complete

## Research Questions

### 1. Gemini Function Calling API

**Question**: How does Gemini's function calling work and what Python SDK is required?

**Decision**: Use `google-genai` package with function declarations

**Rationale**:
- Gemini API supports function calling via JSON schema declarations (OpenAPI-compatible)
- The `google-genai` Python SDK can auto-generate schemas from Python function docstrings
- Gemini returns `functionCall` objects but does NOT execute functions - we handle execution
- Multi-turn conversations supported by appending model responses and function results to history

**Alternatives Considered**:
- OpenAI API - Not available (no API key)
- Langchain abstraction - Over-engineering for hackathon; adds complexity
- Direct HTTP calls - SDK provides better error handling and type safety

**Key Implementation Details**:
```python
from google import genai
from google.genai import types

# Define tool as function declaration
tool_declaration = {
    "name": "add_task",
    "description": "Create a new task for the user",
    "parameters": {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "Task description"}
        },
        "required": ["description"]
    }
}

# Configure with tools
tools = types.Tool(function_declarations=[tool_declaration])
config = types.GenerateContentConfig(tools=[tools])
```

**Sources**:
- [Google AI Function Calling Docs](https://ai.google.dev/gemini-api/docs/function-calling)
- [Gemini by Example - Tool Use](https://geminibyexample.com/021-tool-use-function-calling/)

---

### 2. LLM Abstraction Layer

**Question**: How to structure the LLM adapter for potential future provider swaps?

**Decision**: Simple Protocol-based interface with single Gemini implementation

**Rationale**:
- Python Protocol allows duck-typing without inheritance complexity
- Single implementation for hackathon; interface enables future swaps
- Keep adapter thin - focus on request/response transformation

**Alternatives Considered**:
- ABC abstract base class - More rigid, unnecessary for single implementation
- No abstraction - Would require major refactoring to swap providers
- Full provider SDK abstraction - Over-engineering for MVP

**Interface Design**:
```python
from typing import Protocol

class LLMAdapter(Protocol):
    async def generate(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generate response, potentially with tool calls."""
        ...
```

---

### 3. Tool Call Loop Design

**Question**: How to handle multi-turn tool execution safely?

**Decision**: Bounded loop with max 5 iterations, explicit termination conditions

**Rationale**:
- Prevents infinite loops from LLM errors
- 5 iterations covers most realistic multi-step tasks
- Clear termination: no tool calls, max iterations, or error

**Loop Structure**:
```
1. Send message + tools to LLM
2. If response has tool calls:
   a. Execute each tool via MCP adapter
   b. Append tool results to conversation
   c. Increment iteration counter
   d. If counter < MAX_ITERATIONS: goto 1
   e. Else: terminate with timeout response
3. If response is text only: return as final response
4. If response is empty/error: return error response
```

**Alternatives Considered**:
- Unlimited iterations - Risk of infinite loops
- Single tool call only - Limits capability for complex requests
- 10 iterations - Probably excessive for task management

---

### 4. Error Handling Strategy

**Question**: How to handle Gemini API failures gracefully?

**Decision**: Layered error handling with graceful degradation

**Rationale**:
- Users should never see raw API errors
- System should remain functional even with LLM unavailable
- All errors logged for debugging

**Error Categories**:
| Error Type | Response Strategy |
|------------|-------------------|
| API timeout | Return friendly "service temporarily unavailable" message |
| Rate limit | Return "please try again shortly" with `REFUSAL:RATE_LIMITED` |
| Invalid response | Log error, return "I couldn't process that" message |
| Tool execution failure | Return tool error to LLM for recovery, or surface to user |
| Network error | Retry once, then graceful fallback |

---

### 5. Stateless Execution Model

**Question**: How to maintain stateless design while supporting multi-turn?

**Decision**: Pass complete context in each request, build conversation from DecisionContext

**Rationale**:
- Aligns with Constitution Principle II (Stateless Backend)
- DecisionContext already contains message_history
- No hidden state in engine

**Implementation**:
- `DecisionContext.message_history` provides conversation context
- LLM adapter builds Gemini messages from history
- Tool results NOT persisted - only used within single request cycle
- Pending confirmations handled by existing schema

---

### 6. MCP Tool Bridge

**Question**: How to invoke MCP tools from the LLM runtime?

**Decision**: Direct function calls via tool adapter, NOT MCP protocol

**Rationale**:
- MCP tools are already Python functions decorated with `@mcp.tool()`
- Can call directly: `await add_task(user_id, description, ctx)`
- No need for full MCP client-server communication within same process

**Alternatives Considered**:
- Full MCP client - Over-engineering for same-process calls
- HTTP calls to MCP server - Unnecessary latency

**Implementation**:
```python
from src.mcp_server.tools import add_task, list_tasks, ...

TOOL_REGISTRY = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "complete_task": complete_task,
    "delete_task": delete_task,
}

async def execute_tool(tool_name: str, params: dict, ctx: Context) -> ToolResult:
    tool_fn = TOOL_REGISTRY[tool_name]
    return await tool_fn(**params, ctx=ctx)
```

---

## Technology Stack Decisions

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| LLM API | Google Gemini | Latest | Only available API key |
| Python SDK | google-genai | Latest | Official SDK with function calling |
| Async HTTP | aiohttp | 3.x | Already in project dependencies |
| Validation | Pydantic | 2.x | Existing project standard |
| Testing | pytest + pytest-asyncio | Latest | Existing project standard |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Gemini function calling limitations | Medium | High | Test early with actual tools; document workarounds |
| Rate limiting during hackathon | Medium | Medium | Implement exponential backoff; cache common responses |
| LLM output inconsistency | Medium | Medium | Use temperature=0; validate output schema |
| Tool execution errors | Low | Medium | Robust error handling; return errors to LLM for recovery |

---

## Open Questions (Resolved)

All research questions have been resolved. No outstanding clarifications needed.

# Data Model: LLM-Driven Agent Runtime

**Feature**: 005-llm-agent-runtime
**Date**: 2026-01-04

## Overview

This feature extends the existing agent schemas (Spec 003) with LLM-specific models. The core `DecisionContext` and `AgentDecision` models remain unchanged; new models handle LLM communication.

## New Entities

### 1. LLMMessage

Represents a single message in the LLM conversation format.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role | str (enum) | Yes | "user", "assistant", or "function" |
| content | str | Conditional | Text content (required for user/assistant) |
| function_call | FunctionCall | Conditional | Tool call from assistant |
| function_response | FunctionResponse | Conditional | Result from tool execution |

**Validation Rules**:
- `content` required when `role` is "user" or "assistant" without function_call
- `function_call` only valid when `role` is "assistant"
- `function_response` only valid when `role` is "function"

---

### 2. FunctionCall

Represents an LLM-requested tool invocation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Tool name (must be in whitelist) |
| arguments | dict[str, Any] | Yes | Parameters for the tool |

**Validation Rules**:
- `name` must match one of: add_task, list_tasks, update_task, complete_task, delete_task
- `arguments` validated against tool schema

---

### 3. FunctionResponse

Represents the result of a tool execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Tool name that was called |
| response | dict[str, Any] | Yes | Serialized ToolResult |

---

### 4. LLMRequest

Request sent to the LLM adapter.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| messages | list[LLMMessage] | Yes | Conversation history |
| tools | list[ToolDeclaration] | Yes | Available tools |
| temperature | float | No | Generation temperature (default: 0.0) |
| max_tokens | int | No | Max response tokens (default: 1024) |

---

### 5. LLMResponse

Response from the LLM adapter.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | str | Conditional | Text response |
| function_calls | list[FunctionCall] | Conditional | Requested tool calls |
| finish_reason | str | Yes | "stop", "tool_calls", "max_tokens", or "error" |
| usage | TokenUsage | No | Token consumption stats |

---

### 6. ToolDeclaration

Schema for a tool available to the LLM.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | str | Yes | Tool identifier |
| description | str | Yes | What the tool does |
| parameters | dict | Yes | JSON Schema for parameters |

---

### 7. TokenUsage

Token consumption tracking.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| prompt_tokens | int | Yes | Tokens in input |
| completion_tokens | int | Yes | Tokens in output |
| total_tokens | int | Yes | Sum of above |

---

## Existing Entities (Unchanged)

The following entities from Spec 003 remain unchanged:

- **DecisionContext**: Input to agent engine
- **AgentDecision**: Output from agent engine
- **UserIntent**: Classified intent (now LLM-determined)
- **ToolCall**: Tool invocation request
- **ToolResult**: Tool execution result (from MCP tools)

---

## Entity Relationships

```
DecisionContext
    │
    ├─contains─> message_history: list[Message]
    │
    └─input to─> LLMAgentEngine
                     │
                     ├─builds─> LLMRequest
                     │              │
                     │              └─contains─> LLMMessage[]
                     │              └─contains─> ToolDeclaration[]
                     │
                     ├─sends to─> LLMAdapter (Gemini)
                     │              │
                     │              └─returns─> LLMResponse
                     │                             │
                     │                             └─may contain─> FunctionCall[]
                     │
                     ├─executes─> MCP Tools
                     │              │
                     │              └─returns─> ToolResult
                     │
                     └─produces─> AgentDecision
                                    │
                                    └─contains─> ToolCall[] | response_text
```

---

## State Transitions

The LLM runtime operates in a loop with these states:

```
[START]
    │
    v
[BUILD_REQUEST] ─── Build LLMRequest from DecisionContext
    │
    v
[INVOKE_LLM] ─── Send request to Gemini
    │
    v
[CHECK_RESPONSE]
    │
    ├─ finish_reason="stop" ───────> [BUILD_DECISION] ─> [END]
    │
    ├─ finish_reason="tool_calls" ─> [EXECUTE_TOOLS]
    │                                     │
    │                                     v
    │                               [APPEND_RESULTS]
    │                                     │
    │                                     v
    │                               [CHECK_ITERATIONS]
    │                                     │
    │                                     ├─ < MAX ─> [INVOKE_LLM]
    │                                     │
    │                                     └─ >= MAX ─> [TIMEOUT_RESPONSE] ─> [END]
    │
    └─ finish_reason="error" ──────> [ERROR_RESPONSE] ─> [END]
```

---

## Validation Constraints

### Tool Whitelist
```python
ALLOWED_TOOLS = {"add_task", "list_tasks", "update_task", "complete_task", "delete_task"}
```

### Loop Limits
```python
MAX_TOOL_ITERATIONS = 5
MAX_RESPONSE_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.0  # Deterministic
```

### Message Limits
```python
MAX_MESSAGE_LENGTH = 4000  # Existing constraint
MAX_HISTORY_MESSAGES = 20  # Prevent token overflow
```

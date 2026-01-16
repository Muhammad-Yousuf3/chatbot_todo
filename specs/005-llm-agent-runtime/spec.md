# Feature Specification: LLM-Driven Agent Runtime (Gemini-Backed)

**Feature Branch**: `005-llm-agent-runtime`
**Created**: 2026-01-04
**Status**: Draft
**Input**: User description: "Enable agent decisions to be driven by Gemini LLM using OpenAI Agent SDK-compatible abstractions"

## Purpose

Replace the existing rule-based agent decision system with an LLM-driven runtime that uses Google's Gemini model to intelligently decide when to respond, request clarification, or invoke MCP tools. The system maintains full compatibility with the existing architecture: MCP tools remain the only side-effect layer, the agent remains stateless, and all observability logging continues unchanged.

## Goals

1. Enable LLM-driven decisions: respond directly, request user clarification, or invoke MCP tools
2. Use MCP tools (Spec 002) exclusively for all side effects (task CRUD operations)
3. Emit structured `AgentDecision` objects compatible with observability layer (Spec 004)
4. Maintain stateless operation by passing all context via `DecisionContext`
5. Preserve existing agent policy, response templates, and logging mechanisms

## Constraints

- **LLM Provider**: Gemini API only (OpenAI API key unavailable)
- **Architecture Integrity**: MCP tools are the sole side-effect layer; no direct database access from agent
- **Stateless Design**: All state passed in `DecisionContext`; no session storage in agent runtime
- **Safety**: Constitution/system prompt enforces tool usage boundaries and safety rules
- **Backward Compatibility**: Existing Spec 003 policy rules and Spec 004 logging remain functional

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - LLM Decides to Invoke Tool (Priority: P1)

A user sends a natural language message requesting a task operation. The LLM interprets the intent, decides to invoke the appropriate MCP tool, and returns a helpful response based on the tool result.

**Why this priority**: Core functionality - the primary value proposition is LLM-driven tool invocation replacing rule-based matching.

**Independent Test**: Send "remind me to buy groceries tomorrow" and verify the LLM invokes `add_task` MCP tool with correct parameters, then responds with confirmation.

**Acceptance Scenarios**:

1. **Given** a user message "add a task to call mom", **When** processed by the agent runtime, **Then** the LLM invokes `add_task` tool with description "call mom" and returns a confirmation response
2. **Given** a user message "show my tasks", **When** processed, **Then** the LLM invokes `list_tasks` tool and formats results in a user-friendly response
3. **Given** a user message "mark grocery shopping as done", **When** processed, **Then** the LLM invokes `complete_task` with the matching task and confirms completion

---

### User Story 2 - LLM Responds Directly Without Tools (Priority: P1)

A user sends a message that doesn't require task operations (greeting, general question, off-topic). The LLM responds directly without invoking any tools.

**Why this priority**: Essential for natural conversation flow; prevents unnecessary tool calls.

**Independent Test**: Send "hello, how are you?" and verify no MCP tools are invoked and LLM provides a friendly response.

**Acceptance Scenarios**:

1. **Given** a user greeting "hi there", **When** processed, **Then** the LLM responds with a friendly greeting without invoking tools
2. **Given** a general question "what can you help me with?", **When** processed, **Then** the LLM explains its capabilities without tool invocation
3. **Given** an off-topic request "tell me a joke", **When** processed, **Then** the LLM responds appropriately or politely declines, without tool invocation

---

### User Story 3 - LLM Requests Clarification (Priority: P2)

A user sends an ambiguous message where the intent is unclear. The LLM asks a clarifying question before proceeding.

**Why this priority**: Improves accuracy by avoiding incorrect tool invocations on ambiguous input.

**Independent Test**: Send "groceries" alone and verify the LLM asks for clarification about what action to take.

**Acceptance Scenarios**:

1. **Given** an ambiguous message "groceries", **When** processed, **Then** the LLM asks "Would you like to add 'groceries' as a new task, or are you looking for an existing task about groceries?"
2. **Given** a message with multiple possible intents "milk and eggs", **When** processed, **Then** the LLM clarifies whether to create a task, update existing, or something else
3. **Given** a reference to non-existent context "that one", **When** processed, **Then** the LLM asks which specific item the user is referring to

---

### User Story 4 - Observability Logging (Priority: P2)

All agent decisions, whether tool invocations, direct responses, or clarification requests, are logged with full context for audit and debugging purposes.

**Why this priority**: Critical for debugging, compliance, and behavioral analysis; builds on Spec 004.

**Independent Test**: Process any user message and verify `DecisionLog` and `ToolInvocationLog` records are created with correct categories.

**Acceptance Scenarios**:

1. **Given** a successful tool invocation, **When** complete, **Then** a `DecisionLog` with `SUCCESS:TASK_COMPLETED` and corresponding `ToolInvocationLog` are persisted
2. **Given** a direct response without tools, **When** complete, **Then** a `DecisionLog` with `SUCCESS:RESPONSE_GIVEN` is persisted
3. **Given** a clarification request, **When** complete, **Then** a `DecisionLog` with `AMBIGUITY:UNCLEAR_INTENT` is persisted

---

### User Story 5 - Safety and Refusal Handling (Priority: P2)

When a user requests something outside the agent's capabilities or against safety policies, the LLM politely refuses and explains limitations.

**Why this priority**: Ensures safe operation and clear user expectations.

**Independent Test**: Send "delete all my data permanently" and verify the agent refuses with appropriate explanation.

**Acceptance Scenarios**:

1. **Given** an out-of-scope request "what's the weather?", **When** processed, **Then** the LLM explains it can only help with task management
2. **Given** a potentially harmful request, **When** processed, **Then** the LLM refuses politely and logs `REFUSAL:OUT_OF_SCOPE`
3. **Given** a request exceeding rate limits, **When** processed, **Then** the agent handles gracefully with `REFUSAL:RATE_LIMITED`

---

### User Story 6 - Multi-Turn Tool Execution (Priority: P3)

For complex requests requiring multiple tool calls, the LLM orchestrates the sequence, feeding results back until the task is complete.

**Why this priority**: Advanced functionality for power users; builds on P1 foundation.

**Independent Test**: Send "show my tasks and then mark the first one complete" and verify sequential tool execution.

**Acceptance Scenarios**:

1. **Given** a request requiring two tools "list tasks then complete the grocery one", **When** processed, **Then** the LLM calls `list_tasks` first, then `complete_task` with the correct ID
2. **Given** tool failure on first attempt, **When** processed, **Then** the LLM gracefully handles the error and informs the user

---

### Edge Cases

- What happens when Gemini API is unavailable or times out?
- How does the system handle malformed LLM output (invalid JSON, missing fields)?
- What happens if LLM enters an infinite tool-calling loop?
- How are very long user messages handled (token limits)?
- What happens if tool execution fails mid-sequence?

---

## Architecture Overview

```
API Request → Chat Route → LLM Agent Runtime (Gemini) → MCP Tool Calls → AgentDecision → Response + Logs
                              │
                              ├── LLM Adapter (Gemini Client)
                              ├── Agent Runtime Engine
                              ├── Tool Adapter (MCP Bridge)
                              └── Constitution (System Prompt)
```

## Components

### LLM Adapter
- **gemini_client**: Handles Gemini API communication (auth, requests, responses)
- **llm_interface**: Abstract interface for LLM operations (allows future provider swaps)

### Agent Runtime Engine
- **engine**: Core orchestration logic - builds context, invokes LLM, processes decisions, manages tool loops

### Tool Adapter
- **tools**: Bridges LLM tool-calling format to MCP tool invocations

### Constitution
- **constitution.md**: System prompt defining agent behavior, tool whitelist, safety boundaries

---

## Execution Flow

1. **Receive Request**: API receives user message with conversation context
2. **Build AgentContext**: Construct `DecisionContext` from user message, conversation history, user ID
3. **Invoke LLM**: Send context + constitution to Gemini with available tool definitions
4. **Process Response**: Parse LLM output for reasoning, tool calls, or direct response
5. **Execute Tools** (if applicable): Invoke MCP tools via adapter, collect results
6. **Loop if Needed**: Feed tool results back to LLM for further processing (max iterations bounded)
7. **Build Decision**: Construct structured `AgentDecision` object
8. **Log & Respond**: Persist logs via Spec 004, return user-facing response

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept user messages and return LLM-generated responses
- **FR-002**: System MUST invoke MCP tools when LLM determines tool usage is needed
- **FR-003**: System MUST support direct responses without tool invocation for non-task messages
- **FR-004**: System MUST request clarification when user intent is ambiguous
- **FR-005**: System MUST refuse requests outside defined capabilities with polite explanation
- **FR-006**: System MUST emit `AgentDecision` objects for every request processed
- **FR-007**: System MUST log all decisions via Spec 004 observability layer
- **FR-008**: System MUST pass all context via `DecisionContext` (stateless operation)
- **FR-009**: System MUST enforce tool whitelist defined in constitution
- **FR-010**: System MUST handle Gemini API errors gracefully with user-friendly fallback responses
- **FR-011**: System MUST limit tool-calling loops to prevent infinite execution (max 5 iterations)
- **FR-012**: System MUST validate LLM output format before processing tool calls

### Key Entities

- **DecisionContext**: User message, conversation ID, user ID, conversation history, available tools
- **AgentDecision**: Decision type (RESPOND_ONLY, INVOKE_TOOL, REQUEST_CLARIFICATION, REFUSE), tool calls, response text, outcome category
- **ToolCall**: Tool name, parameters, invocation sequence
- **ToolResult**: Success/failure, result data, error details, duration

---

## Observability

Fully integrated with Spec 004:

- **DecisionLog**: Records every agent decision with intent, decision type, outcome category, duration
- **ToolInvocationLog**: Records each MCP tool call with parameters, result, success/failure, timing
- **OutcomeCategory**: Uses existing taxonomy (SUCCESS, ERROR, REFUSAL, AMBIGUITY with subcategories)

---

## Safety

- **Constitution Enforcement**: System prompt defines allowed behaviors and tool restrictions
- **Tool Whitelist**: Only approved MCP tools (add_task, list_tasks, update_task, complete_task, delete_task) are available
- **Post-Decision Validation**: Validate LLM decisions against policy before execution
- **Rate Limiting**: Respect existing API rate limits
- **Error Boundaries**: Graceful degradation on LLM failures

---

## Testing Strategy

1. **Unit Tests**: Mock Gemini API responses, test tool call parsing, decision construction
2. **Integration Tests**: End-to-end flows with mock LLM, real MCP tools
3. **Tool Loop Tests**: Verify max iteration limits, correct result feeding
4. **Error Handling Tests**: Malformed LLM output, API timeouts, tool failures
5. **Safety Tests**: Refusal scenarios, out-of-scope requests, rate limiting
6. **Determinism Tests**: Same input produces consistent decision structure

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can manage tasks using natural language with 90% success rate for clear requests
- **SC-002**: System responds to user messages within 3 seconds for typical requests
- **SC-003**: All agent decisions are logged with complete audit trail (100% logging coverage)
- **SC-004**: Ambiguous requests receive clarification prompts rather than incorrect tool invocations
- **SC-005**: Out-of-scope requests are refused politely with helpful explanation
- **SC-006**: Tool-calling loops complete within 5 iterations or terminate gracefully
- **SC-007**: System remains functional with graceful degradation when Gemini API is unavailable

---

## Assumptions

- Gemini API key is available and has sufficient quota for development/testing
- Gemini supports function/tool calling in a format compatible with the design
- Existing MCP tools (Spec 002) are fully operational and accessible
- Existing observability layer (Spec 004) is fully operational
- Python 3.11+ environment with async support
- Standard web latency expectations (sub-3-second responses for typical requests)

---

## Out of Scope

- OpenAI API integration (no API key available)
- Multi-model routing or fallback to other LLM providers
- Fine-tuning or custom model training
- Real-time streaming responses (batch response only for MVP)
- Conversation memory beyond current request context
- User authentication/authorization (handled by existing layers)

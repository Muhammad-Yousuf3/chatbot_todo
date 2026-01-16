# Agent Engine Contract

**Feature**: 005-llm-agent-runtime
**Version**: 1.0.0

## Overview

This contract defines the interface for the LLM-powered Agent Decision Engine, which replaces the rule-based engine from Spec 003 while maintaining the same input/output contract.

---

## LLMAgentEngine Interface

```python
class LLMAgentEngine:
    """LLM-powered agent decision engine.

    Replaces rule-based AgentDecisionEngine with LLM-driven decisions
    while maintaining the same DecisionContext -> AgentDecision contract.
    """

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        tool_executor: ToolExecutor,
        constitution: str,
        max_iterations: int = 5,
    ) -> None:
        """
        Initialize the LLM agent engine.

        Args:
            llm_adapter: LLM provider adapter (Gemini)
            tool_executor: MCP tool execution adapter
            constitution: System prompt defining agent behavior
            max_iterations: Max tool-calling loop iterations
        """
        ...

    async def process_message(
        self,
        context: DecisionContext,
    ) -> AgentDecision:
        """
        Process a user message and return an agent decision.

        This is the main entry point, matching the existing engine contract.

        Args:
            context: Complete decision context with message and history

        Returns:
            AgentDecision with response or tool calls

        The method:
        1. Builds LLM request from context
        2. Invokes LLM with constitution + tools
        3. Executes any tool calls
        4. Loops if needed (max iterations)
        5. Returns structured AgentDecision
        """
        ...
```

---

## Execution Flow Contract

### Input: DecisionContext (unchanged from Spec 003)

```python
class DecisionContext(BaseModel):
    user_id: str
    message: str
    conversation_id: str
    message_history: list[Message]
    pending_confirmation: PendingAction | None
```

### Output: AgentDecision (unchanged from Spec 003)

```python
class AgentDecision(BaseModel):
    decision_type: DecisionType
    tool_calls: list[ToolCall] | None
    response_text: str | None
    clarification_question: str | None
    pending_action: PendingAction | None
```

---

## Tool Executor Interface

```python
class ToolExecutor(Protocol):
    """Interface for executing MCP tools."""

    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: str,
    ) -> ToolResult:
        """
        Execute an MCP tool.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters (excluding user_id)
            user_id: Authenticated user ID

        Returns:
            ToolResult from MCP tool execution
        """
        ...

    def get_available_tools(self) -> list[str]:
        """Return list of available tool names."""
        ...
```

---

## Constitution Contract

The constitution (system prompt) defines agent behavior and must include:

```markdown
# Constitution Template

You are a helpful task management assistant. Your capabilities:

## Available Tools
- add_task: Create new tasks
- list_tasks: View user's tasks
- update_task: Modify task descriptions
- complete_task: Mark tasks as done
- delete_task: Remove tasks (requires confirmation)

## Behavioral Rules
1. Only use tools when the user clearly wants a task operation
2. For greetings/general questions, respond conversationally WITHOUT tools
3. If the user's intent is unclear, ask a clarifying question
4. For delete requests, always confirm before proceeding
5. Stay focused on task management - politely decline off-topic requests

## Response Guidelines
- Be concise and helpful
- Confirm successful operations
- Explain errors in user-friendly terms
- Never expose internal details or tool names to users
```

---

## Decision Mapping

The LLM response maps to AgentDecision types:

| LLM Response | AgentDecision Type |
|--------------|-------------------|
| Text only, no tools | RESPOND_ONLY |
| Tool calls requested | INVOKE_TOOL |
| Asks user a question | ASK_CLARIFICATION |
| Delete tool requested | REQUEST_CONFIRMATION |
| Declines request | RESPOND_ONLY (with refusal text) |

---

## Error Handling Contract

### LLM Errors → AgentDecision

```python
# On LLM failure
AgentDecision(
    decision_type=DecisionType.RESPOND_ONLY,
    response_text="I'm having trouble processing your request. Please try again.",
)

# On rate limit
AgentDecision(
    decision_type=DecisionType.RESPOND_ONLY,
    response_text="I'm receiving too many requests. Please wait a moment.",
)

# On max iterations exceeded
AgentDecision(
    decision_type=DecisionType.RESPOND_ONLY,
    response_text="That request is too complex. Could you break it into smaller steps?",
)
```

---

## Observability Integration

The engine MUST emit logs for all operations:

```python
# Before LLM call
await logging_service.write_decision_log(
    decision_id=decision_id,
    conversation_id=context.conversation_id,
    user_id=context.user_id,
    message=context.message,
    intent_type="LLM_PROCESSING",  # Placeholder until LLM responds
    decision_type="PENDING",
    outcome_category="PENDING",
    duration_ms=0,
)

# After tool execution
await logging_service.write_tool_invocation_log(
    decision_id=decision_id,
    tool_name=tool_name,
    parameters=parameters,
    result=tool_result.data,
    success=tool_result.success,
    error_code=tool_result.error_code,
    error_message=tool_result.error,
    duration_ms=duration,
)

# After final decision
# Update decision log with actual outcome
```

---

## Configuration

```python
@dataclass
class AgentEngineConfig:
    max_iterations: int = 5
    include_history_messages: int = 10  # Last N messages
    temperature: float = 0.0
    timeout_seconds: int = 30
```

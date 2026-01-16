# Quickstart: LLM-Driven Agent Runtime

**Feature**: 005-llm-agent-runtime
**Date**: 2026-01-04

## Prerequisites

1. Python 3.11+
2. Gemini API key (set as environment variable)
3. Existing backend running (Specs 001-004 implemented)

## Setup

### 1. Install Dependencies

```bash
cd backend
uv add google-genai
```

### 2. Set Environment Variable

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or add to `.env`:
```
GEMINI_API_KEY=your-api-key-here
```

### 3. Verify Installation

```python
# Quick test
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello!"
)
print(response.text)
```

---

## Basic Usage

### Initialize the Engine

```python
from src.llm_runtime import LLMAgentEngine, GeminiAdapter, ToolExecutor

# Create components
adapter = GeminiAdapter(api_key=os.environ["GEMINI_API_KEY"])
executor = ToolExecutor()
constitution = open("src/llm_runtime/constitution.md").read()

# Initialize engine
engine = LLMAgentEngine(
    llm_adapter=adapter,
    tool_executor=executor,
    constitution=constitution,
)
```

### Process a Message

```python
from src.agent.schemas import DecisionContext, Message

# Build context
context = DecisionContext(
    user_id="user-123",
    message="Add a task to buy groceries",
    conversation_id="conv-456",
    message_history=[],
)

# Process
decision = await engine.process_message(context)

print(f"Decision: {decision.decision_type}")
print(f"Response: {decision.response_text}")
if decision.tool_calls:
    print(f"Tools: {[tc.tool_name for tc in decision.tool_calls]}")
```

---

## Common Scenarios

### Scenario 1: Create Task

```python
context = DecisionContext(
    user_id="user-123",
    message="Remind me to call mom tomorrow",
    conversation_id="conv-1",
    message_history=[],
)

decision = await engine.process_message(context)
# decision.decision_type == DecisionType.INVOKE_TOOL
# decision.tool_calls[0].tool_name == ToolName.ADD_TASK
# decision.response_text == "I've added 'call mom tomorrow' to your tasks."
```

### Scenario 2: Direct Response (No Tools)

```python
context = DecisionContext(
    user_id="user-123",
    message="Hello!",
    conversation_id="conv-1",
    message_history=[],
)

decision = await engine.process_message(context)
# decision.decision_type == DecisionType.RESPOND_ONLY
# decision.tool_calls == None
# decision.response_text == "Hello! How can I help you with your tasks today?"
```

### Scenario 3: Clarification

```python
context = DecisionContext(
    user_id="user-123",
    message="groceries",
    conversation_id="conv-1",
    message_history=[],
)

decision = await engine.process_message(context)
# decision.decision_type == DecisionType.ASK_CLARIFICATION
# decision.clarification_question includes "add" or "list"
```

### Scenario 4: Delete with Confirmation

```python
context = DecisionContext(
    user_id="user-123",
    message="Delete my grocery task",
    conversation_id="conv-1",
    message_history=[],
)

decision = await engine.process_message(context)
# decision.decision_type == DecisionType.REQUEST_CONFIRMATION
# decision.pending_action.task_description == "grocery task"
```

---

## Testing

### Run Unit Tests

```bash
cd backend
uv run pytest tests/llm_runtime/ -v
```

### Run with Mock LLM

```python
from tests.llm_runtime.mocks import MockLLMAdapter

# Use mock for deterministic testing
mock_adapter = MockLLMAdapter(responses={
    "add task": LLMResponse(
        content=None,
        function_calls=[FunctionCall(name="add_task", arguments={"description": "test"})],
        finish_reason="tool_calls",
    ),
})

engine = LLMAgentEngine(llm_adapter=mock_adapter, ...)
```

---

## Troubleshooting

### API Key Not Found

```
Error: GEMINI_API_KEY environment variable not set
```

**Solution**: Set the environment variable or check `.env` file.

### Rate Limiting

```
Error: RateLimitError - 429 Too Many Requests
```

**Solution**: Wait and retry. The engine handles this with exponential backoff.

### Tool Not Found

```
Error: ToolNotFoundError - Unknown tool: invalid_tool
```

**Solution**: Check tool whitelist in constitution. Only allowed tools: add_task, list_tasks, update_task, complete_task, delete_task.

### Timeout

```
Error: TimeoutError - Request timed out after 30s
```

**Solution**: Check network connectivity. Increase timeout in config if needed.

---

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_API_KEY` | Required | Google AI API key |
| `GEMINI_MODEL` | gemini-2.0-flash | Model identifier |
| `LLM_TEMPERATURE` | 0.0 | Sampling temperature |
| `LLM_MAX_TOKENS` | 1024 | Max response tokens |
| `LLM_TIMEOUT` | 30 | Request timeout (seconds) |
| `MAX_TOOL_ITERATIONS` | 5 | Max tool-call loop cycles |

# LLM Adapter Interface Contract

**Feature**: 005-llm-agent-runtime
**Version**: 1.0.0

## Overview

This contract defines the interface between the Agent Runtime Engine and LLM providers. The initial implementation uses Google Gemini, but the interface supports future provider swaps.

---

## LLMAdapter Protocol

```python
from typing import Protocol

class LLMAdapter(Protocol):
    """Abstract interface for LLM providers."""

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: Conversation history in LLMMessage format
            tools: Available tool declarations
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum response tokens

        Returns:
            LLMResponse with content and/or function calls

        Raises:
            LLMError: On API failures
            RateLimitError: When rate limited
            TimeoutError: On request timeout
        """
        ...

    def get_tool_declarations(self, tools: list[str]) -> list[ToolDeclaration]:
        """
        Get tool declarations for the specified tool names.

        Args:
            tools: List of tool names to include

        Returns:
            ToolDeclaration objects in provider-specific format
        """
        ...
```

---

## GeminiAdapter Implementation

```python
class GeminiAdapter:
    """Gemini-specific implementation of LLMAdapter."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google AI API key
            model: Model identifier
        """
        ...

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        Send request to Gemini and parse response.

        Converts internal message format to Gemini format,
        handles function calling, and normalizes response.
        """
        ...
```

---

## Request/Response Contracts

### LLMMessage

```python
@dataclass
class LLMMessage:
    role: Literal["user", "assistant", "function"]
    content: str | None = None
    function_call: FunctionCall | None = None
    function_response: FunctionResponse | None = None
```

### LLMResponse

```python
@dataclass
class LLMResponse:
    content: str | None
    function_calls: list[FunctionCall] | None
    finish_reason: Literal["stop", "tool_calls", "max_tokens", "error"]
    usage: TokenUsage | None = None
    error: str | None = None
```

### FunctionCall

```python
@dataclass
class FunctionCall:
    name: str  # Tool name
    arguments: dict[str, Any]  # Parsed arguments
```

### ToolDeclaration

```python
@dataclass
class ToolDeclaration:
    name: str
    description: str
    parameters: dict  # JSON Schema
```

---

## Error Handling Contract

### Error Types

| Error Class | When Raised | Recommended Handling |
|-------------|-------------|---------------------|
| `LLMError` | Generic API failure | Log, return fallback response |
| `RateLimitError` | Rate limit exceeded | Return REFUSAL:RATE_LIMITED |
| `TimeoutError` | Request timeout | Retry once, then fallback |
| `InvalidResponseError` | Malformed LLM output | Log, return error response |
| `ToolNotFoundError` | Unknown tool requested | Ignore tool call, continue |

### Error Response Format

```python
@dataclass
class LLMError(Exception):
    message: str
    code: str
    retry_after: int | None = None  # For rate limits
```

---

## Tool Declaration Schema

Each MCP tool must be declared in this format:

```json
{
  "name": "add_task",
  "description": "Create a new task for the user. Use this when the user wants to add, create, or remember something as a task.",
  "parameters": {
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "The task description (1-1000 characters)"
      }
    },
    "required": ["description"]
  }
}
```

### Full Tool Registry

```python
TOOL_DECLARATIONS = [
    {
        "name": "add_task",
        "description": "Create a new task. Use when user wants to add, create, or remember something.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Task description"}
            },
            "required": ["description"]
        }
    },
    {
        "name": "list_tasks",
        "description": "Get user's tasks. Use when user wants to see, view, or list their tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "completed", "all"],
                    "description": "Filter by status (default: all)"
                }
            }
        }
    },
    {
        "name": "update_task",
        "description": "Update a task's description. Use when user wants to change, edit, or rename a task.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to update"},
                "description": {"type": "string", "description": "New description"}
            },
            "required": ["task_id", "description"]
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as completed. Use when user says done, finished, or completed.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to complete"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "delete_task",
        "description": "Delete a task permanently. Use when user wants to remove or delete a task.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to delete"}
            },
            "required": ["task_id"]
        }
    }
]
```

---

## Configuration Contract

```python
@dataclass
class LLMConfig:
    api_key: str  # Required, from environment
    model: str = "gemini-2.0-flash"
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_seconds: int = 30
    max_retries: int = 1
```

**Environment Variables**:
- `GEMINI_API_KEY`: Required API key
- `GEMINI_MODEL`: Optional model override

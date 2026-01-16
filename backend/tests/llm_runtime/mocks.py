"""Mock implementations for testing the LLM runtime.

These mocks provide deterministic responses for testing without
requiring actual API calls to Gemini.
"""

from typing import Any, Callable

from src.llm_runtime.schemas import (
    FunctionCall,
    LLMMessage,
    LLMResponse,
    TokenUsage,
    ToolDeclaration,
)


class MockLLMAdapter:
    """Mock LLM adapter for deterministic testing.

    Allows configuring responses based on message content patterns.

    Usage:
        adapter = MockLLMAdapter()
        adapter.add_response("add task", LLMResponse(
            content=None,
            function_calls=[FunctionCall(name="add_task", arguments={"description": "test"})],
            finish_reason="tool_calls",
        ))
    """

    def __init__(self) -> None:
        """Initialize with empty response mapping."""
        self._responses: dict[str, LLMResponse] = {}
        self._default_response: LLMResponse | None = None
        self._call_history: list[tuple[list[LLMMessage], list[ToolDeclaration]]] = []
        self._response_generator: Callable[
            [list[LLMMessage], list[ToolDeclaration]], LLMResponse
        ] | None = None

    def add_response(self, pattern: str, response: LLMResponse) -> None:
        """Add a response for messages containing the pattern.

        Args:
            pattern: Substring to match in user message content.
            response: LLMResponse to return when pattern matches.
        """
        self._responses[pattern.lower()] = response

    def set_default_response(self, response: LLMResponse) -> None:
        """Set a default response when no pattern matches.

        Args:
            response: Default LLMResponse to return.
        """
        self._default_response = response

    def set_response_generator(
        self,
        generator: Callable[[list[LLMMessage], list[ToolDeclaration]], LLMResponse],
    ) -> None:
        """Set a custom function to generate responses.

        Args:
            generator: Function that takes messages and tools, returns LLMResponse.
        """
        self._response_generator = generator

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDeclaration],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a mock response based on configured patterns.

        Args:
            messages: Conversation history.
            tools: Available tool declarations.
            temperature: Ignored in mock.
            max_tokens: Ignored in mock.

        Returns:
            Configured LLMResponse or default response.
        """
        # Record the call for verification
        self._call_history.append((messages, tools))

        # Use custom generator if set
        if self._response_generator:
            return self._response_generator(messages, tools)

        # Find the last user message
        user_content = ""
        for msg in reversed(messages):
            if msg.role == "user" and msg.content:
                user_content = msg.content.lower()
                break

        # Match against configured patterns
        for pattern, response in self._responses.items():
            if pattern in user_content:
                return response

        # Return default response or a generic one
        if self._default_response:
            return self._default_response

        return LLMResponse(
            content="I'm a mock assistant. How can I help you?",
            function_calls=None,
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        )

    def get_call_history(self) -> list[tuple[list[LLMMessage], list[ToolDeclaration]]]:
        """Get the history of calls made to generate().

        Returns:
            List of (messages, tools) tuples from each call.
        """
        return self._call_history

    def reset(self) -> None:
        """Reset the mock to initial state."""
        self._responses.clear()
        self._default_response = None
        self._call_history.clear()
        self._response_generator = None


class MockToolExecutor:
    """Mock tool executor for testing.

    Returns configurable results for tool executions.
    """

    def __init__(self) -> None:
        """Initialize with empty result mapping."""
        self._results: dict[str, dict[str, Any]] = {}
        self._call_history: list[tuple[str, dict[str, Any], str]] = []
        self._should_fail: set[str] = set()

    def set_result(self, tool_name: str, result: dict[str, Any]) -> None:
        """Set the result for a specific tool.

        Args:
            tool_name: Name of the tool.
            result: Result data to return.
        """
        self._results[tool_name] = result

    def set_should_fail(self, tool_name: str) -> None:
        """Mark a tool to fail when executed.

        Args:
            tool_name: Name of the tool that should fail.
        """
        self._should_fail.add(tool_name)

    async def execute(
        self, tool_name: str, parameters: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Execute a mock tool.

        Args:
            tool_name: Name of the tool to execute.
            parameters: Tool parameters.
            user_id: User ID for the execution.

        Returns:
            Configured result or default.

        Raises:
            Exception: If tool is marked to fail.
        """
        self._call_history.append((tool_name, parameters, user_id))

        if tool_name in self._should_fail:
            raise Exception(f"Mock failure for {tool_name}")

        if tool_name in self._results:
            return self._results[tool_name]

        # Default results by tool type
        default_results = {
            "add_task": {
                "success": True,
                "task": {"id": "mock-task-123", "description": parameters.get("description", "")},
            },
            "list_tasks": {
                "success": True,
                "tasks": [
                    {"id": "task-1", "description": "Task 1", "completed": False},
                    {"id": "task-2", "description": "Task 2", "completed": True},
                ],
            },
            "complete_task": {
                "success": True,
                "task": {"id": parameters.get("task_id", ""), "completed": True},
            },
            "update_task": {
                "success": True,
                "task": {
                    "id": parameters.get("task_id", ""),
                    "description": parameters.get("description", ""),
                },
            },
            "delete_task": {
                "success": True,
                "deleted": True,
            },
        }

        return default_results.get(tool_name, {"success": True})

    def get_available_tools(self) -> list[str]:
        """Return list of available tool names."""
        return ["add_task", "list_tasks", "update_task", "complete_task", "delete_task"]

    def get_tool_declarations(self) -> list[ToolDeclaration]:
        """Return tool declarations for all available tools.

        Returns:
            List of ToolDeclaration objects for LLM function calling.
        """
        return [
            ToolDeclaration(
                name="add_task",
                description="Create a new task.",
                parameters={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Task description"}
                    },
                    "required": ["description"],
                },
            ),
            ToolDeclaration(
                name="list_tasks",
                description="Get user's tasks.",
                parameters={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "completed", "all"],
                        }
                    },
                },
            ),
            ToolDeclaration(
                name="update_task",
                description="Update a task's description.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["task_id", "description"],
                },
            ),
            ToolDeclaration(
                name="complete_task",
                description="Mark a task as completed.",
                parameters={
                    "type": "object",
                    "properties": {"task_id": {"type": "string"}},
                    "required": ["task_id"],
                },
            ),
            ToolDeclaration(
                name="delete_task",
                description="Delete a task permanently.",
                parameters={
                    "type": "object",
                    "properties": {"task_id": {"type": "string"}},
                    "required": ["task_id"],
                },
            ),
        ]

    def get_call_history(self) -> list[tuple[str, dict[str, Any], str]]:
        """Get the history of calls made to execute().

        Returns:
            List of (tool_name, parameters, user_id) tuples.
        """
        return self._call_history

    def reset(self) -> None:
        """Reset the mock to initial state."""
        self._results.clear()
        self._call_history.clear()
        self._should_fail.clear()

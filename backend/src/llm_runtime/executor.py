"""Tool executor for bridging LLM tool calls to MCP tools.

This module provides the ToolExecutor class that:
1. Maps LLM tool call requests to actual MCP tool functions
2. Handles user_id injection and parameter validation
3. Returns structured results back to the LLM
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from src.llm_runtime.errors import ToolNotFoundError
from src.llm_runtime.schemas import ToolDeclaration

logger = logging.getLogger(__name__)


# Allowed tools - only these can be called by the LLM
ALLOWED_TOOLS = {"add_task", "list_tasks", "update_task", "complete_task", "delete_task"}


@dataclass
class ToolResult:
    """Result of a tool execution.

    Attributes:
        success: Whether the tool execution succeeded.
        data: Result data from the tool.
        error: Error message if failed.
        error_code: Machine-readable error code.
        duration_ms: Execution time in milliseconds.
    """

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    duration_ms: int = 0


class ToolExecutor:
    """Executes MCP tools on behalf of the LLM agent.

    This class bridges the gap between the LLM's function calls and the
    actual MCP tool implementations. It handles:
    - Tool whitelist validation
    - User ID injection
    - Error handling and result formatting

    Usage:
        executor = ToolExecutor(db_session_factory)
        result = await executor.execute("add_task", {"description": "test"}, "user-123")
    """

    def __init__(
        self,
        context_factory: Callable[[], Any] | None = None,
    ) -> None:
        """Initialize the tool executor.

        Args:
            context_factory: Optional factory function to create MCP Context objects.
                           If not provided, tools will be called without context.
        """
        self._context_factory = context_factory
        self._tool_registry: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}
        self._load_tools()

    def _load_tools(self) -> None:
        """Load MCP tools into the registry.

        Tools are imported from src.mcp_server.tools and registered
        by name for later execution.
        """
        try:
            from src.mcp_server.tools import (
                add_task,
                complete_task,
                delete_task,
                list_tasks,
                update_task,
            )

            self._tool_registry = {
                "add_task": add_task,
                "list_tasks": list_tasks,
                "update_task": update_task,
                "complete_task": complete_task,
                "delete_task": delete_task,
            }
            logger.debug(f"Loaded {len(self._tool_registry)} tools into registry")

        except ImportError as e:
            logger.warning(f"Could not load MCP tools: {e}")
            # Tools will need to be registered manually or through set_tool

    def set_tool(
        self, name: str, func: Callable[..., Coroutine[Any, Any, Any]]
    ) -> None:
        """Register a tool function.

        Useful for testing or custom tool implementations.

        Args:
            name: Tool name.
            func: Async function to execute.
        """
        if name not in ALLOWED_TOOLS:
            raise ValueError(f"Tool '{name}' is not in the allowed tools list")
        self._tool_registry[name] = func

    def set_context_factory(self, factory: Callable[[], Any]) -> None:
        """Set the context factory for MCP tools.

        Args:
            factory: Function that creates MCP Context objects.
        """
        self._context_factory = factory

    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user_id: str,
    ) -> ToolResult:
        """Execute an MCP tool.

        Args:
            tool_name: Name of the tool to execute.
            parameters: Tool parameters (excluding user_id).
            user_id: Authenticated user ID (injected into parameters).

        Returns:
            ToolResult with success/failure, data, and timing.

        Raises:
            ToolNotFoundError: If tool is not in whitelist or registry.
        """
        start_time = time.time()

        # Validate tool name against whitelist
        if tool_name not in ALLOWED_TOOLS:
            logger.warning(f"Attempted to call non-whitelisted tool: {tool_name}")
            raise ToolNotFoundError(tool_name)

        # Check if tool is registered
        if tool_name not in self._tool_registry:
            logger.error(f"Tool '{tool_name}' is allowed but not registered")
            raise ToolNotFoundError(tool_name)

        tool_func = self._tool_registry[tool_name]

        try:
            # Prepare parameters with user_id injection
            call_params = {**parameters, "user_id": user_id}

            # Add context if factory is available
            if self._context_factory:
                call_params["ctx"] = self._context_factory()

            # Execute the tool
            logger.debug(f"Executing tool '{tool_name}' with params: {parameters}")
            result = await tool_func(**call_params)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Handle ToolResult from MCP tools
            if hasattr(result, "success"):
                return ToolResult(
                    success=result.success,
                    data=self._serialize_result_data(result.data) if result.data else None,
                    error=result.error if hasattr(result, "error") else None,
                    error_code=result.error_code if hasattr(result, "error_code") else None,
                    duration_ms=duration_ms,
                )

            # Handle dict results
            if isinstance(result, dict):
                return ToolResult(
                    success=result.get("success", True),
                    data=result,
                    error=result.get("error"),
                    error_code=result.get("error_code"),
                    duration_ms=duration_ms,
                )

            # Handle other results
            return ToolResult(
                success=True,
                data={"result": result},
                duration_ms=duration_ms,
            )

        except ToolNotFoundError:
            raise

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR",
                duration_ms=duration_ms,
            )

    def _serialize_result_data(self, data: Any) -> dict[str, Any]:
        """Serialize result data to a dict format.

        Args:
            data: Result data from MCP tool.

        Returns:
            Serialized dict representation.
        """
        if data is None:
            return {}

        if isinstance(data, dict):
            return data

        if isinstance(data, list):
            return {"items": [self._serialize_result_data(item) for item in data]}

        if hasattr(data, "model_dump"):
            # Pydantic model
            return data.model_dump(mode="json")

        if hasattr(data, "__dict__"):
            return {k: str(v) for k, v in data.__dict__.items()}

        return {"value": str(data)}

    def get_available_tools(self) -> list[str]:
        """Return list of available tool names.

        Returns:
            List of registered tool names that are in the whitelist.
        """
        return [name for name in self._tool_registry if name in ALLOWED_TOOLS]

    def get_tool_declarations(self) -> list[ToolDeclaration]:
        """Get tool declarations for all available tools.

        Returns:
            List of ToolDeclaration objects for LLM function calling.
        """
        declarations = {
            "add_task": ToolDeclaration(
                name="add_task",
                description="Create a new task. Use when user wants to add, create, or remember something. Extract any mentioned due date.",
                parameters={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Task description"},
                        "due_date": {
                            "type": "string",
                            "description": "Due date in ISO format (YYYY-MM-DD). Extract from user's message if mentioned (e.g., '15 January' becomes '2026-01-15', 'tomorrow' becomes tomorrow's date).",
                        },
                    },
                    "required": ["description"],
                },
            ),
            "list_tasks": ToolDeclaration(
                name="list_tasks",
                description="Get user's tasks. Use when user wants to see, view, or list their tasks.",
                parameters={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "completed", "all"],
                            "description": "Filter by status (default: all)",
                        }
                    },
                },
            ),
            "update_task": ToolDeclaration(
                name="update_task",
                description="Update a task's description. Use when user wants to change, edit, or rename a task.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to update"},
                        "description": {"type": "string", "description": "New description"},
                    },
                    "required": ["task_id", "description"],
                },
            ),
            "complete_task": ToolDeclaration(
                name="complete_task",
                description="Mark a task as completed. Use when user says done, finished, or completed.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to complete"}
                    },
                    "required": ["task_id"],
                },
            ),
            "delete_task": ToolDeclaration(
                name="delete_task",
                description="Delete a task permanently. Use when user wants to remove or delete a task.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID to delete"}
                    },
                    "required": ["task_id"],
                },
            ),
        }

        return [declarations[name] for name in self.get_available_tools() if name in declarations]

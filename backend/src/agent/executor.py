"""Tool executor for the Agent Decision Engine.

This module bridges the agent's tool calls with the MCP tools.
It executes tool calls and returns results.

Supports numbered task selection: when list_tasks is called with
_operation context, resolves task references and executes follow-up operations.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent.resolver import resolve_task_reference, find_matching_tasks
from src.agent.schemas import ToolCall, ToolInvocationRecord, ToolName
from src.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes MCP tool calls for the agent.

    This executor directly calls the database operations that the MCP
    tools would perform, allowing the agent to be used within the
    FastAPI context without going through the MCP protocol.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the executor with a database session.

        Args:
            session: SQLModel async session for database operations.
        """
        self.session = session

    async def execute(
        self, tool_call: ToolCall, user_id: str
    ) -> tuple[dict[str, Any], bool, str | None]:
        """Execute a tool call and return the result.

        Args:
            tool_call: The tool call to execute.
            user_id: The authenticated user ID.

        Returns:
            Tuple of (result_dict, success, error_message).
        """
        start_time = datetime.now()

        try:
            result = await self._dispatch_tool(tool_call)
            success = True
            error_message = None
        except Exception as e:
            logger.exception(f"Tool execution failed: {tool_call.tool_name}")
            result = {}
            success = False
            error_message = str(e)

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Log the invocation
        logger.info(
            f"Tool {tool_call.tool_name.value} executed: "
            f"success={success}, duration={duration_ms}ms"
        )

        return result, success, error_message

    async def _dispatch_tool(self, tool_call: ToolCall) -> dict[str, Any]:
        """Dispatch to the appropriate tool handler."""
        handlers = {
            ToolName.ADD_TASK: self._execute_add_task,
            ToolName.LIST_TASKS: self._execute_list_tasks,
            ToolName.UPDATE_TASK: self._execute_update_task,
            ToolName.COMPLETE_TASK: self._execute_complete_task,
            ToolName.DELETE_TASK: self._execute_delete_task,
        }

        handler = handlers.get(tool_call.tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_call.tool_name}")

        return await handler(tool_call.parameters)

    async def _execute_add_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute add_task tool."""
        user_id = params["user_id"]
        description = params["description"]

        task = Task(
            id=uuid4(),
            user_id=user_id,
            description=description.strip(),
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            completed_at=None,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        return {
            "id": str(task.id),
            "description": task.description,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
        }

    async def _execute_list_tasks(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute list_tasks tool with optional follow-up operation.

        When _operation is present, resolves the task reference and executes
        the follow-up operation (complete, update, delete).
        """
        from sqlmodel import select

        user_id = params["user_id"]
        operation = params.get("_operation")
        task_reference = params.get("_task_reference")
        new_description = params.get("_new_description")

        # Get all tasks
        stmt = select(Task).where(Task.user_id == user_id).order_by(Task.created_at)
        result = await self.session.exec(stmt)
        tasks = result.all()

        # Build task list for resolution (uses display order)
        task_list = [
            {
                "id": str(task.id),
                "description": task.description,
                "completed": task.status == TaskStatus.COMPLETED,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ]

        # If no operation context, just return the task list
        if not operation or not task_reference:
            return {"tasks": task_list}

        # Resolve task reference using ALL tasks (not just pending)
        # This allows "complete task 1" to work with the numbered list shown to user
        resolved_task = resolve_task_reference(task_reference, task_list)

        if not resolved_task:
            # Check if multiple matches
            matches = find_matching_tasks(task_reference, task_list, include_completed=True)
            if matches:
                return {
                    "tasks": task_list,
                    "_resolution": "multiple_matches",
                    "_matches": matches,
                    "_reference": task_reference,
                }
            else:
                return {
                    "tasks": task_list,
                    "_resolution": "no_match",
                    "_reference": task_reference,
                }

        task_id = resolved_task["id"]
        task_desc = resolved_task["description"]

        # Execute follow-up operation
        if operation == "complete":
            op_result = await self._execute_complete_task({
                "user_id": user_id,
                "task_id": task_id,
            })
            return {
                "tasks": task_list,
                "_resolution": "success",
                "_operation": "complete",
                "_task": op_result,
            }

        elif operation == "update" and new_description:
            op_result = await self._execute_update_task({
                "user_id": user_id,
                "task_id": task_id,
                "description": new_description,
            })
            return {
                "tasks": task_list,
                "_resolution": "success",
                "_operation": "update",
                "_task": op_result,
            }

        elif operation == "delete":
            # Delete requires confirmation - return task info for confirmation prompt
            return {
                "tasks": task_list,
                "_resolution": "confirm_delete",
                "_operation": "delete",
                "_task_id": task_id,
                "_task_description": task_desc,
            }

        # Fallback - just return task list
        return {"tasks": task_list}

    async def _execute_update_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute update_task tool."""
        from sqlmodel import select

        user_id = params["user_id"]
        task_id = params["task_id"]
        description = params["description"]

        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.exec(stmt)
        task = result.first()

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        old_description = task.description
        task.description = description.strip()
        await self.session.commit()
        await self.session.refresh(task)

        return {
            "id": str(task.id),
            "old_description": old_description,
            "new_description": task.description,
            "status": task.status.value,
        }

    async def _execute_complete_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute complete_task tool."""
        from sqlmodel import select

        user_id = params["user_id"]
        task_id = params["task_id"]

        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.exec(stmt)
        task = result.first()

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(task)

        return {
            "id": str(task.id),
            "description": task.description,
            "status": task.status.value,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def _execute_delete_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute delete_task tool."""
        from sqlmodel import select

        user_id = params["user_id"]
        task_id = params["task_id"]

        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.exec(stmt)
        task = result.first()

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        description = task.description
        await self.session.delete(task)
        await self.session.commit()

        return {
            "id": str(task_id),
            "description": description,
            "deleted": True,
        }

"""MCP tools for task management.

Each tool provides a specific task operation:
- add_task: Create new tasks
- list_tasks: Retrieve user's tasks
- update_task: Modify task descriptions
- complete_task: Mark tasks as completed
- delete_task: Remove tasks permanently
"""

from src.mcp_server.tools.add_task import add_task
from src.mcp_server.tools.list_tasks import list_tasks
from src.mcp_server.tools.update_task import update_task
from src.mcp_server.tools.complete_task import complete_task
from src.mcp_server.tools.delete_task import delete_task

__all__ = ["add_task", "list_tasks", "update_task", "complete_task", "delete_task"]

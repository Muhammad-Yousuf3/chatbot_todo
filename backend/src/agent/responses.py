"""Response templates for the Agent Decision Engine.

This module provides user-friendly response messages for all agent actions.
Templates follow the contract defined in agent-interface.md.
"""


# =============================================================================
# Success Response Templates
# =============================================================================
class SuccessResponses:
    """Templates for successful operations."""

    @staticmethod
    def task_created(description: str) -> str:
        """Response for successful task creation."""
        return f"I've added '{description}' to your tasks."

    @staticmethod
    def tasks_listed(tasks: list[dict]) -> str:
        """Response for listing tasks with numbered selection hint."""
        if not tasks:
            return "You don't have any tasks yet."

        lines = ["Here are your tasks:"]
        for i, task in enumerate(tasks, 1):
            status = "[x]" if task.get("completed", False) else "[ ]"
            desc = task.get("description", "")
            state = "completed" if task.get("completed", False) else "pending"
            lines.append(f"{i}. {status} {desc} ({state})")

        lines.append("")
        lines.append("Tip: Use 'complete task 1' or 'delete task 2' to manage tasks by number.")
        return "\n".join(lines)

    @staticmethod
    def task_completed(description: str) -> str:
        """Response for successful task completion."""
        return f"Done! '{description}' has been marked as completed."

    @staticmethod
    def task_updated(old_description: str, new_description: str) -> str:
        """Response for successful task update."""
        return f"Updated '{old_description}' to '{new_description}'."

    @staticmethod
    def task_deleted(description: str) -> str:
        """Response for successful task deletion."""
        return f"'{description}' has been deleted."


# =============================================================================
# Clarification Question Templates
# =============================================================================
class ClarificationResponses:
    """Templates for clarification questions."""

    @staticmethod
    def ambiguous_intent(possible_intents: list[str]) -> str:
        """Response when intent is ambiguous."""
        # Map intent types to user-friendly actions
        intent_to_action = {
            "CREATE_TASK": "add it as a new task",
            "COMPLETE_TASK": "mark an existing task as complete",
            "UPDATE_TASK": "update an existing task",
            "DELETE_TASK": "delete an existing task",
            "LIST_TASKS": "see your tasks",
        }

        options = [intent_to_action.get(i, i.lower().replace("_", " ")) for i in possible_intents]

        if len(options) == 2:
            return f"I'm not sure what you'd like to do. Would you like to {options[0]}, {options[1]}, or something else?"
        elif len(options) > 2:
            formatted = ", ".join(options[:-1]) + f", or {options[-1]}"
            return f"I'm not sure what you'd like to do. Would you like to {formatted}?"
        else:
            return "I'm not sure what you'd like to do. Could you please clarify?"

    @staticmethod
    def multiple_task_matches(reference: str, tasks: list[dict]) -> str:
        """Response when multiple tasks match the reference."""
        lines = [f"I found multiple tasks that match '{reference}':"]
        for i, task in enumerate(tasks, 1):
            desc = task.get("description", "")
            lines.append(f"{i}. {desc}")
        lines.append("Which one did you mean?")
        return "\n".join(lines)

    @staticmethod
    def no_task_match(reference: str, tasks: list[dict]) -> str:
        """Response when no task matches the reference."""
        if not tasks:
            return f"I couldn't find a task matching '{reference}'. You don't have any tasks yet."

        lines = [f"I couldn't find a task matching '{reference}'. Here are your current tasks:"]
        for i, task in enumerate(tasks, 1):
            status = "[x]" if task.get("completed", False) else "[ ]"
            desc = task.get("description", "")
            lines.append(f"{i}. {status} {desc}")
        return "\n".join(lines)

    @staticmethod
    def missing_description() -> str:
        """Response when task description is missing."""
        return "What would you like the task to say?"

    @staticmethod
    def which_task() -> str:
        """Response when task reference is unclear."""
        return "Which task did you mean?"

    @staticmethod
    def multi_intent(intents: list[str]) -> str:
        """Response when multiple intents are detected (T087).

        Asks user to provide one request at a time for clarity.
        """
        intent_to_action = {
            "CREATE": "adding a task",
            "LIST": "seeing your tasks",
            "COMPLETE": "completing a task",
            "DELETE": "deleting a task",
        }

        actions = [intent_to_action.get(i, i.lower()) for i in intents]

        if len(actions) >= 2:
            return (
                f"It looks like you want to do multiple things ({' and '.join(actions)}). "
                "I can handle one request at a time. Which would you like to do first?"
            )
        return "I can only handle one request at a time. What would you like to do first?"


# =============================================================================
# Confirmation Prompt Templates
# =============================================================================
class ConfirmationResponses:
    """Templates for confirmation prompts."""

    @staticmethod
    def delete_confirmation(description: str) -> str:
        """Response requesting delete confirmation."""
        return (
            f"Are you sure you want to delete '{description}'? "
            "This cannot be undone. Reply 'yes' to confirm or 'no' to cancel."
        )

    @staticmethod
    def delete_cancelled() -> str:
        """Response when deletion is cancelled."""
        return "OK, I won't delete that task."

    @staticmethod
    def confirmation_expired() -> str:
        """Response when confirmation has expired."""
        return "The confirmation request has expired. Please try again if you'd like to delete the task."


# =============================================================================
# Error Response Templates
# =============================================================================
class ErrorResponses:
    """Templates for error responses."""

    @staticmethod
    def tool_failure(action: str) -> str:
        """Response when a tool invocation fails."""
        return f"Sorry, I wasn't able to {action}. Please try again."

    @staticmethod
    def auth_required() -> str:
        """Response when authentication is missing."""
        return "I need you to be logged in to manage tasks."

    @staticmethod
    def invalid_input() -> str:
        """Response when input is invalid."""
        return "I didn't understand that. Could you rephrase?"

    @staticmethod
    def description_too_long() -> str:
        """Response when task description exceeds limit."""
        return "That task description is too long. Please keep it under 1000 characters."

    @staticmethod
    def out_of_scope() -> str:
        """Response when request is outside agent capabilities."""
        return (
            "I can help you manage your tasks - creating, listing, updating, "
            "completing, and deleting them. Is there something task-related I can help with?"
        )


# =============================================================================
# General Conversation Templates
# =============================================================================
class GeneralResponses:
    """Templates for general (non-task) conversation."""

    @staticmethod
    def greeting() -> str:
        """Response to greetings."""
        return "Hello! How can I help you with your tasks today?"

    @staticmethod
    def capabilities() -> str:
        """Response explaining agent capabilities."""
        return (
            "I can help you manage your tasks. You can:\n"
            "- Add new tasks: 'remind me to buy groceries'\n"
            "- See your tasks: 'what are my tasks?'\n"
            "- Complete tasks: 'I finished the groceries'\n"
            "- Update tasks: 'change groceries to buy milk'\n"
            "- Delete tasks: 'delete the groceries task'\n\n"
            "What would you like to do?"
        )

    @staticmethod
    def fallback() -> str:
        """Fallback response for general chat."""
        return (
            "I'm here to help you manage your tasks. "
            "Is there something task-related I can help you with?"
        )


# =============================================================================
# Result Formatting Helper
# =============================================================================
def format_list_tasks_result(result: dict) -> str:
    """Format list_tasks result with resolution handling.

    Handles different resolution outcomes from the executor:
    - success: Task operation completed
    - confirm_delete: Delete confirmation needed
    - no_match: No task matched the reference
    - multiple_matches: Multiple tasks matched
    - (none): Just list the tasks

    Args:
        result: The result dict from executor._execute_list_tasks

    Returns:
        Formatted response string
    """
    resolution = result.get("_resolution")
    tasks = result.get("tasks", [])

    if resolution == "success":
        operation = result.get("_operation")
        task_info = result.get("_task", {})

        if operation == "complete":
            return SuccessResponses.task_completed(task_info.get("description", ""))
        elif operation == "update":
            return SuccessResponses.task_updated(
                task_info.get("old_description", ""),
                task_info.get("new_description", ""),
            )

    elif resolution == "confirm_delete":
        task_desc = result.get("_task_description", "")
        return ConfirmationResponses.delete_confirmation(task_desc)

    elif resolution == "no_match":
        reference = result.get("_reference", "")
        return ClarificationResponses.no_task_match(reference, tasks)

    elif resolution == "multiple_matches":
        reference = result.get("_reference", "")
        matches = result.get("_matches", [])
        return ClarificationResponses.multiple_task_matches(reference, matches)

    # Default: just list tasks
    return SuccessResponses.tasks_listed(tasks)

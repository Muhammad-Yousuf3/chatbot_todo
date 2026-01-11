"""Task reference resolution for the Agent Decision Engine.

This module resolves task references from user messages to actual tasks.
It handles various reference styles: exact match, partial match, position, numeric.
"""

import re
from typing import Any


def resolve_task_reference(
    reference: str,
    tasks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Resolve a task reference to an actual task.

    Resolution order per contract:
    1. Numeric reference ("task 1", "#1") - uses ALL tasks (display order)
    2. Position reference ("first", "last") - uses ALL tasks (display order)
    3. Exact description match (case-insensitive) - pending only
    4. Partial description match (contains reference) - pending only

    For numbered selection (e.g., "complete task 1"), the number maps to the
    displayed task list which includes all tasks.

    Args:
        reference: The task reference from the user message.
        tasks: List of task dictionaries with 'id', 'description', 'completed'.

    Returns:
        The matched task dict, or None if no unique match found.
        Returns None if multiple matches (requires clarification).
    """
    if not tasks or not reference:
        return None

    reference_lower = reference.lower().strip()

    # 1. Numeric reference - use ALL tasks (matches display order)
    numeric_match = _resolve_numeric_reference(reference_lower, tasks)
    if numeric_match:
        return numeric_match

    # 2. Position reference - use ALL tasks (matches display order)
    position_match = _resolve_position_reference(reference_lower, tasks)
    if position_match:
        return position_match

    # For text-based matching, filter to pending tasks only
    pending_tasks = [t for t in tasks if not t.get("completed", False)]

    # 3. Exact description match (case-insensitive)
    exact_matches = [
        t for t in pending_tasks if t.get("description", "").lower() == reference_lower
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        return None  # Multiple matches require clarification

    # 4. Partial description match (contains reference)
    partial_matches = [
        t for t in pending_tasks if reference_lower in t.get("description", "").lower()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        return None  # Multiple matches require clarification

    # No match found
    return None


def find_matching_tasks(
    reference: str,
    tasks: list[dict[str, Any]],
    include_completed: bool = False,
) -> list[dict[str, Any]]:
    """Find all tasks that match a reference.

    Used when multiple matches exist and we need to show options.

    Args:
        reference: The task reference from the user message.
        tasks: List of task dictionaries.
        include_completed: Whether to include completed tasks.

    Returns:
        List of matching task dicts (may be empty).
    """
    if not tasks or not reference:
        return []

    reference_lower = reference.lower().strip()
    if include_completed:
        target_tasks = tasks
    else:
        target_tasks = [t for t in tasks if not t.get("completed", False)]

    matches = []

    # Check for exact matches
    for task in target_tasks:
        desc = task.get("description", "").lower()
        if desc == reference_lower:
            matches.append(task)

    if matches:
        return matches

    # Check for partial matches
    for task in target_tasks:
        desc = task.get("description", "").lower()
        if reference_lower in desc:
            matches.append(task)

    return matches


def _resolve_position_reference(
    reference: str, tasks: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Resolve position-based references like 'first', 'last', 'second'."""
    if not tasks:
        return None

    position_words = {
        "first": 0,
        "1st": 0,
        "second": 1,
        "2nd": 1,
        "third": 2,
        "3rd": 2,
        "fourth": 3,
        "4th": 3,
        "fifth": 4,
        "5th": 4,
        "last": -1,
    }

    # Extract position word from reference
    for word, index in position_words.items():
        if word in reference:
            if index == -1:
                return tasks[-1] if tasks else None
            if index < len(tasks):
                return tasks[index]
            return None

    return None


def _resolve_numeric_reference(
    reference: str, tasks: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Resolve numeric references like 'task 1', '#1', '1'."""
    if not tasks:
        return None

    # Patterns for numeric reference
    patterns = [
        r"task\s*(\d+)",
        r"#\s*(\d+)",
        r"number\s*(\d+)",
        r"^(\d+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, reference)
        if match:
            try:
                num = int(match.group(1))
                # Convert to 0-based index (user says "task 1" for first task)
                index = num - 1
                if 0 <= index < len(tasks):
                    return tasks[index]
            except (ValueError, IndexError):
                pass

    return None


def resolve_task_for_operation(
    reference: str,
    tasks: list[dict[str, Any]],
    include_completed: bool = False,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Resolve a task reference for a mutating operation.

    Args:
        reference: The task reference from the user message.
        tasks: List of all task dictionaries.
        include_completed: Whether to include completed tasks in resolution.

    Returns:
        Tuple of (matched_task, all_matches).
        - matched_task is the unique match, or None if no unique match
        - all_matches is the list of all matches (for clarification)
    """
    matches = find_matching_tasks(reference, tasks, include_completed=include_completed)

    if len(matches) == 1:
        return matches[0], matches
    elif len(matches) > 1:
        return None, matches
    else:
        # Try position/numeric resolution on the appropriate task list
        if include_completed:
            target_tasks = tasks
        else:
            target_tasks = [t for t in tasks if not t.get("completed", False)]
        resolved = resolve_task_reference(reference, target_tasks)
        if resolved:
            return resolved, [resolved]
        return None, []

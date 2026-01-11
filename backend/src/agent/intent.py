"""Intent classification for the Agent Decision Engine.

This module classifies user messages into intent categories and extracts
relevant parameters for tool invocation.
"""

import re
from typing import Any

from src.agent.schemas import IntentType, Message, UserIntent


async def classify_intent(
    message: str, history: list[Message] | None = None
) -> UserIntent:
    """Classify the intent of a user message.

    This function analyzes the user's message and determines what they want to do.
    It uses pattern matching to identify task-related intents.

    Args:
        message: The current user message.
        history: Recent conversation messages for context.

    Returns:
        UserIntent with classified intent type and extracted parameters.
    """
    # Handle edge cases: empty or whitespace-only messages
    if not message or not message.strip():
        return UserIntent(
            intent_type=IntentType.GENERAL_CHAT,
            confidence=0.80,
            extracted_params=None,
        )

    message_lower = message.lower().strip()

    # Handle special characters only messages
    if not any(c.isalnum() for c in message_lower):
        return UserIntent(
            intent_type=IntentType.GENERAL_CHAT,
            confidence=0.75,
            extracted_params=None,
        )

    # Check for multi-intent patterns first (T087)
    multi_intent_result = _check_multi_intent(message, message_lower)
    if multi_intent_result:
        return multi_intent_result

    # Check for confirmation responses first (when there's a pending action)
    if _is_confirm_yes(message_lower):
        return UserIntent(
            intent_type=IntentType.CONFIRM_YES,
            confidence=0.95,
            extracted_params=None,
        )

    if _is_confirm_no(message_lower):
        return UserIntent(
            intent_type=IntentType.CONFIRM_NO,
            confidence=0.95,
            extracted_params=None,
        )

    # Check for task-related intents
    # LIST_TASKS patterns (check before CREATE_TASK to avoid "I need to" matching "what do I need to do")
    if _is_list_tasks(message_lower):
        return UserIntent(
            intent_type=IntentType.LIST_TASKS,
            confidence=0.95,
            extracted_params=None,
        )

    # CREATE_TASK patterns
    create_result = _check_create_task(message, message_lower)
    if create_result:
        return create_result

    # COMPLETE_TASK patterns
    complete_result = _check_complete_task(message, message_lower)
    if complete_result:
        return complete_result

    # UPDATE_TASK patterns
    update_result = _check_update_task(message, message_lower)
    if update_result:
        return update_result

    # DELETE_TASK patterns
    delete_result = _check_delete_task(message, message_lower)
    if delete_result:
        return delete_result

    # Check for ambiguous single words that could be task-related
    if _is_ambiguous(message_lower):
        return UserIntent(
            intent_type=IntentType.AMBIGUOUS,
            confidence=0.40,
            extracted_params={"possible_intents": ["CREATE_TASK", "COMPLETE_TASK"]},
        )

    # Default to general chat
    return UserIntent(
        intent_type=IntentType.GENERAL_CHAT,
        confidence=0.85,
        extracted_params=None,
    )


def _is_confirm_yes(message: str) -> bool:
    """Check if message is a confirmation."""
    confirm_patterns = [
        r"^yes$",
        r"^y$",
        r"^yeah$",
        r"^yep$",
        r"^yup$",
        r"^confirm$",
        r"^do it$",
        r"^go ahead$",
        r"^sure$",
        r"^ok$",
        r"^okay$",
    ]
    return any(re.match(pattern, message) for pattern in confirm_patterns)


def _is_confirm_no(message: str) -> bool:
    """Check if message is a denial."""
    deny_patterns = [
        r"^no$",
        r"^n$",
        r"^nope$",
        r"^cancel$",
        r"^don'?t$",
        r"^never mind$",
        r"^nevermind$",
        r"^stop$",
    ]
    return any(re.match(pattern, message) for pattern in deny_patterns)


def _check_create_task(message: str, message_lower: str) -> UserIntent | None:
    """Check for CREATE_TASK intent and extract description."""
    create_patterns = [
        (r"remind me to (.+)", 1),
        (r"add task:?\s*(.+)", 1),
        (r"create task:?\s*(.+)", 1),
        (r"new task:?\s*(.+)", 1),
        (r"add (.+) to my (?:tasks?|list|todo)", 1),
        (r"i need to (.+)", 1),
        (r"don'?t forget to (.+)", 1),
        (r"todo:?\s*(.+)", 1),
        (r"remember to (.+)", 1),
        (r"add a task to (.+)", 1),
    ]

    for pattern, group in create_patterns:
        match = re.search(pattern, message_lower)
        if match:
            description = match.group(group).strip()
            # Clean up the description
            description = re.sub(r"\s+", " ", description)
            return UserIntent(
                intent_type=IntentType.CREATE_TASK,
                confidence=0.92,
                extracted_params={"description": description},
            )

    return None


def _is_list_tasks(message: str) -> bool:
    """Check if message is a LIST_TASKS intent."""
    list_patterns = [
        r"show (?:me )?(?:my )?tasks",
        r"what are my tasks",
        r"my tasks",
        r"my list",
        r"what do i need to do",
        r"show me what i need to do",
        r"list (?:my )?tasks",
        r"what'?s on my list",
        r"show my todo",
        r"what tasks do i have",
    ]
    return any(re.search(pattern, message) for pattern in list_patterns)


def _check_complete_task(message: str, message_lower: str) -> UserIntent | None:
    """Check for COMPLETE_TASK intent and extract task reference."""
    complete_patterns = [
        (r"i (?:finished|completed|did|done with) (?:the )?(.+)", 1),
        (r"(?:mark|check off) (?:the )?(.+?) (?:as )?(?:done|completed|finished)", 1),
        (r"(.+?) is done", 1),
        (r"done with (?:the )?(.+)", 1),
        (r"finished (?:the )?(.+)", 1),
        (r"completed (?:the )?(.+)", 1),
        (r"i'?ve done (?:the )?(.+)", 1),
        (r"check off (?:the )?(.+)", 1),
    ]

    for pattern, group in complete_patterns:
        match = re.search(pattern, message_lower)
        if match:
            task_reference = match.group(group).strip()
            # Clean up the reference
            task_reference = re.sub(r"\s+", " ", task_reference)
            task_reference = re.sub(r" task$", "", task_reference)
            return UserIntent(
                intent_type=IntentType.COMPLETE_TASK,
                confidence=0.90,
                extracted_params={"task_reference": task_reference},
            )

    return None


def _check_update_task(message: str, message_lower: str) -> UserIntent | None:
    """Check for UPDATE_TASK intent and extract task reference and new description."""
    update_patterns = [
        (r"change (?:the )?(.+?) (?:task )?to (.+)", 1, 2),
        (r"update (?:the )?(.+?) (?:task )?to (.+)", 1, 2),
        (r"modify (?:the )?(.+?) (?:task )?to (.+)", 1, 2),
        (r"edit (?:the )?(.+?) (?:task )?to (.+)", 1, 2),
        (r"rename (?:the )?(.+?) (?:task )?to (.+)", 1, 2),
        (r"add (.+) to (?:the )?(.+?) task", 2, None),  # "add milk to groceries task"
    ]

    for pattern_info in update_patterns:
        if len(pattern_info) == 3:
            pattern, ref_group, desc_group = pattern_info
            match = re.search(pattern, message_lower)
            if match:
                task_reference = match.group(ref_group).strip()
                if desc_group:
                    new_description = match.group(desc_group).strip()
                else:
                    # For "add X to Y task" pattern, combine
                    addition = match.group(1).strip()
                    new_description = f"{task_reference} and {addition}"

                return UserIntent(
                    intent_type=IntentType.UPDATE_TASK,
                    confidence=0.88,
                    extracted_params={
                        "task_reference": task_reference,
                        "new_description": new_description,
                    },
                )

    return None


def _check_delete_task(message: str, message_lower: str) -> UserIntent | None:
    """Check for DELETE_TASK intent and extract task reference."""
    delete_patterns = [
        (r"delete (?:the )?(.+?) task", 1),
        (r"remove (?:the )?(.+?) task", 1),
        (r"cancel (?:the )?(.+?) task", 1),
        (r"get rid of (?:the )?(.+?) task", 1),
        (r"forget (?:the )?(.+?) task", 1),
        (r"delete (?:the )?(.+)", 1),
        (r"remove (?:the )?(.+)", 1),
    ]

    for pattern, group in delete_patterns:
        match = re.search(pattern, message_lower)
        if match:
            task_reference = match.group(group).strip()
            # Clean up the reference
            task_reference = re.sub(r"\s+", " ", task_reference)
            task_reference = re.sub(r" task$", "", task_reference)
            return UserIntent(
                intent_type=IntentType.DELETE_TASK,
                confidence=0.90,
                extracted_params={"task_reference": task_reference},
            )

    return None


def _is_ambiguous(message: str) -> bool:
    """Check if message is ambiguous (single word that could be a task reference)."""
    # Single words without clear intent markers are ambiguous
    words = message.split()
    if len(words) == 1:
        # Skip common greetings and simple responses
        non_ambiguous = {
            "hello",
            "hi",
            "hey",
            "bye",
            "thanks",
            "thank",
            "yes",
            "no",
            "ok",
            "okay",
        }
        if message not in non_ambiguous:
            return True
    return False


def _check_multi_intent(message: str, message_lower: str) -> UserIntent | None:
    """Check if message contains multiple intents (T087).

    Detects patterns like:
    - "add groceries and show my list"
    - "create task X then mark Y done"
    - "remind me to X and also delete Y"
    """
    # Patterns that indicate multiple actions
    multi_intent_connectors = [
        r"\s+and\s+(?:also\s+)?",
        r"\s+then\s+",
        r"\s+also\s+",
        r",\s*(?:and\s+)?",
    ]

    # Check if message has a connector
    has_connector = any(
        re.search(pattern, message_lower) for pattern in multi_intent_connectors
    )

    if not has_connector:
        return None

    # Patterns for detecting intent keywords
    intent_patterns = {
        "CREATE": [
            r"(?:add|create|remind|todo|new)\s+(?:task|to)?",
            r"i need to",
            r"don'?t forget",
        ],
        "LIST": [
            r"show\s+(?:my\s+)?(?:tasks?|list)",
            r"what\s+(?:are|do)\s+(?:my|i)",
            r"my\s+(?:tasks?|list)",
        ],
        "COMPLETE": [
            r"(?:finished|completed|done\s+with|mark)\s+",
            r"(?:check\s+off)",
        ],
        "DELETE": [
            r"(?:delete|remove|cancel)\s+",
        ],
    }

    # Count how many different intent types are present
    detected_intents = []
    for intent_name, patterns in intent_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                if intent_name not in detected_intents:
                    detected_intents.append(intent_name)
                break

    # If we detect 2+ distinct intent types, return MULTI_INTENT
    if len(detected_intents) >= 2:
        return UserIntent(
            intent_type=IntentType.MULTI_INTENT,
            confidence=0.85,
            extracted_params={
                "intents": detected_intents,
                "original_message": message,
            },
        )

    return None

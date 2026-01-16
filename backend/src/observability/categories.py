"""
Outcome category taxonomy for agent decision classification.

This module defines the two-level taxonomy (Category:Subcategory) for
classifying all agent decision outcomes.

Feature: 004-agent-observability
"""

from enum import Enum
from typing import Literal


class OutcomeCategory(str, Enum):
    """
    Top-level outcome categories for agent decisions.

    Format when stored: "CATEGORY:SUBCATEGORY" (e.g., "SUCCESS:TASK_COMPLETED")
    """

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    REFUSAL = "REFUSAL"
    AMBIGUITY = "AMBIGUITY"


class SuccessSubcategory(str, Enum):
    """Subcategories for SUCCESS outcomes."""

    TASK_COMPLETED = "TASK_COMPLETED"
    RESPONSE_GIVEN = "RESPONSE_GIVEN"
    CLARIFICATION_ANSWERED = "CLARIFICATION_ANSWERED"


class ErrorSubcategory(str, Enum):
    """Subcategories for ERROR outcomes."""

    USER_INPUT = "USER_INPUT"
    INTENT_CLASSIFICATION = "INTENT_CLASSIFICATION"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    RESPONSE_GENERATION = "RESPONSE_GENERATION"


class RefusalSubcategory(str, Enum):
    """Subcategories for REFUSAL outcomes."""

    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    MISSING_PERMISSION = "MISSING_PERMISSION"
    RATE_LIMITED = "RATE_LIMITED"


class AmbiguitySubcategory(str, Enum):
    """Subcategories for AMBIGUITY outcomes."""

    UNCLEAR_INTENT = "UNCLEAR_INTENT"
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    MISSING_CONTEXT = "MISSING_CONTEXT"


class ErrorCode(str, Enum):
    """
    Error codes for tool invocation failures.

    Used in ToolInvocationLog.error_code field.
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTENT_ERROR = "INTENT_ERROR"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_ERROR = "TOOL_EXECUTION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# Type aliases for valid category combinations
OutcomeCategoryStr = Literal[
    "SUCCESS:TASK_COMPLETED",
    "SUCCESS:RESPONSE_GIVEN",
    "SUCCESS:CLARIFICATION_ANSWERED",
    "ERROR:USER_INPUT",
    "ERROR:INTENT_CLASSIFICATION",
    "ERROR:TOOL_INVOCATION",
    "ERROR:RESPONSE_GENERATION",
    "REFUSAL:OUT_OF_SCOPE",
    "REFUSAL:MISSING_PERMISSION",
    "REFUSAL:RATE_LIMITED",
    "AMBIGUITY:UNCLEAR_INTENT",
    "AMBIGUITY:MULTIPLE_MATCHES",
    "AMBIGUITY:MISSING_CONTEXT",
]

# Valid category:subcategory combinations
VALID_OUTCOME_CATEGORIES: set[str] = {
    # SUCCESS
    "SUCCESS:TASK_COMPLETED",
    "SUCCESS:RESPONSE_GIVEN",
    "SUCCESS:CLARIFICATION_ANSWERED",
    # ERROR
    "ERROR:USER_INPUT",
    "ERROR:INTENT_CLASSIFICATION",
    "ERROR:TOOL_INVOCATION",
    "ERROR:RESPONSE_GENERATION",
    # REFUSAL
    "REFUSAL:OUT_OF_SCOPE",
    "REFUSAL:MISSING_PERMISSION",
    "REFUSAL:RATE_LIMITED",
    # AMBIGUITY
    "AMBIGUITY:UNCLEAR_INTENT",
    "AMBIGUITY:MULTIPLE_MATCHES",
    "AMBIGUITY:MISSING_CONTEXT",
}


def validate_outcome_category(category: str) -> bool:
    """
    Validate that a category string matches the expected format.

    Args:
        category: The outcome category string (e.g., "SUCCESS:TASK_COMPLETED")

    Returns:
        True if valid, False otherwise
    """
    return category in VALID_OUTCOME_CATEGORIES


def get_category(outcome_category: str) -> str | None:
    """
    Extract the top-level category from an outcome category string.

    Args:
        outcome_category: Full category string (e.g., "SUCCESS:TASK_COMPLETED")

    Returns:
        Top-level category (e.g., "SUCCESS") or None if invalid
    """
    if ":" not in outcome_category:
        return None
    return outcome_category.split(":")[0]


def get_subcategory(outcome_category: str) -> str | None:
    """
    Extract the subcategory from an outcome category string.

    Args:
        outcome_category: Full category string (e.g., "SUCCESS:TASK_COMPLETED")

    Returns:
        Subcategory (e.g., "TASK_COMPLETED") or None if invalid
    """
    if ":" not in outcome_category:
        return None
    parts = outcome_category.split(":")
    return parts[1] if len(parts) > 1 else None


def is_success(outcome_category: str) -> bool:
    """Check if the outcome is a success."""
    return get_category(outcome_category) == OutcomeCategory.SUCCESS


def is_error(outcome_category: str) -> bool:
    """Check if the outcome is an error."""
    return get_category(outcome_category) == OutcomeCategory.ERROR


def is_refusal(outcome_category: str) -> bool:
    """Check if the outcome is a refusal."""
    return get_category(outcome_category) == OutcomeCategory.REFUSAL


def is_ambiguity(outcome_category: str) -> bool:
    """Check if the outcome is ambiguous."""
    return get_category(outcome_category) == OutcomeCategory.AMBIGUITY


def assign_outcome_category(
    *,
    tool_used: bool = False,
    tool_succeeded: bool | None = None,
    is_clarification: bool = False,
    is_out_of_scope: bool = False,
    is_ambiguous: bool = False,
    is_missing_permission: bool = False,
    is_rate_limited: bool = False,
    has_multiple_matches: bool = False,
    has_missing_context: bool = False,
    intent_error: bool = False,
    user_input_error: bool = False,
    response_error: bool = False,
) -> str:
    """
    Determine the appropriate outcome category based on decision state.

    This function implements the category assignment logic for all outcome types.

    Args:
        tool_used: Whether a tool was invoked
        tool_succeeded: Whether the tool invocation succeeded (None if no tool)
        is_clarification: Whether this was a clarification response
        is_out_of_scope: Whether the request was out of scope
        is_ambiguous: Whether the intent was unclear
        is_missing_permission: Whether the user lacks permission
        is_rate_limited: Whether rate limit was hit
        has_multiple_matches: Whether multiple tasks matched
        has_missing_context: Whether more context is needed
        intent_error: Whether intent classification failed
        user_input_error: Whether user input was invalid
        response_error: Whether response generation failed

    Returns:
        Outcome category string (e.g., "SUCCESS:TASK_COMPLETED")
    """
    # Handle REFUSAL cases first
    if is_out_of_scope:
        return "REFUSAL:OUT_OF_SCOPE"
    if is_missing_permission:
        return "REFUSAL:MISSING_PERMISSION"
    if is_rate_limited:
        return "REFUSAL:RATE_LIMITED"

    # Handle AMBIGUITY cases
    if is_ambiguous:
        return "AMBIGUITY:UNCLEAR_INTENT"
    if has_multiple_matches:
        return "AMBIGUITY:MULTIPLE_MATCHES"
    if has_missing_context:
        return "AMBIGUITY:MISSING_CONTEXT"

    # Handle ERROR cases
    if user_input_error:
        return "ERROR:USER_INPUT"
    if intent_error:
        return "ERROR:INTENT_CLASSIFICATION"
    if response_error:
        return "ERROR:RESPONSE_GENERATION"
    if tool_used and tool_succeeded is False:
        return "ERROR:TOOL_INVOCATION"

    # Handle SUCCESS cases
    if is_clarification:
        return "SUCCESS:CLARIFICATION_ANSWERED"
    if tool_used and tool_succeeded is True:
        return "SUCCESS:TASK_COMPLETED"

    # Default: response given without tool
    return "SUCCESS:RESPONSE_GIVEN"

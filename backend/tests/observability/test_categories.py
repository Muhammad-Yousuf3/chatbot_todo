"""
Tests for outcome category assignment logic.

Feature: 004-agent-observability
"""

import pytest

from src.observability.categories import (
    VALID_OUTCOME_CATEGORIES,
    assign_outcome_category,
    get_category,
    get_subcategory,
    is_ambiguity,
    is_error,
    is_refusal,
    is_success,
    validate_outcome_category,
)


class TestValidateOutcomeCategory:
    """Tests for validate_outcome_category function."""

    @pytest.mark.parametrize("category", VALID_OUTCOME_CATEGORIES)
    def test_valid_categories(self, category: str):
        """Test all valid categories are accepted."""
        assert validate_outcome_category(category) is True

    @pytest.mark.parametrize(
        "invalid_category",
        [
            "SUCCESS",  # Missing subcategory
            "INVALID:CATEGORY",  # Invalid category
            "SUCCESS:INVALID",  # Invalid subcategory
            "success:task_completed",  # Wrong case
            "",  # Empty
            "SUCCESS:TASK_COMPLETED:EXTRA",  # Extra level
        ],
    )
    def test_invalid_categories(self, invalid_category: str):
        """Test invalid categories are rejected."""
        assert validate_outcome_category(invalid_category) is False


class TestGetCategoryAndSubcategory:
    """Tests for get_category and get_subcategory functions."""

    def test_get_category_success(self):
        """Test extracting category from valid string."""
        assert get_category("SUCCESS:TASK_COMPLETED") == "SUCCESS"
        assert get_category("ERROR:TOOL_INVOCATION") == "ERROR"
        assert get_category("REFUSAL:OUT_OF_SCOPE") == "REFUSAL"
        assert get_category("AMBIGUITY:UNCLEAR_INTENT") == "AMBIGUITY"

    def test_get_category_invalid(self):
        """Test get_category with invalid format."""
        assert get_category("NO_COLON") is None

    def test_get_subcategory_success(self):
        """Test extracting subcategory from valid string."""
        assert get_subcategory("SUCCESS:TASK_COMPLETED") == "TASK_COMPLETED"
        assert get_subcategory("ERROR:TOOL_INVOCATION") == "TOOL_INVOCATION"

    def test_get_subcategory_invalid(self):
        """Test get_subcategory with invalid format."""
        assert get_subcategory("NO_COLON") is None


class TestCategoryHelpers:
    """Tests for is_success, is_error, is_refusal, is_ambiguity."""

    def test_is_success(self):
        """Test is_success helper."""
        assert is_success("SUCCESS:TASK_COMPLETED") is True
        assert is_success("SUCCESS:RESPONSE_GIVEN") is True
        assert is_success("ERROR:TOOL_INVOCATION") is False

    def test_is_error(self):
        """Test is_error helper."""
        assert is_error("ERROR:TOOL_INVOCATION") is True
        assert is_error("ERROR:USER_INPUT") is True
        assert is_error("SUCCESS:TASK_COMPLETED") is False

    def test_is_refusal(self):
        """Test is_refusal helper."""
        assert is_refusal("REFUSAL:OUT_OF_SCOPE") is True
        assert is_refusal("REFUSAL:RATE_LIMITED") is True
        assert is_refusal("SUCCESS:TASK_COMPLETED") is False

    def test_is_ambiguity(self):
        """Test is_ambiguity helper."""
        assert is_ambiguity("AMBIGUITY:UNCLEAR_INTENT") is True
        assert is_ambiguity("AMBIGUITY:MULTIPLE_MATCHES") is True
        assert is_ambiguity("SUCCESS:TASK_COMPLETED") is False


class TestAssignOutcomeCategory:
    """Tests for assign_outcome_category function."""

    # SUCCESS cases
    def test_assign_success_task_completed(self):
        """Test assignment for successful task completion."""
        result = assign_outcome_category(tool_used=True, tool_succeeded=True)
        assert result == "SUCCESS:TASK_COMPLETED"

    def test_assign_success_response_given(self):
        """Test assignment for response without tool."""
        result = assign_outcome_category(tool_used=False)
        assert result == "SUCCESS:RESPONSE_GIVEN"

    def test_assign_success_clarification_answered(self):
        """Test assignment for clarification response."""
        result = assign_outcome_category(is_clarification=True)
        assert result == "SUCCESS:CLARIFICATION_ANSWERED"

    # ERROR cases
    def test_assign_error_user_input(self):
        """Test assignment for user input error."""
        result = assign_outcome_category(user_input_error=True)
        assert result == "ERROR:USER_INPUT"

    def test_assign_error_intent_classification(self):
        """Test assignment for intent classification error."""
        result = assign_outcome_category(intent_error=True)
        assert result == "ERROR:INTENT_CLASSIFICATION"

    def test_assign_error_tool_invocation(self):
        """Test assignment for tool invocation error."""
        result = assign_outcome_category(tool_used=True, tool_succeeded=False)
        assert result == "ERROR:TOOL_INVOCATION"

    def test_assign_error_response_generation(self):
        """Test assignment for response generation error."""
        result = assign_outcome_category(response_error=True)
        assert result == "ERROR:RESPONSE_GENERATION"

    # REFUSAL cases
    def test_assign_refusal_out_of_scope(self):
        """Test assignment for out of scope refusal."""
        result = assign_outcome_category(is_out_of_scope=True)
        assert result == "REFUSAL:OUT_OF_SCOPE"

    def test_assign_refusal_missing_permission(self):
        """Test assignment for missing permission refusal."""
        result = assign_outcome_category(is_missing_permission=True)
        assert result == "REFUSAL:MISSING_PERMISSION"

    def test_assign_refusal_rate_limited(self):
        """Test assignment for rate limited refusal."""
        result = assign_outcome_category(is_rate_limited=True)
        assert result == "REFUSAL:RATE_LIMITED"

    # AMBIGUITY cases
    def test_assign_ambiguity_unclear_intent(self):
        """Test assignment for unclear intent ambiguity."""
        result = assign_outcome_category(is_ambiguous=True)
        assert result == "AMBIGUITY:UNCLEAR_INTENT"

    def test_assign_ambiguity_multiple_matches(self):
        """Test assignment for multiple matches ambiguity."""
        result = assign_outcome_category(has_multiple_matches=True)
        assert result == "AMBIGUITY:MULTIPLE_MATCHES"

    def test_assign_ambiguity_missing_context(self):
        """Test assignment for missing context ambiguity."""
        result = assign_outcome_category(has_missing_context=True)
        assert result == "AMBIGUITY:MISSING_CONTEXT"

    # Priority tests
    def test_refusal_takes_priority_over_success(self):
        """Test that refusal categories take priority."""
        result = assign_outcome_category(
            tool_used=True,
            tool_succeeded=True,
            is_out_of_scope=True,
        )
        assert result == "REFUSAL:OUT_OF_SCOPE"

    def test_ambiguity_takes_priority_over_success(self):
        """Test that ambiguity categories take priority."""
        result = assign_outcome_category(
            tool_used=True,
            tool_succeeded=True,
            is_ambiguous=True,
        )
        assert result == "AMBIGUITY:UNCLEAR_INTENT"

    def test_error_takes_priority_over_success(self):
        """Test that error categories take priority."""
        result = assign_outcome_category(
            tool_used=True,
            tool_succeeded=True,
            user_input_error=True,
        )
        assert result == "ERROR:USER_INPUT"


class TestAllOutcomeCategoriesValid:
    """Meta-test to ensure all assigned categories are valid."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            # SUCCESS
            {"tool_used": True, "tool_succeeded": True},
            {"tool_used": False},
            {"is_clarification": True},
            # ERROR
            {"user_input_error": True},
            {"intent_error": True},
            {"tool_used": True, "tool_succeeded": False},
            {"response_error": True},
            # REFUSAL
            {"is_out_of_scope": True},
            {"is_missing_permission": True},
            {"is_rate_limited": True},
            # AMBIGUITY
            {"is_ambiguous": True},
            {"has_multiple_matches": True},
            {"has_missing_context": True},
        ],
    )
    def test_assigned_category_is_valid(self, kwargs):
        """Test that all assigned categories pass validation."""
        result = assign_outcome_category(**kwargs)
        assert validate_outcome_category(result), f"Invalid category: {result}"

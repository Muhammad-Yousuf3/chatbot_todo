"""Tests for intent classification."""

import pytest

from src.agent.intent import classify_intent
from src.agent.schemas import IntentType


class TestCreateTaskIntent:
    """Tests for CREATE_TASK intent classification (T016, T017)."""

    @pytest.mark.asyncio
    async def test_remind_me_pattern(self):
        """'remind me to X' should classify as CREATE_TASK."""
        intent = await classify_intent("remind me to buy groceries")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "buy groceries"

    @pytest.mark.asyncio
    async def test_add_task_pattern(self):
        """'add task X' should classify as CREATE_TASK."""
        intent = await classify_intent("add task: call mom")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "call mom"

    @pytest.mark.asyncio
    async def test_i_need_to_pattern(self):
        """'I need to X' should classify as CREATE_TASK."""
        intent = await classify_intent("I need to finish the report")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "finish the report"

    @pytest.mark.asyncio
    async def test_dont_forget_pattern(self):
        """'don't forget to X' should classify as CREATE_TASK."""
        intent = await classify_intent("don't forget to water the plants")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "water the plants"

    @pytest.mark.asyncio
    async def test_todo_pattern(self):
        """'todo: X' should classify as CREATE_TASK."""
        intent = await classify_intent("todo: pick up dry cleaning")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "pick up dry cleaning"

    @pytest.mark.asyncio
    async def test_create_task_pattern(self):
        """'create task X' should classify as CREATE_TASK."""
        intent = await classify_intent("create task send email to boss")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "send email to boss"

    @pytest.mark.asyncio
    async def test_remember_to_pattern(self):
        """'remember to X' should classify as CREATE_TASK."""
        intent = await classify_intent("remember to pay bills")
        assert intent.intent_type == IntentType.CREATE_TASK
        assert intent.extracted_params["description"] == "pay bills"


class TestListTasksIntent:
    """Tests for LIST_TASKS intent classification (T025)."""

    @pytest.mark.asyncio
    async def test_what_are_my_tasks(self):
        """'what are my tasks' should classify as LIST_TASKS."""
        intent = await classify_intent("what are my tasks?")
        assert intent.intent_type == IntentType.LIST_TASKS

    @pytest.mark.asyncio
    async def test_show_tasks(self):
        """'show tasks' should classify as LIST_TASKS."""
        intent = await classify_intent("show my tasks")
        assert intent.intent_type == IntentType.LIST_TASKS

    @pytest.mark.asyncio
    async def test_my_list(self):
        """'my list' should classify as LIST_TASKS."""
        intent = await classify_intent("what's on my list?")
        assert intent.intent_type == IntentType.LIST_TASKS

    @pytest.mark.asyncio
    async def test_what_do_i_need_to_do(self):
        """'what do I need to do' should classify as LIST_TASKS."""
        intent = await classify_intent("what do i need to do")
        assert intent.intent_type == IntentType.LIST_TASKS


class TestCompleteTaskIntent:
    """Tests for COMPLETE_TASK intent classification (T048, T049)."""

    @pytest.mark.asyncio
    async def test_i_finished_pattern(self):
        """'I finished X' should classify as COMPLETE_TASK."""
        intent = await classify_intent("I finished the groceries")
        assert intent.intent_type == IntentType.COMPLETE_TASK
        assert intent.extracted_params["task_reference"] == "groceries"

    @pytest.mark.asyncio
    async def test_mark_as_done_pattern(self):
        """'mark X as done' should classify as COMPLETE_TASK."""
        intent = await classify_intent("mark the call mom task as done")
        assert intent.intent_type == IntentType.COMPLETE_TASK
        assert "call mom" in intent.extracted_params["task_reference"]

    @pytest.mark.asyncio
    async def test_done_with_pattern(self):
        """'done with X' should classify as COMPLETE_TASK."""
        intent = await classify_intent("done with the report")
        assert intent.intent_type == IntentType.COMPLETE_TASK
        assert intent.extracted_params["task_reference"] == "report"


class TestUpdateTaskIntent:
    """Tests for UPDATE_TASK intent classification (T061, T062)."""

    @pytest.mark.asyncio
    async def test_change_to_pattern(self):
        """'change X to Y' should classify as UPDATE_TASK."""
        intent = await classify_intent("change groceries to buy milk and bread")
        assert intent.intent_type == IntentType.UPDATE_TASK
        assert intent.extracted_params["task_reference"] == "groceries"
        assert intent.extracted_params["new_description"] == "buy milk and bread"

    @pytest.mark.asyncio
    async def test_update_to_pattern(self):
        """'update X to Y' should classify as UPDATE_TASK."""
        intent = await classify_intent("update the report task to quarterly report")
        assert intent.intent_type == IntentType.UPDATE_TASK

    @pytest.mark.asyncio
    async def test_modify_pattern(self):
        """'modify X to Y' should classify as UPDATE_TASK."""
        intent = await classify_intent("modify call mom to call mom at 5pm")
        assert intent.intent_type == IntentType.UPDATE_TASK


class TestDeleteTaskIntent:
    """Tests for DELETE_TASK intent classification (T070)."""

    @pytest.mark.asyncio
    async def test_delete_pattern(self):
        """'delete X task' should classify as DELETE_TASK."""
        intent = await classify_intent("delete the groceries task")
        assert intent.intent_type == IntentType.DELETE_TASK
        assert intent.extracted_params["task_reference"] == "groceries"

    @pytest.mark.asyncio
    async def test_remove_pattern(self):
        """'remove X task' should classify as DELETE_TASK."""
        intent = await classify_intent("remove the call mom task")
        assert intent.intent_type == IntentType.DELETE_TASK

    @pytest.mark.asyncio
    async def test_get_rid_of_pattern(self):
        """'get rid of X task' should classify as DELETE_TASK."""
        intent = await classify_intent("get rid of the old task")
        assert intent.intent_type == IntentType.DELETE_TASK


class TestGeneralChatIntent:
    """Tests for GENERAL_CHAT intent classification (T034)."""

    @pytest.mark.asyncio
    async def test_hello_greeting(self):
        """'hello' should classify as GENERAL_CHAT."""
        intent = await classify_intent("hello")
        assert intent.intent_type == IntentType.GENERAL_CHAT

    @pytest.mark.asyncio
    async def test_how_are_you(self):
        """'how are you' should classify as GENERAL_CHAT."""
        intent = await classify_intent("how are you?")
        assert intent.intent_type == IntentType.GENERAL_CHAT

    @pytest.mark.asyncio
    async def test_thanks(self):
        """'thanks' should classify as GENERAL_CHAT."""
        intent = await classify_intent("thanks")
        assert intent.intent_type == IntentType.GENERAL_CHAT


class TestAmbiguousIntent:
    """Tests for AMBIGUOUS intent classification (T041)."""

    @pytest.mark.asyncio
    async def test_single_word_ambiguous(self):
        """Single task-related word should be AMBIGUOUS."""
        intent = await classify_intent("groceries")
        assert intent.intent_type == IntentType.AMBIGUOUS
        assert "possible_intents" in intent.extracted_params

    @pytest.mark.asyncio
    async def test_single_word_not_greeting(self):
        """Single word that's not a greeting should be AMBIGUOUS."""
        intent = await classify_intent("report")
        assert intent.intent_type == IntentType.AMBIGUOUS


class TestConfirmationIntent:
    """Tests for CONFIRM_YES/CONFIRM_NO intent classification (T071)."""

    @pytest.mark.asyncio
    async def test_yes_confirmation(self):
        """'yes' should classify as CONFIRM_YES."""
        intent = await classify_intent("yes")
        assert intent.intent_type == IntentType.CONFIRM_YES

    @pytest.mark.asyncio
    async def test_confirm_confirmation(self):
        """'confirm' should classify as CONFIRM_YES."""
        intent = await classify_intent("confirm")
        assert intent.intent_type == IntentType.CONFIRM_YES

    @pytest.mark.asyncio
    async def test_sure_confirmation(self):
        """'sure' should classify as CONFIRM_YES."""
        intent = await classify_intent("sure")
        assert intent.intent_type == IntentType.CONFIRM_YES

    @pytest.mark.asyncio
    async def test_no_denial(self):
        """'no' should classify as CONFIRM_NO."""
        intent = await classify_intent("no")
        assert intent.intent_type == IntentType.CONFIRM_NO

    @pytest.mark.asyncio
    async def test_cancel_denial(self):
        """'cancel' should classify as CONFIRM_NO."""
        intent = await classify_intent("cancel")
        assert intent.intent_type == IntentType.CONFIRM_NO

    @pytest.mark.asyncio
    async def test_never_mind_denial(self):
        """'never mind' should classify as CONFIRM_NO."""
        intent = await classify_intent("never mind")
        assert intent.intent_type == IntentType.CONFIRM_NO


class TestMultiIntentHandling:
    """Tests for multi-intent detection (T087)."""

    @pytest.mark.asyncio
    async def test_add_and_show_detected_as_multi_intent(self):
        """'add groceries and show my list' should detect multiple intents."""
        intent = await classify_intent("add groceries and show my list")
        # Should detect as multi-intent or handle the primary intent
        assert intent.intent_type in [IntentType.MULTI_INTENT, IntentType.CREATE_TASK]
        if intent.intent_type == IntentType.MULTI_INTENT:
            assert "intents" in intent.extracted_params
            assert len(intent.extracted_params["intents"]) >= 2

    @pytest.mark.asyncio
    async def test_create_and_complete_multi_intent(self):
        """'add buy milk then mark groceries done' should detect multiple intents."""
        intent = await classify_intent("add buy milk then mark groceries done")
        # Should detect as multi-intent or handle primary
        assert intent.intent_type in [IntentType.MULTI_INTENT, IntentType.CREATE_TASK]

    @pytest.mark.asyncio
    async def test_simple_create_not_multi_intent(self):
        """Simple create should not be flagged as multi-intent."""
        intent = await classify_intent("remind me to buy groceries")
        assert intent.intent_type == IntentType.CREATE_TASK
        # Should not have multi-intent marker
        if intent.extracted_params:
            assert "intents" not in intent.extracted_params


class TestEdgeCases:
    """Tests for edge case handling (T088, T090)."""

    @pytest.mark.asyncio
    async def test_empty_message_handled(self):
        """Empty message should be handled gracefully."""
        intent = await classify_intent("")
        assert intent is not None
        assert intent.intent_type == IntentType.GENERAL_CHAT

    @pytest.mark.asyncio
    async def test_whitespace_only_message(self):
        """Whitespace-only message should be handled."""
        intent = await classify_intent("   ")
        assert intent is not None
        assert intent.intent_type == IntentType.GENERAL_CHAT

    @pytest.mark.asyncio
    async def test_numeric_only_message(self):
        """Numeric message should be handled."""
        intent = await classify_intent("123")
        assert intent is not None
        # Could be ambiguous or general chat

    @pytest.mark.asyncio
    async def test_special_characters_only(self):
        """Special characters should be handled safely."""
        intent = await classify_intent("!@#$%^&*()")
        assert intent is not None
        assert intent.intent_type == IntentType.GENERAL_CHAT

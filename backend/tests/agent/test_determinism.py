"""Determinism tests for the Agent Decision Engine.

Tests that same input always produces same output (T094).
"""

import pytest
from uuid import uuid4

from src.agent.engine import AgentDecisionEngine
from src.agent.intent import classify_intent
from src.agent.schemas import DecisionContext


class TestDeterministicClassification:
    """Tests for deterministic intent classification (T094)."""

    @pytest.mark.asyncio
    async def test_same_input_same_intent_10x(self):
        """Same input should produce same intent classification 10 times."""
        message = "remind me to buy groceries"

        intents = []
        for _ in range(10):
            intent = await classify_intent(message)
            intents.append(intent)

        # All should be identical
        first_intent = intents[0]
        for i, intent in enumerate(intents[1:], 2):
            assert intent.intent_type == first_intent.intent_type, f"Run {i} differed"
            assert intent.confidence == first_intent.confidence
            assert intent.extracted_params == first_intent.extracted_params

    @pytest.mark.asyncio
    async def test_deterministic_list_tasks(self):
        """LIST_TASKS classification should be deterministic."""
        message = "what are my tasks?"

        for _ in range(10):
            intent = await classify_intent(message)
            assert intent.intent_type.value == "LIST_TASKS"

    @pytest.mark.asyncio
    async def test_deterministic_general_chat(self):
        """GENERAL_CHAT classification should be deterministic."""
        message = "hello there"

        for _ in range(10):
            intent = await classify_intent(message)
            assert intent.intent_type.value == "GENERAL_CHAT"

    @pytest.mark.asyncio
    async def test_deterministic_complete_task(self):
        """COMPLETE_TASK classification should be deterministic."""
        message = "I finished the groceries"

        for _ in range(10):
            intent = await classify_intent(message)
            assert intent.intent_type.value == "COMPLETE_TASK"
            assert intent.extracted_params["task_reference"] == "groceries"

    @pytest.mark.asyncio
    async def test_deterministic_delete_task(self):
        """DELETE_TASK classification should be deterministic."""
        message = "delete the old task"

        for _ in range(10):
            intent = await classify_intent(message)
            assert intent.intent_type.value == "DELETE_TASK"


class TestDeterministicDecisions:
    """Tests for deterministic decision making (T094)."""

    @pytest.fixture
    def engine(self) -> AgentDecisionEngine:
        """Create a fresh engine instance."""
        return AgentDecisionEngine()

    @pytest.mark.asyncio
    async def test_same_context_same_decision_10x(self, engine):
        """Same context should produce same decision 10 times."""
        base_context = {
            "user_id": "test-user-123",
            "message": "remind me to buy groceries",
            "conversation_id": str(uuid4()),
            "message_history": [],
            "pending_confirmation": None,
        }

        decisions = []
        for _ in range(10):
            context = DecisionContext(**base_context)
            decision = await engine.process_message(context)
            decisions.append(decision)

        # All should be identical in type and tool calls
        first = decisions[0]
        for i, decision in enumerate(decisions[1:], 2):
            assert decision.decision_type == first.decision_type, f"Run {i} differed"
            if first.tool_calls and decision.tool_calls:
                assert len(decision.tool_calls) == len(first.tool_calls)
                for j, (tc1, tc2) in enumerate(zip(first.tool_calls, decision.tool_calls)):
                    assert tc1.tool_name == tc2.tool_name, f"Tool call {j} differed at run {i}"

    @pytest.mark.asyncio
    async def test_decision_order_stability(self, engine):
        """Tool call ordering should be consistent."""
        context = DecisionContext(
            user_id="test-user-123",
            message="show my tasks",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        # Run multiple times
        for _ in range(5):
            decision = await engine.process_message(context)
            if decision.tool_calls:
                # Verify sequence numbers are in order
                sequences = [tc.sequence for tc in decision.tool_calls]
                assert sequences == sorted(sequences)


class TestReproducibleResponses:
    """Tests that responses are reproducible."""

    @pytest.fixture
    def engine(self) -> AgentDecisionEngine:
        """Create a fresh engine instance."""
        return AgentDecisionEngine()

    @pytest.mark.asyncio
    async def test_greeting_response_consistent(self, engine):
        """Greeting responses should be consistent."""
        context = DecisionContext(
            user_id="test-user",
            message="hello",
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        responses = set()
        for _ in range(10):
            decision = await engine.process_message(context)
            responses.add(decision.response_text)

        # All responses should be the same (deterministic)
        assert len(responses) == 1

    @pytest.mark.asyncio
    async def test_clarification_response_consistent(self, engine):
        """Clarification responses should be consistent."""
        context = DecisionContext(
            user_id="test-user",
            message="groceries",  # Ambiguous
            conversation_id=str(uuid4()),
            message_history=[],
            pending_confirmation=None,
        )

        responses = set()
        for _ in range(10):
            decision = await engine.process_message(context)
            responses.add(decision.clarification_question or decision.response_text)

        # All responses should be the same
        assert len(responses) == 1

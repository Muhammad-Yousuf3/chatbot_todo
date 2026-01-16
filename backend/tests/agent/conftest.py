"""Test fixtures for the agent module."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.agent.schemas import (
    DecisionContext,
    IntentType,
    Message,
    PendingAction,
    UserIntent,
)


@pytest.fixture
def sample_user_id() -> str:
    """Return a sample user ID for testing."""
    return "test-user-123"


@pytest.fixture
def sample_conversation_id() -> str:
    """Return a sample conversation ID for testing."""
    return str(uuid4())


@pytest.fixture
def empty_message_history() -> list[Message]:
    """Return an empty message history."""
    return []


@pytest.fixture
def sample_message_history() -> list[Message]:
    """Return a sample message history with a few messages."""
    return [
        Message(role="user", content="hello", timestamp=datetime.now()),
        Message(
            role="assistant",
            content="Hello! How can I help you with your tasks today?",
            timestamp=datetime.now(),
        ),
    ]


@pytest.fixture
def basic_decision_context(
    sample_user_id: str,
    sample_conversation_id: str,
    empty_message_history: list[Message],
) -> DecisionContext:
    """Return a basic decision context for testing."""
    return DecisionContext(
        user_id=sample_user_id,
        message="test message",
        conversation_id=sample_conversation_id,
        message_history=empty_message_history,
        pending_confirmation=None,
    )


@pytest.fixture
def context_with_pending_delete(
    sample_user_id: str,
    sample_conversation_id: str,
    empty_message_history: list[Message],
) -> DecisionContext:
    """Return a decision context with a pending delete confirmation."""
    pending = PendingAction(
        action_type=IntentType.DELETE_TASK,
        task_id=str(uuid4()),
        task_description="buy groceries",
        created_at=datetime.now(),
        expires_at=datetime.now(),
    )
    return DecisionContext(
        user_id=sample_user_id,
        message="yes",
        conversation_id=sample_conversation_id,
        message_history=empty_message_history,
        pending_confirmation=pending,
    )


@pytest.fixture
def create_task_intent() -> UserIntent:
    """Return a CREATE_TASK intent for testing."""
    return UserIntent(
        intent_type=IntentType.CREATE_TASK,
        confidence=0.95,
        extracted_params={"description": "buy groceries"},
    )


@pytest.fixture
def list_tasks_intent() -> UserIntent:
    """Return a LIST_TASKS intent for testing."""
    return UserIntent(
        intent_type=IntentType.LIST_TASKS,
        confidence=0.98,
        extracted_params=None,
    )


@pytest.fixture
def general_chat_intent() -> UserIntent:
    """Return a GENERAL_CHAT intent for testing."""
    return UserIntent(
        intent_type=IntentType.GENERAL_CHAT,
        confidence=0.90,
        extracted_params=None,
    )


@pytest.fixture
def ambiguous_intent() -> UserIntent:
    """Return an AMBIGUOUS intent for testing."""
    return UserIntent(
        intent_type=IntentType.AMBIGUOUS,
        confidence=0.40,
        extracted_params={"possible_intents": ["CREATE_TASK", "COMPLETE_TASK"]},
    )


@pytest.fixture
def sample_tasks() -> list[dict]:
    """Return a list of sample tasks for testing."""
    return [
        {
            "id": str(uuid4()),
            "user_id": "test-user-123",
            "description": "buy groceries",
            "completed": False,
        },
        {
            "id": str(uuid4()),
            "user_id": "test-user-123",
            "description": "call mom",
            "completed": False,
        },
        {
            "id": str(uuid4()),
            "user_id": "test-user-123",
            "description": "finish report",
            "completed": True,
        },
    ]

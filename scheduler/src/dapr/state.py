"""Dapr State Store operations for Scheduler service."""

import logging
from datetime import datetime
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from .client import get_dapr_service

logger = logging.getLogger(__name__)

# Default state store name
STATESTORE_NAME = "statestore"

# TTL for processed events (24 hours in seconds)
PROCESSED_EVENT_TTL = 86400

T = TypeVar("T", bound=BaseModel)


async def save_state(
    key: str,
    value: BaseModel,
    ttl_seconds: Optional[int] = None,
) -> bool:
    """Save state to Dapr State Store.

    Args:
        key: State key
        value: Pydantic model to serialize and store
        ttl_seconds: Optional TTL in seconds

    Returns:
        True if saved successfully, False otherwise
    """
    dapr = get_dapr_service()

    if not dapr.enabled:
        logger.debug(f"Dapr disabled, skipping state save for key: {key}")
        return False

    try:
        metadata = {}
        if ttl_seconds:
            metadata["ttlInSeconds"] = str(ttl_seconds)

        dapr.client.save_state(
            store_name=STATESTORE_NAME,
            key=key,
            value=value.model_dump_json(),
            state_metadata=metadata if metadata else None,
        )
        logger.debug(f"Saved state: {key}")
        return True
    except Exception as e:
        logger.error(f"Failed to save state for key {key}: {e}")
        return False


async def get_state(key: str, model_class: Type[T]) -> Optional[T]:
    """Get state from Dapr State Store.

    Args:
        key: State key
        model_class: Pydantic model class to deserialize into

    Returns:
        Deserialized model instance, or None if not found
    """
    dapr = get_dapr_service()

    if not dapr.enabled:
        logger.debug(f"Dapr disabled, cannot get state for key: {key}")
        return None

    try:
        response = dapr.client.get_state(
            store_name=STATESTORE_NAME,
            key=key,
        )

        if response.data:
            return model_class.model_validate_json(response.data)
        return None
    except Exception as e:
        logger.error(f"Failed to get state for key {key}: {e}")
        return None


async def delete_state(key: str) -> bool:
    """Delete state from Dapr State Store.

    Args:
        key: State key

    Returns:
        True if deleted successfully, False otherwise
    """
    dapr = get_dapr_service()

    if not dapr.enabled:
        logger.debug(f"Dapr disabled, cannot delete state for key: {key}")
        return False

    try:
        dapr.client.delete_state(
            store_name=STATESTORE_NAME,
            key=key,
        )
        logger.debug(f"Deleted state: {key}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete state for key {key}: {e}")
        return False


async def query_state_by_prefix(prefix: str) -> List[str]:
    """Query state keys by prefix using the registry.

    Uses the registry approach since Dapr state store doesn't have
    native prefix query support.

    Args:
        prefix: Key prefix to search for (e.g., "recurring", "reminder")

    Returns:
        List of full state keys matching the prefix
    """
    from src.state.schemas import (
        RECURRING_REGISTRY_KEY,
        REMINDER_REGISTRY_KEY,
        Registry,
        recurring_task_key,
        reminder_key,
    )

    dapr = get_dapr_service()

    if not dapr.enabled:
        logger.debug(f"Dapr disabled, cannot query state by prefix: {prefix}")
        return []

    try:
        # Determine registry key based on prefix
        if prefix == "recurring":
            registry_key = RECURRING_REGISTRY_KEY
            key_func = recurring_task_key
        elif prefix == "reminder":
            registry_key = REMINDER_REGISTRY_KEY
            key_func = reminder_key
        else:
            logger.warning(f"Unknown prefix for registry query: {prefix}")
            return []

        # Get the registry
        registry = await get_state(registry_key, Registry)
        if not registry:
            return []

        # Return full keys
        return [key_func(id) for id in registry.ids]
    except Exception as e:
        logger.error(f"Failed to query state by prefix {prefix}: {e}")
        return []


async def add_to_registry(registry_key: str, item_id: str) -> bool:
    """Add an item ID to a registry.

    Args:
        registry_key: The registry key (e.g., RECURRING_REGISTRY_KEY)
        item_id: The ID to add

    Returns:
        True if successful
    """
    from src.state.schemas import Registry

    dapr = get_dapr_service()

    if not dapr.enabled:
        logger.debug(f"Dapr disabled, cannot add to registry: {registry_key}")
        return False

    try:
        # Get current registry
        registry = await get_state(registry_key, Registry)
        if not registry:
            registry = Registry(ids=[])

        # Add ID if not already present
        if item_id not in registry.ids:
            registry.ids.append(item_id)
            return await save_state(registry_key, registry)
        return True
    except Exception as e:
        logger.error(f"Failed to add {item_id} to registry {registry_key}: {e}")
        return False


async def remove_from_registry(registry_key: str, item_id: str) -> bool:
    """Remove an item ID from a registry.

    Args:
        registry_key: The registry key
        item_id: The ID to remove

    Returns:
        True if successful
    """
    from src.state.schemas import Registry

    dapr = get_dapr_service()

    if not dapr.enabled:
        logger.debug(f"Dapr disabled, cannot remove from registry: {registry_key}")
        return False

    try:
        # Get current registry
        registry = await get_state(registry_key, Registry)
        if not registry:
            return True  # Nothing to remove

        # Remove ID if present
        if item_id in registry.ids:
            registry.ids.remove(item_id)
            return await save_state(registry_key, registry)
        return True
    except Exception as e:
        logger.error(f"Failed to remove {item_id} from registry {registry_key}: {e}")
        return False


async def is_event_processed(service: str, event_id: str) -> bool:
    """Check if an event has already been processed (idempotency check).

    Args:
        service: Service name (e.g., "scheduler")
        event_id: Event ID to check

    Returns:
        True if event was already processed
    """
    from src.state.schemas import ProcessedEventState, processed_event_key

    key = processed_event_key(service, event_id)
    state = await get_state(key, ProcessedEventState)
    return state is not None


async def mark_event_processed(service: str, event_id: str, event_type: str) -> bool:
    """Mark an event as processed (for idempotency).

    Args:
        service: Service name (e.g., "scheduler")
        event_id: Event ID
        event_type: Event type string

    Returns:
        True if marked successfully
    """
    from src.state.schemas import ProcessedEventState, processed_event_key

    key = processed_event_key(service, event_id)
    state = ProcessedEventState(
        event_id=event_id,
        event_type=event_type,
        processed_at=datetime.utcnow(),
    )
    return await save_state(key, state, ttl_seconds=PROCESSED_EVENT_TTL)

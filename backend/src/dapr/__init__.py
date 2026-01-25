"""Dapr integration module for Backend service."""

from .client import DaprService, get_dapr_service, is_dapr_enabled
from .secrets import get_secret

__all__ = [
    "DaprService",
    "get_dapr_service",
    "get_secret",
    "is_dapr_enabled",
]

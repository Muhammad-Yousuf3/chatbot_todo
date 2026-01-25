"""Dapr client wrapper for Scheduler service."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global service instance
_dapr_service: Optional["DaprService"] = None


def is_dapr_enabled() -> bool:
    """Check if Dapr sidecar is available."""
    return os.getenv("DAPR_HTTP_PORT") is not None


class DaprService:
    """Wrapper for Dapr client with graceful fallback."""

    def __init__(self):
        self._client = None
        self._enabled = is_dapr_enabled()

        if self._enabled:
            try:
                from dapr.clients import DaprClient
                self._client = DaprClient()
                logger.info("Dapr client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Dapr client: {e}")
                self._enabled = False
        else:
            logger.info("Dapr sidecar not detected, running in non-Dapr mode")

    @property
    def enabled(self) -> bool:
        """Check if Dapr is enabled and client is available."""
        return self._enabled and self._client is not None

    @property
    def client(self):
        """Get the underlying Dapr client."""
        return self._client

    def check_health(self) -> dict:
        """Check Dapr sidecar health and connectivity.

        Returns:
            Dictionary with health status information
        """
        health = {
            "dapr_enabled": self._enabled,
            "dapr_client_initialized": self._client is not None,
            "dapr_sidecar_detected": is_dapr_enabled(),
        }

        if self._enabled and self._client:
            try:
                # Try to get metadata to verify connectivity
                metadata = self._client.get_metadata()
                health["dapr_sidecar_healthy"] = True
                health["dapr_app_id"] = metadata.application_id if metadata else None
            except Exception as e:
                health["dapr_sidecar_healthy"] = False
                health["dapr_error"] = str(e)
        else:
            health["dapr_sidecar_healthy"] = False

        return health

    async def close(self):
        """Clean up Dapr client resources."""
        if self._client:
            self._client = None
            logger.info("Dapr client closed")


def get_dapr_service() -> DaprService:
    """Get or create the global Dapr service instance."""
    global _dapr_service
    if _dapr_service is None:
        _dapr_service = DaprService()
    return _dapr_service


async def close_dapr_service():
    """Close the Dapr service on shutdown."""
    global _dapr_service
    if _dapr_service:
        await _dapr_service.close()
        _dapr_service = None

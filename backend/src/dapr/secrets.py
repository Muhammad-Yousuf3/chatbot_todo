"""Dapr secrets retrieval helper."""

import logging
import os
from typing import Optional

from .client import get_dapr_service

logger = logging.getLogger(__name__)

# Dapr secrets store name
SECRETS_STORE_NAME = "kubernetes-secrets"
SECRETS_KEY = "app-secrets"


async def get_secret(key: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
    """Retrieve a secret from Dapr Secrets Store with environment variable fallback.

    Args:
        key: The secret key within the secrets store (e.g., "jwt-secret", "database-url")
        fallback_env_var: Environment variable name to use if Dapr is not available

    Returns:
        The secret value, or None if not found
    """
    dapr = get_dapr_service()

    if dapr.enabled:
        try:
            secret = dapr.client.get_secret(
                store_name=SECRETS_STORE_NAME,
                key=SECRETS_KEY,
            )
            if secret and secret.secret:
                value = secret.secret.get(key)
                if value:
                    logger.debug(f"Retrieved secret '{key}' from Dapr")
                    return value
        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{key}' from Dapr: {e}")

    # Fallback to environment variable
    if fallback_env_var:
        value = os.getenv(fallback_env_var)
        if value:
            logger.debug(f"Using fallback env var '{fallback_env_var}' for secret '{key}'")
            return value

    # Direct environment variable lookup with common naming conventions
    env_key = key.upper().replace("-", "_")
    value = os.getenv(env_key)
    if value:
        logger.debug(f"Using env var '{env_key}' for secret '{key}'")
        return value

    logger.warning(f"Secret '{key}' not found in Dapr or environment")
    return None


async def get_jwt_secret() -> Optional[str]:
    """Get the JWT signing secret."""
    return await get_secret("jwt-secret", fallback_env_var="JWT_SECRET")


async def get_database_url() -> Optional[str]:
    """Get the database connection URL."""
    return await get_secret("database-url", fallback_env_var="DATABASE_URL")

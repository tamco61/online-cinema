"""Push providers package"""

import logging
from app.core.config import settings
from app.providers.push.base import PushProvider
from app.providers.push.fcm import FcmPushProvider
from app.providers.push.console import ConsolePushProvider

logger = logging.getLogger(__name__)


def get_push_provider() -> PushProvider:
    """
    Factory function to get push provider based on configuration

    Returns:
        PushProvider instance
    """
    provider_type = settings.PUSH_PROVIDER.lower()

    if provider_type == "fcm":
        logger.info("Using FCM push provider")
        return FcmPushProvider()

    elif provider_type == "console":
        logger.info("Using Console push provider (dev mode)")
        return ConsolePushProvider()

    else:
        logger.warning(f"Unknown push provider: {provider_type}, falling back to console")
        return ConsolePushProvider()


__all__ = [
    "PushProvider",
    "FcmPushProvider",
    "ConsolePushProvider",
    "get_push_provider",
]

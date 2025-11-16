"""
Console Push Provider

Prints push notifications to console for testing
"""

import logging
from typing import List

from app.providers.push.base import PushProvider, PushNotification, PushResponse

logger = logging.getLogger(__name__)


class ConsolePushProvider(PushProvider):
    """
    Console push provider

    Prints push notifications to console instead of sending them
    Useful for development and testing
    """

    async def send_push(self, notification: PushNotification) -> PushResponse:
        """Print push notification to console"""
        try:
            logger.info("=" * 80)
            logger.info("📱 CONSOLE PUSH NOTIFICATION")
            logger.info("=" * 80)
            logger.info(f"Title: {notification.title}")
            logger.info(f"Body: {notification.body}")
            logger.info(f"Recipients: {len(notification.recipients)}")

            for recipient in notification.recipients:
                logger.info(f"  - User: {recipient.user_id}, Token: {recipient.device_token[:20]}...")

            if notification.data:
                logger.info(f"Data: {notification.data}")

            if notification.icon:
                logger.info(f"Icon: {notification.icon}")

            if notification.image:
                logger.info(f"Image: {notification.image}")

            if notification.click_action:
                logger.info(f"Click Action: {notification.click_action}")

            logger.info(f"Priority: {notification.priority}")
            logger.info(f"Sound: {notification.sound}")

            if notification.badge:
                logger.info(f"Badge: {notification.badge}")

            if notification.ttl:
                logger.info(f"TTL: {notification.ttl}s")

            logger.info("=" * 80)

            return PushResponse(
                success=True,
                message_id=f"console-push-{hash(notification.title)}"
            )

        except Exception as e:
            error_msg = f"Console push error: {e}"
            logger.error(error_msg)

            return PushResponse(
                success=False,
                error=error_msg
            )

    async def send_bulk_push(self, notifications: List[PushNotification]) -> List[PushResponse]:
        """Print multiple push notifications to console"""
        responses = []
        for notification in notifications:
            response = await self.send_push(notification)
            responses.append(response)
        return responses

    def validate_configuration(self) -> bool:
        """Console provider always valid"""
        return True

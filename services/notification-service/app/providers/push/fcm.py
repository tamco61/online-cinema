"""
Firebase Cloud Messaging Push Provider

Implementation using Firebase Cloud Messaging
"""

import logging
from typing import List
import httpx

from app.providers.push.base import PushProvider, PushNotification, PushResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class FcmPushProvider(PushProvider):
    """
    Firebase Cloud Messaging push provider

    Uses Firebase Cloud Messaging HTTP v1 API

    Installation:
        pip install firebase-admin

    Setup:
        1. Create Firebase project
        2. Download service account JSON
        3. Set FCM_CREDENTIALS_PATH in .env
    """

    def __init__(self):
        self.server_key = settings.FCM_SERVER_KEY
        self.project_id = settings.FCM_PROJECT_ID
        self.credentials_path = settings.FCM_CREDENTIALS_PATH
        self.fcm_app = None

    def _initialize_fcm(self):
        """Initialize Firebase Admin SDK"""
        if self.fcm_app is None:
            try:
                import firebase_admin
                from firebase_admin import credentials

                # Initialize Firebase app
                if self.credentials_path:
                    cred = credentials.Certificate(self.credentials_path)
                    self.fcm_app = firebase_admin.initialize_app(cred)
                    logger.info("✅ Firebase Admin SDK initialized")
                else:
                    logger.warning("FCM credentials path not configured")

            except ImportError:
                logger.error("firebase-admin not installed. Run: pip install firebase-admin")
            except Exception as e:
                logger.error(f"Error initializing Firebase: {e}")

    async def send_push(self, notification: PushNotification) -> PushResponse:
        """
        Send push notification via FCM

        FCM HTTP v1 API:
        https://firebase.google.com/docs/cloud-messaging/send-message
        """
        try:
            # For now, using legacy HTTP API (simpler, but deprecated)
            # In production, use Firebase Admin SDK

            if not self.server_key:
                logger.warning("FCM server key not configured, simulating push")
                return self._simulate_push(notification)

            # Prepare FCM payload
            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }

            # Send to each recipient
            responses = []
            for recipient in notification.recipients:
                payload = {
                    "to": recipient.device_token,
                    "notification": {
                        "title": notification.title,
                        "body": notification.body,
                        "icon": notification.icon,
                        "sound": notification.sound,
                        "click_action": notification.click_action,
                    },
                    "data": notification.data or {},
                    "priority": notification.priority
                }

                if notification.image:
                    payload["notification"]["image"] = notification.image

                if notification.badge:
                    payload["notification"]["badge"] = notification.badge

                if notification.ttl:
                    payload["time_to_live"] = notification.ttl

                # Send via legacy FCM API
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://fcm.googleapis.com/fcm/send",
                        json=payload,
                        headers=headers,
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success") == 1:
                            message_id = result.get("results", [{}])[0].get("message_id")
                            logger.info(f"✅ Push sent via FCM: {message_id}")

                            return PushResponse(
                                success=True,
                                message_id=message_id
                            )
                        else:
                            error = result.get("results", [{}])[0].get("error", "Unknown error")
                            logger.error(f"FCM error: {error}")

                            return PushResponse(
                                success=False,
                                error=error
                            )
                    else:
                        error_msg = f"FCM HTTP error: {response.status_code} - {response.text}"
                        logger.error(error_msg)

                        return PushResponse(
                            success=False,
                            error=error_msg
                        )

        except Exception as e:
            error_msg = f"FCM exception: {e}"
            logger.error(error_msg)

            return PushResponse(
                success=False,
                error=error_msg
            )

    async def send_bulk_push(self, notifications: List[PushNotification]) -> List[PushResponse]:
        """Send multiple push notifications"""
        responses = []
        for notification in notifications:
            response = await self.send_push(notification)
            responses.append(response)
        return responses

    def validate_configuration(self) -> bool:
        """Validate FCM configuration"""
        if not self.server_key and not self.credentials_path:
            logger.error("FCM server key or credentials path not configured")
            return False

        return True

    def _simulate_push(self, notification: PushNotification) -> PushResponse:
        """Simulate push notification (for testing)"""
        logger.info("=" * 80)
        logger.info("📱 FCM PUSH NOTIFICATION (SIMULATED)")
        logger.info("=" * 80)
        logger.info(f"Title: {notification.title}")
        logger.info(f"Body: {notification.body}")
        logger.info(f"Recipients: {len(notification.recipients)}")

        for recipient in notification.recipients:
            logger.info(f"  - Token: {recipient.device_token[:20]}...")

        if notification.data:
            logger.info(f"Data: {notification.data}")

        if notification.icon:
            logger.info(f"Icon: {notification.icon}")

        if notification.image:
            logger.info(f"Image: {notification.image}")

        logger.info("=" * 80)

        return PushResponse(
            success=True,
            message_id=f"fcm-simulated-{hash(notification.title)}"
        )

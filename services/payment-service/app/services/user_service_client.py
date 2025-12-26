"""
User Service Client

Интеграция с user-service для обновления статуса подписки пользователя
"""

import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)


class UserServiceClient:
    """
    Client for user-service integration

    Updates user subscription status after successful payment
    """

    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.api_key = settings.USER_SERVICE_API_KEY
        self.timeout = 10.0

    def _get_headers(self) -> dict:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    async def update_subscription(
        self,
        user_id: UUID,
        plan_id: str,
        duration_days: int,
        payment_id: UUID
    ) -> bool:
        """
        Update user subscription in user-service

        Args:
            user_id: User UUID
            plan_id: Subscription plan ID
            duration_days: Subscription duration in days
            payment_id: Payment UUID for reference

        Returns:
            True if successful

        Endpoint:
            POST /api/v1/users/{user_id}/subscription

        Request:
            {
                "plan_id": "premium",
                "duration_days": 30,
                "payment_id": "uuid",
                "activated_at": "2024-11-16T10:00:00Z",
                "expires_at": "2024-12-16T10:00:00Z"
            }
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/subscription"

            activated_at = datetime.utcnow()
            expires_at = activated_at + timedelta(days=duration_days)

            payload = {
                "plan_id": plan_id,
                "duration_days": duration_days,
                "payment_id": str(payment_id),
                "activated_at": activated_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "auto_renew": True,
                "status": "active"
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✅ Updated subscription for user {user_id}: {plan_id}")
                    return True
                else:
                    logger.error(
                        f"❌ Failed to update subscription: {response.status_code} - {response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"❌ Timeout updating subscription for user {user_id}")
            return False

        except Exception as e:
            logger.error(f"❌ Error updating subscription: {e}")
            return False

    async def cancel_subscription(self, user_id: UUID, payment_id: UUID) -> bool:
        """
        Cancel user subscription

        Args:
            user_id: User UUID
            payment_id: Payment UUID for reference

        Returns:
            True if successful

        Endpoint:
            DELETE /api/v1/users/{user_id}/subscription
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/subscription"

            params = {"payment_id": str(payment_id)}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    url,
                    params=params,
                    headers=self._get_headers()
                )

                if response.status_code in [200, 204]:
                    logger.info(f"✅ Cancelled subscription for user {user_id}")
                    return True
                else:
                    logger.error(
                        f"❌ Failed to cancel subscription: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Error cancelling subscription: {e}")
            return False

    async def get_user_subscription(self, user_id: UUID) -> Optional[dict]:
        """
        Get user subscription details

        Args:
            user_id: User UUID

        Returns:
            Subscription details or None

        Endpoint:
            GET /api/v1/users/{user_id}/subscription
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/subscription"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.info(f"No subscription found for user {user_id}")
                    return None
                else:
                    logger.error(
                        f"❌ Failed to get subscription: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"❌ Error getting subscription: {e}")
            return None

    async def notify_payment_event(
        self,
        user_id: UUID,
        event_type: str,
        payment_id: UUID,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Send payment event notification to user-service

        Alternative to direct subscription update - use event-driven approach

        Args:
            user_id: User UUID
            event_type: Event type (payment.succeeded, payment.failed, payment.refunded)
            payment_id: Payment UUID
            metadata: Additional metadata

        Returns:
            True if successful

        Endpoint:
            POST /api/v1/events/payment

        This can be replaced with Kafka event publishing:
        producer.send('payment.events', {
            "event_type": event_type,
            "user_id": str(user_id),
            "payment_id": str(payment_id),
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        })
        """
        try:
            url = f"{self.base_url}/api/v1/events/payment"

            payload = {
                "event_type": event_type,
                "user_id": str(user_id),
                "payment_id": str(payment_id),
                "payment_metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )

                if response.status_code in [200, 201, 202]:
                    logger.info(f"✅ Sent payment event: {event_type} for user {user_id}")
                    return True
                else:
                    logger.error(
                        f"❌ Failed to send payment event: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Error sending payment event: {e}")
            return False


# Global user service client instance
user_service_client = UserServiceClient()


def get_user_service_client() -> UserServiceClient:
    """Dependency to get user service client"""
    return user_service_client

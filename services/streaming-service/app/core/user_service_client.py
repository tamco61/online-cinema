import httpx
from app.core.config import settings
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class UserServiceClient:
    """HTTP client for user-service integration"""

    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = settings.USER_SERVICE_TIMEOUT

    async def check_active_subscription(self, user_id: str, access_token: str) -> bool:
        """
        Check if user has active subscription

        Args:
            user_id: User UUID
            access_token: JWT access token

        Returns:
            True if user has active subscription, False otherwise
        """
        # Try cache first
        cached_subscription = await cache.get_cached_subscription(user_id)

        if cached_subscription is not None:
            return cached_subscription.get("is_active", False)

        # Fetch from user-service
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/subscriptions/current",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Cache the result
                    subscription_data = {
                        "is_active": data.get("is_active", False),
                        "plan_id": data.get("plan_id"),
                        "expires_at": data.get("expires_at")
                    }

                    await cache.cache_subscription(user_id, subscription_data)

                    return subscription_data["is_active"]

                elif response.status_code == 404:
                    # No subscription found
                    logger.warning(f"No subscription found for user: {user_id}")

                    # Cache negative result
                    await cache.cache_subscription(user_id, {"is_active": False})

                    return False

                else:
                    logger.error(f"Error checking subscription: {response.status_code} - {response.text}")
                    return False

        except httpx.RequestError as e:
            logger.error(f"Request error to user-service: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error checking subscription: {e}")
            return False

    async def get_user_profile(self, access_token: str) -> dict | None:
        """
        Get user profile from user-service

        Args:
            access_token: JWT access token

        Returns:
            User profile dict or None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/profiles/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code == 200:
                    return response.json()

                return None

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None


# Global client instance
user_service_client = UserServiceClient()


def get_user_service_client() -> UserServiceClient:
    """Dependency to get user service client"""
    return user_service_client

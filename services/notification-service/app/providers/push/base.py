"""
Base Push Provider

Abstract interface for push notification providers
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PushRecipient:
    """Push notification recipient"""
    device_token: str
    user_id: Optional[str] = None


@dataclass
class PushNotification:
    """Push notification message"""
    title: str
    body: str
    recipients: List[PushRecipient]
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    click_action: Optional[str] = None
    sound: Optional[str] = "default"
    badge: Optional[int] = None
    priority: str = "high"  # high, normal
    ttl: Optional[int] = None  # Time to live in seconds


@dataclass
class PushResponse:
    """Push notification send response"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    failed_tokens: Optional[List[str]] = None


class PushProvider(ABC):
    """
    Abstract push notification provider interface

    All push providers must implement this interface
    """

    @abstractmethod
    async def send_push(self, notification: PushNotification) -> PushResponse:
        """
        Send push notification

        Args:
            notification: Push notification to send

        Returns:
            PushResponse with status and message ID
        """
        pass

    @abstractmethod
    async def send_bulk_push(self, notifications: List[PushNotification]) -> List[PushResponse]:
        """
        Send multiple push notifications

        Args:
            notifications: List of push notifications

        Returns:
            List of PushResponse
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate provider configuration

        Returns:
            True if configuration is valid
        """
        pass

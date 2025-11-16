"""
Base Email Provider

Abstract interface for email providers
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class EmailRecipient:
    """Email recipient"""
    email: str
    name: Optional[str] = None


@dataclass
class EmailMessage:
    """Email message"""
    subject: str
    to: List[EmailRecipient]
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[EmailRecipient]] = None
    bcc: Optional[List[EmailRecipient]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


@dataclass
class EmailResponse:
    """Email send response"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    """
    Abstract email provider interface

    All email providers must implement this interface
    """

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailResponse:
        """
        Send email

        Args:
            message: Email message to send

        Returns:
            EmailResponse with status and message ID
        """
        pass

    @abstractmethod
    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """
        Send multiple emails

        Args:
            messages: List of email messages

        Returns:
            List of EmailResponse
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

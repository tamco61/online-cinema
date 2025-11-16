"""Email providers package"""

import logging
from app.core.config import settings
from app.providers.email.base import EmailProvider
from app.providers.email.sendgrid import SendGridEmailProvider
from app.providers.email.aws_ses import AwsSesEmailProvider
from app.providers.email.console import ConsoleEmailProvider

logger = logging.getLogger(__name__)


def get_email_provider() -> EmailProvider:
    """
    Factory function to get email provider based on configuration

    Returns:
        EmailProvider instance
    """
    provider_type = settings.EMAIL_PROVIDER.lower()

    if provider_type == "sendgrid":
        logger.info("Using SendGrid email provider")
        return SendGridEmailProvider()

    elif provider_type == "aws_ses":
        logger.info("Using AWS SES email provider")
        return AwsSesEmailProvider()

    elif provider_type == "console":
        logger.info("Using Console email provider (dev mode)")
        return ConsoleEmailProvider()

    else:
        logger.warning(f"Unknown email provider: {provider_type}, falling back to console")
        return ConsoleEmailProvider()


__all__ = [
    "EmailProvider",
    "SendGridEmailProvider",
    "AwsSesEmailProvider",
    "ConsoleEmailProvider",
    "get_email_provider",
]

"""
Console Email Provider

Prints emails to console for testing
"""

import logging
from typing import List

from app.providers.email.base import EmailProvider, EmailMessage, EmailResponse

logger = logging.getLogger(__name__)


class ConsoleEmailProvider(EmailProvider):
    """
    Console email provider

    Prints emails to console instead of sending them
    Useful for development and testing
    """

    async def send_email(self, message: EmailMessage) -> EmailResponse:
        """Print email to console"""
        try:
            logger.info("=" * 80)
            logger.info("📧 CONSOLE EMAIL")
            logger.info("=" * 80)
            logger.info(f"From: {message.from_name} <{message.from_email}>")
            logger.info(f"To: {', '.join([f'{r.name} <{r.email}>' for r in message.to])}")

            if message.cc:
                logger.info(f"CC: {', '.join([f'{r.name} <{r.email}>' for r in message.cc])}")

            if message.bcc:
                logger.info(f"BCC: {', '.join([f'{r.name} <{r.email}>' for r in message.bcc])}")

            logger.info(f"Subject: {message.subject}")
            logger.info("-" * 80)

            if message.html_body:
                logger.info("HTML Body:")
                logger.info(message.html_body)

            if message.text_body:
                logger.info("Text Body:")
                logger.info(message.text_body)

            if message.template_id:
                logger.info(f"Template ID: {message.template_id}")
                logger.info(f"Template Data: {message.template_data}")

            logger.info("=" * 80)

            return EmailResponse(
                success=True,
                message_id=f"console-{hash(message.subject)}"
            )

        except Exception as e:
            error_msg = f"Console email error: {e}"
            logger.error(error_msg)

            return EmailResponse(
                success=False,
                error=error_msg
            )

    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """Print multiple emails to console"""
        responses = []
        for message in messages:
            response = await self.send_email(message)
            responses.append(response)
        return responses

    def validate_configuration(self) -> bool:
        """Console provider always valid"""
        return True

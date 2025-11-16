"""
AWS SES Email Provider

Implementation using AWS Simple Email Service
"""

import logging
from typing import List

from app.providers.email.base import EmailProvider, EmailMessage, EmailResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class AwsSesEmailProvider(EmailProvider):
    """
    AWS SES email provider

    Uses boto3 to send emails via AWS SES

    Installation:
        pip install boto3
    """

    def __init__(self):
        self.region = settings.AWS_SES_REGION
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME
        self.client = None

    def _get_client(self):
        """Get or create SES client"""
        if self.client is None:
            try:
                import boto3

                self.client = boto3.client(
                    'ses',
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
            except ImportError:
                logger.error("boto3 not installed. Run: pip install boto3")
                raise

        return self.client

    async def send_email(self, message: EmailMessage) -> EmailResponse:
        """Send email via AWS SES"""
        try:
            client = self._get_client()

            # Prepare email
            from_address = message.from_email or self.from_email
            if message.from_name or self.from_name:
                from_address = f"{message.from_name or self.from_name} <{from_address}>"

            # Destination
            destination = {
                'ToAddresses': [r.email for r in message.to]
            }

            if message.cc:
                destination['CcAddresses'] = [r.email for r in message.cc]

            if message.bcc:
                destination['BccAddresses'] = [r.email for r in message.bcc]

            # Message body
            body = {}
            if message.html_body:
                body['Html'] = {
                    'Charset': 'UTF-8',
                    'Data': message.html_body
                }

            if message.text_body:
                body['Text'] = {
                    'Charset': 'UTF-8',
                    'Data': message.text_body
                }

            # Send email
            response = client.send_email(
                Source=from_address,
                Destination=destination,
                Message={
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': message.subject
                    },
                    'Body': body
                },
                ReplyToAddresses=[message.reply_to] if message.reply_to else []
            )

            message_id = response.get('MessageId')
            logger.info(f"✅ Email sent via AWS SES: {message_id}")

            return EmailResponse(
                success=True,
                message_id=message_id
            )

        except Exception as e:
            error_msg = f"AWS SES exception: {e}"
            logger.error(error_msg)

            return EmailResponse(
                success=False,
                error=error_msg
            )

    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        """Send multiple emails"""
        responses = []
        for message in messages:
            response = await self.send_email(message)
            responses.append(response)
        return responses

    def validate_configuration(self) -> bool:
        """Validate AWS SES configuration"""
        if not self.region:
            logger.error("AWS SES region not configured")
            return False

        if not self.from_email:
            logger.error("From email not configured")
            return False

        return True

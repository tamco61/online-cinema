"""
SendGrid Email Provider

Implementation using SendGrid API
"""

import httpx
import logging
from typing import List

from app.providers.email.base import EmailProvider, EmailMessage, EmailResponse, EmailRecipient
from app.core.config import settings

logger = logging.getLogger(__name__)


class SendGridEmailProvider(EmailProvider):
    """
    SendGrid email provider

    Uses SendGrid Web API v3
    https://docs.sendgrid.com/api-reference/mail-send/mail-send
    """

    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.api_url = "https://api.sendgrid.com/v3/mail/send"
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME

    async def send_email(self, message: EmailMessage) -> EmailResponse:
        """Send email via SendGrid"""
        try:
            # Prepare request payload
            payload = self._prepare_payload(message)

            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )

                if response.status_code == 202:
                    # SendGrid returns 202 Accepted on success
                    message_id = response.headers.get("X-Message-Id", "unknown")
                    logger.info(f"✅ Email sent via SendGrid: {message_id}")

                    return EmailResponse(
                        success=True,
                        message_id=message_id
                    )
                else:
                    error_msg = f"SendGrid error: {response.status_code} - {response.text}"
                    logger.error(error_msg)

                    return EmailResponse(
                        success=False,
                        error=error_msg
                    )

        except Exception as e:
            error_msg = f"SendGrid exception: {e}"
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
        """Validate SendGrid configuration"""
        if not self.api_key:
            logger.error("SendGrid API key not configured")
            return False

        if not self.from_email:
            logger.error("From email not configured")
            return False

        return True

    def _prepare_payload(self, message: EmailMessage) -> dict:
        """
        Prepare SendGrid API payload

        SendGrid API format:
        {
          "personalizations": [
            {
              "to": [{"email": "recipient@example.com", "name": "Recipient Name"}],
              "subject": "Subject"
            }
          ],
          "from": {"email": "sender@example.com", "name": "Sender Name"},
          "content": [
            {"type": "text/html", "value": "<html>...</html>"}
          ]
        }
        """
        payload = {
            "personalizations": [
                {
                    "to": [
                        {"email": r.email, "name": r.name or r.email}
                        for r in message.to
                    ],
                    "subject": message.subject
                }
            ],
            "from": {
                "email": message.from_email or self.from_email,
                "name": message.from_name or self.from_name
            },
            "content": []
        }

        # Add content
        if message.html_body:
            payload["content"].append({
                "type": "text/html",
                "value": message.html_body
            })

        if message.text_body:
            payload["content"].append({
                "type": "text/plain",
                "value": message.text_body
            })

        # Add reply-to
        if message.reply_to:
            payload["reply_to"] = {"email": message.reply_to}

        # Add CC
        if message.cc:
            payload["personalizations"][0]["cc"] = [
                {"email": r.email, "name": r.name or r.email}
                for r in message.cc
            ]

        # Add BCC
        if message.bcc:
            payload["personalizations"][0]["bcc"] = [
                {"email": r.email, "name": r.name or r.email}
                for r in message.bcc
            ]

        # Template support
        if message.template_id:
            payload["template_id"] = message.template_id
            if message.template_data:
                payload["personalizations"][0]["dynamic_template_data"] = message.template_data

        return payload

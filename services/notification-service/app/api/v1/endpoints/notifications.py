"""
Notification API endpoints

Admin endpoints for testing notifications
"""

from fastapi import APIRouter, HTTPException
import logging

from app.schemas.notification import (
    TestEmailRequest,
    TestPushRequest,
    NotificationResponse
)
from app.providers.email import get_email_provider
from app.providers.email.base import EmailMessage, EmailRecipient
from app.providers.push import get_push_provider
from app.providers.push.base import PushNotification, PushRecipient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/test-email", response_model=NotificationResponse)
async def send_test_email(request: TestEmailRequest):
    """
    Send test email

    **Admin endpoint** for testing email provider configuration

    **Request:**
    ```json
    {
        "to_email": "user@example.com",
        "to_name": "John Doe",
        "subject": "Test Email",
        "body": "<h1>Hello!</h1><p>This is a test.</p>"
    }
    ```

    **Response:**
    ```json
    {
        "success": true,
        "message": "Email sent successfully",
        "message_id": "msg-12345"
    }
    ```

    **Example:**
    ```bash
    curl -X POST http://localhost:8008/api/v1/notifications/test-email \\
      -H "Content-Type: application/json" \\
      -d '{
        "to_email": "user@example.com",
        "subject": "Test",
        "body": "<h1>Test Email</h1>"
      }'
    ```
    """
    try:
        # Get email provider
        email_provider = get_email_provider()

        # Create email message
        message = EmailMessage(
            subject=request.subject,
            to=[EmailRecipient(email=request.to_email, name=request.to_name)],
            html_body=request.body
        )

        # Send email
        response = await email_provider.send_email(message)

        if response.success:
            logger.info(f"✅ Test email sent to {request.to_email}")
            return NotificationResponse(
                success=True,
                message="Email sent successfully",
                message_id=response.message_id
            )
        else:
            logger.error(f"❌ Failed to send test email: {response.error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {response.error}"
            )

    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-push", response_model=NotificationResponse)
async def send_test_push(request: TestPushRequest):
    """
    Send test push notification

    **Admin endpoint** for testing push provider configuration

    **Request:**
    ```json
    {
        "device_token": "fcm-token",
        "title": "Test Notification",
        "body": "This is a test",
        "data": {"key": "value"}
    }
    ```

    **Response:**
    ```json
    {
        "success": true,
        "message": "Push notification sent successfully",
        "message_id": "fcm-12345"
    }
    ```

    **Example:**
    ```bash
    curl -X POST http://localhost:8008/api/v1/notifications/test-push \\
      -H "Content-Type: application/json" \\
      -d '{
        "device_token": "your-fcm-token",
        "title": "Test",
        "body": "Test push"
      }'
    ```
    """
    try:
        # Get push provider
        push_provider = get_push_provider()

        # Create push notification
        notification = PushNotification(
            title=request.title,
            body=request.body,
            recipients=[PushRecipient(device_token=request.device_token)],
            data=request.data
        )

        # Send push
        response = await push_provider.send_push(notification)

        if response.success:
            logger.info(f"✅ Test push sent")
            return NotificationResponse(
                success=True,
                message="Push notification sent successfully",
                message_id=response.message_id
            )
        else:
            logger.error(f"❌ Failed to send test push: {response.error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send push: {response.error}"
            )

    except Exception as e:
        logger.error(f"Error sending test push: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_providers():
    """
    Get configured notification providers

    **Returns:** Information about configured email and push providers

    **Example:**
    ```bash
    curl http://localhost:8008/api/v1/notifications/providers
    ```
    """
    from app.core.config import settings

    email_provider = get_email_provider()
    push_provider = get_push_provider()

    return {
        "email": {
            "provider": settings.EMAIL_PROVIDER,
            "configured": email_provider.validate_configuration(),
            "enabled": settings.ENABLE_EMAIL_NOTIFICATIONS
        },
        "push": {
            "provider": settings.PUSH_PROVIDER,
            "configured": push_provider.validate_configuration(),
            "enabled": settings.ENABLE_PUSH_NOTIFICATIONS
        },
        "kafka": {
            "enabled": settings.ENABLE_KAFKA,
            "topics": [
                settings.KAFKA_TOPIC_USER_EVENTS,
                settings.KAFKA_TOPIC_CATALOG_EVENTS,
                settings.KAFKA_TOPIC_RECOMMENDATION_EVENTS
            ]
        }
    }

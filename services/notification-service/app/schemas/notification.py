"""Notification schemas"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


class TestEmailRequest(BaseModel):
    """Request to send test email"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    to_name: Optional[str] = Field(None, description="Recipient name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (HTML)")

    class Config:
        json_schema_extra = {
            "example": {
                "to_email": "user@example.com",
                "to_name": "John Doe",
                "subject": "Test Email",
                "body": "<h1>Hello!</h1><p>This is a test email.</p>"
            }
        }


class TestPushRequest(BaseModel):
    """Request to send test push notification"""
    device_token: str = Field(..., description="Device FCM token")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")

    class Config:
        json_schema_extra = {
            "example": {
                "device_token": "fcm-device-token-here",
                "title": "Test Notification",
                "body": "This is a test push notification",
                "data": {"type": "test", "key": "value"}
            }
        }


class NotificationResponse(BaseModel):
    """Generic notification response"""
    success: bool
    message: str
    message_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Notification sent successfully",
                "message_id": "msg-12345"
            }
        }

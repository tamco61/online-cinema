"""
YooMoney Webhook Handler

Processes webhooks from YooMoney payment provider
"""

import logging
from typing import Dict, Any
from fastapi import Request, HTTPException

from app.services.payment_service import PaymentService
from app.services.yoomoney_client import YooMoneyClient

logger = logging.getLogger(__name__)


class YooMoneyWebhookHandler:
    """
    YooMoney webhook handler

    Supported events:
    - payment.succeeded - Payment succeeded
    - payment.canceled - Payment cancelled
    - refund.succeeded - Refund succeeded
    """

    def __init__(self, payment_service: PaymentService, yoomoney_client: YooMoneyClient):
        self.payment_service = payment_service
        self.yoomoney = yoomoney_client

    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Handle YooMoney webhook

        Args:
            request: FastAPI Request object

        Returns:
            Response dict

        Steps:
            1. Verify webhook signature
            2. Parse webhook data
            3. Route to appropriate handler
            4. Return response
        """
        try:
            # 1. Get raw body for signature verification
            raw_body = await request.body()

            # Get signature from headers
            signature = request.headers.get("X-YooKassa-Signature", "")

            # Verify signature
            if not self.yoomoney.verify_webhook_signature(raw_body, signature):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=400, detail="Invalid signature")

            # 2. Parse webhook data
            webhook_data = await request.json()

            event_type = webhook_data.get("event")
            payment_object = webhook_data.get("object", {})

            logger.info(f"📨 Received webhook: {event_type}")

            # 3. Route to handler
            if event_type == "payment.succeeded":
                await self._handle_payment_succeeded(payment_object)

            elif event_type == "payment.canceled":
                await self._handle_payment_cancelled(payment_object)

            elif event_type == "refund.succeeded":
                await self._handle_refund_succeeded(payment_object)

            else:
                logger.warning(f"Unknown webhook event: {event_type}")

            # 4. Return success response
            return {"success": True, "message": "Webhook processed"}

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"❌ Error handling webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def _handle_payment_succeeded(self, payment_data: dict):
        """
        Handle payment.succeeded event

        Args:
            payment_data: Payment object from webhook

        Example payment_data:
        {
            "id": "2d8b8b7a-000f-5000-9000-1b7e3f9e0e9f",
            "status": "succeeded",
            "paid": true,
            "amount": {
                "value": "599.00",
                "currency": "RUB"
            },
            "metadata": {
                "payment_id": "uuid",
                "user_id": "uuid"
            }
        }
        """
        try:
            provider_payment_id = payment_data.get("id")

            if not provider_payment_id:
                logger.error("Missing payment ID in webhook")
                return

            logger.info(f"Processing successful payment: {provider_payment_id}")

            # Process payment
            success = await self.payment_service.process_successful_payment(provider_payment_id)

            if success:
                logger.info(f"✅ Successfully processed payment: {provider_payment_id}")
            else:
                logger.error(f"❌ Failed to process payment: {provider_payment_id}")

        except Exception as e:
            logger.error(f"❌ Error handling payment.succeeded: {e}")

    async def _handle_payment_cancelled(self, payment_data: dict):
        """
        Handle payment.canceled event

        Args:
            payment_data: Payment object from webhook
        """
        try:
            provider_payment_id = payment_data.get("id")

            if not provider_payment_id:
                logger.error("Missing payment ID in webhook")
                return

            logger.info(f"Processing cancelled payment: {provider_payment_id}")

            # Process cancellation
            success = await self.payment_service.process_cancelled_payment(provider_payment_id)

            if success:
                logger.info(f"✅ Successfully processed cancellation: {provider_payment_id}")
            else:
                logger.error(f"❌ Failed to process cancellation: {provider_payment_id}")

        except Exception as e:
            logger.error(f"❌ Error handling payment.canceled: {e}")

    async def _handle_refund_succeeded(self, refund_data: dict):
        """
        Handle refund.succeeded event

        Args:
            refund_data: Refund object from webhook

        Example refund_data:
        {
            "id": "refund_id",
            "payment_id": "2d8b8b7a-000f-5000-9000-1b7e3f9e0e9f",
            "status": "succeeded",
            "amount": {
                "value": "599.00",
                "currency": "RUB"
            }
        }
        """
        try:
            payment_id = refund_data.get("payment_id")
            amount_data = refund_data.get("amount", {})
            amount = float(amount_data.get("value", 0))

            if not payment_id:
                logger.error("Missing payment ID in refund webhook")
                return

            logger.info(f"Processing refund for payment: {payment_id}, amount: {amount}")

            # Process refund
            success = await self.payment_service.process_refund(payment_id, amount)

            if success:
                logger.info(f"✅ Successfully processed refund: {payment_id}")
            else:
                logger.error(f"❌ Failed to process refund: {payment_id}")

        except Exception as e:
            logger.error(f"❌ Error handling refund.succeeded: {e}")

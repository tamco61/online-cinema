"""
YooMoney (YooKassa) Client Wrapper

Абстракция над YooMoney API для создания платежей и обработки вебхуков.
В production используйте официальный SDK: yookassa

pip install yookassa

Здесь реализована упрощенная версия для демонстрации интерфейса.
"""

import requests
import logging
import uuid
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class YooMoneyClient:
    """
    YooMoney API client wrapper

    В production замените на:
    from yookassa import Payment, Configuration
    Configuration.account_id = settings.YOOMONEY_SHOP_ID
    Configuration.secret_key = settings.YOOMONEY_SECRET_KEY
    """

    def __init__(self):
        self.shop_id = settings.YOOMONEY_SHOP_ID
        self.secret_key = settings.YOOMONEY_SECRET_KEY
        self.api_url = settings.YOOMONEY_API_URL
        self.webhook_secret = settings.YOOMONEY_WEBHOOK_SECRET

    def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create payment in YooMoney

        Args:
            amount: Payment amount
            currency: Currency code (RUB, USD, EUR)
            description: Payment description
            return_url: URL to redirect after payment
            metadata: Additional metadata
            idempotency_key: Idempotency key

        Returns:
            Payment object with checkout URL

        Production implementation:
        from yookassa import Payment
        payment = Payment.create({
            "amount": {"value": str(amount), "currency": currency},
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "description": description,
            "metadata": metadata,
            "capture": True
        }, idempotency_key)
        """
        try:
            # Симуляция создания платежа
            # В production используйте настоящий SDK

            payment_id = str(uuid.uuid4())
            idempotency_key = idempotency_key or str(uuid.uuid4())

            # Симуляция checkout URL
            checkout_url = f"https://yookassa.ru/checkout/payments/{payment_id}"

            payment_data = {
                "id": payment_id,
                "status": "pending",
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": currency
                },
                "description": description,
                "confirmation": {
                    "type": "redirect",
                    "confirmation_url": checkout_url,
                    "return_url": return_url
                },
                "payment_metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=settings.PAYMENT_TIMEOUT_MINUTES)).isoformat(),
                "paid": False,
                "refundable": False,
                "test": True  # Test mode
            }

            logger.info(f"✅ Created YooMoney payment: {payment_id}")
            return payment_data

        except Exception as e:
            logger.error(f"❌ Error creating YooMoney payment: {e}")
            raise

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Get payment details from YooMoney

        Production implementation:
        from yookassa import Payment
        payment = Payment.find_one(payment_id)
        """
        try:
            # Симуляция получения платежа
            # В production используйте настоящий SDK

            logger.info(f"Fetching payment: {payment_id}")

            payment_data = {
                "id": payment_id,
                "status": "pending",
                "paid": False,
                "amount": {"value": "599.00", "currency": "RUB"},
                "created_at": datetime.utcnow().isoformat()
            }

            return payment_data

        except Exception as e:
            logger.error(f"❌ Error fetching payment: {e}")
            raise

    def capture_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Capture (confirm) payment

        Production implementation:
        from yookassa import Payment
        payment = Payment.capture(payment_id, {"amount": {"value": str(amount), "currency": "RUB"}})
        """
        try:
            logger.info(f"Capturing payment: {payment_id}")

            # Симуляция подтверждения платежа
            payment_data = {
                "id": payment_id,
                "status": "succeeded",
                "paid": True,
                "amount": {"value": f"{amount:.2f}" if amount else "599.00", "currency": "RUB"},
            }

            return payment_data

        except Exception as e:
            logger.error(f"❌ Error capturing payment: {e}")
            raise

    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Cancel payment

        Production implementation:
        from yookassa import Payment
        payment = Payment.cancel(payment_id)
        """
        try:
            logger.info(f"Cancelling payment: {payment_id}")

            payment_data = {
                "id": payment_id,
                "status": "canceled",
                "paid": False,
            }

            return payment_data

        except Exception as e:
            logger.error(f"❌ Error cancelling payment: {e}")
            raise

    def create_refund(
        self,
        payment_id: str,
        amount: float,
        currency: str = "RUB",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create refund for payment

        Production implementation:
        from yookassa import Refund
        refund = Refund.create({
            "payment_id": payment_id,
            "amount": {"value": str(amount), "currency": currency}
        }, idempotency_key)
        """
        try:
            logger.info(f"Creating refund for payment: {payment_id}")

            refund_id = str(uuid.uuid4())
            idempotency_key = idempotency_key or str(uuid.uuid4())

            refund_data = {
                "id": refund_id,
                "payment_id": payment_id,
                "status": "succeeded",
                "amount": {"value": f"{amount:.2f}", "currency": currency},
                "created_at": datetime.utcnow().isoformat()
            }

            return refund_data

        except Exception as e:
            logger.error(f"❌ Error creating refund: {e}")
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify YooMoney webhook signature

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers

        Returns:
            True if signature is valid

        Production implementation:
        import hashlib
        import hmac

        calculated_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(calculated_signature, signature)
        """
        try:
            if not self.webhook_secret:
                logger.warning("⚠️  Webhook secret not configured, skipping verification")
                return True

            # Вычисляем HMAC подпись
            calculated_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Сравниваем с полученной подписью
            is_valid = hmac.compare_digest(calculated_signature, signature)

            if is_valid:
                logger.info("✅ Webhook signature verified")
            else:
                logger.warning("⚠️  Invalid webhook signature")

            return is_valid

        except Exception as e:
            logger.error(f"❌ Error verifying webhook signature: {e}")
            return False


# Global YooMoney client instance
yoomoney_client = YooMoneyClient()


def get_yoomoney_client() -> YooMoneyClient:
    """Dependency to get YooMoney client"""
    return yoomoney_client

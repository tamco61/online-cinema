"""
Payment Service

Main business logic for payment processing
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.payment import Payment, PaymentStatus, PaymentProvider
from app.models.invoice import Invoice, InvoiceStatus
from app.core.config import settings
from app.core.redis_client import RedisClient
from app.services.yoomoney_client import YooMoneyClient
from app.services.user_service_client import UserServiceClient

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment service with business logic"""

    def __init__(
        self,
        db: Session,
        redis_client: RedisClient,
        yoomoney_client: YooMoneyClient,
        user_service_client: UserServiceClient
    ):
        self.db = db
        self.redis = redis_client
        self.yoomoney = yoomoney_client
        self.user_service = user_service_client

    def create_checkout_session(
        self,
        user_id: UUID,
        plan_id: str,
        idempotency_key: Optional[str] = None
    ) -> Payment:
        """
        Create checkout session for subscription payment

        Args:
            user_id: User UUID
            plan_id: Subscription plan ID
            idempotency_key: Idempotency key for duplicate prevention

        Returns:
            Payment object with checkout URL

        Steps:
            1. Check idempotency key
            2. Validate plan
            3. Create payment record
            4. Create YooMoney payment
            5. Store idempotency key
            6. Return payment with checkout URL
        """
        try:
            # 1. Check idempotency key
            if idempotency_key:
                cached_result = self.redis.check_idempotency_key(idempotency_key)
                if cached_result:
                    logger.info(f"Returning cached payment for idempotency key: {idempotency_key}")
                    payment_id = cached_result.get("payment_id")
                    payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
                    if payment:
                        return payment

            # 2. Validate plan
            if plan_id not in settings.PLANS:
                raise ValueError(f"Invalid plan_id: {plan_id}")

            plan = settings.PLANS[plan_id]
            amount = plan["price"]
            duration_days = plan["duration_days"]

            # 3. Create payment record
            payment = Payment(
                user_id=user_id,
                amount=amount,
                currency=settings.DEFAULT_CURRENCY,
                status=PaymentStatus.PENDING,
                provider=PaymentProvider.YOOMONEY,
                plan_id=plan_id,
                subscription_duration_days=duration_days,
                idempotency_key=idempotency_key
            )

            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)

            logger.info(f"Created payment: {payment.id} for user {user_id}, plan {plan_id}")

            # 4. Create YooMoney payment
            try:
                return_url = f"{settings.SUCCESS_REDIRECT_URL}?payment_id={payment.id}"

                yoomoney_payment = self.yoomoney.create_payment(
                    amount=amount,
                    currency=settings.DEFAULT_CURRENCY,
                    description=f"Подписка {plan['name']} на {duration_days} дней",
                    return_url=return_url,
                    metadata={
                        "payment_id": str(payment.id),
                        "user_id": str(user_id),
                        "plan_id": plan_id
                    },
                    idempotency_key=idempotency_key
                )

                # Update payment with YooMoney data
                payment.provider_payment_id = yoomoney_payment["id"]
                payment.checkout_url = yoomoney_payment["confirmation"]["confirmation_url"]
                payment.status = PaymentStatus.PENDING

                self.db.commit()
                self.db.refresh(payment)

                logger.info(f"✅ Created YooMoney payment: {yoomoney_payment['id']}")

            except Exception as e:
                logger.error(f"❌ Error creating YooMoney payment: {e}")
                payment.status = PaymentStatus.FAILED
                payment.error_message = str(e)
                self.db.commit()
                raise

            # 5. Store idempotency key
            if idempotency_key:
                self.redis.store_idempotency_key(
                    idempotency_key,
                    {"payment_id": str(payment.id)}
                )

            return payment

        except Exception as e:
            logger.error(f"❌ Error creating checkout session: {e}")
            self.db.rollback()
            raise

    async def process_successful_payment(self, provider_payment_id: str) -> bool:
        """
        Process successful payment

        Args:
            provider_payment_id: YooMoney payment ID

        Returns:
            True if successful

        Steps:
            1. Find payment by provider_payment_id
            2. Update payment status to succeeded
            3. Update user subscription in user-service
            4. Create invoice (optional)
        """
        try:
            # 1. Find payment
            payment = self.db.query(Payment).filter(
                Payment.provider_payment_id == provider_payment_id
            ).first()

            if not payment:
                logger.error(f"Payment not found: {provider_payment_id}")
                return False

            # Check if already processed
            if payment.status == PaymentStatus.SUCCEEDED:
                logger.info(f"Payment already processed: {payment.id}")
                return True

            # 2. Update payment status
            payment.status = PaymentStatus.SUCCEEDED
            payment.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"✅ Payment succeeded: {payment.id}")

            # 3. Update user subscription
            success = await self.user_service.update_subscription(
                user_id=payment.user_id,
                plan_id=payment.plan_id,
                duration_days=payment.subscription_duration_days,
                payment_id=payment.id
            )

            if not success:
                logger.warning(f"⚠️  Failed to update user subscription for payment {payment.id}")
                # Continue anyway - payment is successful

            # 4. Create invoice (optional)
            self._create_invoice(payment)

            return True

        except Exception as e:
            logger.error(f"❌ Error processing successful payment: {e}")
            self.db.rollback()
            return False

    async def process_failed_payment(self, provider_payment_id: str, error_message: str) -> bool:
        """
        Process failed payment

        Args:
            provider_payment_id: YooMoney payment ID
            error_message: Error message

        Returns:
            True if successful
        """
        try:
            payment = self.db.query(Payment).filter(
                Payment.provider_payment_id == provider_payment_id
            ).first()

            if not payment:
                logger.error(f"Payment not found: {provider_payment_id}")
                return False

            payment.status = PaymentStatus.FAILED
            payment.error_message = error_message
            payment.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Payment failed: {payment.id}")

            # Notify user-service about failed payment
            await self.user_service.notify_payment_event(
                user_id=payment.user_id,
                event_type="payment.failed",
                payment_id=payment.id,
                metadata={"error": error_message}
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error processing failed payment: {e}")
            self.db.rollback()
            return False

    async def process_cancelled_payment(self, provider_payment_id: str) -> bool:
        """
        Process cancelled payment

        Args:
            provider_payment_id: YooMoney payment ID

        Returns:
            True if successful
        """
        try:
            payment = self.db.query(Payment).filter(
                Payment.provider_payment_id == provider_payment_id
            ).first()

            if not payment:
                logger.error(f"Payment not found: {provider_payment_id}")
                return False

            payment.status = PaymentStatus.CANCELLED
            payment.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Payment cancelled: {payment.id}")

            return True

        except Exception as e:
            logger.error(f"❌ Error processing cancelled payment: {e}")
            self.db.rollback()
            return False

    async def process_refund(self, provider_payment_id: str, amount: Optional[float] = None) -> bool:
        """
        Process refund

        Args:
            provider_payment_id: YooMoney payment ID
            amount: Refund amount (None for full refund)

        Returns:
            True if successful
        """
        try:
            payment = self.db.query(Payment).filter(
                Payment.provider_payment_id == provider_payment_id
            ).first()

            if not payment:
                logger.error(f"Payment not found: {provider_payment_id}")
                return False

            # Create refund in YooMoney
            refund_amount = amount or payment.amount

            self.yoomoney.create_refund(
                payment_id=provider_payment_id,
                amount=refund_amount,
                currency=payment.currency
            )

            # Update payment status
            payment.status = PaymentStatus.REFUNDED
            payment.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"✅ Payment refunded: {payment.id}, amount: {refund_amount}")

            # Cancel subscription in user-service
            await self.user_service.cancel_subscription(
                user_id=payment.user_id,
                payment_id=payment.id
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error processing refund: {e}")
            self.db.rollback()
            return False

    def get_payment_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Payment], int]:
        """
        Get payment history for user

        Args:
            user_id: User UUID
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (payments list, total count)
        """
        try:
            query = self.db.query(Payment).filter(Payment.user_id == user_id)

            total = query.count()

            payments = query.order_by(desc(Payment.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return payments, total

        except Exception as e:
            logger.error(f"❌ Error getting payment history: {e}")
            return [], 0

    def get_payment_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def _create_invoice(self, payment: Payment):
        """Create invoice for payment"""
        try:
            invoice = Invoice(
                user_id=payment.user_id,
                payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                status=InvoiceStatus.PAID,
                description=f"Подписка {payment.plan_id} на {payment.subscription_duration_days} дней",
                plan_id=payment.plan_id,
                paid_date=datetime.utcnow()
            )

            invoice.invoice_number = invoice.generate_invoice_number()

            self.db.add(invoice)
            self.db.commit()

            logger.info(f"✅ Created invoice: {invoice.invoice_number}")

        except Exception as e:
            logger.error(f"❌ Error creating invoice: {e}")
            # Don't fail if invoice creation fails

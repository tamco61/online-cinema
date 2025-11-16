from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.redis_client import get_redis, RedisClient
from app.schemas.payment import (
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    PaymentResponse,
    PaymentHistoryResponse,
    WebhookResponse,
)
from app.services.payment_service import PaymentService
from app.services.yoomoney_client import get_yoomoney_client, YooMoneyClient
from app.services.user_service_client import get_user_service_client, UserServiceClient
from app.webhooks.yoomoney_webhook import YooMoneyWebhookHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_payment_service(
    db: Session = Depends(get_db),
    redis_client: RedisClient = Depends(get_redis),
    yoomoney_client: YooMoneyClient = Depends(get_yoomoney_client),
    user_service_client: UserServiceClient = Depends(get_user_service_client)
) -> PaymentService:
    """Dependency to get payment service"""
    return PaymentService(db, redis_client, yoomoney_client, user_service_client)


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Create checkout session for subscription payment

    **Idempotency:**
    - Use `X-Idempotency-Key` header or `idempotency_key` field
    - Prevents duplicate payments if request is retried
    - Cached for 24 hours

    **Request:**
    ```json
    {
        "plan_id": "premium",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "idempotency_key": "optional-unique-key"
    }
    ```

    **Response:**
    ```json
    {
        "payment_id": "uuid",
        "checkout_url": "https://yookassa.ru/checkout/...",
        "amount": 599.00,
        "currency": "RUB",
        "plan_id": "premium"
    }
    ```

    **Example:**
    ```bash
    curl -X POST http://localhost:8007/api/v1/payments/create-checkout-session \\
      -H "Content-Type: application/json" \\
      -H "X-Idempotency-Key: unique-key-123" \\
      -d '{
        "plan_id": "premium",
        "user_id": "00000000-0000-0000-0000-000000000001"
      }'
    ```
    """
    try:
        # Use header idempotency key if provided, otherwise use request field
        final_idempotency_key = idempotency_key or request.idempotency_key

        payment = payment_service.create_checkout_session(
            user_id=request.user_id,
            plan_id=request.plan_id,
            idempotency_key=final_idempotency_key
        )

        return CheckoutSessionResponse(
            payment_id=payment.id,
            checkout_url=payment.checkout_url,
            amount=payment.amount,
            currency=payment.currency,
            plan_id=payment.plan_id,
            expires_at=None  # Can be calculated from created_at + timeout
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),
    yoomoney_client: YooMoneyClient = Depends(get_yoomoney_client)
):
    """
    YooMoney webhook handler

    **Supported Events:**
    - `payment.succeeded` - Payment completed successfully
    - `payment.canceled` - Payment cancelled by user or timeout
    - `refund.succeeded` - Refund processed

    **Webhook Configuration:**
    Set webhook URL in YooMoney dashboard:
    ```
    https://your-domain.com/api/v1/payments/webhook
    ```

    **Security:**
    - Webhook signature verification using HMAC-SHA256
    - Set `YOOMONEY_WEBHOOK_SECRET` in environment

    **Example Webhook Payload:**
    ```json
    {
        "type": "notification",
        "event": "payment.succeeded",
        "object": {
            "id": "2d8b8b7a-000f-5000-9000-1b7e3f9e0e9f",
            "status": "succeeded",
            "paid": true,
            "amount": {
                "value": "599.00",
                "currency": "RUB"
            },
            "metadata": {
                "payment_id": "uuid"
            }
        }
    }
    ```

    **Testing:**
    ```bash
    curl -X POST http://localhost:8007/api/v1/payments/webhook \\
      -H "Content-Type: application/json" \\
      -H "X-YooKassa-Signature: signature" \\
      -d '{
        "type": "notification",
        "event": "payment.succeeded",
        "object": {
            "id": "provider-payment-id",
            "status": "succeeded"
        }
      }'
    ```
    """
    try:
        webhook_handler = YooMoneyWebhookHandler(payment_service, yoomoney_client)
        result = await webhook_handler.handle_webhook(request)

        return WebhookResponse(
            success=True,
            message="Webhook processed successfully"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.get("/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    user_id: UUID = Query(..., description="User UUID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get payment history for user

    **Query Parameters:**
    - `user_id` - User UUID (required)
    - `page` - Page number (default: 1)
    - `page_size` - Items per page (default: 20, max: 100)

    **Response:**
    ```json
    {
        "payments": [
            {
                "id": "uuid",
                "user_id": "uuid",
                "amount": 599.00,
                "currency": "RUB",
                "status": "succeeded",
                "provider": "yoomoney",
                "plan_id": "premium",
                "created_at": "2024-11-16T10:00:00Z"
            }
        ],
        "total": 10,
        "page": 1,
        "page_size": 20
    }
    ```

    **Example:**
    ```bash
    curl "http://localhost:8007/api/v1/payments/history?user_id={uuid}&page=1&page_size=20"
    ```
    """
    try:
        payments, total = payment_service.get_payment_history(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        payment_responses = [
            PaymentResponse(
                id=p.id,
                user_id=p.user_id,
                amount=p.amount,
                currency=p.currency,
                status=p.status,
                provider=p.provider,
                provider_payment_id=p.provider_payment_id,
                plan_id=p.plan_id,
                subscription_duration_days=p.subscription_duration_days,
                checkout_url=p.checkout_url,
                created_at=p.created_at,
                updated_at=p.updated_at,
                completed_at=p.completed_at
            )
            for p in payments
        ]

        return PaymentHistoryResponse(
            payments=payment_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment history")


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Get payment details by ID

    **Example:**
    ```bash
    curl "http://localhost:8007/api/v1/payments/{payment_id}"
    ```
    """
    try:
        payment = payment_service.get_payment_by_id(payment_id)

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        return PaymentResponse(
            id=payment.id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            provider_payment_id=payment.provider_payment_id,
            plan_id=payment.plan_id,
            subscription_duration_days=payment.subscription_duration_days,
            checkout_url=payment.checkout_url,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            completed_at=payment.completed_at
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment")

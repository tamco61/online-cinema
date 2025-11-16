# Payment Service

Payment processing service for online cinema platform with YooMoney integration, subscription management, and idempotency guarantees.

**Location:** `services/payment-service/`

## Features

### Payment Processing
- **YooMoney Integration**: Create payments and handle webhooks
- **Subscription Plans**: Basic, Premium, Family
- **Idempotency**: Redis-based idempotency keys prevent duplicate payments
- **Webhook Processing**: Handle payment.succeeded, payment.canceled, refund.succeeded

### Database
- **PostgreSQL**: Payments and invoices storage
- **Redis**: Idempotency keys caching

### User Service Integration
- **Subscription Updates**: Automatically activate subscriptions after successful payment
- **Event Notifications**: Notify user-service about payment events

## Architecture

```
payment-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── payments.py           # API endpoints
│   ├── core/
│   │   ├── config.py                     # Configuration
│   │   ├── database.py                   # PostgreSQL database
│   │   └── redis_client.py               # Redis client
│   ├── models/
│   │   ├── payment.py                    # Payment model
│   │   └── invoice.py                    # Invoice model
│   ├── schemas/
│   │   └── payment.py                    # Pydantic schemas
│   ├── services/
│   │   ├── payment_service.py            # Business logic
│   │   ├── yoomoney_client.py            # YooMoney API wrapper
│   │   └── user_service_client.py        # User-service integration
│   ├── webhooks/
│   │   └── yoomoney_webhook.py           # Webhook handler
│   └── main.py                           # Application entry point
├── alembic/                              # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Database Models

### Payment
```python
{
    "id": "uuid",
    "user_id": "uuid",
    "amount": 599.00,
    "currency": "RUB",
    "status": "succeeded",  # pending, processing, succeeded, failed, cancelled, refunded
    "provider": "yoomoney",
    "provider_payment_id": "yoomoney-payment-id",
    "plan_id": "premium",
    "subscription_duration_days": 30,
    "idempotency_key": "unique-key",
    "checkout_url": "https://yookassa.ru/checkout/...",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "completed_at": "timestamp"
}
```

### Invoice (Optional)
```python
{
    "id": "uuid",
    "invoice_number": "INV-20241116-00001",
    "user_id": "uuid",
    "payment_id": "uuid",
    "amount": 599.00,
    "currency": "RUB",
    "status": "paid",
    "description": "Подписка Premium на 30 дней",
    "created_at": "timestamp"
}
```

## API Endpoints

### 1. Create Checkout Session
```http
POST /api/v1/payments/create-checkout-session
```

Create payment and get checkout URL.

**Request:**
```json
{
    "plan_id": "premium",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "idempotency_key": "optional-unique-key"
}
```

**Headers:**
```
X-Idempotency-Key: unique-key-123  (optional, alternative to body field)
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
curl -X POST http://localhost:8007/api/v1/payments/create-checkout-session \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: unique-key-123" \
  -d '{
    "plan_id": "premium",
    "user_id": "00000000-0000-0000-0000-000000000001"
  }'
```

### 2. YooMoney Webhook
```http
POST /api/v1/payments/webhook
```

Handle webhooks from YooMoney.

**Events:**
- `payment.succeeded` - Payment completed
- `payment.canceled` - Payment cancelled
- `refund.succeeded` - Refund processed

**Webhook Payload:**
```json
{
    "type": "notification",
    "event": "payment.succeeded",
    "object": {
        "id": "yoomoney-payment-id",
        "status": "succeeded",
        "amount": {"value": "599.00", "currency": "RUB"}
    }
}
```

### 3. Payment History
```http
GET /api/v1/payments/history?user_id={uuid}&page=1&page_size=20
```

Get payment history for user.

**Response:**
```json
{
    "payments": [...],
    "total": 10,
    "page": 1,
    "page_size": 20
}
```

### 4. Get Payment
```http
GET /api/v1/payments/{payment_id}
```

Get payment details by ID.

### 5. Get Plans
```http
GET /plans
```

Get available subscription plans.

**Response:**
```json
{
    "plans": [
        {
            "id": "basic",
            "name": "Basic",
            "price": 299.00,
            "currency": "RUB",
            "duration_days": 30
        },
        {
            "id": "premium",
            "name": "Premium",
            "price": 599.00,
            "currency": "RUB",
            "duration_days": 30
        },
        {
            "id": "family",
            "name": "Family",
            "price": 899.00,
            "currency": "RUB",
            "duration_days": 30
        }
    ]
}
```

## Idempotency

Prevents duplicate payments using Redis-based idempotency keys.

**How it works:**
1. Client provides idempotency key in header or request body
2. Service checks if key exists in Redis
3. If exists, returns cached result
4. If not, processes request and caches result for 24 hours

**Usage:**
```bash
# First request - creates payment
curl -X POST http://localhost:8007/api/v1/payments/create-checkout-session \
  -H "X-Idempotency-Key: unique-key-123" \
  -d '{"plan_id": "premium", "user_id": "uuid"}'

# Retry - returns same payment (no duplicate)
curl -X POST http://localhost:8007/api/v1/payments/create-checkout-session \
  -H "X-Idempotency-Key: unique-key-123" \
  -d '{"plan_id": "premium", "user_id": "uuid"}'
```

## YooMoney Integration

### Configuration

Set environment variables:
```env
YOOMONEY_SHOP_ID=your-shop-id
YOOMONEY_SECRET_KEY=your-secret-key
YOOMONEY_WEBHOOK_SECRET=your-webhook-secret
```

### Webhook Setup

1. Go to YooMoney dashboard
2. Set webhook URL: `https://your-domain.com/api/v1/payments/webhook`
3. Enable events: payment.succeeded, payment.canceled, refund.succeeded
4. Copy webhook secret to `YOOMONEY_WEBHOOK_SECRET`

### Production SDK

For production, install official SDK:
```bash
pip install yookassa
```

Update `yoomoney_client.py` to use real SDK instead of simulation.

## User Service Integration

After successful payment, the service updates user subscription:

**HTTP Request to User Service:**
```http
POST /api/v1/users/{user_id}/subscription
```

**Request:**
```json
{
    "plan_id": "premium",
    "duration_days": 30,
    "payment_id": "uuid",
    "activated_at": "2024-11-16T10:00:00Z",
    "expires_at": "2024-12-16T10:00:00Z",
    "status": "active"
}
```

**Alternative: Event-Driven**
```python
# Publish to Kafka
producer.send('payment.events', {
    "event_type": "payment.succeeded",
    "user_id": "uuid",
    "payment_id": "uuid"
})
```

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- YooMoney account (for production)

### Installation

1. Clone repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run migrations:
```bash
alembic upgrade head
```

### Running Locally

```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload

# Or run directly
python -m app.main
```

### Running with Docker

```bash
# Start all services
make docker-up

# View logs
make logs

# Stop services
make docker-down
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | postgresql://... |
| `REDIS_HOST` | Redis server host | localhost |
| `REDIS_PORT` | Redis server port | 6379 |
| `YOOMONEY_SHOP_ID` | YooMoney shop ID | - |
| `YOOMONEY_SECRET_KEY` | YooMoney secret key | - |
| `YOOMONEY_WEBHOOK_SECRET` | Webhook verification secret | - |
| `USER_SERVICE_URL` | User service URL | http://localhost:8002 |
| `DEFAULT_CURRENCY` | Default currency | RUB |
| `IDEMPOTENCY_KEY_TTL` | Idempotency key TTL (seconds) | 86400 |

## Payment Flow

### Successful Payment

1. **Create Checkout Session**
   - User selects plan
   - Frontend calls `POST /create-checkout-session`
   - Service creates payment record
   - Service creates YooMoney payment
   - Returns checkout URL

2. **User Completes Payment**
   - User redirected to YooMoney
   - User completes payment
   - YooMoney sends webhook

3. **Webhook Processing**
   - Service receives `payment.succeeded` webhook
   - Verifies signature
   - Updates payment status
   - Updates user subscription in user-service
   - Creates invoice

4. **User Redirected**
   - YooMoney redirects to success URL
   - Frontend shows success message

### Failed Payment

1. Payment times out or user cancels
2. YooMoney sends `payment.canceled` webhook
3. Service updates payment status
4. User can retry

### Refund

1. Admin initiates refund
2. Service calls YooMoney refund API
3. YooMoney sends `refund.succeeded` webhook
4. Service updates payment status
5. Service cancels subscription in user-service

## Database Migrations

```bash
# Create new migration
make migration MSG="Add payment metadata"

# Run migrations
make migrate

# Rollback migration
alembic downgrade -1
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8007/docs
- **ReDoc**: http://localhost:8007/redoc

## Health Check

```bash
curl http://localhost:8007/health
```

Returns:
```json
{
    "status": "healthy",
    "database": "healthy",
    "redis": "healthy"
}
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app
```

## Development

### Project Structure
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas for validation
- `app/services/` - Business logic
- `app/api/v1/endpoints/` - API routes
- `app/webhooks/` - Webhook handlers
- `alembic/versions/` - Database migrations

### Adding New Payment Provider

1. Create provider client in `app/services/`
2. Update `PaymentProvider` enum
3. Add provider-specific webhook handler
4. Update `payment_service.py` to support new provider

## Security

- **Webhook Signature Verification**: HMAC-SHA256
- **Idempotency**: Prevent duplicate payments
- **HTTPS Only**: Use HTTPS in production
- **API Keys**: Service-to-service authentication
- **Database**: Parameterized queries prevent SQL injection

## Monitoring

- Health check endpoint
- Structured logging
- Database connection pooling
- Redis connection monitoring

## Future Enhancements

- [ ] Support multiple payment providers (Stripe, PayPal)
- [ ] Recurring payments / auto-renewal
- [ ] Payment analytics dashboard
- [ ] Fraud detection
- [ ] Currency conversion
- [ ] Promocodes and discounts
- [ ] Payment receipts via email

## License

Internal use only.

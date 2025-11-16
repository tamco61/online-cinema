# Notification Service

Notification service for online cinema platform with multi-channel support (Email, Push) and Kafka event processing.

**Location:** `services/notification-service/`

## Features

### Notification Channels

#### Email Providers
- **SendGrid** - Full implementation with HTTP API
- **AWS SES** - Full implementation with boto3
- **Console** - Development mode (prints to console)

#### Push Providers
- **Firebase Cloud Messaging (FCM)** - Full implementation
- **Console** - Development mode (prints to console)

### Event Processing (Kafka)

**User Events** (`user.events`)
- `subscription.created` → Welcome email
- `subscription.expired` → Expiry notification
- `subscription.renewed` → Renewal confirmation

**Catalog Events** (`catalog.events`)
- `movie.published` → Notify interested users based on genre/actor preferences

**Recommendation Events** (`recommendation.events`)
- `daily_digest` → Daily personalized movie recommendations
- `personalized_recommendation` → Real-time ML-based suggestions

## Architecture

```
notification-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── notifications.py      # Admin test endpoints
│   ├── core/
│   │   └── config.py                     # Configuration
│   ├── kafka/
│   │   ├── consumer.py                   # Kafka consumer & router
│   │   └── handlers/
│   │       ├── subscription_handler.py   # Subscription events
│   │       ├── catalog_handler.py        # Catalog events
│   │       └── recommendation_handler.py # Recommendation events
│   ├── providers/
│   │   ├── email/
│   │   │   ├── base.py                   # Email provider interface
│   │   │   ├── sendgrid.py               # SendGrid implementation
│   │   │   ├── aws_ses.py                # AWS SES implementation
│   │   │   └── console.py                # Console implementation
│   │   └── push/
│   │       ├── base.py                   # Push provider interface
│   │       ├── fcm.py                    # FCM implementation
│   │       └── console.py                # Console implementation
│   ├── schemas/
│   │   └── notification.py               # Pydantic schemas
│   └── main.py                           # Application entry point
├── tests/
│   └── test_api.py                       # Unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Provider Abstraction

### Email Provider Interface

```python
class EmailProvider(ABC):
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailResponse:
        pass

    @abstractmethod
    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[EmailResponse]:
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        pass
```

### Push Provider Interface

```python
class PushProvider(ABC):
    @abstractmethod
    async def send_push(self, notification: PushNotification) -> PushResponse:
        pass

    @abstractmethod
    async def send_bulk_push(self, notifications: List[PushNotification]) -> List[PushResponse]:
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        pass
```

## Kafka Event Flow

### 1. Subscription Created

**Event:**
```json
{
    "event_type": "subscription.created",
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "plan_id": "premium",
    "plan_name": "Premium",
    "expires_at": "2024-12-16T10:00:00Z"
}
```

**Actions:**
- Send welcome email with subscription details
- Send push notification (if device token provided)

### 2. Subscription Expired

**Event:**
```json
{
    "event_type": "subscription.expired",
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "plan_id": "premium"
}
```

**Actions:**
- Send expiry email with renewal link
- Send push notification encouraging renewal

### 3. Movie Published

**Event:**
```json
{
    "event_type": "movie.published",
    "movie_id": "uuid",
    "title": "The Matrix",
    "genre": "Sci-Fi",
    "director": "Wachowski",
    "actors": ["Keanu Reeves"],
    "poster_url": "https://...",
    "interested_users": [...]
}
```

**Actions:**
- Query user-service for users interested in genre/actors
- Send email notifications to interested users
- Send push notifications

## API Endpoints

### Test Email
```http
POST /api/v1/notifications/test-email
```

Send test email for configuration testing.

**Request:**
```json
{
    "to_email": "user@example.com",
    "to_name": "John Doe",
    "subject": "Test Email",
    "body": "<h1>Hello!</h1><p>This is a test.</p>"
}
```

**Example:**
```bash
curl -X POST http://localhost:8008/api/v1/notifications/test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "subject": "Test",
    "body": "<h1>Test Email</h1>"
  }'
```

### Test Push
```http
POST /api/v1/notifications/test-push
```

Send test push notification.

**Request:**
```json
{
    "device_token": "fcm-token",
    "title": "Test Notification",
    "body": "This is a test",
    "data": {"key": "value"}
}
```

### Get Providers
```http
GET /api/v1/notifications/providers
```

Get information about configured providers.

## Configuration

### Email Providers

**SendGrid:**
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-api-key
EMAIL_FROM_ADDRESS=noreply@cinema.example.com
EMAIL_FROM_NAME=Online Cinema
```

**AWS SES:**
```env
EMAIL_PROVIDER=aws_ses
AWS_SES_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
EMAIL_FROM_ADDRESS=noreply@cinema.example.com
```

**Console (Dev):**
```env
EMAIL_PROVIDER=console
```

### Push Providers

**FCM:**
```env
PUSH_PROVIDER=fcm
FCM_SERVER_KEY=your-server-key
FCM_PROJECT_ID=your-project-id
FCM_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

**Console (Dev):**
```env
PUSH_PROVIDER=console
```

### Kafka

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=notification-service
ENABLE_KAFKA=True

KAFKA_TOPIC_USER_EVENTS=user.events
KAFKA_TOPIC_CATALOG_EVENTS=catalog.events
KAFKA_TOPIC_RECOMMENDATION_EVENTS=recommendation.events
```

## Setup

### Prerequisites
- Python 3.11+
- Kafka (optional, for event processing)
- SendGrid API key or AWS SES credentials (optional, use console for dev)
- Firebase project (optional, for push notifications)

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

### Running Locally

```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload

# Or run directly
python -m app.main
```

### Running with Docker

```bash
# Start all services (Notification Service + Kafka)
make docker-up

# View logs
make logs

# Stop services
make docker-down
```

## Event Handlers

### Subscription Handler

```python
async def handle_subscription_created(event: dict):
    # 1. Extract user info
    # 2. Render email template
    # 3. Send welcome email
    # 4. Send push notification (if available)
```

### Catalog Handler

```python
async def handle_movie_published(event: dict):
    # 1. Get interested users (by genre/actor preferences)
    # 2. Send personalized emails
    # 3. Send push notifications
```

### Recommendation Handler

```python
async def handle_daily_digest(event: dict):
    # 1. Get user recommendations
    # 2. Render digest email
    # 3. Send email
```

## Email Templates

### Welcome Email (subscription.created)
- Gradient header with cinema theme
- Subscription details (plan, expiry date)
- List of benefits
- Call-to-action button
- Footer with branding

### Expiry Email (subscription.expired)
- Alert header
- Expiry notification
- Renewal call-to-action
- Special offer (10% discount)

### Movie Published
- Movie poster image
- Title, genre, description
- Call-to-action to watch
- Genre preference note

### Daily Digest
- List of 5 personalized recommendations
- Movie posters, ratings, genres
- Links to watch each movie

## Testing

```bash
# Run tests
pytest

# Test email provider
curl -X POST http://localhost:8008/api/v1/notifications/test-email \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test",
    "body": "<h1>Test</h1>"
  }'

# Test push provider
curl -X POST http://localhost:8008/api/v1/notifications/test-push \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "test-token",
    "title": "Test",
    "body": "Test push"
  }'
```

## Development

### Adding New Email Provider

1. Create new file in `app/providers/email/`
2. Implement `EmailProvider` interface
3. Add to factory function in `app/providers/email/__init__.py`

### Adding New Push Provider

1. Create new file in `app/providers/push/`
2. Implement `PushProvider` interface
3. Add to factory function in `app/providers/push/__init__.py`

### Adding New Event Handler

1. Create handler in `app/kafka/handlers/`
2. Register in `app/kafka/consumer.py` event router

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8008/docs
- **ReDoc**: http://localhost:8008/redoc

## Health Check

```bash
curl http://localhost:8008/health
```

Returns:
```json
{
    "status": "healthy",
    "email": "healthy",
    "push": "healthy",
    "kafka": "enabled"
}
```

## Future Enhancements

- [ ] SMS notifications via Twilio
- [ ] In-app notifications
- [ ] Notification preferences management
- [ ] Template management system
- [ ] A/B testing for notifications
- [ ] Analytics dashboard
- [ ] Rate limiting
- [ ] Retry mechanisms with exponential backoff
- [ ] Dead letter queue for failed notifications

## License

Internal use only.

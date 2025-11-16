# Cinema Common Library

Shared Python library for Cinema microservices platform. Provides middleware, logging, metrics, and tracing components.

## Features

- **Correlation ID Middleware** - Request tracing across services
- **Error Handling** - Unified error responses with custom exceptions
- **Rate Limiting** - In-memory and Redis-backed rate limiting
- **Structured Logging** - JSON logging with correlation IDs
- **Prometheus Metrics** - Automatic HTTP metrics collection
- **Distributed Tracing** - OpenTelemetry + Jaeger integration
- **Easy Setup** - One-line configuration for FastAPI apps

## Installation

### Development Mode (Editable)

```bash
# From the repository root
cd shared/python-common
pip install -e .

# With all dependencies
pip install -e ".[all]"
```

### Production Mode

```bash
pip install cinema-common
```

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from cinema_common import setup_application

app = FastAPI(title="My Service")

# Configure everything with one function
setup_application(
    app=app,
    service_name="catalog-service",
    service_version="1.0.0",
    log_level="INFO",
    environment="production",
    enable_metrics=True,
    enable_tracing=True,
    jaeger_host="localhost",
    jaeger_port=6831,
)

@app.get("/movies")
async def list_movies():
    return {"movies": []}
```

### Manual Setup

```python
from fastapi import FastAPI
from cinema_common import (
    CorrelationIdMiddleware,
    setup_error_handlers,
    setup_logging,
    setup_metrics,
    setup_tracing,
)

app = FastAPI()

# 1. Setup logging
setup_logging(
    service_name="catalog-service",
    log_level="INFO",
    json_logs=True
)

# 2. Add error handlers
setup_error_handlers(app)

# 3. Add correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# 4. Setup metrics
setup_metrics(app, service_name="catalog-service")

# 5. Setup tracing
setup_tracing(
    app=app,
    service_name="catalog-service",
    jaeger_host="localhost"
)
```

## Usage Examples

### 1. Logging

```python
from cinema_common import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Processing request")

# With extra context
logger.info(
    "Movie fetched",
    extra={
        "movie_id": 123,
        "user_id": 456,
    }
)

# Error logging
try:
    result = await db.query()
except Exception as e:
    logger.error("Database error", exc_info=True)
```

**JSON Output:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "service": "catalog-service",
  "correlation_id": "abc-123-def",
  "message": "Movie fetched",
  "extra": {
    "movie_id": 123,
    "user_id": 456
  }
}
```

### 2. Custom Exceptions

```python
from cinema_common import (
    NotFoundException,
    UnauthorizedException,
    BadRequestException,
)

@app.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    movie = await db.get(movie_id)

    if not movie:
        raise NotFoundException(
            message=f"Movie {movie_id} not found",
            details={"movie_id": movie_id}
        )

    return movie

# Returns:
# {
#   "error": "NOT_FOUND",
#   "message": "Movie 123 not found",
#   "details": {"movie_id": 123},
#   "correlation_id": "abc-123"
# }
```

### 3. Rate Limiting

```python
from cinema_common import RateLimiterMiddleware

# In-memory (development)
app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=60,
    backend="memory"
)

# Redis-backed (production)
from redis import asyncio as aioredis

redis = aioredis.from_url("redis://localhost:6379")

app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=100,
    requests_per_hour=1000,
    backend="redis",
    redis_client=redis
)
```

### 4. Metrics

```python
from cinema_common.utils.metrics import (
    track_business_event,
    track_cache_hit,
    track_cache_miss,
)

# Track business events
track_business_event("streaming-service", "video_started")

# Track cache operations
result = await redis.get(key)
if result:
    track_cache_hit("catalog-service", "movie_cache")
else:
    track_cache_miss("catalog-service", "movie_cache")

# Custom metrics with context manager
from cinema_common.utils.metrics import (
    MetricsContext,
    db_query_duration_seconds
)

async def get_movie(movie_id: int):
    with MetricsContext(
        db_query_duration_seconds,
        service="catalog",
        operation="select"
    ):
        return await db.execute(query)
```

### 5. Distributed Tracing

```python
from cinema_common.utils.tracer import (
    trace_span,
    add_span_attribute,
    add_span_event,
)

async def process_payment(user_id: int, amount: float):
    # Create custom span
    with trace_span(
        "process_payment",
        attributes={"user_id": user_id, "amount": amount}
    ):
        # Add attributes during execution
        add_span_attribute("payment_method", "stripe")

        # Call payment gateway
        result = await stripe.charge(user_id, amount)

        # Record events
        add_span_event("payment_completed", {"transaction_id": result.id})

        return result

# Auto-instrumented database calls
from cinema_common.utils.tracer import instrument_sqlalchemy

engine = create_engine("postgresql://...")
instrument_sqlalchemy(engine)
# Now all database queries are automatically traced!
```

### 6. Correlation ID

```python
from cinema_common import get_correlation_id, set_correlation_id

@app.get("/movies")
async def list_movies(request: Request):
    # Get correlation ID (automatically set by middleware)
    correlation_id = get_correlation_id()

    logger.info(
        "Listing movies",
        extra={"correlation_id": correlation_id}
    )

    return {"movies": []}

# Background tasks
async def background_task():
    # Manually set correlation ID for background tasks
    set_correlation_id("task-123")

    logger.info("Background task running")
```

### 7. Inter-Service Communication

```python
import httpx
from cinema_common import get_correlation_id

async def call_user_service(user_id: int):
    async with httpx.AsyncClient() as client:
        # Propagate correlation ID to downstream service
        headers = {
            "X-Correlation-ID": get_correlation_id() or "unknown"
        }

        response = await client.get(
            f"http://user-service/users/{user_id}",
            headers=headers
        )

        return response.json()

# HTTPX is auto-instrumented for tracing!
from cinema_common.utils.tracer import setup_tracing

tracer = setup_tracing(app, "catalog-service")
# All HTTPX calls now appear in Jaeger traces
```

## Configuration via Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production

# Jaeger
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379

# Metrics
PROMETHEUS_PORT=9090
```

## API Reference

### Middleware

- `CorrelationIdMiddleware` - Manages correlation IDs
- `ErrorHandlerMiddleware` - Global error handling
- `RateLimiterMiddleware` - Request rate limiting

### Exceptions

- `CinemaException` - Base exception
- `NotFoundException` - 404 errors
- `UnauthorizedException` - 401 errors
- `ForbiddenException` - 403 errors
- `BadRequestException` - 400 errors
- `ConflictException` - 409 errors
- `ServiceUnavailableException` - 503 errors

### Logging

- `setup_logging()` - Configure structured logging
- `get_logger()` - Get logger instance

### Metrics

- `setup_metrics()` - Configure Prometheus metrics
- `track_business_event()` - Track custom events
- `track_cache_hit()` / `track_cache_miss()` - Cache metrics
- `MetricsContext` - Context manager for timing

### Tracing

- `setup_tracing()` - Configure OpenTelemetry
- `trace_span()` - Create custom spans
- `add_span_attribute()` - Add span attributes
- `add_span_event()` - Add span events
- `instrument_sqlalchemy()` - Instrument SQLAlchemy
- `instrument_redis()` - Instrument Redis

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .
ruff check --fix .

# Type checking
mypy .
```

## Integration with Services

In each microservice's `requirements.txt`:

```txt
# For local development
-e ../shared/python-common

# For production (if published to PyPI)
cinema-common==0.1.0
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://cinema.example.com/docs/common
- Issues: https://github.com/cinema/cinema-common/issues
- Email: devops@cinema.example.com

# Quick Usage Guide

## Installation in Microservices

Add to `requirements.txt`:

```txt
# For local development (editable install)
-e ../../shared/python-common

# Or for production
cinema-common==0.1.0
```

## Minimal Setup

```python
from fastapi import FastAPI
from cinema_common import setup_application

app = FastAPI(title="My Service")

setup_application(
    app=app,
    service_name="my-service",
    service_version="1.0.0",
)
```

That's it! You now have:
- ✅ Structured JSON logging
- ✅ Correlation ID tracking
- ✅ Error handling with unified responses
- ✅ Prometheus metrics at `/metrics`
- ✅ Distributed tracing (Jaeger)

## Common Patterns

### 1. Custom Exception

```python
from cinema_common import NotFoundException

@app.get("/movies/{id}")
async def get_movie(id: int):
    movie = await db.get(id)
    if not movie:
        raise NotFoundException(f"Movie {id} not found")
    return movie
```

### 2. Logging with Context

```python
from cinema_common import get_logger

logger = get_logger(__name__)

logger.info("User logged in", extra={"user_id": 123})
```

### 3. Custom Tracing

```python
from cinema_common.utils.tracer import trace_span

async def expensive_operation():
    with trace_span("expensive_operation"):
        result = await do_work()
    return result
```

### 4. Business Metrics

```python
from cinema_common.utils.metrics import track_business_event

track_business_event("catalog-service", "movie_created")
```

## Configuration via Environment

```bash
# .env
LOG_LEVEL=INFO
ENVIRONMENT=production
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831
```

```python
import os

setup_application(
    app=app,
    service_name="catalog-service",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    environment=os.getenv("ENVIRONMENT", "development"),
    jaeger_host=os.getenv("JAEGER_AGENT_HOST", "localhost"),
    jaeger_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
)
```

## Testing

```python
from fastapi.testclient import TestClient

def test_endpoint():
    client = TestClient(app)
    response = client.get("/movies/1")

    # Check correlation ID in response
    assert "X-Correlation-ID" in response.headers

    # Check error format
    response = client.get("/movies/999")
    assert response.status_code == 404
    assert response.json()["error"] == "NOT_FOUND"
```

## Inter-Service Calls

```python
import httpx
from cinema_common import get_correlation_id

async def call_user_service(user_id: int):
    headers = {"X-Correlation-ID": get_correlation_id()}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://user-service/users/{user_id}",
            headers=headers
        )

    return response.json()
```

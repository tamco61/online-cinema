"""
Example FastAPI application using cinema-common library.

Run with:
    uvicorn example_app:app --reload --port 8000

Access:
    - API: http://localhost:8000/
    - Docs: http://localhost:8000/docs
    - Metrics: http://localhost:8000/metrics
"""

from fastapi import FastAPI, HTTPException

from cinema_common import (
    NotFoundException,
    get_correlation_id,
    get_logger,
    setup_application,
)
from cinema_common.utils.metrics import track_business_event
from cinema_common.utils.tracer import add_span_attribute, trace_span

# Create FastAPI app
app = FastAPI(
    title="Cinema Common Example",
    version="1.0.0",
    description="Example application demonstrating cinema-common library features",
)

# Setup all components
setup_application(
    app=app,
    service_name="example-service",
    service_version="1.0.0",
    log_level="INFO",
    environment="development",
    enable_metrics=True,
    enable_tracing=True,
    jaeger_host="localhost",
    jaeger_port=6831,
    enable_rate_limiting=False,  # Disable for demo
)

# Get logger
logger = get_logger(__name__)


@app.get("/")
async def root():
    """Root endpoint."""
    correlation_id = get_correlation_id()
    logger.info("Root endpoint called", extra={"correlation_id": correlation_id})

    return {
        "message": "Cinema Common Example API",
        "correlation_id": correlation_id,
        "endpoints": {
            "docs": "/docs",
            "metrics": "/metrics",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    """
    Get movie by ID (demonstrates custom exceptions and tracing).
    """
    logger.info(f"Fetching movie {movie_id}")

    # Add trace attributes
    add_span_attribute("movie_id", movie_id)

    # Simulate database lookup
    if movie_id == 404:
        logger.warning(f"Movie {movie_id} not found")
        raise NotFoundException(
            message=f"Movie {movie_id} not found",
            details={"movie_id": movie_id, "reason": "Does not exist in database"},
        )

    # Track business event
    track_business_event("example-service", "movie_fetched")

    movie = {
        "id": movie_id,
        "title": f"Movie {movie_id}",
        "year": 2024,
        "correlation_id": get_correlation_id(),
    }

    logger.info(f"Movie {movie_id} fetched successfully", extra={"movie": movie})

    return movie


@app.post("/movies/{movie_id}/view")
async def record_view(movie_id: int):
    """
    Record movie view (demonstrates custom spans).
    """
    with trace_span(
        "record_movie_view",
        attributes={"movie_id": movie_id, "event_type": "view"},
    ):
        logger.info(f"Recording view for movie {movie_id}")

        # Track business event
        track_business_event("example-service", "movie_viewed")

        return {
            "movie_id": movie_id,
            "status": "recorded",
            "correlation_id": get_correlation_id(),
        }


@app.get("/error")
async def trigger_error():
    """
    Trigger an error (demonstrates error handling).
    """
    logger.error("Intentional error triggered")
    raise HTTPException(status_code=500, detail="Intentional server error")


@app.get("/test/logging")
async def test_logging():
    """
    Test structured logging.
    """
    logger.debug("Debug message")
    logger.info("Info message", extra={"user_id": 123, "action": "test"})
    logger.warning("Warning message")

    return {
        "message": "Check logs for structured output",
        "correlation_id": get_correlation_id(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

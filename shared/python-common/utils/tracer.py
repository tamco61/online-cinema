"""
OpenTelemetry distributed tracing integration for Cinema microservices.

Features:
- Automatic HTTP request tracing
- Jaeger exporter support
- Database query tracing
- Custom span creation
- Context propagation across services
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .logger import get_logger

logger = get_logger(__name__)


def setup_tracing(
    app: FastAPI,
    service_name: str,
    service_version: str = "1.0.0",
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    environment: str = "development",
    sample_rate: float = 1.0,
    enable_auto_instrumentation: bool = True,
) -> trace.Tracer:
    """
    Setup OpenTelemetry tracing with Jaeger exporter.

    Args:
        app: FastAPI application
        service_name: Name of the microservice
        service_version: Service version
        jaeger_host: Jaeger agent hostname
        jaeger_port: Jaeger agent port (default: 6831)
        environment: Deployment environment
        sample_rate: Sampling rate (0.0 to 1.0, default: 1.0 = 100%)
        enable_auto_instrumentation: Auto-instrument FastAPI, HTTPX, etc.

    Returns:
        Configured tracer instance

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common.utils import setup_tracing

        app = FastAPI()
        tracer = setup_tracing(
            app=app,
            service_name="catalog-service",
            jaeger_host="localhost",
            jaeger_port=6831
        )
        ```
    """
    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": environment,
        }
    )

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )

    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Get tracer
    tracer = trace.get_tracer(__name__)

    # Auto-instrument FastAPI
    if enable_auto_instrumentation:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument HTTPX (for inter-service calls)
        HTTPXClientInstrumentor().instrument()

        logger.info(
            f"Auto-instrumentation enabled for {service_name}",
            extra={"instrumented": ["FastAPI", "HTTPX"]},
        )

    logger.info(
        f"Distributed tracing configured for {service_name}",
        extra={
            "jaeger_host": jaeger_host,
            "jaeger_port": jaeger_port,
            "sample_rate": sample_rate,
            "environment": environment,
        },
    )

    return tracer


def instrument_redis(redis_client) -> None:
    """
    Instrument Redis client for tracing.

    Args:
        redis_client: Redis client instance

    Example:
        ```python
        from redis import asyncio as aioredis
        from cinema_common.utils.tracer import instrument_redis

        redis = aioredis.from_url("redis://localhost:6379")
        instrument_redis(redis)
        ```
    """
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")


def instrument_sqlalchemy(engine) -> None:
    """
    Instrument SQLAlchemy engine for tracing.

    Args:
        engine: SQLAlchemy engine instance

    Example:
        ```python
        from sqlalchemy import create_engine
        from cinema_common.utils.tracer import instrument_sqlalchemy

        engine = create_engine("postgresql://...")
        instrument_sqlalchemy(engine)
        ```
    """
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Context manager for creating custom trace spans.

    Args:
        name: Span name
        attributes: Additional span attributes
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)

    Example:
        ```python
        from cinema_common.utils.tracer import trace_span

        async def process_payment(user_id: int, amount: float):
            with trace_span(
                "process_payment",
                attributes={"user_id": user_id, "amount": amount}
            ):
                # Payment processing logic
                result = await payment_gateway.charge(user_id, amount)
                return result
        ```
    """
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span(name, kind=kind) as span:
        # Add attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        try:
            yield span
        except Exception as e:
            # Record exception in span
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


def add_span_attribute(key: str, value: Any) -> None:
    """
    Add attribute to current span.

    Args:
        key: Attribute key
        value: Attribute value

    Example:
        ```python
        from cinema_common.utils.tracer import add_span_attribute

        async def get_movie(movie_id: int):
            add_span_attribute("movie_id", movie_id)
            movie = await db.get(movie_id)
            add_span_attribute("movie_title", movie.title)
            return movie
        ```
    """
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add event to current span.

    Args:
        name: Event name
        attributes: Event attributes

    Example:
        ```python
        from cinema_common.utils.tracer import add_span_event

        async def send_email(user_id: int):
            add_span_event("email_queued", {"user_id": user_id})
            await email_service.send(user_id)
            add_span_event("email_sent", {"user_id": user_id})
        ```
    """
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def get_trace_id() -> str:
    """
    Get current trace ID.

    Returns:
        Trace ID as hex string, or empty string if no active trace

    Example:
        ```python
        from cinema_common.utils.tracer import get_trace_id

        trace_id = get_trace_id()
        logger.info("Processing request", extra={"trace_id": trace_id})
        ```
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return ""


def get_span_id() -> str:
    """
    Get current span ID.

    Returns:
        Span ID as hex string, or empty string if no active span
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return ""


class TracingContext:
    """
    Context manager for detailed operation tracing.

    Example:
        ```python
        from cinema_common.utils.tracer import TracingContext

        async def complex_operation():
            with TracingContext("database_migration") as ctx:
                ctx.add_attribute("table", "movies")
                await migrate_table()
                ctx.add_event("migration_complete")
        ```
    """

    def __init__(self, operation_name: str, **attributes):
        """
        Initialize tracing context.

        Args:
            operation_name: Name of the operation
            **attributes: Initial attributes
        """
        self.operation_name = operation_name
        self.attributes = attributes
        self.span = None
        self.tracer = trace.get_tracer(__name__)

    def __enter__(self):
        """Start span."""
        self.span = self.tracer.start_span(self.operation_name)
        self.span.__enter__()

        # Add initial attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End span."""
        if exc_type:
            # Record exception
            self.span.record_exception(exc_val)
            self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))

        self.span.__exit__(exc_type, exc_val, exc_tb)

    def add_attribute(self, key: str, value: Any) -> None:
        """Add attribute to span."""
        if self.span:
            self.span.set_attribute(key, value)

    def add_event(self, name: str, **attributes) -> None:
        """Add event to span."""
        if self.span:
            self.span.add_event(name, attributes=attributes)


# Convenience function for backward compatibility
def get_current_span() -> Optional[trace.Span]:
    """
    Get current active span.

    Returns:
        Current span or None
    """
    return trace.get_current_span()

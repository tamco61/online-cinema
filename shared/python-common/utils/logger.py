"""
Structured JSON logging configuration for Cinema microservices.

Features:
- JSON formatted logs for easy parsing
- Correlation ID integration
- Configurable log levels via environment
- Service name and version tracking
- Automatic exception formatting
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from ..middleware.correlation_id import get_correlation_id


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format with:
    - Timestamp (ISO 8601)
    - Log level
    - Service name
    - Message
    - Correlation ID (if available)
    - Exception info (if present)
    - Additional context fields
    """

    def __init__(
        self,
        service_name: str = "cinema-service",
        service_version: str = "1.0.0",
        environment: str = "development",
    ):
        """
        Initialize JSON formatter.

        Args:
            service_name: Name of the microservice
            service_version: Service version
            environment: Deployment environment (dev, staging, prod)
        """
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "version": self.service_version,
            "environment": self.environment,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record
        # Skip built-in fields and private fields
        skip_fields = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "message", "pathname", "process", "processName", "relativeCreated",
            "thread", "threadName", "exc_info", "exc_text", "stack_info",
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in skip_fields and not key.startswith("_")
        }

        if extra_fields:
            log_data["extra"] = extra_fields

        # Return JSON string
        return json.dumps(log_data, default=str, ensure_ascii=False)


class CorrelationIdFilter(logging.Filter):
    """
    Filter to add correlation ID to log records.

    This allows correlation ID to be used in non-JSON formatters.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to record.

        Args:
            record: Log record to modify

        Returns:
            True (always allow the record)
        """
        record.correlation_id = get_correlation_id() or "N/A"
        return True


def setup_logging(
    service_name: str,
    service_version: str = "1.0.0",
    log_level: str = "INFO",
    environment: str = "development",
    json_logs: bool = True,
) -> None:
    """
    Configure structured logging for the service.

    Args:
        service_name: Name of the microservice
        service_version: Service version
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Deployment environment
        json_logs: Use JSON formatting (recommended for production)

    Example:
        ```python
        from cinema_common.utils import setup_logging

        setup_logging(
            service_name="catalog-service",
            service_version="1.0.0",
            log_level="INFO",
            environment="production",
            json_logs=True
        )
        ```
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter
    if json_logs:
        formatter = JSONFormatter(
            service_name=service_name,
            service_version=service_version,
            environment=environment,
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Add correlation ID filter for non-JSON logs
        console_handler.addFilter(CorrelationIdFilter())

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info(
        f"Logging configured for {service_name}",
        extra={
            "log_level": log_level,
            "json_logs": json_logs,
            "environment": environment,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance

    Example:
        ```python
        from cinema_common.utils import get_logger

        logger = get_logger(__name__)
        logger.info("Processing request", extra={"user_id": 123})
        ```
    """
    return logging.getLogger(name)


# Convenience logger for this module
logger = get_logger(__name__)

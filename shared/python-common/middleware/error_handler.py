"""
Global Error Handler Middleware for FastAPI applications.

Provides:
- Unified error response format across all microservices
- Automatic logging of exceptions with context
- Custom exception classes for common HTTP errors
- Integration with correlation ID for tracing
"""

import logging
import traceback
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .correlation_id import get_correlation_id

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    All errors across the platform follow this structure.
    """

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Union[Dict[str, Any], list]] = Field(
        None, description="Additional error details"
    )
    correlation_id: Optional[str] = Field(
        None, description="Request correlation ID for tracing"
    )
    path: Optional[str] = Field(None, description="Request path where error occurred")


class CinemaException(Exception):
    """
    Base exception for Cinema platform.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            error_code: Machine-readable error code
            details: Additional error context
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details
        super().__init__(self.message)


class NotFoundException(CinemaException):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class UnauthorizedException(CinemaException):
    """Authentication required (401)."""

    def __init__(self, message: str = "Authentication required", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenException(CinemaException):
    """Access forbidden (403)."""

    def __init__(self, message: str = "Access forbidden", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            details=details,
        )


class BadRequestException(CinemaException):
    """Invalid request (400)."""

    def __init__(self, message: str = "Invalid request", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            details=details,
        )


class ConflictException(CinemaException):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource conflict", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class ServiceUnavailableException(CinemaException):
    """Service temporarily unavailable (503)."""

    def __init__(
        self, message: str = "Service temporarily unavailable", details: Optional[Dict] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Union[Dict, list]] = None,
    path: Optional[str] = None,
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        error_code: Machine-readable error code
        message: Human-readable message
        status_code: HTTP status code
        details: Additional error details
        path: Request path

    Returns:
        JSONResponse with error details
    """
    correlation_id = get_correlation_id()

    error_response = ErrorResponse(
        error=error_code,
        message=message,
        details=details,
        correlation_id=correlation_id,
        path=path,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def cinema_exception_handler(request: Request, exc: CinemaException) -> JSONResponse:
    """
    Handle custom Cinema exceptions.

    Args:
        request: FastAPI request
        exc: Cinema exception

    Returns:
        Formatted error response
    """
    logger.warning(
        f"Cinema exception: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "correlation_id": get_correlation_id(),
        },
    )

    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=str(request.url.path),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions.

    Args:
        request: FastAPI request
        exc: HTTP exception

    Returns:
        Formatted error response
    """
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url),
            "correlation_id": get_correlation_id(),
        },
    )

    return create_error_response(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        status_code=exc.status_code,
        path=str(request.url.path),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        Formatted error response with validation details
    """
    errors = exc.errors()

    logger.warning(
        "Validation error",
        extra={
            "errors": errors,
            "path": str(request.url),
            "correlation_id": get_correlation_id(),
        },
    )

    # Format validation errors for better readability
    formatted_errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in errors
    ]

    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=formatted_errors,
        path=str(request.url.path),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Unhandled exception

    Returns:
        Formatted error response (without leaking internal details)
    """
    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}",
        extra={
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc),
            "path": str(request.url),
            "correlation_id": get_correlation_id(),
        },
        exc_info=True,
    )

    # Don't expose internal error details to clients
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        path=str(request.url.path),
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with FastAPI app.

    Args:
        app: FastAPI application instance

    Example:
        ```python
        from fastapi import FastAPI
        from cinema_common.middleware import setup_error_handlers

        app = FastAPI()
        setup_error_handlers(app)
        ```
    """
    app.add_exception_handler(CinemaException, cinema_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    logger.info("Error handlers registered successfully")


class ErrorHandlerMiddleware:
    """
    Deprecated: Use setup_error_handlers() instead.

    This class is kept for backwards compatibility.
    """

    def __init__(self, app: FastAPI):
        logger.warning(
            "ErrorHandlerMiddleware is deprecated. Use setup_error_handlers() instead."
        )
        setup_error_handlers(app)

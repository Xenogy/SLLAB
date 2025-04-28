"""
Error handling package for the AccountDB application.

This package provides a centralized error handling system, including
exception classes, error handlers, and error reporting.
"""

from .exceptions import (
    AppError, ValidationError, NotFoundError, UnauthorizedError,
    ForbiddenError, DatabaseError, ConfigurationError, ExternalServiceError,
    RateLimitError, TimeoutError, ConflictError, BadRequestError
)

from .handlers import (
    handle_exception, get_exception_details, safe_execute,
    exception_handler, validation_exception_handler, http_exception_handler,
    request_validation_exception_handler, not_found_exception_handler,
    server_error_handler
)

from .middleware import (
    ErrorHandlingMiddleware, setup_error_handling
)

from .reporting import (
    report_error, get_error_summary, track_error_rate,
    notify_error, log_error
)

from .recovery import (
    retry_operation, circuit_breaker, fallback_handler,
    graceful_degradation
)

__all__ = [
    # Exception classes
    'AppError', 'ValidationError', 'NotFoundError', 'UnauthorizedError',
    'ForbiddenError', 'DatabaseError', 'ConfigurationError', 'ExternalServiceError',
    'RateLimitError', 'TimeoutError', 'ConflictError', 'BadRequestError',
    
    # Error handlers
    'handle_exception', 'get_exception_details', 'safe_execute',
    'exception_handler', 'validation_exception_handler', 'http_exception_handler',
    'request_validation_exception_handler', 'not_found_exception_handler',
    'server_error_handler',
    
    # Middleware
    'ErrorHandlingMiddleware', 'setup_error_handling',
    
    # Error reporting
    'report_error', 'get_error_summary', 'track_error_rate',
    'notify_error', 'log_error',
    
    # Error recovery
    'retry_operation', 'circuit_breaker', 'fallback_handler',
    'graceful_degradation'
]

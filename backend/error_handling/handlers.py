"""
Error handlers for the AccountDB application.

This module provides functions for handling exceptions and converting them to HTTP responses.
"""

import sys
import traceback
import logging
import json
from typing import Optional, Dict, List, Any, Union, Callable, Type
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler as fastapi_http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppError
from .reporting import log_error, report_error

# Configure logging
logger = logging.getLogger(__name__)

def get_exception_details(exception: Exception) -> Dict[str, Any]:
    """
    Get details about an exception.

    Args:
        exception: The exception

    Returns:
        Dict[str, Any]: The exception details
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()

    return {
        "type": exc_type.__name__ if exc_type else None,
        "message": str(exception),
        "traceback": traceback.format_exc(),
        "args": getattr(exception, "args", [])
    }

def handle_exception(
    exception: Exception,
    request: Optional[Request] = None,
    log_level: int = logging.ERROR,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Handle an exception and convert it to a JSONResponse.

    Args:
        exception: The exception to handle
        request: The request that caused the exception
        log_level: The logging level to use
        include_traceback: Whether to include the traceback in the response

    Returns:
        JSONResponse: The JSON response
    """
    # Get exception details
    details = get_exception_details(exception)

    # Log the exception
    log_error(exception, request, level=log_level)

    # Report the error if it's a server error
    if isinstance(exception, AppError) and exception.status_code >= 500:
        report_error(exception, request)
    elif not isinstance(exception, (AppError, StarletteHTTPException)) or (
        isinstance(exception, StarletteHTTPException) and exception.status_code >= 500
    ):
        report_error(exception, request)

    # Convert AppError to JSONResponse
    if isinstance(exception, AppError):
        response_data = exception.to_dict()

        # Include traceback in development mode
        if include_traceback:
            response_data["traceback"] = details["traceback"]

        return JSONResponse(
            status_code=exception.status_code,
            content=response_data
        )

    # Convert other exceptions to JSONResponse
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exception, StarletteHTTPException):
        status_code = exception.status_code

    response_data = {
        "error": details["type"] or "UNKNOWN_ERROR",
        "message": str(exception),
        "status_code": status_code,
        "details": {}
    }

    # Include traceback in development mode
    if include_traceback:
        response_data["traceback"] = details["traceback"]

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function safely and handle exceptions.

    Args:
        func: The function to execute
        *args: The positional arguments to pass to the function
        **kwargs: The keyword arguments to pass to the function

    Returns:
        Any: The result of the function

    Raises:
        JSONResponse: If an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        response = handle_exception(e)
        raise response

async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.

    Args:
        request: The request that caused the exception
        exc: The exception

    Returns:
        JSONResponse: The JSON response
    """
    return handle_exception(exc, request=request)

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Exception handler for validation errors.

    Args:
        request: The request that caused the exception
        exc: The validation error

    Returns:
        JSONResponse: The JSON response
    """
    # Log the validation error
    log_error(exc, request, level=logging.WARNING)

    # Convert validation errors to a more user-friendly format
    errors = {}
    for error in exc.errors():
        location = error["loc"]
        if len(location) > 0:
            field = ".".join(str(loc) for loc in location if loc != "body")
            if field not in errors:
                errors[field] = []
            errors[field].append(error["msg"])

    # Create a ValidationError
    from .exceptions import ValidationError
    validation_error = ValidationError(
        message="Validation error",
        errors=errors,
        context={"request_path": request.url.path}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=validation_error.to_dict()
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """
    Exception handler for HTTP exceptions.

    Args:
        request: The request that caused the exception
        exc: The HTTP exception

    Returns:
        Response: The response
    """
    # Log the HTTP exception
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    log_error(exc, request, level=log_level)

    # Use the default handler for non-JSON responses
    if not request.headers.get("accept", "").startswith("application/json"):
        return await fastapi_http_exception_handler(request, exc)

    # Create a JSON response
    response_data = {
        "error": "HTTP_ERROR",
        "message": str(exc.detail),
        "status_code": exc.status_code,
        "details": {}
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )

async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Exception handler for request validation errors.

    Args:
        request: The request that caused the exception
        exc: The validation error

    Returns:
        JSONResponse: The JSON response
    """
    return await validation_exception_handler(request, exc)

async def not_found_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for 404 errors.

    Args:
        request: The request that caused the exception
        exc: The exception

    Returns:
        JSONResponse: The JSON response
    """
    # Log the 404 error
    log_error(exc, request, level=logging.INFO)

    # Create a NotFoundError
    from .exceptions import NotFoundError
    not_found_error = NotFoundError(
        resource_type="Endpoint",
        context={"request_path": request.url.path}
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=not_found_error.to_dict()
    )

async def server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for 500 errors.

    Args:
        request: The request that caused the exception
        exc: The exception

    Returns:
        JSONResponse: The JSON response
    """
    # Log the server error
    log_error(exc, request, level=logging.ERROR)

    # Report the error
    report_error(exc, request)

    # Create a generic server error response
    response_data = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "details": {}
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )

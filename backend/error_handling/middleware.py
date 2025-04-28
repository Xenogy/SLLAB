"""
Error handling middleware for the AccountDB application.

This module provides middleware for catching and handling exceptions.
"""

import time
import logging
import traceback
from typing import Optional, Dict, List, Any, Union, Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .exceptions import AppError
from .handlers import (
    exception_handler, validation_exception_handler,
    http_exception_handler, request_validation_exception_handler,
    not_found_exception_handler, server_error_handler
)
from .reporting import log_error, report_error

# Configure logging
logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process a request and handle any errors.
        
        Args:
            request: The request to process
            call_next: The next middleware or endpoint to call
            
        Returns:
            Response: The response
        """
        # Add request ID to the request state
        request.state.request_id = request.headers.get("X-Request-ID", None)
        
        # Add start time to the request state
        request.state.start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add request ID to the response headers
            if request.state.request_id:
                response.headers["X-Request-ID"] = request.state.request_id
            
            # Add processing time to the response headers
            processing_time = time.time() - request.state.start_time
            response.headers["X-Processing-Time"] = str(processing_time)
            
            return response
        except Exception as exc:
            # Calculate processing time
            processing_time = time.time() - request.state.start_time
            
            # Handle the exception
            if isinstance(exc, RequestValidationError):
                response = await validation_exception_handler(request, exc)
            elif isinstance(exc, StarletteHTTPException):
                response = await http_exception_handler(request, exc)
            elif isinstance(exc, AppError):
                response = await exception_handler(request, exc)
            else:
                response = await server_error_handler(request, exc)
            
            # Add request ID to the response headers
            if request.state.request_id:
                response.headers["X-Request-ID"] = request.state.request_id
            
            # Add processing time to the response headers
            response.headers["X-Processing-Time"] = str(processing_time)
            
            return response

def setup_error_handling(app: FastAPI) -> None:
    """
    Set up error handling for a FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Add the error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add exception handlers
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(AppError, exception_handler)
    app.add_exception_handler(404, not_found_exception_handler)
    app.add_exception_handler(500, server_error_handler)
    app.add_exception_handler(Exception, exception_handler)

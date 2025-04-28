"""
Error handling utility functions for the AccountDB application.

This module provides utility functions for error handling.
"""

import logging
import traceback
import sys
from typing import Optional, Dict, List, Any, Union, Type, Callable
from fastapi import HTTPException, status

# Configure logging
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base class for application errors."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    """Error raised when validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": errors or {}}
        )

class NotFoundError(AppError):
    """Error raised when a resource is not found."""
    
    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: Optional[str] = None
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )

class UnauthorizedError(AppError):
    """Error raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Unauthorized"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class ForbiddenError(AppError):
    """Error raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Forbidden"
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class DatabaseError(AppError):
    """Error raised when a database operation fails."""
    
    def __init__(
        self,
        message: str = "Database error",
        original_error: Optional[Exception] = None
    ):
        details = {}
        if original_error:
            details["original_error"] = str(original_error)
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

def handle_exception(exception: Exception) -> HTTPException:
    """
    Handle an exception and convert it to an HTTPException.
    
    Args:
        exception: The exception to handle
        
    Returns:
        HTTPException: The HTTP exception
    """
    # Log the exception
    logger.error(f"Exception: {str(exception)}")
    logger.debug(traceback.format_exc())
    
    # Convert AppError to HTTPException
    if isinstance(exception, AppError):
        return HTTPException(
            status_code=exception.status_code,
            detail={
                "message": exception.message,
                "details": exception.details
            }
        )
    
    # Convert other exceptions to HTTPException
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "message": "An unexpected error occurred",
            "details": {
                "error": str(exception)
            }
        }
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
        HTTPException: If an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise handle_exception(e)

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
        "args": exception.args
    }

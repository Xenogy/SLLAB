"""
Exception classes for the AccountDB application.

This module defines a hierarchy of custom exception classes for the application.
"""

from typing import Optional, Dict, List, Any, Union
from fastapi import status

class AppError(Exception):
    """Base class for application errors."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an AppError.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            error_code: Machine-readable error code
            context: Context information about the error
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            Dict[str, Any]: The error as a dictionary
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }

class ValidationError(AppError):
    """Error raised when validation fails."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[Dict[str, List[str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ValidationError.
        
        Args:
            message: Human-readable error message
            errors: Validation errors by field
            context: Context information about the error
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": errors or {}},
            error_code="VALIDATION_ERROR",
            context=context
        )

class BadRequestError(AppError):
    """Error raised when the request is invalid."""
    
    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a BadRequestError.
        
        Args:
            message: Human-readable error message
            details: Additional error details
            context: Context information about the error
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            error_code="BAD_REQUEST",
            context=context
        )

class NotFoundError(AppError):
    """Error raised when a resource is not found."""
    
    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a NotFoundError.
        
        Args:
            resource_type: The type of resource that was not found
            resource_id: The ID of the resource that was not found
            context: Context information about the error
        """
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            error_code="NOT_FOUND",
            context=context
        )

class UnauthorizedError(AppError):
    """Error raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Unauthorized",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an UnauthorizedError.
        
        Args:
            message: Human-readable error message
            details: Additional error details
            context: Context information about the error
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            error_code="UNAUTHORIZED",
            context=context
        )

class ForbiddenError(AppError):
    """Error raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Forbidden",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ForbiddenError.
        
        Args:
            message: Human-readable error message
            details: Additional error details
            context: Context information about the error
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            error_code="FORBIDDEN",
            context=context
        )

class ConflictError(AppError):
    """Error raised when there is a conflict with the current state."""
    
    def __init__(
        self,
        message: str = "Conflict",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ConflictError.
        
        Args:
            message: Human-readable error message
            details: Additional error details
            context: Context information about the error
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            error_code="CONFLICT",
            context=context
        )

class RateLimitError(AppError):
    """Error raised when a rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a RateLimitError.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying
            context: Context information about the error
        """
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            error_code="RATE_LIMIT_EXCEEDED",
            context=context
        )

class TimeoutError(AppError):
    """Error raised when an operation times out."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        operation: Optional[str] = None,
        timeout: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a TimeoutError.
        
        Args:
            message: Human-readable error message
            operation: The operation that timed out
            timeout: The timeout in seconds
            context: Context information about the error
        """
        details = {}
        if operation:
            details["operation"] = operation
        if timeout:
            details["timeout"] = timeout
        
        super().__init__(
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details=details,
            error_code="TIMEOUT",
            context=context
        )

class DatabaseError(AppError):
    """Error raised when a database operation fails."""
    
    def __init__(
        self,
        message: str = "Database error",
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a DatabaseError.
        
        Args:
            message: Human-readable error message
            operation: The database operation that failed
            original_error: The original exception
            context: Context information about the error
        """
        details = {}
        if operation:
            details["operation"] = operation
        if original_error:
            details["original_error"] = str(original_error)
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            error_code="DATABASE_ERROR",
            context=context
        )

class ConfigurationError(AppError):
    """Error raised when there is a configuration error."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ConfigurationError.
        
        Args:
            message: Human-readable error message
            config_key: The configuration key that caused the error
            context: Context information about the error
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            error_code="CONFIGURATION_ERROR",
            context=context
        )

class ExternalServiceError(AppError):
    """Error raised when an external service fails."""
    
    def __init__(
        self,
        message: str = "External service error",
        service: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an ExternalServiceError.
        
        Args:
            message: Human-readable error message
            service: The external service that failed
            status_code: The status code returned by the external service
            response: The response from the external service
            context: Context information about the error
        """
        details = {}
        if service:
            details["service"] = service
        if status_code:
            details["status_code"] = status_code
        if response:
            details["response"] = response
        
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            error_code="EXTERNAL_SERVICE_ERROR",
            context=context
        )

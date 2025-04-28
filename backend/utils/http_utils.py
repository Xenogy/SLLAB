"""
HTTP utility functions for the AccountDB application.

This module provides utility functions for HTTP operations.
"""

import json
from typing import Optional, Dict, List, Any, Union
from fastapi import Response, status
from fastapi.responses import JSONResponse

def create_success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    Create a success response.
    
    Args:
        data: The response data
        message: The success message
        status_code: The HTTP status code
        
    Returns:
        JSONResponse: The success response
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data
        }
    )

def create_error_response(
    message: str = "An error occurred",
    errors: Optional[List[Dict[str, Any]]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    Create an error response.
    
    Args:
        message: The error message
        errors: The list of errors
        status_code: The HTTP status code
        
    Returns:
        JSONResponse: The error response
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "errors": errors or []
        }
    )

def create_validation_error_response(
    errors: Dict[str, List[str]],
    message: str = "Validation error"
) -> JSONResponse:
    """
    Create a validation error response.
    
    Args:
        errors: The validation errors
        message: The error message
        
    Returns:
        JSONResponse: The validation error response
    """
    error_list = []
    
    for field, messages in errors.items():
        for msg in messages:
            error_list.append({
                "field": field,
                "message": msg
            })
    
    return create_error_response(
        message=message,
        errors=error_list,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

def create_not_found_response(
    resource_type: str = "Resource",
    resource_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a not found response.
    
    Args:
        resource_type: The type of resource
        resource_id: The ID of the resource
        
    Returns:
        JSONResponse: The not found response
    """
    message = f"{resource_type} not found"
    if resource_id:
        message = f"{resource_type} with ID {resource_id} not found"
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_404_NOT_FOUND
    )

def create_unauthorized_response(
    message: str = "Unauthorized"
) -> JSONResponse:
    """
    Create an unauthorized response.
    
    Args:
        message: The error message
        
    Returns:
        JSONResponse: The unauthorized response
    """
    return create_error_response(
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED
    )

def create_forbidden_response(
    message: str = "Forbidden"
) -> JSONResponse:
    """
    Create a forbidden response.
    
    Args:
        message: The error message
        
    Returns:
        JSONResponse: The forbidden response
    """
    return create_error_response(
        message=message,
        status_code=status.HTTP_403_FORBIDDEN
    )

def create_pagination_response(
    data: List[Any],
    total: int,
    limit: int,
    offset: int,
    message: str = "Success"
) -> JSONResponse:
    """
    Create a paginated response.
    
    Args:
        data: The paginated data
        total: The total number of items
        limit: The limit per page
        offset: The offset
        message: The success message
        
    Returns:
        JSONResponse: The paginated response
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(data) < total
            }
        }
    )

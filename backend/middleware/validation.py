"""
Validation middleware for the AccountDB application.

This module provides middleware for validating request data before it reaches
the endpoint handlers.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
import json

from validation import (
    validate_file, validate_pagination_params, validate_sort_params,
    validate_search_param, validate_filter_params, MAX_FILE_SIZE, ALLOWED_FILE_TYPES
)

# Configure logging
logger = logging.getLogger(__name__)

async def validate_request_body(request: Request, model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Validate request body against a Pydantic model.

    Args:
        request: The FastAPI request object
        model: The Pydantic model to validate against

    Returns:
        Dict[str, Any]: The validated data

    Raises:
        HTTPException: If validation fails
    """
    try:
        body = await request.json()
        validated_data = model(**body)
        return validated_data.dict()
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        errors = []
        for error in e.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"]
            })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors}
        )

async def validate_file_upload(request: Request, file_type: str = None, max_size: int = MAX_FILE_SIZE) -> None:
    """
    Validate file upload.

    Args:
        request: The FastAPI request object
        file_type: The expected file type (json, csv, image, text)
        max_size: The maximum allowed file size in bytes

    Raises:
        HTTPException: If validation fails
    """
    content_type = request.headers.get("content-type", "")
    content_length = request.headers.get("content-length", "0")

    try:
        size = int(content_length)
    except ValueError:
        logger.error(f"Invalid content-length header: {content_length}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content-length header"
        )

    # Validate file type and size
    result = validate_file(content_type, size, file_type, max_size)
    if not result.valid:
        logger.error(f"File validation failed: {result.errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.errors}
        )

def validate_pagination(limit: int = 100, offset: int = 0) -> Dict[str, int]:
    """
    Validate pagination parameters.

    Args:
        limit: The limit parameter
        offset: The offset parameter

    Returns:
        Dict[str, int]: The validated pagination parameters

    Raises:
        HTTPException: If validation fails
    """
    result = validate_pagination_params(limit, offset)
    if not result.valid:
        logger.error(f"Pagination validation failed: {result.errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.errors}
        )

    return {"limit": int(limit), "offset": int(offset)}

def validate_sorting(sort_by: str, sort_order: str, allowed_fields: List[str]) -> Dict[str, str]:
    """
    Validate sorting parameters.

    Args:
        sort_by: The sort_by parameter
        sort_order: The sort_order parameter
        allowed_fields: A list of allowed fields to sort by

    Returns:
        Dict[str, str]: The validated sorting parameters

    Raises:
        HTTPException: If validation fails
    """
    result = validate_sort_params(sort_by, sort_order, allowed_fields)
    if not result.valid:
        logger.error(f"Sorting validation failed: {result.errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.errors}
        )

    return {"sort_by": sort_by, "sort_order": sort_order}

def validate_search(search: Optional[str] = None) -> Optional[str]:
    """
    Validate search parameter.

    Args:
        search: The search parameter

    Returns:
        Optional[str]: The validated search parameter

    Raises:
        HTTPException: If validation fails
    """
    if search is None:
        return None

    result = validate_search_param(search)
    if not result.valid:
        logger.error(f"Search validation failed: {result.errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.errors}
        )

    return search

def validate_filters(params: Dict[str, Any], allowed_filters: List[str]) -> Dict[str, Any]:
    """
    Validate filter parameters.

    Args:
        params: The filter parameters
        allowed_filters: A list of allowed filter names

    Returns:
        Dict[str, Any]: The validated filter parameters

    Raises:
        HTTPException: If validation fails
    """
    result = validate_filter_params(params, allowed_filters)
    if not result.valid:
        logger.error(f"Filter validation failed: {result.errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.errors}
        )

    return params

class ValidationMiddleware:
    """Middleware for validating requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        # Check for file uploads
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data"):
            # File upload validation will be handled by the endpoint
            await self.app(scope, receive, send)
            return

        # For JSON requests, validate the request body
        if content_type.startswith("application/json"):
            try:
                await request.json()
            except json.JSONDecodeError:
                response = JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid JSON in request body"}
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

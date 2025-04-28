"""
Size limit middleware for the API.

This module provides middleware for limiting the size of request bodies.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE
import logging

# Configure logging
logger = logging.getLogger(__name__)

class SizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for limiting the size of request bodies."""
    
    def __init__(
        self,
        app,
        max_size: int = 1024 * 1024,  # 1 MB
        exclude_paths: list = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            max_size: The maximum size in bytes
            exclude_paths: List of paths to exclude from size limiting
        """
        super().__init__(app)
        self.max_size = max_size
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response
        """
        # Skip size limiting for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger.warning(f"Request body too large: {content_length} bytes")
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                media_type="application/json"
            )
        
        # Process request
        return await call_next(request)

"""
Timeout middleware for the API.

This module provides middleware for timing out long-running requests.
"""

import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_504_GATEWAY_TIMEOUT
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware for timing out long-running requests."""
    
    def __init__(
        self,
        app,
        timeout: int = 30,  # 30 seconds
        exclude_paths: list = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            timeout: The timeout in seconds
            exclude_paths: List of paths to exclude from timeout
        """
        super().__init__(app)
        self.timeout = timeout
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
        # Skip timeout for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Set up timeout
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Request timed out after {self.timeout} seconds: {request.url.path}")
            return Response(
                content='{"detail":"Request timed out"}',
                status_code=HTTP_504_GATEWAY_TIMEOUT,
                media_type="application/json"
            )

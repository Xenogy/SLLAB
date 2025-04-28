"""
Rate limiting middleware for the API.

This module provides middleware for rate limiting API requests.
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import logging

# Configure logging
logger = logging.getLogger(__name__)

class InMemoryStore:
    """Simple in-memory store for rate limiting."""
    
    def __init__(self):
        self.store = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 60  # 1 minute
    
    async def increment(self, key: str, window: int, max_requests: int) -> tuple:
        """
        Increment the counter for the given key.
        
        Args:
            key: The rate limit key
            window: The time window in seconds
            max_requests: The maximum number of requests allowed in the window
            
        Returns:
            tuple: (current_count, is_allowed, reset_time)
        """
        now = time.time()
        
        # Clean up expired entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup(now)
            self.last_cleanup = now
        
        # Get or create entry
        if key not in self.store:
            self.store[key] = {
                "count": 0,
                "reset_at": now + window
            }
        
        # Reset if window has expired
        if now > self.store[key]["reset_at"]:
            self.store[key] = {
                "count": 0,
                "reset_at": now + window
            }
        
        # Increment counter
        self.store[key]["count"] += 1
        
        # Check if allowed
        is_allowed = self.store[key]["count"] <= max_requests
        
        return (
            self.store[key]["count"],
            is_allowed,
            self.store[key]["reset_at"]
        )
    
    def _cleanup(self, now: float):
        """Remove expired entries from the store."""
        keys_to_remove = []
        for key, data in self.store.items():
            if now > data["reset_at"]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.store[key]

# Create a global store instance
store = InMemoryStore()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(
        self,
        app,
        window: int = 60,  # 1 minute
        max_requests: int = 100,  # 100 requests per minute
        exclude_paths: list = None
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            window: The time window in seconds
            max_requests: The maximum number of requests allowed in the window
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.window = window
        self.max_requests = max_requests
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
        # Skip rate limiting for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Get rate limit key
        rate_limit_key = f"rate_limit:{client_ip}:{request.url.path}"
        
        # Check rate limit
        count, is_allowed, reset_at = await store.increment(
            rate_limit_key,
            self.window,
            self.max_requests
        )
        
        # If rate limit exceeded, return 429 Too Many Requests
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            return Response(
                content='{"detail":"Too many requests"}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at - time.time())),
                    "Retry-After": str(int(reset_at - time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - count)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at - time.time()))
        
        return response

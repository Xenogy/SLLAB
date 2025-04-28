"""
Logging utility functions for the AccountDB application.

This module provides utility functions for logging.
"""

import logging
import time
import traceback
import json
from typing import Optional, Dict, Any, Union

def setup_logging(
    level: int = logging.INFO,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None
) -> None:
    """
    Set up logging configuration.
    
    Args:
        level: The logging level
        format_str: The log format string
        log_file: The log file path, or None to log to console only
    """
    # Configure the root logger
    logging.basicConfig(
        level=level,
        format=format_str,
        filename=log_file
    )
    
    # Configure the console handler if logging to a file
    if log_file:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(format_str))
        logging.getLogger().addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The logger name
        
    Returns:
        logging.Logger: The logger
    """
    return logging.getLogger(name)

def log_exception(logger: logging.Logger, exception: Exception, message: str = "An error occurred") -> None:
    """
    Log an exception.
    
    Args:
        logger: The logger to use
        exception: The exception to log
        message: The message to log
    """
    logger.error(f"{message}: {str(exception)}")
    logger.debug(traceback.format_exc())

def log_request(logger: logging.Logger, request: Any, include_body: bool = False) -> None:
    """
    Log a request.
    
    Args:
        logger: The logger to use
        request: The request to log
        include_body: Whether to include the request body
    """
    # Extract request information
    info = {
        "method": getattr(request, "method", "UNKNOWN"),
        "url": getattr(request, "url", "UNKNOWN"),
        "headers": dict(getattr(request, "headers", {})),
        "client": getattr(request, "client", None),
        "timestamp": time.time()
    }
    
    # Include the request body if requested
    if include_body:
        try:
            body = getattr(request, "body", None)
            if body:
                info["body"] = body
        except Exception:
            pass
    
    # Log the request
    logger.info(f"Request: {json.dumps(info, default=str)}")

def log_response(logger: logging.Logger, response: Any, include_body: bool = False) -> None:
    """
    Log a response.
    
    Args:
        logger: The logger to use
        response: The response to log
        include_body: Whether to include the response body
    """
    # Extract response information
    info = {
        "status_code": getattr(response, "status_code", 0),
        "headers": dict(getattr(response, "headers", {})),
        "timestamp": time.time()
    }
    
    # Include the response body if requested
    if include_body:
        try:
            body = getattr(response, "body", None)
            if body:
                info["body"] = body
        except Exception:
            pass
    
    # Log the response
    logger.info(f"Response: {json.dumps(info, default=str)}")

def log_database_query(logger: logging.Logger, query: str, params: Any = None, duration: Optional[float] = None) -> None:
    """
    Log a database query.
    
    Args:
        logger: The logger to use
        query: The query to log
        params: The query parameters
        duration: The query duration in seconds
    """
    # Sanitize the query
    sanitized_query = query.strip()
    
    # Log the query
    if duration is not None:
        logger.debug(f"Query ({duration:.6f}s): {sanitized_query} - Params: {params}")
    else:
        logger.debug(f"Query: {sanitized_query} - Params: {params}")

def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """
    Log a performance metric.
    
    Args:
        logger: The logger to use
        operation: The operation name
        duration: The operation duration in seconds
    """
    logger.info(f"Performance: {operation} took {duration:.6f} seconds")

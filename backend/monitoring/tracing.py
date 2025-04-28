"""
Tracing module.

This module provides functions for distributed tracing.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import monitoring_config

# Configure logging
logger = logging.getLogger(__name__)

# Trace context
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")
parent_span_id_var: ContextVar[str] = ContextVar("parent_span_id", default="")

# Trace storage
traces: Dict[str, Dict[str, Any]] = {}

def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        str: A unique ID
    """
    return str(uuid.uuid4())

def get_trace_id() -> str:
    """
    Get the current trace ID.
    
    Returns:
        str: The current trace ID
    """
    return trace_id_var.get()

def get_span_id() -> str:
    """
    Get the current span ID.
    
    Returns:
        str: The current span ID
    """
    return span_id_var.get()

def get_parent_span_id() -> str:
    """
    Get the current parent span ID.
    
    Returns:
        str: The current parent span ID
    """
    return parent_span_id_var.get()

def start_trace() -> str:
    """
    Start a new trace.
    
    Returns:
        str: The trace ID
    """
    if not monitoring_config["tracing"]["enabled"]:
        return ""
    
    trace_id = generate_id()
    span_id = generate_id()
    
    trace_id_var.set(trace_id)
    span_id_var.set(span_id)
    parent_span_id_var.set("")
    
    traces[trace_id] = {
        "trace_id": trace_id,
        "spans": {
            span_id: {
                "span_id": span_id,
                "parent_span_id": "",
                "start_time": time.time(),
                "end_time": None,
                "name": "root",
                "attributes": {}
            }
        }
    }
    
    return trace_id

def start_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
    """
    Start a new span.
    
    Args:
        name: The span name
        attributes: The span attributes
        
    Returns:
        str: The span ID
    """
    if not monitoring_config["tracing"]["enabled"]:
        return ""
    
    trace_id = get_trace_id()
    parent_span_id = get_span_id()
    span_id = generate_id()
    
    if not trace_id:
        trace_id = start_trace()
        parent_span_id = get_span_id()
    
    span_id_var.set(span_id)
    parent_span_id_var.set(parent_span_id)
    
    if trace_id in traces:
        traces[trace_id]["spans"][span_id] = {
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "start_time": time.time(),
            "end_time": None,
            "name": name,
            "attributes": attributes or {}
        }
    
    return span_id

def end_span() -> None:
    """
    End the current span.
    """
    if not monitoring_config["tracing"]["enabled"]:
        return
    
    trace_id = get_trace_id()
    span_id = get_span_id()
    parent_span_id = get_parent_span_id()
    
    if trace_id in traces and span_id in traces[trace_id]["spans"]:
        traces[trace_id]["spans"][span_id]["end_time"] = time.time()
    
    span_id_var.set(parent_span_id)
    
    if parent_span_id:
        parent_parent_span_id = ""
        for span in traces[trace_id]["spans"].values():
            if span["span_id"] == parent_span_id:
                parent_parent_span_id = span["parent_span_id"]
                break
        parent_span_id_var.set(parent_parent_span_id)

def add_span_attribute(key: str, value: Any) -> None:
    """
    Add an attribute to the current span.
    
    Args:
        key: The attribute key
        value: The attribute value
    """
    if not monitoring_config["tracing"]["enabled"]:
        return
    
    trace_id = get_trace_id()
    span_id = get_span_id()
    
    if trace_id in traces and span_id in traces[trace_id]["spans"]:
        traces[trace_id]["spans"][span_id]["attributes"][key] = value

def get_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a trace by ID.
    
    Args:
        trace_id: The trace ID
        
    Returns:
        Optional[Dict[str, Any]]: The trace or None if not found
    """
    if not monitoring_config["tracing"]["enabled"]:
        return None
    
    return traces.get(trace_id)

def get_span(trace_id: str, span_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a span by trace ID and span ID.
    
    Args:
        trace_id: The trace ID
        span_id: The span ID
        
    Returns:
        Optional[Dict[str, Any]]: The span or None if not found
    """
    if not monitoring_config["tracing"]["enabled"]:
        return None
    
    trace = get_trace(trace_id)
    if trace:
        return trace["spans"].get(span_id)
    return None

def clear_traces() -> None:
    """
    Clear all traces.
    """
    if not monitoring_config["tracing"]["enabled"]:
        return
    
    traces.clear()

def init_tracing() -> None:
    """
    Initialize tracing.
    """
    if not monitoring_config["tracing"]["enabled"]:
        logger.info("Tracing disabled")
        return
    
    try:
        logger.info("Tracing initialized")
    except Exception as e:
        logger.error(f"Error initializing tracing: {e}", exc_info=True)

def shutdown_tracing() -> None:
    """
    Shutdown tracing.
    """
    if not monitoring_config["tracing"]["enabled"]:
        return
    
    try:
        clear_traces()
        logger.info("Tracing shutdown")
    except Exception as e:
        logger.error(f"Error shutting down tracing: {e}", exc_info=True)

class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed tracing.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response
        """
        if not monitoring_config["tracing"]["enabled"]:
            return await call_next(request)
        
        # Check if we should sample this request
        if monitoring_config["tracing"]["sample_rate"] < 1.0:
            import random
            if random.random() > monitoring_config["tracing"]["sample_rate"]:
                return await call_next(request)
        
        # Start a new trace
        trace_id = start_trace()
        
        # Add request attributes
        add_span_attribute("http.method", request.method)
        add_span_attribute("http.url", str(request.url))
        add_span_attribute("http.host", request.headers.get("host", ""))
        add_span_attribute("http.user_agent", request.headers.get("user-agent", ""))
        add_span_attribute("http.client_ip", request.client.host)
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Add response attributes
            add_span_attribute("http.status_code", response.status_code)
            
            # End the span
            end_span()
            
            # Add trace headers to the response
            response.headers["X-Trace-ID"] = trace_id
            
            return response
        except Exception as e:
            # Add error attributes
            add_span_attribute("error", True)
            add_span_attribute("error.message", str(e))
            add_span_attribute("error.type", type(e).__name__)
            
            # End the span
            end_span()
            
            # Re-raise the exception
            raise

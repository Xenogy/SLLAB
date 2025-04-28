"""
Logging configuration module.

This module provides functions for configuring logging.
"""

import os
import logging
import logging.handlers
import json
from typing import Dict, Any, Optional, List, Callable

from .config import monitoring_config

def configure_logging() -> None:
    """
    Configure logging.
    """
    if not monitoring_config["logging"]["enabled"]:
        return
    
    try:
        # Get configuration
        log_level = monitoring_config["logging"]["level"]
        log_format = monitoring_config["logging"]["format"]
        log_file = monitoring_config["logging"]["file"]
        log_rotation = monitoring_config["logging"]["rotation"]
        log_rotation_size = monitoring_config["logging"]["rotation_size"]
        log_rotation_count = monitoring_config["logging"]["rotation_count"]
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Create handlers
        handlers = []
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
        
        # Add file handler if specified
        if log_file:
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            if log_rotation:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=log_rotation_size,
                    backupCount=log_rotation_count
                )
            else:
                file_handler = logging.FileHandler(log_file)
            
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add handlers
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Configure library loggers
        logging.getLogger("uvicorn").setLevel(log_level)
        logging.getLogger("uvicorn.access").setLevel(log_level)
        logging.getLogger("uvicorn.error").setLevel(log_level)
        
        # Log configuration
        logger = logging.getLogger(__name__)
        logger.info("Logging configured")
        logger.debug(f"Log level: {logging.getLevelName(log_level)}")
        logger.debug(f"Log format: {log_format}")
        logger.debug(f"Log file: {log_file}")
        logger.debug(f"Log rotation: {log_rotation}")
        logger.debug(f"Log rotation size: {log_rotation_size}")
        logger.debug(f"Log rotation count: {log_rotation_count}")
    except Exception as e:
        print(f"Error configuring logging: {e}")

class JsonFormatter(logging.Formatter):
    """
    JSON formatter for logging.
    """
    
    def format(self, record):
        """
        Format the record as JSON.
        
        Args:
            record: The log record
            
        Returns:
            str: The formatted log record
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        
        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def configure_json_logging() -> None:
    """
    Configure JSON logging.
    """
    if not monitoring_config["logging"]["enabled"]:
        return
    
    try:
        # Get configuration
        log_level = monitoring_config["logging"]["level"]
        log_file = monitoring_config["logging"]["file"]
        log_rotation = monitoring_config["logging"]["rotation"]
        log_rotation_size = monitoring_config["logging"]["rotation_size"]
        log_rotation_count = monitoring_config["logging"]["rotation_count"]
        
        # Create formatter
        formatter = JsonFormatter()
        
        # Create handlers
        handlers = []
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
        
        # Add file handler if specified
        if log_file:
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            if log_rotation:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=log_rotation_size,
                    backupCount=log_rotation_count
                )
            else:
                file_handler = logging.FileHandler(log_file)
            
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add handlers
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Configure library loggers
        logging.getLogger("uvicorn").setLevel(log_level)
        logging.getLogger("uvicorn.access").setLevel(log_level)
        logging.getLogger("uvicorn.error").setLevel(log_level)
        
        # Log configuration
        logger = logging.getLogger(__name__)
        logger.info("JSON logging configured")
    except Exception as e:
        print(f"Error configuring JSON logging: {e}")

class TraceContextFilter(logging.Filter):
    """
    Filter for adding trace context to log records.
    """
    
    def filter(self, record):
        """
        Add trace context to the log record.
        
        Args:
            record: The log record
            
        Returns:
            bool: Always True
        """
        from .tracing import get_trace_id, get_span_id
        
        record.trace_id = get_trace_id()
        record.span_id = get_span_id()
        
        return True

def add_trace_context_to_logging() -> None:
    """
    Add trace context to logging.
    """
    if not monitoring_config["logging"]["enabled"] or not monitoring_config["tracing"]["enabled"]:
        return
    
    try:
        # Create filter
        trace_filter = TraceContextFilter()
        
        # Add filter to root logger
        root_logger = logging.getLogger()
        root_logger.addFilter(trace_filter)
        
        # Log configuration
        logger = logging.getLogger(__name__)
        logger.info("Trace context added to logging")
    except Exception as e:
        print(f"Error adding trace context to logging: {e}")

def init_logging() -> None:
    """
    Initialize logging.
    """
    if not monitoring_config["logging"]["enabled"]:
        print("Logging disabled")
        return
    
    try:
        # Configure logging
        configure_logging()
        
        # Add trace context to logging
        if monitoring_config["tracing"]["enabled"]:
            add_trace_context_to_logging()
        
        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info("Logging initialized")
    except Exception as e:
        print(f"Error initializing logging: {e}")

def shutdown_logging() -> None:
    """
    Shutdown logging.
    """
    if not monitoring_config["logging"]["enabled"]:
        return
    
    try:
        # Log shutdown
        logger = logging.getLogger(__name__)
        logger.info("Logging shutdown")
        
        # Shutdown logging
        logging.shutdown()
    except Exception as e:
        print(f"Error shutting down logging: {e}")

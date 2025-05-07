"""
Utility functions for logging.

This module provides utility functions for logging events to the log storage system.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import traceback
import threading
import queue
import time
import os

from db.repositories.logs import LogRepository
from monitoring.tracing import get_trace_id, get_span_id, get_parent_span_id

# Configure logging
logger = logging.getLogger(__name__)

# Create a thread-local storage for log context
_log_context = threading.local()

# Create a queue for asynchronous logging
_log_queue = queue.Queue()

# Flag to control the background thread
_log_thread_running = False
_log_thread = None

def set_log_context(
    user_id: Optional[int] = None,
    user_role: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None
) -> None:
    """
    Set context for logging.

    Args:
        user_id (Optional[int], optional): User ID. Defaults to None.
        user_role (Optional[str], optional): User role. Defaults to None.
        source (Optional[str], optional): Log source. Defaults to None.
        category (Optional[str], optional): Log category. Defaults to None.
        entity_type (Optional[str], optional): Entity type. Defaults to None.
        entity_id (Optional[str], optional): Entity ID. Defaults to None.
    """
    if not hasattr(_log_context, 'context'):
        _log_context.context = {}

    if user_id is not None:
        _log_context.context['user_id'] = user_id

    if user_role is not None:
        _log_context.context['user_role'] = user_role

    if source is not None:
        _log_context.context['source'] = source

    if category is not None:
        _log_context.context['category'] = category

    if entity_type is not None:
        _log_context.context['entity_type'] = entity_type

    if entity_id is not None:
        _log_context.context['entity_id'] = entity_id

def get_log_context() -> Dict[str, Any]:
    """
    Get the current log context.

    Returns:
        Dict[str, Any]: The current log context
    """
    if not hasattr(_log_context, 'context'):
        _log_context.context = {}

    return _log_context.context

def clear_log_context() -> None:
    """
    Clear the current log context.
    """
    if hasattr(_log_context, 'context'):
        _log_context.context = {}

def log_event(
    message: str,
    level: str = "INFO",
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    timestamp: Optional[datetime] = None,
    async_log: bool = False  # Changed default to False to ensure logs are stored
) -> Optional[int]:
    """
    Log an event to the log storage system.

    Args:
        message (str): The log message
        level (str, optional): The log level. Defaults to "INFO".
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        user_id (Optional[int], optional): The user ID. Defaults to None.
        owner_id (Optional[int], optional): The owner ID. Defaults to None.
        trace_id (Optional[str], optional): The trace ID. Defaults to None.
        span_id (Optional[str], optional): The span ID. Defaults to None.
        parent_span_id (Optional[str], optional): The parent span ID. Defaults to None.
        timestamp (Optional[datetime], optional): The timestamp. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to False.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    try:
        # Get context values if not provided
        context = get_log_context()

        if category is None and 'category' in context:
            category = context['category']

        if source is None and 'source' in context:
            source = context['source']

        if entity_type is None and 'entity_type' in context:
            entity_type = context['entity_type']

        if entity_id is None and 'entity_id' in context:
            entity_id = context['entity_id']

        if user_id is None and 'user_id' in context:
            user_id = context['user_id']

        # Set default source to 'backend' if not provided
        if source is None:
            source = 'backend'

        # Ensure source is a string
        if not isinstance(source, str):
            source = str(source)

        # Get trace context if not provided
        if trace_id is None:
            trace_id = get_trace_id()

        if span_id is None:
            span_id = get_span_id()

        if parent_span_id is None:
            parent_span_id = get_parent_span_id()

        # Set timestamp to current time if not provided
        if timestamp is None:
            timestamp = datetime.now()

        # Log to Python logger as well
        python_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(python_level, message)

        # If async logging is enabled, add to queue and return
        if async_log:
            logger.debug(f"Adding log to queue: {message}")
            _log_queue.put({
                'message': message,
                'level': level,
                'category': category,
                'source': source,
                'details': details,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'user_id': user_id,
                'owner_id': owner_id,
                'trace_id': trace_id,
                'span_id': span_id,
                'parent_span_id': parent_span_id,
                'timestamp': timestamp
            })

            # Start the background thread if not running
            start_log_thread()
            logger.debug(f"Log queue size after adding: {_log_queue.qsize()}")

            return None

        # Otherwise, log synchronously
        # Create log repository with admin context to bypass RLS
        logger.debug(f"Logging synchronously: {message}")
        log_repo = LogRepository(user_id=1, user_role="admin")

        # Add log entry
        log = log_repo.add_log(
            message=message,
            level=level,
            category=category,
            source=source,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            owner_id=owner_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            timestamp=timestamp
        )

        if log and isinstance(log, dict) and 'id' in log:
            logger.debug(f"Log entry created with ID: {log['id']}")
            return log['id']
        elif log and isinstance(log, dict) and 'log_id' in log:
            logger.debug(f"Log entry created with ID: {log['log_id']}")
            return log['log_id']
        else:
            logger.warning(f"Log entry created but no ID returned: {log}")
            return None
    except Exception as e:
        # Log the error to the Python logger
        logger.error(f"Error logging event: {e}")
        logger.error(traceback.format_exc())
        return None

def log_debug(
    message: str,
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    async_log: bool = False
) -> Optional[int]:
    """
    Log a debug event.

    Args:
        message (str): The log message
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to True.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    return log_event(
        message=message,
        level="DEBUG",
        category=category,
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        async_log=async_log
    )

def log_info(
    message: str,
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    async_log: bool = False
) -> Optional[int]:
    """
    Log an info event.

    Args:
        message (str): The log message
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to True.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    return log_event(
        message=message,
        level="INFO",
        category=category,
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        async_log=async_log
    )

def log_warning(
    message: str,
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    async_log: bool = False
) -> Optional[int]:
    """
    Log a warning event.

    Args:
        message (str): The log message
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to True.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    return log_event(
        message=message,
        level="WARNING",
        category=category,
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        async_log=async_log
    )

def log_error(
    message: str,
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    exception: Optional[Exception] = None,
    async_log: bool = False
) -> Optional[int]:
    """
    Log an error event.

    Args:
        message (str): The log message
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        exception (Optional[Exception], optional): The exception. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to True.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    # Add exception details if provided
    if exception:
        if details is None:
            details = {}

        details['exception'] = {
            'type': type(exception).__name__,
            'message': str(exception),
            'traceback': traceback.format_exc()
        }

    return log_event(
        message=message,
        level="ERROR",
        category=category,
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        async_log=async_log
    )

def log_critical(
    message: str,
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    exception: Optional[Exception] = None,
    async_log: bool = False  # Critical logs are synchronous by default
) -> Optional[int]:
    """
    Log a critical event.

    Args:
        message (str): The log message
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        exception (Optional[Exception], optional): The exception. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to False.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    # Add exception details if provided
    if exception:
        if details is None:
            details = {}

        details['exception'] = {
            'type': type(exception).__name__,
            'message': str(exception),
            'traceback': traceback.format_exc()
        }

    return log_event(
        message=message,
        level="CRITICAL",
        category=category,
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        async_log=async_log
    )

def log_exception(
    exception: Exception,
    message: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    async_log: bool = False
) -> Optional[int]:
    """
    Log an exception.

    Args:
        exception (Exception): The exception to log
        message (Optional[str], optional): The log message. Defaults to None.
        category (Optional[str], optional): The log category. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to True.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    # Use exception message if no message provided
    if message is None:
        message = f"Exception: {str(exception)}"

    return log_error(
        message=message,
        category=category,
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        exception=exception,
        async_log=async_log
    )

def log_audit(
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    owner_id: Optional[int] = None,
    async_log: bool = False  # Audit logs are synchronous by default
) -> Optional[int]:
    """
    Log an audit event.

    Args:
        action (str): The action being audited
        user_id (Optional[int], optional): The user ID. Defaults to None.
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        owner_id (Optional[int], optional): The owner ID for RLS. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to False.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    # Get user_id from context if not provided
    if user_id is None:
        context = get_log_context()
        if 'user_id' in context:
            user_id = context['user_id']

    # Set owner_id to user_id if not provided
    if owner_id is None and user_id is not None:
        owner_id = user_id

    # Set default source if not provided
    if source is None:
        source = 'backend'

    # Ensure source is a string
    if not isinstance(source, str):
        source = str(source)

    return log_event(
        message=f"AUDIT: {action}",
        level="INFO",
        category="audit",
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        owner_id=owner_id,
        async_log=async_log
    )

def log_security(
    event: str,
    user_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    level: str = "WARNING",
    owner_id: Optional[int] = None,
    async_log: bool = False  # Security logs are synchronous by default
) -> Optional[int]:
    """
    Log a security event.

    Args:
        event (str): The security event
        user_id (Optional[int], optional): The user ID. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        level (str, optional): The log level. Defaults to "WARNING".
        owner_id (Optional[int], optional): The owner ID for RLS. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to False.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    # Get user_id from context if not provided
    if user_id is None:
        context = get_log_context()
        if 'user_id' in context:
            user_id = context['user_id']

    # Set owner_id to user_id if not provided
    if owner_id is None and user_id is not None:
        owner_id = user_id

    # Set default source if not provided
    if source is None:
        source = 'backend'

    # Ensure source is a string
    if not isinstance(source, str):
        source = str(source)

    return log_event(
        message=f"SECURITY: {event}",
        level=level,
        category="security",
        source=source,
        details=details,
        user_id=user_id,
        owner_id=owner_id,
        async_log=async_log
    )

def log_performance(
    operation: str,
    duration_ms: float,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    async_log: bool = False
) -> Optional[int]:
    """
    Log a performance event.

    Args:
        operation (str): The operation being measured
        duration_ms (float): The duration in milliseconds
        entity_type (Optional[str], optional): The entity type. Defaults to None.
        entity_id (Optional[str], optional): The entity ID. Defaults to None.
        details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
        source (Optional[str], optional): The log source. Defaults to None.
        async_log (bool, optional): Whether to log asynchronously. Defaults to True.

    Returns:
        Optional[int]: The ID of the inserted log entry or None if insertion failed or async
    """
    if details is None:
        details = {}

    details['duration_ms'] = duration_ms

    # Determine level based on duration
    level = "INFO"
    if duration_ms > 1000:  # More than 1 second
        level = "WARNING"
    elif duration_ms > 5000:  # More than 5 seconds
        level = "ERROR"

    # Set default source if not provided
    if source is None:
        source = 'backend'

    # Ensure source is a string
    if not isinstance(source, str):
        source = str(source)

    return log_event(
        message=f"PERFORMANCE: {operation} took {duration_ms:.2f}ms",
        level=level,
        category="performance",
        source=source,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
        async_log=async_log
    )

def _process_log_queue() -> None:
    """
    Process the log queue in a background thread.
    """
    global _log_thread_running

    logger.info("Starting log queue processing thread")

    try:
        # Create log repository with admin context to bypass RLS
        log_repo = LogRepository(user_id=1, user_role="admin")

        while _log_thread_running:
            try:
                # Get a batch of log entries (up to 100)
                batch = []
                try:
                    while len(batch) < 100:
                        # Get an item with a timeout to allow thread to exit
                        item = _log_queue.get(timeout=0.1)
                        batch.append(item)
                        _log_queue.task_done()
                except queue.Empty:
                    # No more items in the queue
                    pass

                # If batch is empty, continue
                if not batch:
                    time.sleep(0.1)
                    continue

                # Process the batch
                for log_entry in batch:
                    try:
                        log_repo.add_log(
                            message=log_entry['message'],
                            level=log_entry['level'],
                            category=log_entry['category'],
                            source=log_entry['source'],
                            details=log_entry['details'],
                            entity_type=log_entry['entity_type'],
                            entity_id=log_entry['entity_id'],
                            user_id=log_entry['user_id'],
                            owner_id=log_entry['owner_id'],
                            trace_id=log_entry['trace_id'],
                            span_id=log_entry['span_id'],
                            parent_span_id=log_entry['parent_span_id'],
                            timestamp=log_entry['timestamp']
                        )
                    except Exception as e:
                        logger.error(f"Error processing log entry: {e}")

            except Exception as e:
                logger.error(f"Error in log queue processing thread: {e}")
                logger.error(traceback.format_exc())
                time.sleep(1)  # Sleep to avoid tight loop in case of persistent errors

    except Exception as e:
        logger.error(f"Fatal error in log queue processing thread: {e}")
        logger.error(traceback.format_exc())

    finally:
        logger.info("Log queue processing thread stopped")
        _log_thread_running = False

def start_log_thread() -> None:
    """
    Start the background thread for processing the log queue.
    """
    global _log_thread_running, _log_thread

    if _log_thread_running and _log_thread and _log_thread.is_alive():
        # Thread is already running
        return

    # Set the flag and start the thread
    _log_thread_running = True
    _log_thread = threading.Thread(target=_process_log_queue, daemon=True)
    _log_thread.start()

def stop_log_thread() -> None:
    """
    Stop the background thread for processing the log queue.
    """
    global _log_thread_running, _log_thread

    if not _log_thread_running or not _log_thread:
        # Thread is not running
        return

    # Set the flag to stop the thread
    _log_thread_running = False

    # Wait for the thread to finish (with timeout)
    if _log_thread:
        _log_thread.join(timeout=5.0)
        if _log_thread.is_alive():
            logger.warning("Log queue processing thread did not stop gracefully")
        _log_thread = None

def init_logging() -> None:
    """
    Initialize the logging system.
    """
    try:
        # Start the background thread
        start_log_thread()

        # Create a test log entry synchronously to verify the logging system is working
        test_log_id = log_info(
            "Log storage system initialized",
            category="system",
            source="backend",
            async_log=False  # Use synchronous logging for initialization
        )

        if test_log_id:
            logger.info(f"Test log entry created successfully with ID: {test_log_id}")
        else:
            logger.warning("Failed to create test log entry during initialization")

    except Exception as e:
        logger.error(f"Error initializing log storage system: {e}")
        logger.error(traceback.format_exc())

def shutdown_logging() -> None:
    """
    Shutdown the logging system.
    """
    try:
        # Log shutdown
        log_info("Log storage system shutting down", category="system", source="backend", async_log=False)

        # Stop the background thread
        stop_log_thread()

        # Process any remaining items in the queue
        while not _log_queue.empty():
            try:
                item = _log_queue.get(block=False)

                # Create log repository with admin context to bypass RLS
                log_repo = LogRepository(user_id=1, user_role="admin")

                log_repo.add_log(
                    message=item['message'],
                    level=item['level'],
                    category=item['category'],
                    source=item['source'],
                    details=item['details'],
                    entity_type=item['entity_type'],
                    entity_id=item['entity_id'],
                    user_id=item['user_id'],
                    owner_id=item['owner_id'],
                    trace_id=item['trace_id'],
                    span_id=item['span_id'],
                    parent_span_id=item['parent_span_id'],
                    timestamp=item['timestamp']
                )

                _log_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing remaining log entry during shutdown: {e}")
    except Exception as e:
        logger.error(f"Error shutting down log storage system: {e}")
        logger.error(traceback.format_exc())

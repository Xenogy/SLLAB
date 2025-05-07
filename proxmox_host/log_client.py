"""
Log client for the Proxmox Host Agent.

This module provides a client for sending logs to the central log storage system.
"""

import asyncio
import aiohttp
import json
import socket
import platform
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

class LogClient:
    """Client for sending logs to the central log storage system."""

    def __init__(self, api_url: str, api_key: str, node_id: int):
        """
        Initialize the log client.

        Args:
            api_url: Base URL of the API.
            api_key: API key for authentication.
            node_id: Node ID in AccountDB.
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.node_id = node_id
        self.hostname = socket.gethostname()

        # Create a queue for asynchronous logging
        self._log_queue = asyncio.Queue()
        self._log_task = None
        self._log_task_running = False

        # Start the background task
        self._start_log_task()

    def _start_log_task(self) -> None:
        """Start the background task for processing the log queue."""
        if self._log_task_running and self._log_task and not self._log_task.done():
            # Task is already running
            return

        # Set the flag and start the task
        self._log_task_running = True
        self._log_task = asyncio.create_task(self._process_log_queue())

    async def _process_log_queue(self) -> None:
        """Process the log queue in a background task."""
        logger.info("Starting log queue processing task")

        try:
            while self._log_task_running:
                try:
                    # Get a batch of log entries (up to 10)
                    batch = []
                    try:
                        for _ in range(10):
                            # Get an item with a timeout to allow task to exit
                            try:
                                item = await asyncio.wait_for(self._log_queue.get(), 0.1)
                                batch.append(item)
                                self._log_queue.task_done()
                            except asyncio.TimeoutError:
                                # No more items in the queue
                                break
                    except Exception as e:
                        logger.error(f"Error getting items from queue: {e}")

                    # If batch is empty, continue
                    if not batch:
                        await asyncio.sleep(1)
                        continue

                    # Process the batch
                    await self._send_logs_batch(batch)

                except Exception as e:
                    logger.error(f"Error in log queue processing task: {e}")
                    await asyncio.sleep(1)  # Sleep to avoid tight loop in case of persistent errors

        except Exception as e:
            logger.error(f"Fatal error in log queue processing task: {e}")

        finally:
            logger.info("Log queue processing task stopped")
            self._log_task_running = False

    async def _send_logs_batch(self, logs: List[Dict[str, Any]]) -> None:
        """
        Send a batch of logs to the central log storage system.

        Args:
            logs: List of log entries to send.
        """
        try:
            # Prepare the URL with API key as query parameter
            url = f"{self.api_url}/logs?api_key={self.api_key}"

            # Send each log individually (could be optimized with a batch endpoint)
            async with aiohttp.ClientSession() as session:
                for log_entry in logs:
                    try:
                        async with session.post(url, json=log_entry) as response:
                            if response.status != 200 and response.status != 201:
                                response_text = await response.text()
                                logger.error(f"Failed to send log to central storage: {response.status} {response_text}")
                    except Exception as e:
                        logger.error(f"Error sending log to central storage: {e}")

        except Exception as e:
            logger.error(f"Error sending log batch to central storage: {e}")

    async def log(self,
                 message: str,
                 level: str = "INFO",
                 category: str = "proxmox_host",
                 details: Optional[Dict[str, Any]] = None,
                 entity_type: Optional[str] = None,
                 entity_id: Optional[str] = None,
                 async_log: bool = True) -> None:
        """
        Log a message to the central log storage system.

        Args:
            message: The log message.
            level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            category: The log category.
            details: Additional details for the log entry.
            entity_type: The type of entity related to the log.
            entity_id: The ID of the entity related to the log.
            async_log: Whether to log asynchronously.
        """
        # Create the log entry
        log_entry = {
            "message": message,
            "level": level,
            "category": category,
            "source": "proxmox_host",
            "details": details or {},
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add node information to details
        if "node_info" not in log_entry["details"]:
            log_entry["details"]["node_info"] = {
                "node_id": self.node_id,
                "hostname": self.hostname,
                "platform": platform.system(),
                "platform_version": platform.release()
            }

        # Log to Python logger as well
        log_level = getattr(logger.level, level.upper(), logger.level.INFO)
        logger.log(log_level, f"[{category}] {message}")

        # If async logging is enabled, add to queue and return
        if async_log:
            await self._log_queue.put(log_entry)
            return

        # Otherwise, log synchronously
        try:
            # Prepare the URL with API key as query parameter
            url = f"{self.api_url}/logs?api_key={self.api_key}"

            # Send the log entry
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=log_entry) as response:
                    if response.status != 200 and response.status != 201:
                        response_text = await response.text()
                        logger.error(f"Failed to send log to central storage: {response.status} {response_text}")

        except Exception as e:
            logger.error(f"Error sending log to central storage: {e}")

    async def log_debug(self, message: str, category: str = "proxmox_host", details: Optional[Dict[str, Any]] = None,
                       entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> None:
        """Log a debug message."""
        await self.log(message, "DEBUG", category, details, entity_type, entity_id)

    async def log_info(self, message: str, category: str = "proxmox_host", details: Optional[Dict[str, Any]] = None,
                      entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> None:
        """Log an info message."""
        await self.log(message, "INFO", category, details, entity_type, entity_id)

    async def log_warning(self, message: str, category: str = "proxmox_host", details: Optional[Dict[str, Any]] = None,
                         entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> None:
        """Log a warning message."""
        await self.log(message, "WARNING", category, details, entity_type, entity_id)

    async def log_error(self, message: str, category: str = "proxmox_host", details: Optional[Dict[str, Any]] = None,
                       entity_type: Optional[str] = None, entity_id: Optional[str] = None,
                       exception: Optional[Exception] = None) -> None:
        """Log an error message."""
        if exception and details is None:
            details = {}

        if exception and details is not None:
            details["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }

        await self.log(message, "ERROR", category, details, entity_type, entity_id)

    async def log_critical(self, message: str, category: str = "proxmox_host", details: Optional[Dict[str, Any]] = None,
                          entity_type: Optional[str] = None, entity_id: Optional[str] = None,
                          exception: Optional[Exception] = None) -> None:
        """Log a critical message."""
        if exception and details is None:
            details = {}

        if exception and details is not None:
            details["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }

        # Critical logs are sent synchronously by default
        await self.log(message, "CRITICAL", category, details, entity_type, entity_id, async_log=False)

    async def log_auth(self, message: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an authentication event.

        Args:
            message: The log message.
            success: Whether the authentication was successful.
            details: Additional details for the log entry.
        """
        if details is None:
            details = {}

        details["auth_success"] = success

        category = "security"
        level = "INFO" if success else "WARNING"

        await self.log(message, level, category, details)

    async def log_api_call(self, endpoint: str, method: str, status_code: Optional[int] = None,
                          error: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an API call.

        Args:
            endpoint: The API endpoint.
            method: The HTTP method.
            status_code: The HTTP status code.
            error: The error message, if any.
            details: Additional details for the log entry.
        """
        if details is None:
            details = {}

        details.update({
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        })

        if error:
            details["error"] = error
            message = f"API call failed: {method} {endpoint} - {error}"
            level = "ERROR"
        else:
            message = f"API call: {method} {endpoint}"
            level = "DEBUG"

        await self.log(message, level, "api", details)

    async def log_webhook(self, webhook_type: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a webhook event.

        Args:
            webhook_type: The type of webhook.
            success: Whether the webhook was successful.
            details: Additional details for the log entry.
        """
        if details is None:
            details = {}

        details["webhook_type"] = webhook_type
        details["webhook_success"] = success

        message = f"Webhook {webhook_type}: {'Success' if success else 'Failed'}"
        level = "INFO" if success else "WARNING"

        await self.log(message, level, "webhook", details)

    def create_loguru_sink(self):
        """
        Create a loguru sink that sends logs to the central log storage system.

        Returns:
            callable: A function that can be used as a loguru sink.
        """
        async def _async_log_handler(message):
            """Asynchronous handler for loguru messages."""
            record = message.record

            # Extract details from the record
            details = {
                "function": record["function"],
                "file": record["file"].name,
                "line": record["line"],
                "process": record["process"].id,
            }

            # Add exception information if available
            if record["exception"]:
                details["exception"] = {
                    "type": record["exception"].type.__name__ if hasattr(record["exception"], "type") else "Exception",
                    "value": str(record["exception"].value) if hasattr(record["exception"], "value") else str(record["exception"]),
                    "traceback": record["exception"].traceback if hasattr(record["exception"], "traceback") else None
                }

            # Send the log
            await self.log(
                message=record["message"],
                level=record["level"].name,
                category="proxmox_host",
                details=details,
                async_log=True
            )

        def sink(message):
            """Synchronous wrapper for the asynchronous handler."""
            # Create a new event loop in the current thread if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async handler
            if loop.is_running():
                # If the loop is already running, create a task
                asyncio.create_task(_async_log_handler(message))
            else:
                # Otherwise, run the coroutine directly
                loop.run_until_complete(_async_log_handler(message))

        return sink

    async def shutdown(self) -> None:
        """Shutdown the log client and flush any pending logs."""
        logger.info("Shutting down log client")

        # Stop the background task
        self._log_task_running = False

        if self._log_task:
            try:
                # Wait for the task to complete
                await asyncio.wait_for(self._log_task, 5.0)
            except asyncio.TimeoutError:
                logger.warning("Log queue processing task did not stop gracefully")

        # Process any remaining items in the queue
        remaining_logs = []
        while not self._log_queue.empty():
            try:
                log_entry = self._log_queue.get_nowait()
                remaining_logs.append(log_entry)
                self._log_queue.task_done()
            except asyncio.QueueEmpty:
                break

        if remaining_logs:
            logger.info(f"Sending {len(remaining_logs)} remaining logs")
            await self._send_logs_batch(remaining_logs)

        logger.info("Log client shutdown complete")

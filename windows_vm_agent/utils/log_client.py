"""
Log client for the Windows VM Agent.

This module provides a client for sending logs to the central log storage system.
"""

import logging
import requests
import json
import socket
import platform
import threading
import queue
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class LogClient:
    """Client for sending logs to the central log storage system."""

    def __init__(self, api_url: str, api_key: str, vm_identifier: str):
        """
        Initialize the log client.

        Args:
            api_url: Base URL of the API.
            api_key: API key for authentication.
            vm_identifier: Identifier for this VM.
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.vm_identifier = vm_identifier
        self.hostname = socket.gethostname()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': f'WindowsVMAgent/1.0 ({platform.system()} {platform.release()})'
        })

        # Create a queue for asynchronous logging
        self._log_queue = queue.Queue()
        self._log_thread = None
        self._log_thread_running = False

        # Start the background thread
        self._start_log_thread()

    def _start_log_thread(self) -> None:
        """Start the background thread for processing the log queue."""
        if self._log_thread_running and self._log_thread and self._log_thread.is_alive():
            # Thread is already running
            return

        # Set the flag and start the thread
        self._log_thread_running = True
        self._log_thread = threading.Thread(target=self._process_log_queue, daemon=True)
        self._log_thread.start()

    def _process_log_queue(self) -> None:
        """Process the log queue in a background thread."""
        logger.info("Starting log queue processing thread")

        try:
            while self._log_thread_running:
                try:
                    # Get a batch of log entries (up to 10)
                    batch = []
                    try:
                        while len(batch) < 10:
                            # Get an item with a timeout to allow thread to exit
                            item = self._log_queue.get(timeout=0.1)
                            batch.append(item)
                            self._log_queue.task_done()
                    except queue.Empty:
                        # No more items in the queue
                        pass

                    # If batch is empty, continue
                    if not batch:
                        time.sleep(1)
                        continue

                    # Process the batch
                    self._send_logs_batch(batch)

                except Exception as e:
                    logger.error(f"Error in log queue processing thread: {e}")
                    time.sleep(1)  # Sleep to avoid tight loop in case of persistent errors

        except Exception as e:
            logger.error(f"Fatal error in log queue processing thread: {e}")

        finally:
            logger.info("Log queue processing thread stopped")
            self._log_thread_running = False

    def _send_logs_batch(self, logs: List[Dict[str, Any]]) -> None:
        """
        Send a batch of logs to the central log storage system.

        Args:
            logs: List of log entries to send.
        """
        try:
            # Prepare the URL with API key as query parameter
            # Check if the base URL already contains the endpoint path
            if self.api_url.endswith('/api'):
                # If the base URL ends with /api, use the correct path
                url = f"{self.api_url}/windows-vm-agent/logs?api_key={self.api_key}"
            else:
                # Otherwise, assume the base URL is the root
                url = f"{self.api_url}/windows-vm-agent/logs?api_key={self.api_key}"

            logger.info(f"Sending logs to URL: {url}")

            # Send each log individually (could be optimized with a batch endpoint)
            for log_entry in logs:
                try:
                    # Log the request details for debugging
                    logger.debug(f"Sending log entry: {json.dumps(log_entry)}")

                    # Make the request
                    response = self.session.post(url, json=log_entry)

                    if response.status_code != 200 and response.status_code != 201:
                        logger.error(f"Failed to send log to central storage: {response.status_code} {response.text}")
                        # Log more details about the error for debugging
                        if response.text:
                            try:
                                error_data = response.json()
                                logger.error(f"Error details: {json.dumps(error_data)}")
                            except:
                                logger.error(f"Error response (raw): {response.text}")

                        # Try alternative URL if the first one fails with 404
                        if response.status_code == 404:
                            logger.info("Trying alternative URL format...")

                            # If the URL was using /api/windows-vm-agent/logs, try without /api
                            if '/api/windows-vm-agent/' in url:
                                alt_url = url.replace('/api/windows-vm-agent/', '/windows-vm-agent/')
                            # If the URL was using /windows-vm-agent/logs, try with /api
                            else:
                                base_url = self.api_url.rstrip('/')
                                if not base_url.endswith('/api'):
                                    alt_url = f"{base_url}/api/windows-vm-agent/logs?api_key={self.api_key}"
                                else:
                                    alt_url = url

                            if alt_url != url:
                                logger.info(f"Trying alternative URL: {alt_url}")
                                alt_response = self.session.post(alt_url, json=log_entry)

                                if alt_response.status_code == 200 or alt_response.status_code == 201:
                                    logger.info(f"Alternative URL succeeded: {alt_response.status_code}")
                                    # Update the URL for future requests
                                    url = alt_url
                                else:
                                    logger.error(f"Alternative URL also failed: {alt_response.status_code} {alt_response.text}")
                    else:
                        logger.debug(f"Successfully sent log to central storage: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error sending log to central storage: {e}")

        except Exception as e:
            logger.error(f"Error sending log batch to central storage: {e}")

    def log(self,
            message: str,
            level: str = "INFO",
            category: str = "windows_vm_agent",
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
            "source": "windows_vm_agent",
            "details": details or {},
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add VM information to details
        if "vm_info" not in log_entry["details"]:
            log_entry["details"]["vm_info"] = {
                "vm_identifier": self.vm_identifier,
                "hostname": self.hostname,
                "platform": platform.system(),
                "platform_version": platform.release()
            }

        # Log to Python logger as well
        python_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(python_level, f"[{category}] {message}")

        # If async logging is enabled, add to queue and return
        if async_log:
            self._log_queue.put(log_entry)
            return

        # Otherwise, log synchronously
        try:
            # Prepare the URL with API key as query parameter
            # Check if the base URL already contains the endpoint path
            if self.api_url.endswith('/api'):
                # If the base URL ends with /api, use the correct path
                url = f"{self.api_url}/windows-vm-agent/logs?api_key={self.api_key}"
            else:
                # Otherwise, assume the base URL is the root
                url = f"{self.api_url}/windows-vm-agent/logs?api_key={self.api_key}"

            logger.info(f"Sending log to URL: {url}")

            # Log the request details for debugging
            logger.debug(f"Sending log entry: {json.dumps(log_entry)}")

            # Send the log entry
            response = self.session.post(url, json=log_entry)

            if response.status_code != 200 and response.status_code != 201:
                logger.error(f"Failed to send log to central storage: {response.status_code} {response.text}")
                # Log more details about the error for debugging
                if response.text:
                    try:
                        error_data = response.json()
                        logger.error(f"Error details: {json.dumps(error_data)}")
                    except:
                        logger.error(f"Error response (raw): {response.text}")

                # Try alternative URL if the first one fails with 404
                if response.status_code == 404:
                    logger.info("Trying alternative URL format...")

                    # If the URL was using /api/windows-vm-agent/logs, try without /api
                    if '/api/windows-vm-agent/' in url:
                        alt_url = url.replace('/api/windows-vm-agent/', '/windows-vm-agent/')
                    # If the URL was using /windows-vm-agent/logs, try with /api
                    else:
                        base_url = self.api_url.rstrip('/')
                        if not base_url.endswith('/api'):
                            alt_url = f"{base_url}/api/windows-vm-agent/logs?api_key={self.api_key}"
                        else:
                            alt_url = url

                    if alt_url != url:
                        logger.info(f"Trying alternative URL: {alt_url}")
                        alt_response = self.session.post(alt_url, json=log_entry)

                        if alt_response.status_code == 200 or alt_response.status_code == 201:
                            logger.info(f"Alternative URL succeeded: {alt_response.status_code}")
                            # Update the URL for future requests
                            self.api_url = alt_url.split('/windows-vm-agent/logs')[0]
                            logger.info(f"Updated base URL to: {self.api_url}")
                        else:
                            logger.error(f"Alternative URL also failed: {alt_response.status_code} {alt_response.text}")
            else:
                logger.debug(f"Successfully sent log to central storage: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending log to central storage: {e}")

    def log_debug(self, message: str, category: str = "windows_vm_agent", details: Optional[Dict[str, Any]] = None,
                 entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> None:
        """Log a debug message."""
        self.log(message, "DEBUG", category, details, entity_type, entity_id)

    def log_info(self, message: str, category: str = "windows_vm_agent", details: Optional[Dict[str, Any]] = None,
                entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> None:
        """Log an info message."""
        self.log(message, "INFO", category, details, entity_type, entity_id)

    def log_warning(self, message: str, category: str = "windows_vm_agent", details: Optional[Dict[str, Any]] = None,
                   entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> None:
        """Log a warning message."""
        self.log(message, "WARNING", category, details, entity_type, entity_id)

    def log_error(self, message: str, category: str = "windows_vm_agent", details: Optional[Dict[str, Any]] = None,
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

        self.log(message, "ERROR", category, details, entity_type, entity_id)

    def log_critical(self, message: str, category: str = "windows_vm_agent", details: Optional[Dict[str, Any]] = None,
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
        self.log(message, "CRITICAL", category, details, entity_type, entity_id, async_log=False)

    def log_auth(self, message: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
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

        self.log(message, level, category, details)

    def log_api_call(self, endpoint: str, method: str, status_code: Optional[int] = None,
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

        self.log(message, level, "api", details)

    def log_webhook(self, webhook_type: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
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

        self.log(message, level, "webhook", details)

    def shutdown(self) -> None:
        """Shutdown the log client and flush any pending logs."""
        logger.info("Shutting down log client")

        # Stop the background thread
        self._log_thread_running = False

        if self._log_thread:
            self._log_thread.join(timeout=5.0)
            if self._log_thread.is_alive():
                logger.warning("Log queue processing thread did not stop gracefully")

        # Process any remaining items in the queue
        remaining_logs = []
        while not self._log_queue.empty():
            try:
                log_entry = self._log_queue.get(block=False)
                remaining_logs.append(log_entry)
                self._log_queue.task_done()
            except queue.Empty:
                break

        if remaining_logs:
            logger.info(f"Sending {len(remaining_logs)} remaining logs")
            self._send_logs_batch(remaining_logs)

        logger.info("Log client shutdown complete")

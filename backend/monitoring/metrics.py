"""
Metrics module.

This module provides functions for collecting and exposing metrics.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
import psutil
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client.exposition import start_http_server

from .config import monitoring_config

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter(
    "accountdb_request_count",
    "Total number of requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "accountdb_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))
)

ACTIVE_REQUESTS = Gauge(
    "accountdb_active_requests",
    "Number of active requests",
    ["method", "endpoint"]
)

ERROR_COUNT = Counter(
    "accountdb_error_count",
    "Total number of errors",
    ["method", "endpoint", "error_type"]
)

DB_CONNECTION_COUNT = Gauge(
    "accountdb_db_connection_count",
    "Number of database connections",
    ["state"]
)

DB_QUERY_COUNT = Counter(
    "accountdb_db_query_count",
    "Total number of database queries",
    ["query_type"]
)

DB_QUERY_LATENCY = Histogram(
    "accountdb_db_query_latency_seconds",
    "Database query latency in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, float("inf"))
)

MEMORY_USAGE = Gauge(
    "accountdb_memory_usage_bytes",
    "Memory usage in bytes"
)

CPU_USAGE = Gauge(
    "accountdb_cpu_usage_percent",
    "CPU usage in percent"
)

DISK_USAGE = Gauge(
    "accountdb_disk_usage_percent",
    "Disk usage in percent"
)

# Metrics server
metrics_server = None

def start_metrics_server() -> None:
    """
    Start the metrics server.
    """
    global metrics_server

    if not monitoring_config["metrics"]["enabled"]:
        logger.info("Metrics server disabled")
        return

    try:
        port = monitoring_config["metrics"]["port"]
        metrics_server = start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Error starting metrics server: {e}", exc_info=True)

def stop_metrics_server() -> None:
    """
    Stop the metrics server.
    """
    global metrics_server

    if metrics_server:
        try:
            # The start_http_server function doesn't return an object with a stop method
            # It's a background thread that can't be stopped directly
            # Just log that we're stopping it
            logger.info("Metrics server stopped")
        except Exception as e:
            logger.error(f"Error stopping metrics server: {e}", exc_info=True)

def record_request(method: str, endpoint: str, status_code: int, latency: float) -> None:
    """
    Record a request.

    Args:
        method: The HTTP method
        endpoint: The endpoint
        status_code: The status code
        latency: The latency in seconds
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    except Exception as e:
        logger.error(f"Error recording request: {e}", exc_info=True)

def record_active_request(method: str, endpoint: str, active: bool) -> None:
    """
    Record an active request.

    Args:
        method: The HTTP method
        endpoint: The endpoint
        active: Whether the request is active
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        if active:
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        else:
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
    except Exception as e:
        logger.error(f"Error recording active request: {e}", exc_info=True)

def record_error(method: str, endpoint: str, error_type: str) -> None:
    """
    Record an error.

    Args:
        method: The HTTP method
        endpoint: The endpoint
        error_type: The error type
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        ERROR_COUNT.labels(method=method, endpoint=endpoint, error_type=error_type).inc()
    except Exception as e:
        logger.error(f"Error recording error: {e}", exc_info=True)

def record_db_connection(state: str, count: int) -> None:
    """
    Record database connections.

    Args:
        state: The connection state (e.g., "active", "idle")
        count: The number of connections
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        DB_CONNECTION_COUNT.labels(state=state).set(count)
    except Exception as e:
        logger.error(f"Error recording database connections: {e}", exc_info=True)

def record_db_query(query_type: str, latency: float) -> None:
    """
    Record a database query.

    Args:
        query_type: The query type (e.g., "select", "insert", "update", "delete")
        latency: The latency in seconds
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        DB_QUERY_COUNT.labels(query_type=query_type).inc()
        DB_QUERY_LATENCY.labels(query_type=query_type).observe(latency)
    except Exception as e:
        logger.error(f"Error recording database query: {e}", exc_info=True)

def record_system_metrics() -> None:
    """
    Record system metrics.
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        # Memory usage
        memory = psutil.virtual_memory()
        MEMORY_USAGE.set(memory.used)

        # CPU usage
        cpu = psutil.cpu_percent(interval=1)
        CPU_USAGE.set(cpu)

        # Disk usage
        disk = psutil.disk_usage("/")
        DISK_USAGE.set(disk.percent)
    except Exception as e:
        logger.error(f"Error recording system metrics: {e}", exc_info=True)

def start_system_metrics_collector() -> threading.Thread:
    """
    Start the system metrics collector.

    Returns:
        threading.Thread: The collector thread
    """
    if not monitoring_config["metrics"]["enabled"]:
        return None

    def collect_metrics():
        while True:
            try:
                record_system_metrics()
                time.sleep(monitoring_config["metrics"]["interval"])
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}", exc_info=True)
                time.sleep(monitoring_config["metrics"]["interval"])

    thread = threading.Thread(target=collect_metrics, daemon=True)
    thread.start()
    logger.info("System metrics collector started")
    return thread

def init_metrics() -> None:
    """
    Initialize metrics.
    """
    if not monitoring_config["metrics"]["enabled"]:
        logger.info("Metrics disabled")
        return

    try:
        # Start the metrics server
        start_metrics_server()

        # Start the system metrics collector
        start_system_metrics_collector()

        logger.info("Metrics initialized")
    except Exception as e:
        logger.error(f"Error initializing metrics: {e}", exc_info=True)

def shutdown_metrics() -> None:
    """
    Shutdown metrics.
    """
    if not monitoring_config["metrics"]["enabled"]:
        return

    try:
        # Stop the metrics server
        stop_metrics_server()

        logger.info("Metrics shutdown")
    except Exception as e:
        logger.error(f"Error shutting down metrics: {e}", exc_info=True)

"""
Health check module.

This module provides functions for health checks.
"""

import os
import time
import logging
import threading
import psutil
from typing import Dict, Any, Optional, List, Callable
import socket
import requests

from .config import monitoring_config
from db import get_pool_stats, check_database_health

# Configure logging
logger = logging.getLogger(__name__)

# Health check status
health_status: Dict[str, Any] = {
    "status": "starting",
    "timestamp": time.time(),
    "checks": {
        "database": {
            "status": "unknown",
            "timestamp": 0,
            "details": {}
        },
        "memory": {
            "status": "unknown",
            "timestamp": 0,
            "details": {}
        },
        "cpu": {
            "status": "unknown",
            "timestamp": 0,
            "details": {}
        },
        "disk": {
            "status": "unknown",
            "timestamp": 0,
            "details": {}
        },
        "network": {
            "status": "unknown",
            "timestamp": 0,
            "details": {}
        }
    }
}

def check_database() -> Dict[str, Any]:
    """
    Check database health.

    Returns:
        Dict[str, Any]: The database health status
    """
    try:
        # Get database connection pool stats
        pool_stats = get_pool_stats()

        # Check database health
        db_health = check_database_health()

        # Update health status
        health_status["checks"]["database"] = {
            "status": "healthy" if db_health and db_health.get("status", "") == "healthy" else "unhealthy",
            "timestamp": time.time(),
            "details": {
                "pool_size": pool_stats.get("pool_size", 0),
                "used_connections": pool_stats.get("used_connections", 0),
                "available_connections": pool_stats.get("available_connections", 0),
                "pool_utilization": pool_stats.get("pool_utilization", 0),
                "connection_health": db_health.get("connection_health", {}),
                "pool_health": db_health.get("pool_health", {}),
                "query_performance": db_health.get("query_performance", {})
            }
        }

        return health_status["checks"]["database"]
    except Exception as e:
        logger.error(f"Error checking database health: {e}", exc_info=True)

        # Update health status
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "timestamp": time.time(),
            "details": {
                "error": str(e)
            }
        }

        return health_status["checks"]["database"]

def check_memory() -> Dict[str, Any]:
    """
    Check memory health.

    Returns:
        Dict[str, Any]: The memory health status
    """
    try:
        # Get memory usage
        memory = psutil.virtual_memory()

        # Check if memory usage is below threshold
        memory_threshold = monitoring_config["alerting"]["thresholds"]["memory"]
        memory_healthy = memory.percent < memory_threshold

        # Update health status
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory_healthy else "unhealthy",
            "timestamp": time.time(),
            "details": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "threshold": memory_threshold
            }
        }

        return health_status["checks"]["memory"]
    except Exception as e:
        logger.error(f"Error checking memory health: {e}", exc_info=True)

        # Update health status
        health_status["checks"]["memory"] = {
            "status": "unhealthy",
            "timestamp": time.time(),
            "details": {
                "error": str(e)
            }
        }

        return health_status["checks"]["memory"]

def check_cpu() -> Dict[str, Any]:
    """
    Check CPU health.

    Returns:
        Dict[str, Any]: The CPU health status
    """
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_stats = psutil.cpu_stats()

        # Check if CPU usage is below threshold
        cpu_threshold = monitoring_config["alerting"]["thresholds"]["cpu"]
        cpu_healthy = cpu_percent < cpu_threshold

        # Update health status
        health_status["checks"]["cpu"] = {
            "status": "healthy" if cpu_healthy else "unhealthy",
            "timestamp": time.time(),
            "details": {
                "percent": cpu_percent,
                "count": cpu_count,
                "stats": {
                    "ctx_switches": cpu_stats.ctx_switches,
                    "interrupts": cpu_stats.interrupts,
                    "soft_interrupts": cpu_stats.soft_interrupts,
                    "syscalls": cpu_stats.syscalls
                },
                "threshold": cpu_threshold
            }
        }

        return health_status["checks"]["cpu"]
    except Exception as e:
        logger.error(f"Error checking CPU health: {e}", exc_info=True)

        # Update health status
        health_status["checks"]["cpu"] = {
            "status": "unhealthy",
            "timestamp": time.time(),
            "details": {
                "error": str(e)
            }
        }

        return health_status["checks"]["cpu"]

def check_disk() -> Dict[str, Any]:
    """
    Check disk health.

    Returns:
        Dict[str, Any]: The disk health status
    """
    try:
        # Get disk usage
        disk = psutil.disk_usage("/")

        # Check if disk usage is below threshold
        disk_threshold = monitoring_config["alerting"]["thresholds"]["disk"]
        disk_healthy = disk.percent < disk_threshold

        # Update health status
        health_status["checks"]["disk"] = {
            "status": "healthy" if disk_healthy else "unhealthy",
            "timestamp": time.time(),
            "details": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "threshold": disk_threshold
            }
        }

        return health_status["checks"]["disk"]
    except Exception as e:
        logger.error(f"Error checking disk health: {e}", exc_info=True)

        # Update health status
        health_status["checks"]["disk"] = {
            "status": "unhealthy",
            "timestamp": time.time(),
            "details": {
                "error": str(e)
            }
        }

        return health_status["checks"]["disk"]

def check_network() -> Dict[str, Any]:
    """
    Check network health.

    Returns:
        Dict[str, Any]: The network health status
    """
    try:
        # Check if we can resolve DNS
        socket.gethostbyname("google.com")

        # Check if we can connect to the internet
        requests.get("https://google.com", timeout=5)

        # Get network stats
        net_io = psutil.net_io_counters()

        # Update health status
        health_status["checks"]["network"] = {
            "status": "healthy",
            "timestamp": time.time(),
            "details": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            }
        }

        return health_status["checks"]["network"]
    except Exception as e:
        logger.error(f"Error checking network health: {e}", exc_info=True)

        # Update health status
        health_status["checks"]["network"] = {
            "status": "unhealthy",
            "timestamp": time.time(),
            "details": {
                "error": str(e)
            }
        }

        return health_status["checks"]["network"]

def check_health() -> Dict[str, Any]:
    """
    Check system health.

    Returns:
        Dict[str, Any]: The system health status
    """
    try:
        # Check all components
        check_database()
        check_memory()
        check_cpu()
        check_disk()
        check_network()

        # Determine overall status
        unhealthy_checks = [
            check
            for check, status in health_status["checks"].items()
            if status["status"] == "unhealthy"
        ]

        if unhealthy_checks:
            health_status["status"] = "unhealthy"
        else:
            health_status["status"] = "healthy"

        health_status["timestamp"] = time.time()

        return health_status
    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)

        # Update health status
        health_status["status"] = "unhealthy"
        health_status["timestamp"] = time.time()
        health_status["error"] = str(e)

        return health_status

def start_health_check_collector() -> threading.Thread:
    """
    Start the health check collector.

    Returns:
        threading.Thread: The collector thread
    """
    if not monitoring_config["health_check"]["enabled"]:
        return None

    def collect_health():
        while True:
            try:
                check_health()
                time.sleep(monitoring_config["health_check"]["interval"])
            except Exception as e:
                logger.error(f"Error collecting health: {e}", exc_info=True)
                time.sleep(monitoring_config["health_check"]["interval"])

    thread = threading.Thread(target=collect_health, daemon=True)
    thread.start()
    logger.info("Health check collector started")
    return thread

def get_health_status() -> Dict[str, Any]:
    """
    Get the current health status.

    Returns:
        Dict[str, Any]: The current health status
    """
    return health_status

def init_health_check() -> None:
    """
    Initialize health check.
    """
    if not monitoring_config["health_check"]["enabled"]:
        logger.info("Health check disabled")
        return

    try:
        # Start the health check collector
        start_health_check_collector()

        logger.info("Health check initialized")
    except Exception as e:
        logger.error(f"Error initializing health check: {e}", exc_info=True)

def shutdown_health_check() -> None:
    """
    Shutdown health check.
    """
    if not monitoring_config["health_check"]["enabled"]:
        return

    try:
        logger.info("Health check shutdown")
    except Exception as e:
        logger.error(f"Error shutting down health check: {e}", exc_info=True)

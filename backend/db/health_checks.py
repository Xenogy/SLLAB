"""
Database health checks.

This module provides functions for checking database health and performing automatic recovery.
It includes health check endpoints and monitoring of connection pool usage and database availability.
"""

import logging
import time
import threading
import json
import os
import psycopg2
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from datetime import datetime, timedelta

from db.connection import get_db_connection, get_pool_stats, check_database_health, recreate_connection_pool
from db.monitoring import get_monitoring_data, get_alerts

# Configure logging
logger = logging.getLogger(__name__)

# Health check configuration
DEFAULT_HEALTH_CHECK_INTERVAL = 60  # seconds
DEFAULT_ENABLE_HEALTH_CHECKS = True
DEFAULT_AUTO_RECOVERY = True
DEFAULT_MAX_RECOVERY_ATTEMPTS = 3
DEFAULT_RECOVERY_COOLDOWN = 300  # seconds

# Health check state
_health_check_thread = None
_health_check_stop_event = threading.Event()
_health_check_enabled = DEFAULT_ENABLE_HEALTH_CHECKS
_auto_recovery_enabled = DEFAULT_AUTO_RECOVERY
_last_recovery_attempt = 0
_recovery_attempts = 0

# Health check data
_health_check_data = {
    "last_check": None,
    "healthy": True,
    "status": "ok",
    "details": {},
    "history": [],
    "recovery_attempts": []
}

def perform_health_check() -> Dict[str, Any]:
    """
    Perform a health check.
    
    Returns:
        Dict[str, Any]: Health check results
    """
    health = {
        "timestamp": time.time(),
        "healthy": True,
        "status": "ok",
        "details": {}
    }
    
    try:
        # Check database health
        db_health = check_database_health()
        health["details"]["database"] = db_health
        
        if not db_health.get("healthy", True):
            health["healthy"] = False
            health["status"] = "database_unhealthy"
        
        # Check connection pool
        pool_stats = get_pool_stats()
        health["details"]["connection_pool"] = pool_stats
        
        # Check if pool is overloaded
        if pool_stats.get("pool_utilization", 0) > 80:
            health["healthy"] = False
            health["status"] = "pool_overloaded"
        
        # Check for critical alerts
        alerts = get_alerts(level="critical", limit=10)
        if alerts:
            health["healthy"] = False
            health["status"] = "critical_alerts"
            health["details"]["alerts"] = alerts
        
        # Check for warning alerts
        warnings = get_alerts(level="warning", limit=10)
        if warnings and health["healthy"]:
            health["status"] = "warnings"
            health["details"]["warnings"] = warnings
    except Exception as e:
        health["healthy"] = False
        health["status"] = "error"
        health["details"]["error"] = str(e)
    
    return health

def update_health_check_data() -> None:
    """
    Update health check data.
    """
    global _health_check_data
    
    # Perform health check
    health = perform_health_check()
    
    # Update health check data
    _health_check_data["last_check"] = health["timestamp"]
    _health_check_data["healthy"] = health["healthy"]
    _health_check_data["status"] = health["status"]
    _health_check_data["details"] = health["details"]
    
    # Add to history
    _health_check_data["history"].append({
        "timestamp": health["timestamp"],
        "healthy": health["healthy"],
        "status": health["status"]
    })
    
    # Limit history size
    if len(_health_check_data["history"]) > 100:
        _health_check_data["history"].pop(0)
    
    # Attempt recovery if needed
    if not health["healthy"] and _auto_recovery_enabled:
        attempt_recovery(health)

def attempt_recovery(health: Dict[str, Any]) -> None:
    """
    Attempt to recover from an unhealthy state.
    
    Args:
        health (Dict[str, Any]): Health check results
    """
    global _last_recovery_attempt
    global _recovery_attempts
    global _health_check_data
    
    # Check if we're in the cooldown period
    if time.time() - _last_recovery_attempt < DEFAULT_RECOVERY_COOLDOWN:
        logger.info("Recovery cooldown period active, skipping recovery attempt")
        return
    
    # Check if we've exceeded the maximum number of recovery attempts
    if _recovery_attempts >= DEFAULT_MAX_RECOVERY_ATTEMPTS:
        logger.warning("Maximum recovery attempts exceeded, skipping recovery attempt")
        return
    
    # Update recovery attempt counters
    _last_recovery_attempt = time.time()
    _recovery_attempts += 1
    
    # Create recovery attempt record
    recovery_attempt = {
        "timestamp": _last_recovery_attempt,
        "attempt": _recovery_attempts,
        "status": health["status"],
        "actions": [],
        "successful": False
    }
    
    try:
        # Perform recovery actions based on the status
        if health["status"] == "database_unhealthy":
            # Try to reconnect to the database
            logger.info("Attempting to recover from database unhealthy state")
            recovery_attempt["actions"].append("reconnect_database")
            
            # Recreate the connection pool
            new_pool = recreate_connection_pool()
            
            if new_pool:
                logger.info("Successfully recreated connection pool")
                recovery_attempt["successful"] = True
            else:
                logger.error("Failed to recreate connection pool")
        
        elif health["status"] == "pool_overloaded":
            # Try to increase the connection pool size
            logger.info("Attempting to recover from pool overloaded state")
            recovery_attempt["actions"].append("increase_pool_size")
            
            # Get current pool size
            pool_stats = get_pool_stats()
            current_size = pool_stats.get("pool_size", 10)
            
            # Increase pool size by 50%
            new_size = int(current_size * 1.5)
            
            # Recreate the connection pool with the new size
            new_pool = recreate_connection_pool(max_connections=new_size)
            
            if new_pool:
                logger.info(f"Successfully increased connection pool size to {new_size}")
                recovery_attempt["successful"] = True
            else:
                logger.error("Failed to increase connection pool size")
        
        elif health["status"] == "critical_alerts" or health["status"] == "warnings":
            # Log the alerts
            logger.info("Attempting to recover from alerts")
            recovery_attempt["actions"].append("log_alerts")
            
            # Get the alerts
            alerts = health["details"].get("alerts", [])
            warnings = health["details"].get("warnings", [])
            
            # Log each alert
            for alert in alerts:
                logger.critical(f"Critical alert: {alert['message']}")
            
            for warning in warnings:
                logger.warning(f"Warning: {warning['message']}")
            
            # Mark as successful (we can't do much more than log the alerts)
            recovery_attempt["successful"] = True
        
        elif health["status"] == "error":
            # Log the error
            logger.info("Attempting to recover from error")
            recovery_attempt["actions"].append("log_error")
            
            error = health["details"].get("error", "Unknown error")
            logger.error(f"Health check error: {error}")
            
            # Try to recreate the connection pool
            recovery_attempt["actions"].append("reconnect_database")
            
            new_pool = recreate_connection_pool()
            
            if new_pool:
                logger.info("Successfully recreated connection pool")
                recovery_attempt["successful"] = True
            else:
                logger.error("Failed to recreate connection pool")
    
    except Exception as e:
        logger.error(f"Error during recovery attempt: {e}")
        recovery_attempt["error"] = str(e)
    
    # Add recovery attempt to history
    _health_check_data["recovery_attempts"].append(recovery_attempt)
    
    # Reset recovery attempts if successful
    if recovery_attempt["successful"]:
        _recovery_attempts = 0
        logger.info("Recovery successful, reset recovery attempts counter")

def health_check_thread_func() -> None:
    """
    Health check thread function.
    """
    logger.info("Database health check thread started")
    
    while not _health_check_stop_event.is_set():
        try:
            # Update health check data
            update_health_check_data()
            
            # Sleep until next interval
            _health_check_stop_event.wait(DEFAULT_HEALTH_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Error in health check thread: {e}")
            # Sleep for a short time to avoid busy-waiting in case of persistent errors
            _health_check_stop_event.wait(5)
    
    logger.info("Database health check thread stopped")

def start_health_checks() -> None:
    """
    Start database health checks.
    """
    global _health_check_thread
    global _health_check_stop_event
    global _health_check_enabled
    
    if _health_check_thread and _health_check_thread.is_alive():
        logger.warning("Health check thread is already running")
        return
    
    # Reset stop event
    _health_check_stop_event.clear()
    
    # Create and start health check thread
    _health_check_thread = threading.Thread(target=health_check_thread_func, daemon=True)
    _health_check_thread.start()
    
    _health_check_enabled = True
    
    logger.info("Database health checks started")

def stop_health_checks() -> None:
    """
    Stop database health checks.
    """
    global _health_check_thread
    global _health_check_stop_event
    global _health_check_enabled
    
    if not _health_check_thread or not _health_check_thread.is_alive():
        logger.warning("Health check thread is not running")
        return
    
    # Set stop event
    _health_check_stop_event.set()
    
    # Wait for thread to stop
    _health_check_thread.join(timeout=5)
    
    _health_check_enabled = False
    
    logger.info("Database health checks stopped")

def is_health_checks_enabled() -> bool:
    """
    Check if health checks are enabled.
    
    Returns:
        bool: True if health checks are enabled, False otherwise
    """
    return _health_check_enabled

def enable_auto_recovery() -> None:
    """
    Enable automatic recovery.
    """
    global _auto_recovery_enabled
    _auto_recovery_enabled = True
    
    logger.info("Automatic recovery enabled")

def disable_auto_recovery() -> None:
    """
    Disable automatic recovery.
    """
    global _auto_recovery_enabled
    _auto_recovery_enabled = False
    
    logger.info("Automatic recovery disabled")

def is_auto_recovery_enabled() -> bool:
    """
    Check if automatic recovery is enabled.
    
    Returns:
        bool: True if automatic recovery is enabled, False otherwise
    """
    return _auto_recovery_enabled

def get_health_check_data() -> Dict[str, Any]:
    """
    Get health check data.
    
    Returns:
        Dict[str, Any]: Health check data
    """
    return _health_check_data

def get_recovery_attempts() -> List[Dict[str, Any]]:
    """
    Get recovery attempts.
    
    Returns:
        List[Dict[str, Any]]: Recovery attempts
    """
    return _health_check_data["recovery_attempts"]

def reset_recovery_attempts() -> None:
    """
    Reset recovery attempts.
    """
    global _recovery_attempts
    global _last_recovery_attempt
    
    _recovery_attempts = 0
    _last_recovery_attempt = 0
    
    logger.info("Recovery attempts reset")

def set_health_check_interval(interval: int) -> None:
    """
    Set the health check interval.
    
    Args:
        interval (int): The interval in seconds
    """
    global DEFAULT_HEALTH_CHECK_INTERVAL
    DEFAULT_HEALTH_CHECK_INTERVAL = interval
    
    logger.info(f"Health check interval set to {interval} seconds")

def set_max_recovery_attempts(max_attempts: int) -> None:
    """
    Set the maximum number of recovery attempts.
    
    Args:
        max_attempts (int): The maximum number of attempts
    """
    global DEFAULT_MAX_RECOVERY_ATTEMPTS
    DEFAULT_MAX_RECOVERY_ATTEMPTS = max_attempts
    
    logger.info(f"Maximum recovery attempts set to {max_attempts}")

def set_recovery_cooldown(cooldown: int) -> None:
    """
    Set the recovery cooldown period.
    
    Args:
        cooldown (int): The cooldown period in seconds
    """
    global DEFAULT_RECOVERY_COOLDOWN
    DEFAULT_RECOVERY_COOLDOWN = cooldown
    
    logger.info(f"Recovery cooldown period set to {cooldown} seconds")

def get_health_check_report() -> str:
    """
    Get a health check report.
    
    Returns:
        str: The report
    """
    data = _health_check_data
    
    report = []
    report.append("Database Health Check Report")
    report.append("===========================")
    report.append("")
    
    # Last check
    if data["last_check"]:
        last_check_time = datetime.fromtimestamp(data["last_check"]).strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"Last check: {last_check_time}")
    else:
        report.append("Last check: Never")
    
    # Health status
    report.append(f"Healthy: {data['healthy']}")
    report.append(f"Status: {data['status']}")
    report.append("")
    
    # Details
    report.append("Details:")
    
    # Database health
    db_health = data["details"].get("database", {})
    report.append("  Database:")
    report.append(f"    Healthy: {db_health.get('healthy', 'N/A')}")
    
    # Connection pool
    pool = data["details"].get("connection_pool", {})
    report.append("  Connection Pool:")
    report.append(f"    Pool size: {pool.get('pool_size', 'N/A')}")
    report.append(f"    Used connections: {pool.get('used_connections', 'N/A')}")
    report.append(f"    Available connections: {pool.get('available_connections', 'N/A')}")
    report.append(f"    Pool utilization: {pool.get('pool_utilization', 'N/A')}%")
    report.append("")
    
    # Recovery attempts
    recovery_attempts = data["recovery_attempts"]
    report.append("Recent Recovery Attempts:")
    
    if not recovery_attempts:
        report.append("  No recovery attempts")
    else:
        for i, attempt in enumerate(recovery_attempts[-5:]):
            attempt_time = datetime.fromtimestamp(attempt["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            report.append(f"  {i+1}. [{attempt_time}] Attempt {attempt['attempt']}: {attempt['status']}")
            report.append(f"     Actions: {', '.join(attempt['actions'])}")
            report.append(f"     Successful: {attempt['successful']}")
            if "error" in attempt:
                report.append(f"     Error: {attempt['error']}")
    
    return "\n".join(report)

def export_health_check_data(file_path: str) -> None:
    """
    Export health check data to a file.
    
    Args:
        file_path (str): The file path
    """
    with open(file_path, "w") as f:
        json.dump(_health_check_data, f, indent=2)
    
    logger.info(f"Health check data exported to {file_path}")

def import_health_check_data(file_path: str) -> None:
    """
    Import health check data from a file.
    
    Args:
        file_path (str): The file path
    """
    global _health_check_data
    
    with open(file_path, "r") as f:
        _health_check_data = json.load(f)
    
    logger.info(f"Health check data imported from {file_path}")

def init_health_checks() -> None:
    """
    Initialize database health checks.
    """
    # Start health checks if enabled by default
    if DEFAULT_ENABLE_HEALTH_CHECKS:
        start_health_checks()
    
    logger.info("Database health checks initialized")

def shutdown_health_checks() -> None:
    """
    Shutdown database health checks.
    """
    # Stop health checks
    stop_health_checks()
    
    logger.info("Database health checks shutdown")

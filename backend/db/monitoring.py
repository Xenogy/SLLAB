"""
Database monitoring system.

This module provides functions for monitoring database performance and health.
It tracks query execution times, resource usage, and connection pool statistics.
"""

import logging
import time
import threading
import json
import os
import psutil
import psycopg2
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from datetime import datetime, timedelta

from db.connection import get_db_connection, get_pool_stats
from db.query_analyzer import get_query_stats, get_recent_slow_queries
from db.query_cache import get_cache_stats

# Configure logging
logger = logging.getLogger(__name__)

# Monitoring configuration
DEFAULT_MONITORING_INTERVAL = 60  # seconds
DEFAULT_ENABLE_MONITORING = True
DEFAULT_ALERT_THRESHOLD = 0.8  # 80% utilization
DEFAULT_CRITICAL_THRESHOLD = 0.95  # 95% utilization
DEFAULT_HISTORY_SIZE = 60  # 1 hour at 1 minute intervals

# Monitoring state
_monitoring_thread = None
_monitoring_stop_event = threading.Event()
_monitoring_enabled = DEFAULT_ENABLE_MONITORING

# Monitoring data
_monitoring_data = {
    "last_check": None,
    "connection_pool": {
        "current": {},
        "history": []
    },
    "query_stats": {
        "current": {},
        "history": []
    },
    "cache_stats": {
        "current": {},
        "history": []
    },
    "resource_usage": {
        "current": {},
        "history": []
    },
    "alerts": []
}

def get_resource_usage() -> Dict[str, Any]:
    """
    Get resource usage statistics.
    
    Returns:
        Dict[str, Any]: Resource usage statistics
    """
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get disk usage
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
        
        # Get network usage
        net_io_counters = psutil.net_io_counters()
        
        return {
            "timestamp": time.time(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "net_bytes_sent": net_io_counters.bytes_sent,
            "net_bytes_recv": net_io_counters.bytes_recv
        }
    except Exception as e:
        logger.error(f"Error getting resource usage: {e}")
        return {
            "timestamp": time.time(),
            "error": str(e)
        }

def check_database_health() -> Dict[str, Any]:
    """
    Check database health.
    
    Returns:
        Dict[str, Any]: Database health information
    """
    health = {
        "timestamp": time.time(),
        "healthy": True,
        "connection_health": {},
        "pool_health": {},
        "query_performance": {}
    }
    
    try:
        # Check if we can get a connection
        with get_db_connection() as conn:
            if not conn:
                health["healthy"] = False
                health["connection_health"]["can_connect"] = False
                return health
            
            health["connection_health"]["can_connect"] = True
            
            # Check if we can execute a query
            cursor = conn.cursor()
            
            # Check connection info
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            health["connection_health"]["version"] = version
            
            # Check current connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]
            health["connection_health"]["active_connections"] = connections
            
            # Check pool health
            pool_stats = get_pool_stats()
            health["pool_health"] = pool_stats
            
            # Check if pool is overloaded
            if pool_stats.get("pool_utilization", 0) > DEFAULT_ALERT_THRESHOLD * 100:
                health["healthy"] = False
                health["pool_health"]["overloaded"] = True
            
            # Check query performance
            start_time = time.time()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            query_time = time.time() - start_time
            health["query_performance"]["simple_query_time"] = query_time
            
            # Check if query is too slow
            if query_time > 0.1:
                health["healthy"] = False
                health["query_performance"]["slow_query"] = True
            
            # Close cursor
            cursor.close()
    except Exception as e:
        health["healthy"] = False
        health["error"] = str(e)
    
    return health

def collect_monitoring_data() -> Dict[str, Any]:
    """
    Collect monitoring data.
    
    Returns:
        Dict[str, Any]: Monitoring data
    """
    data = {
        "timestamp": time.time(),
        "connection_pool": get_pool_stats(),
        "query_stats": get_query_stats(),
        "cache_stats": get_cache_stats(),
        "resource_usage": get_resource_usage(),
        "health": check_database_health()
    }
    
    return data

def update_monitoring_data() -> None:
    """
    Update monitoring data.
    """
    global _monitoring_data
    
    # Collect monitoring data
    data = collect_monitoring_data()
    
    # Update current data
    _monitoring_data["last_check"] = data["timestamp"]
    _monitoring_data["connection_pool"]["current"] = data["connection_pool"]
    _monitoring_data["query_stats"]["current"] = data["query_stats"]
    _monitoring_data["cache_stats"]["current"] = data["cache_stats"]
    _monitoring_data["resource_usage"]["current"] = data["resource_usage"]
    
    # Add to history
    _monitoring_data["connection_pool"]["history"].append(data["connection_pool"])
    _monitoring_data["query_stats"]["history"].append(data["query_stats"])
    _monitoring_data["cache_stats"]["history"].append(data["cache_stats"])
    _monitoring_data["resource_usage"]["history"].append(data["resource_usage"])
    
    # Limit history size
    if len(_monitoring_data["connection_pool"]["history"]) > DEFAULT_HISTORY_SIZE:
        _monitoring_data["connection_pool"]["history"].pop(0)
    if len(_monitoring_data["query_stats"]["history"]) > DEFAULT_HISTORY_SIZE:
        _monitoring_data["query_stats"]["history"].pop(0)
    if len(_monitoring_data["cache_stats"]["history"]) > DEFAULT_HISTORY_SIZE:
        _monitoring_data["cache_stats"]["history"].pop(0)
    if len(_monitoring_data["resource_usage"]["history"]) > DEFAULT_HISTORY_SIZE:
        _monitoring_data["resource_usage"]["history"].pop(0)
    
    # Check for alerts
    check_for_alerts(data)

def check_for_alerts(data: Dict[str, Any]) -> None:
    """
    Check for alerts based on monitoring data.
    
    Args:
        data (Dict[str, Any]): Monitoring data
    """
    alerts = []
    
    # Check connection pool utilization
    pool_utilization = data["connection_pool"].get("pool_utilization", 0)
    if pool_utilization > DEFAULT_CRITICAL_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "critical",
            "message": f"Connection pool utilization is critical: {pool_utilization:.2f}%",
            "component": "connection_pool"
        })
    elif pool_utilization > DEFAULT_ALERT_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "warning",
            "message": f"Connection pool utilization is high: {pool_utilization:.2f}%",
            "component": "connection_pool"
        })
    
    # Check for slow queries
    slow_queries = data["query_stats"].get("slow_queries", 0)
    very_slow_queries = data["query_stats"].get("very_slow_queries", 0)
    
    if very_slow_queries > 0:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "critical",
            "message": f"There are {very_slow_queries} very slow queries",
            "component": "query_performance"
        })
    elif slow_queries > 0:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "warning",
            "message": f"There are {slow_queries} slow queries",
            "component": "query_performance"
        })
    
    # Check resource usage
    cpu_percent = data["resource_usage"].get("cpu_percent", 0)
    memory_percent = data["resource_usage"].get("memory_percent", 0)
    disk_percent = data["resource_usage"].get("disk_percent", 0)
    
    if cpu_percent > DEFAULT_CRITICAL_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "critical",
            "message": f"CPU usage is critical: {cpu_percent:.2f}%",
            "component": "resource_usage"
        })
    elif cpu_percent > DEFAULT_ALERT_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "warning",
            "message": f"CPU usage is high: {cpu_percent:.2f}%",
            "component": "resource_usage"
        })
    
    if memory_percent > DEFAULT_CRITICAL_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "critical",
            "message": f"Memory usage is critical: {memory_percent:.2f}%",
            "component": "resource_usage"
        })
    elif memory_percent > DEFAULT_ALERT_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "warning",
            "message": f"Memory usage is high: {memory_percent:.2f}%",
            "component": "resource_usage"
        })
    
    if disk_percent > DEFAULT_CRITICAL_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "critical",
            "message": f"Disk usage is critical: {disk_percent:.2f}%",
            "component": "resource_usage"
        })
    elif disk_percent > DEFAULT_ALERT_THRESHOLD * 100:
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "warning",
            "message": f"Disk usage is high: {disk_percent:.2f}%",
            "component": "resource_usage"
        })
    
    # Check database health
    if not data["health"].get("healthy", True):
        alerts.append({
            "timestamp": data["timestamp"],
            "level": "critical",
            "message": "Database health check failed",
            "component": "database_health",
            "details": data["health"].get("error", "Unknown error")
        })
    
    # Add alerts to monitoring data
    if alerts:
        global _monitoring_data
        _monitoring_data["alerts"].extend(alerts)
        
        # Log alerts
        for alert in alerts:
            if alert["level"] == "critical":
                logger.critical(f"Database alert: {alert['message']}")
            else:
                logger.warning(f"Database alert: {alert['message']}")

def monitoring_thread_func() -> None:
    """
    Monitoring thread function.
    """
    logger.info("Database monitoring thread started")
    
    while not _monitoring_stop_event.is_set():
        try:
            # Update monitoring data
            update_monitoring_data()
            
            # Sleep until next interval
            _monitoring_stop_event.wait(DEFAULT_MONITORING_INTERVAL)
        except Exception as e:
            logger.error(f"Error in monitoring thread: {e}")
            # Sleep for a short time to avoid busy-waiting in case of persistent errors
            _monitoring_stop_event.wait(5)
    
    logger.info("Database monitoring thread stopped")

def start_monitoring() -> None:
    """
    Start database monitoring.
    """
    global _monitoring_thread
    global _monitoring_stop_event
    global _monitoring_enabled
    
    if _monitoring_thread and _monitoring_thread.is_alive():
        logger.warning("Monitoring thread is already running")
        return
    
    # Reset stop event
    _monitoring_stop_event.clear()
    
    # Create and start monitoring thread
    _monitoring_thread = threading.Thread(target=monitoring_thread_func, daemon=True)
    _monitoring_thread.start()
    
    _monitoring_enabled = True
    
    logger.info("Database monitoring started")

def stop_monitoring() -> None:
    """
    Stop database monitoring.
    """
    global _monitoring_thread
    global _monitoring_stop_event
    global _monitoring_enabled
    
    if not _monitoring_thread or not _monitoring_thread.is_alive():
        logger.warning("Monitoring thread is not running")
        return
    
    # Set stop event
    _monitoring_stop_event.set()
    
    # Wait for thread to stop
    _monitoring_thread.join(timeout=5)
    
    _monitoring_enabled = False
    
    logger.info("Database monitoring stopped")

def is_monitoring_enabled() -> bool:
    """
    Check if monitoring is enabled.
    
    Returns:
        bool: True if monitoring is enabled, False otherwise
    """
    return _monitoring_enabled

def get_monitoring_data() -> Dict[str, Any]:
    """
    Get monitoring data.
    
    Returns:
        Dict[str, Any]: Monitoring data
    """
    return _monitoring_data

def get_alerts(level: Optional[str] = None, component: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get alerts.
    
    Args:
        level (Optional[str], optional): Alert level. Defaults to None.
        component (Optional[str], optional): Alert component. Defaults to None.
        limit (int, optional): Maximum number of alerts to return. Defaults to 100.
        
    Returns:
        List[Dict[str, Any]]: Alerts
    """
    alerts = _monitoring_data["alerts"]
    
    # Filter by level
    if level:
        alerts = [a for a in alerts if a["level"] == level]
    
    # Filter by component
    if component:
        alerts = [a for a in alerts if a["component"] == component]
    
    # Sort by timestamp (newest first)
    alerts = sorted(alerts, key=lambda a: a["timestamp"], reverse=True)
    
    # Limit number of alerts
    alerts = alerts[:limit]
    
    return alerts

def clear_alerts() -> None:
    """
    Clear all alerts.
    """
    global _monitoring_data
    _monitoring_data["alerts"] = []
    
    logger.info("Alerts cleared")

def set_monitoring_interval(interval: int) -> None:
    """
    Set the monitoring interval.
    
    Args:
        interval (int): The interval in seconds
    """
    global DEFAULT_MONITORING_INTERVAL
    DEFAULT_MONITORING_INTERVAL = interval
    
    logger.info(f"Monitoring interval set to {interval} seconds")

def set_alert_threshold(threshold: float) -> None:
    """
    Set the alert threshold.
    
    Args:
        threshold (float): The threshold (0.0 to 1.0)
    """
    global DEFAULT_ALERT_THRESHOLD
    DEFAULT_ALERT_THRESHOLD = max(0.0, min(1.0, threshold))
    
    logger.info(f"Alert threshold set to {DEFAULT_ALERT_THRESHOLD * 100:.2f}%")

def set_critical_threshold(threshold: float) -> None:
    """
    Set the critical threshold.
    
    Args:
        threshold (float): The threshold (0.0 to 1.0)
    """
    global DEFAULT_CRITICAL_THRESHOLD
    DEFAULT_CRITICAL_THRESHOLD = max(0.0, min(1.0, threshold))
    
    logger.info(f"Critical threshold set to {DEFAULT_CRITICAL_THRESHOLD * 100:.2f}%")

def set_history_size(size: int) -> None:
    """
    Set the history size.
    
    Args:
        size (int): The history size
    """
    global DEFAULT_HISTORY_SIZE
    DEFAULT_HISTORY_SIZE = max(1, size)
    
    logger.info(f"History size set to {DEFAULT_HISTORY_SIZE}")

def get_monitoring_report() -> str:
    """
    Get a monitoring report.
    
    Returns:
        str: The report
    """
    data = _monitoring_data
    
    report = []
    report.append("Database Monitoring Report")
    report.append("=========================")
    report.append("")
    
    # Last check
    if data["last_check"]:
        last_check_time = datetime.fromtimestamp(data["last_check"]).strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"Last check: {last_check_time}")
    else:
        report.append("Last check: Never")
    
    report.append("")
    
    # Connection pool
    pool = data["connection_pool"]["current"]
    report.append("Connection Pool:")
    report.append(f"  Pool size: {pool.get('pool_size', 'N/A')}")
    report.append(f"  Used connections: {pool.get('used_connections', 'N/A')}")
    report.append(f"  Available connections: {pool.get('available_connections', 'N/A')}")
    report.append(f"  Pool utilization: {pool.get('pool_utilization', 'N/A')}%")
    report.append("")
    
    # Query stats
    query_stats = data["query_stats"]["current"]
    report.append("Query Statistics:")
    report.append(f"  Total queries: {query_stats.get('total_queries', 'N/A')}")
    report.append(f"  Slow queries: {query_stats.get('slow_queries', 'N/A')}")
    report.append(f"  Very slow queries: {query_stats.get('very_slow_queries', 'N/A')}")
    report.append(f"  Average execution time: {query_stats.get('avg_execution_time', 'N/A'):.6f}s")
    report.append(f"  Maximum execution time: {query_stats.get('max_execution_time', 'N/A'):.6f}s")
    report.append("")
    
    # Cache stats
    cache_stats = data["cache_stats"]["current"]
    report.append("Cache Statistics:")
    report.append(f"  Size: {cache_stats.get('size', 'N/A')}")
    report.append(f"  Hits: {cache_stats.get('hits', 'N/A')}")
    report.append(f"  Misses: {cache_stats.get('misses', 'N/A')}")
    
    total_requests = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
    if total_requests > 0:
        hit_ratio = cache_stats.get("hits", 0) / total_requests * 100
        report.append(f"  Hit ratio: {hit_ratio:.2f}%")
    
    report.append("")
    
    # Resource usage
    resource_usage = data["resource_usage"]["current"]
    report.append("Resource Usage:")
    report.append(f"  CPU: {resource_usage.get('cpu_percent', 'N/A')}%")
    report.append(f"  Memory: {resource_usage.get('memory_percent', 'N/A')}%")
    report.append(f"  Disk: {resource_usage.get('disk_percent', 'N/A')}%")
    report.append("")
    
    # Alerts
    alerts = get_alerts(limit=10)
    report.append("Recent Alerts:")
    
    if not alerts:
        report.append("  No alerts")
    else:
        for i, alert in enumerate(alerts):
            alert_time = datetime.fromtimestamp(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            report.append(f"  {i+1}. [{alert_time}] [{alert['level'].upper()}] {alert['message']}")
    
    return "\n".join(report)

def export_monitoring_data(file_path: str) -> None:
    """
    Export monitoring data to a file.
    
    Args:
        file_path (str): The file path
    """
    with open(file_path, "w") as f:
        json.dump(_monitoring_data, f, indent=2)
    
    logger.info(f"Monitoring data exported to {file_path}")

def import_monitoring_data(file_path: str) -> None:
    """
    Import monitoring data from a file.
    
    Args:
        file_path (str): The file path
    """
    global _monitoring_data
    
    with open(file_path, "r") as f:
        _monitoring_data = json.load(f)
    
    logger.info(f"Monitoring data imported from {file_path}")

def init_monitoring() -> None:
    """
    Initialize database monitoring.
    """
    # Start monitoring if enabled by default
    if DEFAULT_ENABLE_MONITORING:
        start_monitoring()
    
    logger.info("Database monitoring initialized")

def shutdown_monitoring() -> None:
    """
    Shutdown database monitoring.
    """
    # Stop monitoring
    stop_monitoring()
    
    logger.info("Database monitoring shutdown")

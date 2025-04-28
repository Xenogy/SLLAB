"""
Alerting module.

This module provides functions for alerting.
"""

import os
import time
import logging
import threading
import json
from typing import Dict, Any, Optional, List, Callable
import requests

from .config import monitoring_config
from .health import get_health_status

# Configure logging
logger = logging.getLogger(__name__)

# Alert status
alert_status: Dict[str, Any] = {
    "alerts": [],
    "last_alert_time": 0,
    "alert_count": 0
}

def send_alert(alert_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send an alert.
    
    Args:
        alert_type: The alert type
        message: The alert message
        details: The alert details
        
    Returns:
        bool: True if the alert was sent successfully, False otherwise
    """
    if not monitoring_config["alerting"]["enabled"]:
        return False
    
    try:
        # Create alert
        alert = {
            "type": alert_type,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        
        # Add alert to status
        alert_status["alerts"].append(alert)
        alert_status["last_alert_time"] = alert["timestamp"]
        alert_status["alert_count"] += 1
        
        # Limit alerts
        if len(alert_status["alerts"]) > 100:
            alert_status["alerts"] = alert_status["alerts"][-100:]
        
        # Log alert
        logger.warning(f"Alert: {alert_type} - {message}")
        
        # Send alert to endpoints
        success = True
        for endpoint in monitoring_config["alerting"]["endpoints"]:
            try:
                response = requests.post(
                    endpoint,
                    json=alert,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code != 200:
                    logger.error(f"Error sending alert to {endpoint}: {response.status_code} {response.text}")
                    success = False
            except Exception as e:
                logger.error(f"Error sending alert to {endpoint}: {e}", exc_info=True)
                success = False
        
        return success
    except Exception as e:
        logger.error(f"Error sending alert: {e}", exc_info=True)
        return False

def check_alerts() -> None:
    """
    Check for alerts.
    """
    if not monitoring_config["alerting"]["enabled"]:
        return
    
    try:
        # Get health status
        health = get_health_status()
        
        # Check overall status
        if health["status"] == "unhealthy":
            send_alert(
                "system_unhealthy",
                "System is unhealthy",
                {
                    "health": health
                }
            )
        
        # Check database
        if health["checks"]["database"]["status"] == "unhealthy":
            send_alert(
                "database_unhealthy",
                "Database is unhealthy",
                {
                    "database": health["checks"]["database"]
                }
            )
        
        # Check memory
        if health["checks"]["memory"]["status"] == "unhealthy":
            send_alert(
                "memory_usage_high",
                "Memory usage is high",
                {
                    "memory": health["checks"]["memory"]
                }
            )
        
        # Check CPU
        if health["checks"]["cpu"]["status"] == "unhealthy":
            send_alert(
                "cpu_usage_high",
                "CPU usage is high",
                {
                    "cpu": health["checks"]["cpu"]
                }
            )
        
        # Check disk
        if health["checks"]["disk"]["status"] == "unhealthy":
            send_alert(
                "disk_usage_high",
                "Disk usage is high",
                {
                    "disk": health["checks"]["disk"]
                }
            )
        
        # Check network
        if health["checks"]["network"]["status"] == "unhealthy":
            send_alert(
                "network_unhealthy",
                "Network is unhealthy",
                {
                    "network": health["checks"]["network"]
                }
            )
    except Exception as e:
        logger.error(f"Error checking alerts: {e}", exc_info=True)

def start_alert_checker() -> threading.Thread:
    """
    Start the alert checker.
    
    Returns:
        threading.Thread: The checker thread
    """
    if not monitoring_config["alerting"]["enabled"]:
        return None
    
    def check_alerts_loop():
        while True:
            try:
                check_alerts()
                time.sleep(monitoring_config["health_check"]["interval"])
            except Exception as e:
                logger.error(f"Error checking alerts: {e}", exc_info=True)
                time.sleep(monitoring_config["health_check"]["interval"])
    
    thread = threading.Thread(target=check_alerts_loop, daemon=True)
    thread.start()
    logger.info("Alert checker started")
    return thread

def get_alert_status() -> Dict[str, Any]:
    """
    Get the current alert status.
    
    Returns:
        Dict[str, Any]: The current alert status
    """
    return alert_status

def init_alerting() -> None:
    """
    Initialize alerting.
    """
    if not monitoring_config["alerting"]["enabled"]:
        logger.info("Alerting disabled")
        return
    
    try:
        # Start the alert checker
        start_alert_checker()
        
        logger.info("Alerting initialized")
    except Exception as e:
        logger.error(f"Error initializing alerting: {e}", exc_info=True)

def shutdown_alerting() -> None:
    """
    Shutdown alerting.
    """
    if not monitoring_config["alerting"]["enabled"]:
        return
    
    try:
        logger.info("Alerting shutdown")
    except Exception as e:
        logger.error(f"Error shutting down alerting: {e}", exc_info=True)

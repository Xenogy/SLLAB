"""
Monitoring configuration module.

This module provides configuration for monitoring and logging.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from config import Config

# Default monitoring configuration
DEFAULT_MONITORING_ENABLED = True
DEFAULT_METRICS_ENABLED = True
DEFAULT_TRACING_ENABLED = True
DEFAULT_LOGGING_ENABLED = True
DEFAULT_HEALTH_CHECK_ENABLED = True
DEFAULT_ALERTING_ENABLED = False

DEFAULT_METRICS_PORT = 8001
DEFAULT_METRICS_PATH = "/metrics"
DEFAULT_METRICS_INTERVAL = 15  # seconds

DEFAULT_TRACING_SAMPLE_RATE = 0.1  # 10% of requests
DEFAULT_TRACING_SERVICE_NAME = "accountdb-api"

DEFAULT_HEALTH_CHECK_PATH = "/health"
DEFAULT_HEALTH_CHECK_INTERVAL = 60  # seconds

DEFAULT_ALERTING_ENDPOINTS = []
DEFAULT_ALERTING_THRESHOLD_CPU = 80  # percent
DEFAULT_ALERTING_THRESHOLD_MEMORY = 80  # percent
DEFAULT_ALERTING_THRESHOLD_DISK = 80  # percent
DEFAULT_ALERTING_THRESHOLD_ERROR_RATE = 5  # percent
DEFAULT_ALERTING_THRESHOLD_RESPONSE_TIME = 1000  # milliseconds

# Load configuration from environment variables
MONITORING_ENABLED = os.environ.get("MONITORING_ENABLED", DEFAULT_MONITORING_ENABLED)
if isinstance(MONITORING_ENABLED, str):
    MONITORING_ENABLED = MONITORING_ENABLED.lower() in ("true", "1", "yes", "y")

METRICS_ENABLED = os.environ.get("METRICS_ENABLED", DEFAULT_METRICS_ENABLED)
if isinstance(METRICS_ENABLED, str):
    METRICS_ENABLED = METRICS_ENABLED.lower() in ("true", "1", "yes", "y")

TRACING_ENABLED = os.environ.get("TRACING_ENABLED", DEFAULT_TRACING_ENABLED)
if isinstance(TRACING_ENABLED, str):
    TRACING_ENABLED = TRACING_ENABLED.lower() in ("true", "1", "yes", "y")

LOGGING_ENABLED = os.environ.get("LOGGING_ENABLED", DEFAULT_LOGGING_ENABLED)
if isinstance(LOGGING_ENABLED, str):
    LOGGING_ENABLED = LOGGING_ENABLED.lower() in ("true", "1", "yes", "y")

HEALTH_CHECK_ENABLED = os.environ.get("HEALTH_CHECK_ENABLED", DEFAULT_HEALTH_CHECK_ENABLED)
if isinstance(HEALTH_CHECK_ENABLED, str):
    HEALTH_CHECK_ENABLED = HEALTH_CHECK_ENABLED.lower() in ("true", "1", "yes", "y")

ALERTING_ENABLED = os.environ.get("ALERTING_ENABLED", DEFAULT_ALERTING_ENABLED)
if isinstance(ALERTING_ENABLED, str):
    ALERTING_ENABLED = ALERTING_ENABLED.lower() in ("true", "1", "yes", "y")

# Metrics configuration
METRICS_PORT = int(os.environ.get("METRICS_PORT", DEFAULT_METRICS_PORT))
METRICS_PATH = os.environ.get("METRICS_PATH", DEFAULT_METRICS_PATH)
METRICS_INTERVAL = int(os.environ.get("METRICS_INTERVAL", DEFAULT_METRICS_INTERVAL))

# Tracing configuration
TRACING_SAMPLE_RATE = float(os.environ.get("TRACING_SAMPLE_RATE", DEFAULT_TRACING_SAMPLE_RATE))
TRACING_SERVICE_NAME = os.environ.get("TRACING_SERVICE_NAME", DEFAULT_TRACING_SERVICE_NAME)

# Health check configuration
HEALTH_CHECK_PATH = os.environ.get("HEALTH_CHECK_PATH", DEFAULT_HEALTH_CHECK_PATH)
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", DEFAULT_HEALTH_CHECK_INTERVAL))

# Alerting configuration
ALERTING_ENDPOINTS_STR = os.environ.get("ALERTING_ENDPOINTS", "")
ALERTING_ENDPOINTS = ALERTING_ENDPOINTS_STR.split(",") if ALERTING_ENDPOINTS_STR else DEFAULT_ALERTING_ENDPOINTS

ALERTING_THRESHOLD_CPU = int(os.environ.get("ALERTING_THRESHOLD_CPU", DEFAULT_ALERTING_THRESHOLD_CPU))
ALERTING_THRESHOLD_MEMORY = int(os.environ.get("ALERTING_THRESHOLD_MEMORY", DEFAULT_ALERTING_THRESHOLD_MEMORY))
ALERTING_THRESHOLD_DISK = int(os.environ.get("ALERTING_THRESHOLD_DISK", DEFAULT_ALERTING_THRESHOLD_DISK))
ALERTING_THRESHOLD_ERROR_RATE = int(os.environ.get("ALERTING_THRESHOLD_ERROR_RATE", DEFAULT_ALERTING_THRESHOLD_ERROR_RATE))
ALERTING_THRESHOLD_RESPONSE_TIME = int(os.environ.get("ALERTING_THRESHOLD_RESPONSE_TIME", DEFAULT_ALERTING_THRESHOLD_RESPONSE_TIME))

# Logging configuration
LOG_LEVEL = getattr(logging, Config.LOG_LEVEL)
LOG_FORMAT = Config.LOG_FORMAT
LOG_FILE = Config.LOG_FILE
LOG_ROTATION = Config.LOG_ROTATION
LOG_ROTATION_SIZE = Config.LOG_MAX_SIZE
LOG_ROTATION_COUNT = Config.LOG_BACKUP_COUNT

# Monitoring configuration dictionary
monitoring_config: Dict[str, Any] = {
    "enabled": MONITORING_ENABLED,
    "metrics": {
        "enabled": METRICS_ENABLED,
        "port": METRICS_PORT,
        "path": METRICS_PATH,
        "interval": METRICS_INTERVAL
    },
    "tracing": {
        "enabled": TRACING_ENABLED,
        "sample_rate": TRACING_SAMPLE_RATE,
        "service_name": TRACING_SERVICE_NAME
    },
    "logging": {
        "enabled": LOGGING_ENABLED,
        "level": LOG_LEVEL,
        "format": LOG_FORMAT,
        "file": LOG_FILE,
        "rotation": LOG_ROTATION,
        "rotation_size": LOG_ROTATION_SIZE,
        "rotation_count": LOG_ROTATION_COUNT
    },
    "health_check": {
        "enabled": HEALTH_CHECK_ENABLED,
        "path": HEALTH_CHECK_PATH,
        "interval": HEALTH_CHECK_INTERVAL
    },
    "alerting": {
        "enabled": ALERTING_ENABLED,
        "endpoints": ALERTING_ENDPOINTS,
        "thresholds": {
            "cpu": ALERTING_THRESHOLD_CPU,
            "memory": ALERTING_THRESHOLD_MEMORY,
            "disk": ALERTING_THRESHOLD_DISK,
            "error_rate": ALERTING_THRESHOLD_ERROR_RATE,
            "response_time": ALERTING_THRESHOLD_RESPONSE_TIME
        }
    }
}

def get_monitoring_config() -> Dict[str, Any]:
    """
    Get the monitoring configuration.

    Returns:
        Dict[str, Any]: The monitoring configuration.
    """
    return monitoring_config

def log_monitoring_config() -> None:
    """
    Log the monitoring configuration.
    """
    logger = logging.getLogger(__name__)
    logger.info("Monitoring configuration:")
    logger.info(f"  Enabled: {MONITORING_ENABLED}")
    logger.info(f"  Metrics enabled: {METRICS_ENABLED}")
    logger.info(f"  Tracing enabled: {TRACING_ENABLED}")
    logger.info(f"  Logging enabled: {LOGGING_ENABLED}")
    logger.info(f"  Health check enabled: {HEALTH_CHECK_ENABLED}")
    logger.info(f"  Alerting enabled: {ALERTING_ENABLED}")

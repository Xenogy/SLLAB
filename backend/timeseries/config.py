"""
Timeseries configuration module.

This module provides configuration for the timeseries package.
"""

import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_COLLECTION_INTERVAL = 30  # seconds
DEFAULT_AGGREGATION_INTERVAL = 3600  # seconds (1 hour)
DEFAULT_RETENTION_PERIOD = 30  # days
DEFAULT_ENABLE_COLLECTION = True
DEFAULT_ENABLE_AGGREGATION = True

# Timeseries configuration
timeseries_config = {
    "collection": {
        "enabled": os.environ.get("TIMESERIES_COLLECTION_ENABLED", "true").lower() == "true",
        "interval": int(os.environ.get("TIMESERIES_COLLECTION_INTERVAL", DEFAULT_COLLECTION_INTERVAL)),
        "metrics": {
            "system": os.environ.get("TIMESERIES_COLLECT_SYSTEM", "true").lower() == "true",
            "vm": os.environ.get("TIMESERIES_COLLECT_VM", "true").lower() == "true",
            "account": os.environ.get("TIMESERIES_COLLECT_ACCOUNT", "true").lower() == "true",
            "job": os.environ.get("TIMESERIES_COLLECT_JOB", "true").lower() == "true"
        }
    },
    "aggregation": {
        "enabled": os.environ.get("TIMESERIES_AGGREGATION_ENABLED", "true").lower() == "true",
        "interval": int(os.environ.get("TIMESERIES_AGGREGATION_INTERVAL", DEFAULT_AGGREGATION_INTERVAL)),
        "periods": {
            "hourly": os.environ.get("TIMESERIES_AGGREGATE_HOURLY", "true").lower() == "true",
            "daily": os.environ.get("TIMESERIES_AGGREGATE_DAILY", "true").lower() == "true",
            "weekly": os.environ.get("TIMESERIES_AGGREGATE_WEEKLY", "true").lower() == "true",
            "monthly": os.environ.get("TIMESERIES_AGGREGATE_MONTHLY", "true").lower() == "true"
        }
    },
    "retention": {
        "raw_data_days": int(os.environ.get("TIMESERIES_RETENTION_RAW", DEFAULT_RETENTION_PERIOD)),
        "hourly_aggregates_days": int(os.environ.get("TIMESERIES_RETENTION_HOURLY", DEFAULT_RETENTION_PERIOD * 2)),
        "daily_aggregates_days": int(os.environ.get("TIMESERIES_RETENTION_DAILY", DEFAULT_RETENTION_PERIOD * 6)),
        "weekly_aggregates_days": int(os.environ.get("TIMESERIES_RETENTION_WEEKLY", DEFAULT_RETENTION_PERIOD * 12)),
        "monthly_aggregates_days": int(os.environ.get("TIMESERIES_RETENTION_MONTHLY", DEFAULT_RETENTION_PERIOD * 24))
    }
}

def get_timeseries_config() -> Dict[str, Any]:
    """
    Get the timeseries configuration.

    Returns:
        Dict[str, Any]: The timeseries configuration
    """
    return timeseries_config

def log_timeseries_config() -> None:
    """
    Log the timeseries configuration.
    """
    logger.info("Timeseries configuration:")
    logger.info(f"  Collection enabled: {timeseries_config['collection']['enabled']}")
    logger.info(f"  Collection interval: {timeseries_config['collection']['interval']} seconds")
    logger.info(f"  Collect system metrics: {timeseries_config['collection']['metrics']['system']}")
    logger.info(f"  Collect VM metrics: {timeseries_config['collection']['metrics']['vm']}")
    logger.info(f"  Collect account metrics: {timeseries_config['collection']['metrics']['account']}")
    logger.info(f"  Collect job metrics: {timeseries_config['collection']['metrics']['job']}")
    logger.info(f"  Aggregation enabled: {timeseries_config['aggregation']['enabled']}")
    logger.info(f"  Aggregation interval: {timeseries_config['aggregation']['interval']} seconds")
    logger.info(f"  Aggregate hourly: {timeseries_config['aggregation']['periods']['hourly']}")
    logger.info(f"  Aggregate daily: {timeseries_config['aggregation']['periods']['daily']}")
    logger.info(f"  Aggregate weekly: {timeseries_config['aggregation']['periods']['weekly']}")
    logger.info(f"  Aggregate monthly: {timeseries_config['aggregation']['periods']['monthly']}")
    logger.info(f"  Raw data retention: {timeseries_config['retention']['raw_data_days']} days")
    logger.info(f"  Hourly aggregates retention: {timeseries_config['retention']['hourly_aggregates_days']} days")
    logger.info(f"  Daily aggregates retention: {timeseries_config['retention']['daily_aggregates_days']} days")
    logger.info(f"  Weekly aggregates retention: {timeseries_config['retention']['weekly_aggregates_days']} days")
    logger.info(f"  Monthly aggregates retention: {timeseries_config['retention']['monthly_aggregates_days']} days")

#!/usr/bin/env python3
"""
Script to manually trigger metrics collection.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timeseries.collector import collect_all_metrics
from timeseries.vm_status import collect_vm_status_distribution

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def trigger_collection():
    """Trigger metrics collection."""
    try:
        logger.info("Triggering metrics collection...")
        
        # Collect all metrics
        collect_all_metrics()
        
        # Collect VM status distribution
        vm_status_metrics = collect_vm_status_distribution()
        logger.info(f"Collected {len(vm_status_metrics)} VM status metrics")
        
        logger.info("Metrics collection completed")
    except Exception as e:
        logger.error(f"Error triggering metrics collection: {e}", exc_info=True)

if __name__ == "__main__":
    trigger_collection()

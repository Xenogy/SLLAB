#!/usr/bin/env python3
"""
Script to check if there are any metrics in the database.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db_connection
from db.user_connection import get_user_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_metrics():
    """Check if there are any metrics in the database."""
    try:
        # Get database connection
        with get_user_db_connection(user_id=1, user_role='admin') as conn:
            if not conn:
                logger.error("Failed to get database connection")
                return
            
            cursor = conn.cursor()
            
            # Check metrics_definitions table
            cursor.execute("SELECT COUNT(*) FROM public.metrics_definitions")
            metrics_count = cursor.fetchone()[0]
            logger.info(f"Found {metrics_count} metric definitions")
            
            # Check timeseries_data table
            cursor.execute("SELECT COUNT(*) FROM public.timeseries_data")
            data_count = cursor.fetchone()[0]
            logger.info(f"Found {data_count} timeseries data points")
            
            # Check timeseries_aggregates table
            cursor.execute("SELECT COUNT(*) FROM public.timeseries_aggregates")
            aggregates_count = cursor.fetchone()[0]
            logger.info(f"Found {aggregates_count} timeseries aggregates")
            
            # Get sample of metrics
            if data_count > 0:
                cursor.execute("""
                    SELECT m.name, t.timestamp, 
                        COALESCE(t.value_float, t.value_int::float, t.value_bool::int::float, 0) as value,
                        t.entity_type, t.entity_id, t.owner_id
                    FROM public.timeseries_data t
                    JOIN public.metrics_definitions m ON t.metric_id = m.id
                    ORDER BY t.timestamp DESC
                    LIMIT 10
                """)
                
                logger.info("Recent metrics:")
                for row in cursor.fetchall():
                    name, timestamp, value, entity_type, entity_id, owner_id = row
                    logger.info(f"  {name}: {value} ({timestamp}) - entity: {entity_type}/{entity_id}, owner: {owner_id}")
            
            cursor.close()
    except Exception as e:
        logger.error(f"Error checking metrics: {e}")

if __name__ == "__main__":
    check_metrics()

"""
VM status distribution collection module.

This module provides functions for collecting VM status distribution data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from db.connection import get_db_connection
from db.user_connection import get_user_db_connection

# Configure logging
logger = logging.getLogger(__name__)

def collect_vm_status_distribution() -> List[Dict[str, Any]]:
    """
    Collect VM status distribution data.

    Returns:
        List[Dict[str, Any]]: List of VM status distribution data points
    """
    try:
        # Get database connection with RLS context
        with get_user_db_connection(user_id=1, user_role='admin') as conn:
            if not conn:
                logger.error("Failed to get database connection for VM status distribution")
                return []

            cursor = conn.cursor()

            # Get VM counts by status and owner
            cursor.execute("""
                SELECT 
                    status, 
                    owner_id, 
                    COUNT(*) 
                FROM public.vms 
                GROUP BY status, owner_id
            """)

            # Process results
            status_counts = {}
            for row in cursor.fetchall():
                status, owner_id, count = row
                
                # Skip if owner_id is None
                if owner_id is None:
                    continue
                
                # Initialize owner dict if not exists
                if owner_id not in status_counts:
                    status_counts[owner_id] = {
                        'running': 0,
                        'stopped': 0,
                        'error': 0
                    }
                
                # Update status count
                if status == 'running':
                    status_counts[owner_id]['running'] += count
                elif status == 'stopped':
                    status_counts[owner_id]['stopped'] += count
                elif status == 'error':
                    status_counts[owner_id]['error'] += count
            
            cursor.close()
        
        # Create data points
        data_points = []
        timestamp = datetime.now()
        
        for owner_id, counts in status_counts.items():
            # Insert into vm_status_distribution table
            with get_user_db_connection(user_id=1, user_role='admin') as conn:
                if not conn:
                    logger.error("Failed to get database connection for VM status distribution")
                    continue
                
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO public.vm_status_distribution 
                    (timestamp, running, stopped, error, owner_id) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    timestamp,
                    counts['running'],
                    counts['stopped'],
                    counts['error'],
                    owner_id
                ))
                
                conn.commit()
                cursor.close()
            
            # Add to metrics
            data_points.append({
                'metric_name': 'vm_running_count',
                'value': counts['running'],
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': owner_id,
                'timestamp': timestamp
            })
            
            data_points.append({
                'metric_name': 'vm_stopped_count',
                'value': counts['stopped'],
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': owner_id,
                'timestamp': timestamp
            })
            
            data_points.append({
                'metric_name': 'vm_error_count',
                'value': counts['error'],
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': owner_id,
                'timestamp': timestamp
            })
        
        return data_points
    except Exception as e:
        logger.error(f"Error collecting VM status distribution: {e}")
        return []

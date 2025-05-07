"""
Timeseries storage module.

This module provides functions for storing and retrieving timeseries data.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

from db.connection import get_db_connection
from db.user_connection import get_user_db_connection
from .config import timeseries_config

# Configure logging
logger = logging.getLogger(__name__)

def store_metric(
    metric_name: str,
    value: Union[float, int, bool, str],
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_id: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    user_id: Optional[int] = 1,  # Default to admin user
    user_role: Optional[str] = 'admin'  # Default to admin role
) -> bool:
    """
    Store a single metric value.

    Args:
        metric_name: The name of the metric
        value: The metric value
        entity_type: The entity type (e.g., 'vm', 'account', 'system')
        entity_id: The entity ID (e.g., VM ID, account ID)
        owner_id: The owner ID for RLS
        timestamp: The timestamp of the measurement (defaults to now)
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')

    Returns:
        bool: True if the metric was stored successfully, False otherwise
    """
    try:
        # Get database connection with RLS context
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for storing metric")
                return False

            cursor = conn.cursor()

            # Get metric ID
            cursor.execute(
                "SELECT id, data_type FROM public.metrics_definitions WHERE name = %s",
                (metric_name,)
            )
            result = cursor.fetchone()

            if not result:
                logger.error(f"Metric '{metric_name}' not found")
                return False

            metric_id, data_type = result

            # Set timestamp to now if not provided
            if timestamp is None:
                timestamp = datetime.now()

            # Determine which value column to use based on data type
            value_float = None
            value_int = None
            value_bool = None
            value_text = None

            if data_type == 'float':
                value_float = float(value)
            elif data_type == 'integer':
                value_int = int(value)
            elif data_type == 'boolean':
                value_bool = bool(value)
            elif data_type == 'string':
                value_text = str(value)
            else:
                logger.error(f"Unknown data type '{data_type}' for metric '{metric_name}'")
                return False

            # Insert metric value
            cursor.execute(
                """
                INSERT INTO public.timeseries_data
                (metric_id, timestamp, value_float, value_int, value_bool, value_text, entity_type, entity_id, owner_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (metric_id, timestamp, value_float, value_int, value_bool, value_text, entity_type, entity_id, owner_id)
            )

            # Commit transaction
            conn.commit()
            cursor.close()

        return True
    except Exception as e:
        logger.error(f"Error storing metric '{metric_name}': {e}")
        return False
    finally:
        # Close cursor
        if 'cursor' in locals() and cursor:
            cursor.close()

def store_metrics_batch(
    metrics: List[Dict[str, Any]],
    user_id: Optional[int] = 1,  # Default to admin user
    user_role: Optional[str] = 'admin'  # Default to admin role
) -> Tuple[int, int]:
    """
    Store multiple metric values in a batch.

    Args:
        metrics: List of metric dictionaries, each containing:
            - metric_name: The name of the metric
            - value: The metric value
            - entity_type: The entity type (optional)
            - entity_id: The entity ID (optional)
            - owner_id: The owner ID for RLS (optional)
            - timestamp: The timestamp of the measurement (optional, defaults to now)
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')

    Returns:
        Tuple[int, int]: (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0

    try:
        logger.info(f"Storing {len(metrics)} metrics with user_id={user_id}, user_role={user_role}")

        # Log the first few metrics for debugging
        if metrics and len(metrics) > 0:
            sample_metrics = metrics[:3]  # First 3 metrics
            logger.info(f"Sample metrics: {sample_metrics}")

        # Get database connection with RLS context
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for storing metrics batch")
                return success_count, failure_count

            cursor = conn.cursor()

            # Get all metric definitions
            cursor.execute(
                "SELECT id, name, data_type FROM public.metrics_definitions"
            )
            metric_defs = {row[1]: (row[0], row[2]) for row in cursor.fetchall()}
            logger.info(f"Found {len(metric_defs)} metric definitions")

            # Prepare batch data
            batch_data = []

            for metric in metrics:
                metric_name = metric.get('metric_name')

                if metric_name not in metric_defs:
                    logger.error(f"Metric '{metric_name}' not found")
                    failure_count += 1
                    continue

                metric_id, data_type = metric_defs[metric_name]
                value = metric.get('value')
                entity_type = metric.get('entity_type')
                entity_id = metric.get('entity_id')
                owner_id = metric.get('owner_id')

                # Ensure owner_id is set to a valid value (use the user_id parameter if not provided)
                if owner_id is None:
                    owner_id = user_id
                    logger.debug(f"Setting default owner_id={owner_id} for metric '{metric_name}'")

                timestamp = metric.get('timestamp', datetime.now())

                # Determine which value column to use based on data type
                value_float = None
                value_int = None
                value_bool = None
                value_text = None

                try:
                    if data_type == 'float':
                        value_float = float(value)
                    elif data_type == 'integer':
                        value_int = int(value)
                    elif data_type == 'boolean':
                        value_bool = bool(value)
                    elif data_type == 'string':
                        value_text = str(value)
                    else:
                        logger.error(f"Unknown data type '{data_type}' for metric '{metric_name}'")
                        failure_count += 1
                        continue

                    batch_data.append((
                        metric_id, timestamp, value_float, value_int, value_bool, value_text,
                        entity_type, entity_id, owner_id
                    ))
                    success_count += 1
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting value '{value}' for metric '{metric_name}': {e}")
                    failure_count += 1

            # Insert batch data
            if batch_data:
                logger.info(f"Inserting {len(batch_data)} metrics into timeseries_data")
                try:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO public.timeseries_data
                        (metric_id, timestamp, value_float, value_int, value_bool, value_text, entity_type, entity_id, owner_id)
                        VALUES %s
                        """,
                        batch_data
                    )

                    # Commit transaction
                    conn.commit()
                    logger.info(f"Successfully inserted {len(batch_data)} metrics")
                except Exception as e:
                    logger.error(f"Error inserting batch data: {e}")
                    # Log the first few batch data entries for debugging
                    for i, data in enumerate(batch_data[:3]):
                        logger.error(f"Batch data {i}: {data}")
                    failure_count += len(batch_data)
                    success_count = 0
                    return success_count, failure_count

            return success_count, failure_count
    except Exception as e:
        logger.error(f"Error storing metrics batch: {e}")
        return success_count, failure_count + (len(metrics) - success_count)
    finally:
        # Close cursor
        if 'cursor' in locals() and cursor:
            cursor.close()

def get_metric_data(
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_id: Optional[int] = None,
    limit: int = 1000,
    offset: int = 0,
    user_id: Optional[int] = 1,  # Default to admin user
    user_role: Optional[str] = 'admin'  # Default to admin role
) -> List[Dict[str, Any]]:
    """
    Get metric data for a specific time range.

    Args:
        metric_name: The name of the metric
        start_time: The start time of the range
        end_time: The end time of the range
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
        owner_id: The owner ID for RLS (optional)
        limit: The maximum number of data points to return
        offset: The offset for pagination
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')

    Returns:
        List[Dict[str, Any]]: List of metric data points
    """
    try:
        logger.info(f"Getting metric data: metric={metric_name}, entity_type={entity_type}, entity_id={entity_id}, owner_id={owner_id}, user_id={user_id}, user_role={user_role}")
        # Get database connection with RLS context
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for retrieving metric data")
                return []

            cursor = conn.cursor()

            # Get metric ID and data type
            cursor.execute(
                "SELECT id, data_type FROM public.metrics_definitions WHERE name = %s",
                (metric_name,)
            )
            result = cursor.fetchone()

            if not result:
                logger.error(f"Metric '{metric_name}' not found")
                cursor.close()
                return []

            metric_id, data_type = result

            # Build query
            query = """
            SELECT
                id, timestamp,
                CASE
                    WHEN %s = 'float' THEN value_float
                    WHEN %s = 'integer' THEN value_int::float
                    WHEN %s = 'boolean' THEN value_bool::int::float
                    ELSE NULL
                END AS value,
                entity_type, entity_id
            FROM public.timeseries_data
            WHERE metric_id = %s
            AND timestamp BETWEEN %s AND %s
            """

            params = [data_type, data_type, data_type, metric_id, start_time, end_time]

            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = %s"
                params.append(entity_id)

            if owner_id:
                query += " AND owner_id = %s"
                params.append(owner_id)

            query += " ORDER BY timestamp ASC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute query
            cursor.execute(query, params)

            # Process results
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'value': row[2],
                    'entity_type': row[3],
                    'entity_id': row[4]
                })

            cursor.close()
            return results
    except Exception as e:
        logger.error(f"Error getting metric data for '{metric_name}': {e}")
        return []
    finally:
        # Close cursor
        if 'cursor' in locals() and cursor:
            cursor.close()

def get_metric_aggregates(
    metric_name: str,
    period_type: str,
    start_time: datetime,
    end_time: datetime,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_id: Optional[int] = None,
    limit: int = 1000,
    offset: int = 0,
    user_id: Optional[int] = 1,  # Default to admin user
    user_role: Optional[str] = 'admin'  # Default to admin role
) -> List[Dict[str, Any]]:
    """
    Get metric aggregates for a specific time range and period type.

    Args:
        metric_name: The name of the metric
        period_type: The aggregation period type (hourly, daily, weekly, monthly)
        start_time: The start time of the range
        end_time: The end time of the range
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
        owner_id: The owner ID for RLS (optional)
        limit: The maximum number of data points to return
        offset: The offset for pagination
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')

    Returns:
        List[Dict[str, Any]]: List of metric aggregate data points
    """
    try:
        logger.info(f"Getting metric aggregates: metric={metric_name}, period_type={period_type}, entity_type={entity_type}, entity_id={entity_id}, owner_id={owner_id}, user_id={user_id}, user_role={user_role}")
        # Get database connection with RLS context
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for retrieving metric aggregates")
                return []

            cursor = conn.cursor()

            # Get metric ID
            cursor.execute(
                "SELECT id FROM public.metrics_definitions WHERE name = %s",
                (metric_name,)
            )
            result = cursor.fetchone()

            if not result:
                logger.error(f"Metric '{metric_name}' not found")
                cursor.close()
                return []

            metric_id = result[0]

            # Build query
            query = """
            SELECT
                id, period_start, period_end, min_value, max_value, avg_value, sum_value, count_value,
                entity_type, entity_id
            FROM public.timeseries_aggregates
            WHERE metric_id = %s
            AND period_type = %s
            AND period_start >= %s
            AND period_end <= %s
            """

            params = [metric_id, period_type, start_time, end_time]

            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = %s"
                params.append(entity_id)

            if owner_id:
                query += " AND owner_id = %s"
                params.append(owner_id)

            query += " ORDER BY period_start ASC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute query
            cursor.execute(query, params)

            # Process results
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'period_start': row[1],
                    'period_end': row[2],
                    'min': row[3],
                    'max': row[4],
                    'avg': row[5],
                    'sum': row[6],
                    'count': row[7],
                    'entity_type': row[8],
                    'entity_id': row[9]
                })

            cursor.close()
            return results
    except Exception as e:
        logger.error(f"Error getting metric aggregates for '{metric_name}': {e}")
        return []
    finally:
        # Close cursor
        if 'cursor' in locals() and cursor:
            cursor.close()

def get_latest_metric_value(
    metric_name: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_id: Optional[int] = None,
    user_id: Optional[int] = 1,  # Default to admin user
    user_role: Optional[str] = 'admin'  # Default to admin role
) -> Optional[Dict[str, Any]]:
    """
    Get the latest value for a metric.

    Args:
        metric_name: The name of the metric
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
        owner_id: The owner ID for RLS (optional)
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')

    Returns:
        Optional[Dict[str, Any]]: The latest metric value or None if not found
    """
    try:
        logger.info(f"Getting latest metric value: metric={metric_name}, entity_type={entity_type}, entity_id={entity_id}, owner_id={owner_id}, user_id={user_id}, user_role={user_role}")
        # Get database connection with RLS context
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for retrieving latest metric value")
                return None

            cursor = conn.cursor()

            # Get metric ID and data type
            cursor.execute(
                "SELECT id, data_type FROM public.metrics_definitions WHERE name = %s",
                (metric_name,)
            )
            result = cursor.fetchone()

            if not result:
                logger.error(f"Metric '{metric_name}' not found")
                cursor.close()
                return None

            metric_id, data_type = result

            # Build query
            query = """
            SELECT
                id, timestamp,
                CASE
                    WHEN %s = 'float' THEN value_float
                    WHEN %s = 'integer' THEN value_int::float
                    WHEN %s = 'boolean' THEN value_bool::int::float
                    ELSE NULL
                END AS value,
                entity_type, entity_id
            FROM public.timeseries_data
            WHERE metric_id = %s
            """

            params = [data_type, data_type, data_type, metric_id]

            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = %s"
                params.append(entity_id)

            if owner_id:
                query += " AND owner_id = %s"
                params.append(owner_id)

            query += " ORDER BY timestamp DESC LIMIT 1"

            # Execute query
            cursor.execute(query, params)

            # Process result
            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    'id': row[0],
                    'timestamp': row[1],
                    'value': row[2],
                    'entity_type': row[3],
                    'entity_id': row[4]
                }

            return None
    except Exception as e:
        logger.error(f"Error getting latest metric value for '{metric_name}': {e}")
        return None
    finally:
        # Close cursor
        if 'cursor' in locals() and cursor:
            cursor.close()

def get_metric_statistics(
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get statistics for a metric over a specific time range.

    Args:
        metric_name: The name of the metric
        start_time: The start time of the range
        end_time: The end time of the range
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
        owner_id: The owner ID for RLS (optional)

    Returns:
        Dict[str, Any]: Statistics for the metric
    """
    try:
        # Get database connection
        with get_db_connection() as conn:
            if not conn:
                logger.error("Failed to get database connection for retrieving metric statistics")
                return {
                    'min': None,
                    'max': None,
                    'avg': None,
                    'sum': None,
                    'count': 0
                }

            cursor = conn.cursor()

            # Get metric ID and data type
            cursor.execute(
                "SELECT id, data_type FROM public.metrics_definitions WHERE name = %s",
                (metric_name,)
            )
            result = cursor.fetchone()

            if not result:
                logger.error(f"Metric '{metric_name}' not found")
                cursor.close()
                return {
                    'min': None,
                    'max': None,
                    'avg': None,
                    'sum': None,
                    'count': 0
                }

            metric_id, data_type = result

            # Build query
            query = """
            SELECT
                MIN(CASE
                    WHEN %s = 'float' THEN value_float
                    WHEN %s = 'integer' THEN value_int::float
                    WHEN %s = 'boolean' THEN value_bool::int::float
                    ELSE NULL
                END) AS min_value,
                MAX(CASE
                    WHEN %s = 'float' THEN value_float
                    WHEN %s = 'integer' THEN value_int::float
                    WHEN %s = 'boolean' THEN value_bool::int::float
                    ELSE NULL
                END) AS max_value,
                AVG(CASE
                    WHEN %s = 'float' THEN value_float
                    WHEN %s = 'integer' THEN value_int::float
                    WHEN %s = 'boolean' THEN value_bool::int::float
                    ELSE NULL
                END) AS avg_value,
                SUM(CASE
                    WHEN %s = 'float' THEN value_float
                    WHEN %s = 'integer' THEN value_int::float
                    WHEN %s = 'boolean' THEN value_bool::int::float
                    ELSE NULL
                END) AS sum_value,
                COUNT(*) AS count_value
            FROM public.timeseries_data
            WHERE metric_id = %s
            AND timestamp BETWEEN %s AND %s
            """

            params = [
                data_type, data_type, data_type,
                data_type, data_type, data_type,
                data_type, data_type, data_type,
                data_type, data_type, data_type,
                metric_id, start_time, end_time
            ]

            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)

            if entity_id:
                query += " AND entity_id = %s"
                params.append(entity_id)

            if owner_id:
                query += " AND owner_id = %s"
                params.append(owner_id)

            # Execute query
            cursor.execute(query, params)

            # Process result
            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    'min': row[0],
                    'max': row[1],
                    'avg': row[2],
                    'sum': row[3],
                    'count': row[4]
                }

            return {
                'min': None,
                'max': None,
                'avg': None,
                'sum': None,
                'count': 0
            }
    except Exception as e:
        logger.error(f"Error getting metric statistics for '{metric_name}': {e}")
        return {
            'min': None,
            'max': None,
            'avg': None,
            'sum': None,
            'count': 0
        }
    finally:
        # Close cursor
        if 'cursor' in locals() and cursor:
            cursor.close()

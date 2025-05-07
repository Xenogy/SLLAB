"""
Timeseries aggregator module.

This module provides functions for aggregating timeseries data.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

from db.connection import get_db_connection
from db.user_connection import get_user_db_connection
from .config import timeseries_config

# Configure logging
logger = logging.getLogger(__name__)

# Aggregator state
_aggregator_thread = None
_aggregator_stop_event = threading.Event()

def aggregate_metrics(
    period_type: str,
    start_time: datetime,
    end_time: datetime,
    user_id: int = 1,  # Default to admin user
    user_role: str = 'admin'  # Default to admin role
) -> Tuple[int, int]:
    """
    Aggregate metrics for a specific period.

    Args:
        period_type: The aggregation period type (hourly, daily, weekly, monthly)
        start_time: The start time of the period
        end_time: The end time of the period
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')

    Returns:
        Tuple[int, int]: (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0

    try:
        # Get database connection with RLS context - use a single connection for the entire operation
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for aggregating metrics")
                return 0, 0

            # Get all metric definitions
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id, name, data_type FROM public.metrics_definitions"
                )
                metric_defs = cursor.fetchall()
                logger.debug(f"Found {len(metric_defs)} metric definitions for aggregation")
            finally:
                cursor.close()

            # Process each metric
            for metric_id, metric_name, data_type in metric_defs:
                try:
                    # Get all entity types and IDs for this metric
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            """
                            SELECT DISTINCT entity_type, entity_id, owner_id
                            FROM public.timeseries_data
                            WHERE metric_id = %s
                            AND timestamp BETWEEN %s AND %s
                            """,
                            (metric_id, start_time, end_time)
                        )
                        entities = cursor.fetchall()
                        logger.debug(f"Found {len(entities)} entities for metric '{metric_name}' in period {start_time} to {end_time}")
                    finally:
                        cursor.close()

                    # Process each entity
                    for entity_type, entity_id, owner_id in entities:
                        try:
                            # Calculate aggregates
                            cursor = conn.cursor()
                            try:
                                cursor.execute(
                                    """
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
                                    AND entity_type = %s
                                    AND entity_id = %s
                                    AND timestamp BETWEEN %s AND %s
                                    """,
                                    (
                                        data_type, data_type, data_type,
                                        data_type, data_type, data_type,
                                        data_type, data_type, data_type,
                                        data_type, data_type, data_type,
                                        metric_id, entity_type, entity_id, start_time, end_time
                                    )
                                )
                                result = cursor.fetchone()
                                min_value, max_value, avg_value, sum_value, count_value = result
                            finally:
                                cursor.close()

                            # Skip if no data
                            if count_value == 0:
                                continue

                            # Check if aggregate already exists and update/insert in a single operation
                            cursor = conn.cursor()
                            try:
                                # First try to update existing record
                                cursor.execute(
                                    """
                                    UPDATE public.timeseries_aggregates
                                    SET min_value = %s, max_value = %s, avg_value = %s, sum_value = %s, count_value = %s
                                    WHERE metric_id = %s
                                    AND period_type = %s
                                    AND period_start = %s
                                    AND period_end = %s
                                    AND entity_type = %s
                                    AND entity_id = %s
                                    RETURNING id
                                    """,
                                    (min_value, max_value, avg_value, sum_value, count_value,
                                     metric_id, period_type, start_time, end_time, entity_type, entity_id)
                                )

                                # If no rows were updated, insert a new record
                                if cursor.rowcount == 0:
                                    cursor.execute(
                                        """
                                        INSERT INTO public.timeseries_aggregates
                                        (metric_id, period_start, period_end, period_type, min_value, max_value, avg_value, sum_value, count_value, entity_type, entity_id, owner_id)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        """,
                                        (metric_id, start_time, end_time, period_type, min_value, max_value, avg_value, sum_value, count_value, entity_type, entity_id, owner_id)
                                    )

                                conn.commit()
                            finally:
                                cursor.close()

                            success_count += 1
                        except Exception as e:
                            logger.error(f"Error aggregating metric '{metric_name}' for entity '{entity_type}:{entity_id}': {e}")
                            failure_count += 1
                except Exception as e:
                    logger.error(f"Error processing metric '{metric_name}': {e}")
                    failure_count += 1

        return success_count, failure_count
    except Exception as e:
        logger.error(f"Error aggregating metrics: {e}")
        return 0, 0

def clean_old_data(
    user_id: int = 1,  # Default to admin user
    user_role: str = 'admin'  # Default to admin role
) -> None:
    """
    Clean old data based on retention policy.

    Args:
        user_id: The user ID for RLS context (defaults to 1 for admin)
        user_role: The user role for RLS context (defaults to 'admin')
    """
    try:
        # Get database connection with RLS context - use a single connection for the entire operation
        with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
            if not conn:
                logger.error("Failed to get database connection for cleaning old data")
                return

            cursor = conn.cursor()
            try:
                # Clean raw data
                raw_retention = timeseries_config['retention']['raw_data_days']
                raw_cutoff = datetime.now() - timedelta(days=raw_retention)

                cursor.execute(
                    "DELETE FROM public.timeseries_data WHERE timestamp < %s",
                    (raw_cutoff,)
                )

                raw_deleted = cursor.rowcount
                logger.info(f"Deleted {raw_deleted} raw data points older than {raw_cutoff}")

                # Clean hourly aggregates
                hourly_retention = timeseries_config['retention']['hourly_aggregates_days']
                hourly_cutoff = datetime.now() - timedelta(days=hourly_retention)

                cursor.execute(
                    "DELETE FROM public.timeseries_aggregates WHERE period_type = 'hourly' AND period_end < %s",
                    (hourly_cutoff,)
                )

                hourly_deleted = cursor.rowcount
                logger.info(f"Deleted {hourly_deleted} hourly aggregates older than {hourly_cutoff}")

                # Clean daily aggregates
                daily_retention = timeseries_config['retention']['daily_aggregates_days']
                daily_cutoff = datetime.now() - timedelta(days=daily_retention)

                cursor.execute(
                    "DELETE FROM public.timeseries_aggregates WHERE period_type = 'daily' AND period_end < %s",
                    (daily_cutoff,)
                )

                daily_deleted = cursor.rowcount
                logger.info(f"Deleted {daily_deleted} daily aggregates older than {daily_cutoff}")

                # Clean weekly aggregates
                weekly_retention = timeseries_config['retention']['weekly_aggregates_days']
                weekly_cutoff = datetime.now() - timedelta(days=weekly_retention)

                cursor.execute(
                    "DELETE FROM public.timeseries_aggregates WHERE period_type = 'weekly' AND period_end < %s",
                    (weekly_cutoff,)
                )

                weekly_deleted = cursor.rowcount
                logger.info(f"Deleted {weekly_deleted} weekly aggregates older than {weekly_cutoff}")

                # Clean monthly aggregates
                monthly_retention = timeseries_config['retention']['monthly_aggregates_days']
                monthly_cutoff = datetime.now() - timedelta(days=monthly_retention)

                cursor.execute(
                    "DELETE FROM public.timeseries_aggregates WHERE period_type = 'monthly' AND period_end < %s",
                    (monthly_cutoff,)
                )

                monthly_deleted = cursor.rowcount
                logger.info(f"Deleted {monthly_deleted} monthly aggregates older than {monthly_cutoff}")

                # Commit transaction
                conn.commit()
            finally:
                cursor.close()
    except Exception as e:
        logger.error(f"Error cleaning old data: {e}")

def aggregator_thread_func() -> None:
    """
    Aggregator thread function.
    """
    logger.info("Timeseries aggregator thread started")

    while not _aggregator_stop_event.is_set():
        try:
            now = datetime.now()

            # Hourly aggregation
            if timeseries_config['aggregation']['periods']['hourly']:
                # Round to the current hour
                hour_start = now.replace(minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)

                logger.info(f"Aggregating hourly data for {hour_start} to {hour_end}")
                success, failure = aggregate_metrics(
                    period_type='hourly',
                    start_time=hour_start,
                    end_time=hour_end,
                    user_id=1,  # Admin user ID
                    user_role='admin'  # Admin role
                )
                logger.info(f"Hourly aggregation: {success} successes, {failure} failures")

            # Daily aggregation (at midnight)
            if timeseries_config['aggregation']['periods']['daily'] and now.hour == 0 and now.minute < 10:
                # Round to the previous day
                day_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
                day_start = day_end - timedelta(days=1)

                logger.info(f"Aggregating daily data for {day_start} to {day_end}")
                success, failure = aggregate_metrics(
                    period_type='daily',
                    start_time=day_start,
                    end_time=day_end,
                    user_id=1,  # Admin user ID
                    user_role='admin'  # Admin role
                )
                logger.info(f"Daily aggregation: {success} successes, {failure} failures")

            # Weekly aggregation (on Monday)
            if timeseries_config['aggregation']['periods']['weekly'] and now.weekday() == 0 and now.hour == 1 and now.minute < 10:
                # Round to the previous week (Monday to Monday)
                week_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = week_end - timedelta(days=7)

                logger.info(f"Aggregating weekly data for {week_start} to {week_end}")
                success, failure = aggregate_metrics(
                    period_type='weekly',
                    start_time=week_start,
                    end_time=week_end,
                    user_id=1,  # Admin user ID
                    user_role='admin'  # Admin role
                )
                logger.info(f"Weekly aggregation: {success} successes, {failure} failures")

            # Monthly aggregation (on the 1st of the month)
            if timeseries_config['aggregation']['periods']['monthly'] and now.day == 1 and now.hour == 2 and now.minute < 10:
                # Round to the previous month
                month_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                # Get the last day of the previous month
                if month_end.month == 1:
                    month_start = month_end.replace(year=month_end.year-1, month=12, day=1)
                else:
                    month_start = month_end.replace(month=month_end.month-1, day=1)

                logger.info(f"Aggregating monthly data for {month_start} to {month_end}")
                success, failure = aggregate_metrics(
                    period_type='monthly',
                    start_time=month_start,
                    end_time=month_end,
                    user_id=1,  # Admin user ID
                    user_role='admin'  # Admin role
                )
                logger.info(f"Monthly aggregation: {success} successes, {failure} failures")

            # Clean old data (once a day at 3 AM)
            if now.hour == 3 and now.minute < 10:
                logger.info("Cleaning old data")
                clean_old_data(
                    user_id=1,  # Admin user ID
                    user_role='admin'  # Admin role
                )

            # Sleep until next interval
            _aggregator_stop_event.wait(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in aggregator thread: {e}")
            # Sleep for a short time to avoid busy-waiting in case of persistent errors
            _aggregator_stop_event.wait(60)

    logger.info("Timeseries aggregator thread stopped")

def start_aggregator_thread() -> threading.Thread:
    """
    Start the aggregator thread.

    Returns:
        threading.Thread: The aggregator thread
    """
    global _aggregator_thread, _aggregator_stop_event

    if not timeseries_config['aggregation']['enabled']:
        logger.info("Timeseries aggregation is disabled")
        return None

    if _aggregator_thread and _aggregator_thread.is_alive():
        logger.info("Timeseries aggregator thread is already running")
        return _aggregator_thread

    _aggregator_stop_event.clear()
    _aggregator_thread = threading.Thread(target=aggregator_thread_func, daemon=True)
    _aggregator_thread.start()

    return _aggregator_thread

def stop_aggregator_thread() -> None:
    """
    Stop the aggregator thread.
    """
    global _aggregator_thread, _aggregator_stop_event

    if _aggregator_thread and _aggregator_thread.is_alive():
        logger.info("Stopping timeseries aggregator thread")
        _aggregator_stop_event.set()
        _aggregator_thread.join(timeout=5)
        _aggregator_thread = None

def init_aggregator() -> None:
    """
    Initialize the timeseries aggregator.
    """
    logger.info("Initializing timeseries aggregator")
    start_aggregator_thread()

def shutdown_aggregator() -> None:
    """
    Shutdown the timeseries aggregator.
    """
    logger.info("Shutting down timeseries aggregator")
    stop_aggregator_thread()

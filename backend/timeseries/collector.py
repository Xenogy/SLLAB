"""
Timeseries collector module.

This module provides functions for collecting timeseries data.
"""

import logging
import time
import threading
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from db.connection import get_db_connection
from db.user_connection import get_user_db_connection
from .config import timeseries_config
from .vm_status import collect_vm_status_distribution
from .storage import store_metric, store_metrics_batch

# Configure logging
logger = logging.getLogger(__name__)

# Collector state
_collector_thread = None
_collector_stop_event = threading.Event()

def collect_system_metrics() -> List[Dict[str, Any]]:
    """
    Collect system metrics.

    Returns:
        List[Dict[str, Any]]: List of system metrics
    """
    try:
        metrics = []
        timestamp = datetime.now()

        # Get all user IDs to store metrics for each user (for RLS)
        user_ids = [1]  # Start with admin user
        try:
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM public.users WHERE is_active = TRUE")
                    for row in cursor.fetchall():
                        if row[0] != 1:  # Skip admin user (already added)
                            user_ids.append(row[0])
                    cursor.close()
        except Exception as e:
            logger.error(f"Error getting user IDs: {e}")

        logger.info(f"Collecting system metrics for {len(user_ids)} users")

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        for user_id in user_ids:
            metrics.append({
                'metric_name': 'cpu_usage',
                'value': cpu_percent,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

        # Memory usage
        memory = psutil.virtual_memory()
        for user_id in user_ids:
            metrics.append({
                'metric_name': 'memory_usage',
                'value': memory.percent,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

        # Disk usage
        disk = psutil.disk_usage('/')
        for user_id in user_ids:
            metrics.append({
                'metric_name': 'disk_usage',
                'value': disk.percent,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

        # Network usage
        net_io = psutil.net_io_counters()
        for user_id in user_ids:
            metrics.append({
                'metric_name': 'network_in',
                'value': net_io.bytes_recv / 1024,  # KB
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })
            metrics.append({
                'metric_name': 'network_out',
                'value': net_io.bytes_sent / 1024,  # KB
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

        # Database connections
        try:
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
                    active_connections = cursor.fetchone()[0]
                    cursor.close()

                    for user_id in user_ids:
                        metrics.append({
                            'metric_name': 'active_connections',
                            'value': active_connections,
                            'entity_type': 'system',
                            'entity_id': 'system',
                            'owner_id': user_id,
                            'timestamp': timestamp
                        })
        except Exception as e:
            logger.error(f"Error getting database connection count: {e}")

        return metrics
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return []

def collect_vm_metrics() -> List[Dict[str, Any]]:
    """
    Collect VM metrics.

    Returns:
        List[Dict[str, Any]]: List of VM metrics
    """
    try:
        metrics = []
        timestamp = datetime.now()

        # Get all user IDs to store metrics for each user (for RLS)
        user_ids = [1]  # Start with admin user
        try:
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM public.users WHERE is_active = TRUE")
                    for row in cursor.fetchall():
                        if row[0] != 1:  # Skip admin user (already added)
                            user_ids.append(row[0])
                    cursor.close()
        except Exception as e:
            logger.error(f"Error getting user IDs: {e}")

        logger.info(f"Collecting VM metrics for {len(user_ids)} users")

        # Get database connection with RLS context
        with get_user_db_connection(user_id=1, user_role='admin') as conn:
            if not conn:
                logger.error("Failed to get database connection for VM metrics")
                return []

            cursor = conn.cursor()

            # Get VM counts by status
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM public.vms
                GROUP BY status
            """)

            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Calculate total VMs
        total_vms = sum(status_counts.values())

        # Add VM count metrics for each user
        for user_id in user_ids:
            metrics.append({
                'metric_name': 'vm_count',
                'value': total_vms,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

            running_vms = status_counts.get('running', 0)
            metrics.append({
                'metric_name': 'vm_running_count',
                'value': running_vms,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

            stopped_vms = status_counts.get('stopped', 0)
            metrics.append({
                'metric_name': 'vm_stopped_count',
                'value': stopped_vms,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

            error_vms = status_counts.get('error', 0)
            metrics.append({
                'metric_name': 'vm_error_count',
                'value': error_vms,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

        with get_user_db_connection(user_id=1, user_role='admin') as conn:
            if not conn:
                logger.error("Failed to get database connection for VM metrics")
                return metrics

            cursor = conn.cursor()

            # Get individual VM metrics
            cursor.execute("""
                SELECT
                    id, vmid, name, status, cpu_usage_percent,
                    memory_mb, uptime_seconds, owner_id
                FROM public.vms
            """)

            for row in cursor.fetchall():
                vm_id, vmid, name, status, cpu_usage, memory_mb, uptime, owner_id = row

                # Use default owner_id if it's None or empty
                safe_owner_id = owner_id if owner_id else 1

                # Add CPU usage metric
                if cpu_usage is not None:
                    metrics.append({
                        'metric_name': 'vm_cpu_usage',
                        'value': cpu_usage,
                        'entity_type': 'vm',
                        'entity_id': str(vm_id),
                        'owner_id': safe_owner_id,
                        'timestamp': timestamp
                    })

                # Add uptime metric
                if uptime is not None:
                    metrics.append({
                        'metric_name': 'vm_uptime',
                        'value': uptime,
                        'entity_type': 'vm',
                        'entity_id': str(vm_id),
                        'owner_id': safe_owner_id,
                        'timestamp': timestamp
                    })

            # Get Windows VM agent metrics
            cursor.execute("""
                SELECT
                    vm_id, cpu_usage_percent, memory_usage_percent,
                    disk_usage_percent, uptime_seconds, owner_id
                FROM public.windows_vm_agents
                WHERE status = 'active'
            """)

            for row in cursor.fetchall():
                vm_id, cpu_usage, memory_usage, disk_usage, uptime, owner_id = row

                # Use default owner_id if it's None or empty
                safe_owner_id = owner_id if owner_id else 1

                # Add CPU usage metric
                if cpu_usage is not None:
                    metrics.append({
                        'metric_name': 'vm_cpu_usage',
                        'value': cpu_usage,
                        'entity_type': 'vm_agent',
                        'entity_id': vm_id,
                        'owner_id': safe_owner_id,
                        'timestamp': timestamp
                    })

                # Add memory usage metric
                if memory_usage is not None:
                    metrics.append({
                        'metric_name': 'vm_memory_usage',
                        'value': memory_usage,
                        'entity_type': 'vm_agent',
                        'entity_id': vm_id,
                        'owner_id': safe_owner_id,
                        'timestamp': timestamp
                    })

                # Add disk usage metric
                if disk_usage is not None:
                    metrics.append({
                        'metric_name': 'vm_disk_usage',
                        'value': disk_usage,
                        'entity_type': 'vm_agent',
                        'entity_id': vm_id,
                        'owner_id': safe_owner_id,
                        'timestamp': timestamp
                    })

                # Add uptime metric
                if uptime is not None:
                    metrics.append({
                        'metric_name': 'vm_uptime',
                        'value': uptime,
                        'entity_type': 'vm_agent',
                        'entity_id': vm_id,
                        'owner_id': safe_owner_id,
                        'timestamp': timestamp
                    })

            cursor.close()

        return metrics
    except Exception as e:
        logger.error(f"Error collecting VM metrics: {e}")
        return []

def collect_account_metrics() -> List[Dict[str, Any]]:
    """
    Collect account metrics.

    Returns:
        List[Dict[str, Any]]: List of account metrics
    """
    try:
        metrics = []
        timestamp = datetime.now()

        # Get all user IDs to store metrics for each user (for RLS)
        user_ids = [1]  # Start with admin user
        try:
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM public.users WHERE is_active = TRUE")
                    for row in cursor.fetchall():
                        if row[0] != 1:  # Skip admin user (already added)
                            user_ids.append(row[0])
                    cursor.close()
        except Exception as e:
            logger.error(f"Error getting user IDs: {e}")

        logger.info(f"Collecting account metrics for {len(user_ids)} users")

        # Get database connection with RLS context
        with get_user_db_connection(user_id=1, user_role='admin') as conn:
            if not conn:
                logger.error("Failed to get database connection for account metrics")
                return []

            cursor = conn.cursor()

            # Get account counts
            cursor.execute("SELECT COUNT(*) FROM public.accounts")
            total_accounts = cursor.fetchone()[0]

            # Get locked account counts
            cursor.execute("SELECT COUNT(*) FROM public.accounts WHERE lock = TRUE")
            locked_accounts = cursor.fetchone()[0]

            cursor.close()

        # Get active account count (not locked)
        active_accounts = total_accounts - locked_accounts

        # Add metrics for each user
        for user_id in user_ids:
            metrics.append({
                'metric_name': 'account_count',
                'value': total_accounts,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

            metrics.append({
                'metric_name': 'account_locked_count',
                'value': locked_accounts,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

            metrics.append({
                'metric_name': 'account_active_count',
                'value': active_accounts,
                'entity_type': 'system',
                'entity_id': 'system',
                'owner_id': user_id,
                'timestamp': timestamp
            })

        return metrics
    except Exception as e:
        logger.error(f"Error collecting account metrics: {e}")
        return []

def collect_job_metrics() -> List[Dict[str, Any]]:
    """
    Collect job metrics.

    Returns:
        List[Dict[str, Any]]: List of job metrics
    """
    # This is a placeholder for job metrics collection
    # Implement based on your job tracking system
    return []

def collect_all_metrics() -> None:
    """
    Collect all metrics and store them.
    """
    try:
        all_metrics = []

        # Collect system metrics
        if timeseries_config['collection']['metrics']['system']:
            system_metrics = collect_system_metrics()
            all_metrics.extend(system_metrics)

        # Collect VM metrics
        if timeseries_config['collection']['metrics']['vm']:
            vm_metrics = collect_vm_metrics()
            all_metrics.extend(vm_metrics)

            # Collect VM status distribution
            vm_status_metrics = collect_vm_status_distribution()
            all_metrics.extend(vm_status_metrics)

        # Collect account metrics
        if timeseries_config['collection']['metrics']['account']:
            account_metrics = collect_account_metrics()
            all_metrics.extend(account_metrics)

        # Collect job metrics
        if timeseries_config['collection']['metrics']['job']:
            job_metrics = collect_job_metrics()
            all_metrics.extend(job_metrics)

        # Log metrics count by type
        metric_types = {}
        for metric in all_metrics:
            metric_name = metric.get('metric_name', 'unknown')
            if metric_name not in metric_types:
                metric_types[metric_name] = 0
            metric_types[metric_name] += 1

        logger.info(f"Collected metrics by type: {metric_types}")

        # Store metrics with admin RLS context
        if all_metrics:
            logger.info(f"Storing {len(all_metrics)} metrics...")
            success_count, failure_count = store_metrics_batch(
                metrics=all_metrics,
                user_id=1,  # Admin user ID
                user_role='admin'  # Admin role
            )
            logger.info(f"Stored {success_count} metrics, {failure_count} failures")
        else:
            logger.warning("No metrics collected!")
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}", exc_info=True)

def collector_thread_func() -> None:
    """
    Collector thread function.
    """
    logger.info("Timeseries collector thread started")

    while not _collector_stop_event.is_set():
        try:
            # Collect and store metrics
            collect_all_metrics()

            # Sleep until next interval
            _collector_stop_event.wait(timeseries_config['collection']['interval'])
        except Exception as e:
            logger.error(f"Error in collector thread: {e}")
            # Sleep for a short time to avoid busy-waiting in case of persistent errors
            _collector_stop_event.wait(5)

    logger.info("Timeseries collector thread stopped")

def start_collector_thread() -> threading.Thread:
    """
    Start the collector thread.

    Returns:
        threading.Thread: The collector thread
    """
    global _collector_thread, _collector_stop_event

    if not timeseries_config['collection']['enabled']:
        logger.info("Timeseries collection is disabled")
        return None

    if _collector_thread and _collector_thread.is_alive():
        logger.info("Timeseries collector thread is already running")
        return _collector_thread

    _collector_stop_event.clear()
    _collector_thread = threading.Thread(target=collector_thread_func, daemon=True)
    _collector_thread.start()

    return _collector_thread

def stop_collector_thread() -> None:
    """
    Stop the collector thread.
    """
    global _collector_thread, _collector_stop_event

    if _collector_thread and _collector_thread.is_alive():
        logger.info("Stopping timeseries collector thread")
        _collector_stop_event.set()
        _collector_thread.join(timeout=5)
        _collector_thread = None

def init_collector() -> None:
    """
    Initialize the timeseries collector.
    """
    logger.info("Initializing timeseries collector")
    start_collector_thread()

def shutdown_collector() -> None:
    """
    Shutdown the timeseries collector.
    """
    logger.info("Shutting down timeseries collector")
    stop_collector_thread()

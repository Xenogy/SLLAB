"""
Timeseries router for the AccountDB API.

This module provides endpoints for accessing timeseries data.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from routers.auth import get_current_active_user, get_current_admin_user
from timeseries.storage import (
    get_metric_data, get_metric_aggregates, get_latest_metric_value, get_metric_statistics
)
from db.connection import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/timeseries",
    tags=["timeseries"],
    responses={404: {"description": "Not found"}},
)

@router.get("/metrics")
async def list_metrics(current_user = Depends(get_current_active_user)):
    """
    List available metrics.

    Returns a list of available metrics with their definitions.
    """
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all metric categories
        cursor.execute(
            """
            SELECT id, name, description
            FROM public.metrics_categories
            ORDER BY name
            """
        )

        categories = []
        for row in cursor.fetchall():
            category_id, name, description = row

            # Get metrics for this category
            cursor.execute(
                """
                SELECT id, name, display_name, description, unit, data_type
                FROM public.metrics_definitions
                WHERE category_id = %s AND is_active = TRUE
                ORDER BY name
                """,
                (category_id,)
            )

            metrics = []
            for metric_row in cursor.fetchall():
                metric_id, metric_name, display_name, metric_description, unit, data_type = metric_row

                metrics.append({
                    "id": metric_id,
                    "name": metric_name,
                    "display_name": display_name,
                    "description": metric_description,
                    "unit": unit,
                    "data_type": data_type
                })

            categories.append({
                "id": category_id,
                "name": name,
                "description": description,
                "metrics": metrics
            })

        cursor.close()

        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing metrics: {str(e)}")

@router.get("/data/{metric_name}")
async def get_metric_data_endpoint(
    metric_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_active_user)
):
    """
    Get metric data for a specific time range.

    Args:
        metric_name: The name of the metric
        start_time: The start time of the range (defaults to 24 hours ago)
        end_time: The end time of the range (defaults to now)
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
        period: The aggregation period (raw, hourly, daily, weekly, monthly)
        limit: The maximum number of data points to return
        offset: The offset for pagination
    """
    try:
        # Set default time range if not provided
        if end_time is None:
            end_time = datetime.now()

        if start_time is None:
            # Default to different time ranges based on period
            if period == "monthly":
                start_time = end_time - timedelta(days=365)
            elif period == "weekly":
                start_time = end_time - timedelta(days=90)
            elif period == "daily":
                start_time = end_time - timedelta(days=30)
            elif period == "hourly":
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(days=1)

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get data based on period
        if period in ["hourly", "daily", "weekly", "monthly"]:
            data = get_metric_aggregates(
                metric_name=metric_name,
                period_type=period,
                start_time=start_time,
                end_time=end_time,
                entity_type=entity_type,
                entity_id=entity_id,
                owner_id=owner_id,
                limit=limit,
                offset=offset
            )

            # Format data for response
            formatted_data = []
            for point in data:
                formatted_data.append({
                    "timestamp": point["period_start"],
                    "end_time": point["period_end"],
                    "min": point["min"],
                    "max": point["max"],
                    "avg": point["avg"],
                    "sum": point["sum"],
                    "count": point["count"],
                    "entity_type": point["entity_type"],
                    "entity_id": point["entity_id"]
                })

            return {
                "metric": metric_name,
                "period": period,
                "start_time": start_time,
                "end_time": end_time,
                "data": formatted_data,
                "count": len(formatted_data)
            }
        else:
            # Get raw data
            data = get_metric_data(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                entity_type=entity_type,
                entity_id=entity_id,
                owner_id=owner_id,
                limit=limit,
                offset=offset
            )

            # Format data for response
            formatted_data = []
            for point in data:
                formatted_data.append({
                    "timestamp": point["timestamp"],
                    "value": point["value"],
                    "entity_type": point["entity_type"],
                    "entity_id": point["entity_id"]
                })

            return {
                "metric": metric_name,
                "period": "raw",
                "start_time": start_time,
                "end_time": end_time,
                "data": formatted_data,
                "count": len(formatted_data)
            }
    except Exception as e:
        logger.error(f"Error getting metric data for '{metric_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metric data: {str(e)}")

@router.get("/latest/{metric_name}")
async def get_latest_metric_value_endpoint(
    metric_name: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """
    Get the latest value for a metric.

    Args:
        metric_name: The name of the metric
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
    """
    try:
        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get latest value
        data = get_latest_metric_value(
            metric_name=metric_name,
            entity_type=entity_type,
            entity_id=entity_id,
            owner_id=owner_id
        )

        if data is None:
            return {
                "metric": metric_name,
                "value": None,
                "timestamp": None,
                "entity_type": entity_type,
                "entity_id": entity_id
            }

        return {
            "metric": metric_name,
            "value": data["value"],
            "timestamp": data["timestamp"],
            "entity_type": data["entity_type"],
            "entity_id": data["entity_id"]
        }
    except Exception as e:
        logger.error(f"Error getting latest metric value for '{metric_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error getting latest metric value: {str(e)}")

@router.get("/statistics/{metric_name}")
async def get_metric_statistics_endpoint(
    metric_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """
    Get statistics for a metric over a specific time range.

    Args:
        metric_name: The name of the metric
        start_time: The start time of the range (defaults to 24 hours ago)
        end_time: The end time of the range (defaults to now)
        entity_type: The entity type to filter by (optional)
        entity_id: The entity ID to filter by (optional)
    """
    try:
        # Set default time range if not provided
        if end_time is None:
            end_time = datetime.now()

        if start_time is None:
            start_time = end_time - timedelta(days=1)

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get statistics
        stats = get_metric_statistics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            entity_type=entity_type,
            entity_id=entity_id,
            owner_id=owner_id
        )

        return {
            "metric": metric_name,
            "start_time": start_time,
            "end_time": end_time,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting metric statistics for '{metric_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metric statistics: {str(e)}")

@router.get("/system/overview")
async def get_system_overview(
    period: Optional[str] = "hourly",
    duration: Optional[str] = "day",
    current_user = Depends(get_current_active_user)
):
    """
    Get system overview metrics.

    Args:
        period: The aggregation period (raw, hourly, daily, weekly, monthly)
        duration: The time duration (hour, day, week, month, year)
    """
    try:
        # Log user information
        logger.info(f"System overview request: user={current_user['username']}, id={current_user['id']}, role={current_user['role']}")
        logger.info(f"Request parameters: period={period}, duration={duration}")
        # Set time range based on duration
        end_time = datetime.now()

        if duration == "hour":
            start_time = end_time - timedelta(hours=1)
        elif duration == "week":
            start_time = end_time - timedelta(days=7)
        elif duration == "month":
            start_time = end_time - timedelta(days=30)
        elif duration == "year":
            start_time = end_time - timedelta(days=365)
        else:  # default to day
            start_time = end_time - timedelta(days=1)

        logger.info(f"Time range: {start_time} to {end_time}")

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get system metrics
        system_metrics = [
            "cpu_usage", "memory_usage", "disk_usage",
            "vm_count", "vm_running_count", "vm_stopped_count", "vm_error_count",
            "account_count", "account_active_count", "account_locked_count"
        ]

        metrics_data = {}

        for metric_name in system_metrics:
            # Get latest value
            latest = get_latest_metric_value(
                metric_name=metric_name,
                entity_type="system",
                entity_id="system",
                owner_id=owner_id
            )

            # Get statistics
            stats = get_metric_statistics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                entity_type="system",
                entity_id="system",
                owner_id=owner_id
            )

            # Get time series data
            if period in ["hourly", "daily", "weekly", "monthly"]:
                data = get_metric_aggregates(
                    metric_name=metric_name,
                    period_type=period,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=1000,
                    offset=0
                )

                # Format data for response
                formatted_data = []
                for point in data:
                    formatted_data.append({
                        "timestamp": point["period_start"],
                        "value": point["avg"]  # Use average for time series
                    })
            else:
                # Get raw data
                data = get_metric_data(
                    metric_name=metric_name,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=1000,
                    offset=0
                )

                # Format data for response
                formatted_data = []
                for point in data:
                    formatted_data.append({
                        "timestamp": point["timestamp"],
                        "value": point["value"]
                    })

            metrics_data[metric_name] = {
                "latest": latest["value"] if latest else None,
                "timestamp": latest["timestamp"] if latest else None,
                "statistics": stats,
                "data": formatted_data
            }

        # Format data for frontend
        cpu_usage = metrics_data.get('cpu_usage', {}).get('data', [])
        memory_usage = metrics_data.get('memory_usage', {}).get('data', [])
        disk_usage = metrics_data.get('disk_usage', {}).get('data', [])
        vm_count = metrics_data.get('vm_count', {}).get('data', [])
        account_count = metrics_data.get('account_count', {}).get('data', [])

        return {
            "period": period,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "vm_count": vm_count,
            "account_count": account_count
        }
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system overview: {str(e)}")

@router.get("/vm/overview")
async def get_vm_overview(
    vm_id: Optional[str] = None,
    period: Optional[str] = "hourly",
    duration: Optional[str] = "day",
    current_user = Depends(get_current_active_user)
):
    """
    Get VM overview metrics.

    Args:
        vm_id: The VM ID to filter by (optional)
        period: The aggregation period (raw, hourly, daily, weekly, monthly)
        duration: The time duration (hour, day, week, month, year)
    """
    try:
        # Set time range based on duration
        end_time = datetime.now()

        if duration == "hour":
            start_time = end_time - timedelta(hours=1)
        elif duration == "week":
            start_time = end_time - timedelta(days=7)
        elif duration == "month":
            start_time = end_time - timedelta(days=30)
        elif duration == "year":
            start_time = end_time - timedelta(days=365)
        else:  # default to day
            start_time = end_time - timedelta(days=1)

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get VM metrics
        vm_metrics = ["vm_cpu_usage", "vm_memory_usage", "vm_disk_usage", "vm_uptime"]

        # Get database connection to fetch VM list
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query to get VMs
        if vm_id:
            cursor.execute(
                """
                SELECT id, vmid, name, status, owner_id
                FROM public.vms
                WHERE id = %s OR vmid::text = %s
                """,
                (vm_id, vm_id)
            )
        else:
            # Get all VMs for the user or all VMs for admin
            if current_user["role"] == "admin":
                cursor.execute(
                    """
                    SELECT id, vmid, name, status, owner_id
                    FROM public.vms
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, vmid, name, status, owner_id
                    FROM public.vms
                    WHERE owner_id = %s
                    """,
                    (current_user["id"],)
                )

        vms = []
        for row in cursor.fetchall():
            vm_id, vmid, name, status, vm_owner_id = row

            vm_data = {
                "id": vm_id,
                "vmid": vmid,
                "name": name,
                "status": status,
                "metrics": {}
            }

            for metric_name in vm_metrics:
                # Get latest value
                latest = get_latest_metric_value(
                    metric_name=metric_name,
                    entity_type="vm",
                    entity_id=str(vm_id),
                    owner_id=owner_id
                )

                # Get statistics
                stats = get_metric_statistics(
                    metric_name=metric_name,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="vm",
                    entity_id=str(vm_id),
                    owner_id=owner_id
                )

                # Get time series data
                if period in ["hourly", "daily", "weekly", "monthly"]:
                    data = get_metric_aggregates(
                        metric_name=metric_name,
                        period_type=period,
                        start_time=start_time,
                        end_time=end_time,
                        entity_type="vm",
                        entity_id=str(vm_id),
                        owner_id=owner_id,
                        limit=1000,
                        offset=0
                    )

                    # Format data for response
                    formatted_data = []
                    for point in data:
                        formatted_data.append({
                            "timestamp": point["period_start"],
                            "value": point["avg"]  # Use average for time series
                        })
                else:
                    # Get raw data
                    data = get_metric_data(
                        metric_name=metric_name,
                        start_time=start_time,
                        end_time=end_time,
                        entity_type="vm",
                        entity_id=str(vm_id),
                        owner_id=owner_id,
                        limit=1000,
                        offset=0
                    )

                    # Format data for response
                    formatted_data = []
                    for point in data:
                        formatted_data.append({
                            "timestamp": point["timestamp"],
                            "value": point["value"]
                        })

                vm_data["metrics"][metric_name] = {
                    "latest": latest["value"] if latest else None,
                    "timestamp": latest["timestamp"] if latest else None,
                    "statistics": stats,
                    "data": formatted_data
                }

            vms.append(vm_data)

        cursor.close()

        return {
            "period": period,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "vms": vms
        }
    except Exception as e:
        logger.error(f"Error getting VM overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting VM overview: {str(e)}")

@router.get("/account/overview")
async def get_account_overview(
    period: Optional[str] = "hourly",
    duration: Optional[str] = "day",
    current_user = Depends(get_current_active_user)
):
    """
    Get account overview metrics.

    Args:
        period: The aggregation period (raw, hourly, daily, weekly, monthly)
        duration: The time duration (hour, day, week, month, year)
    """
    try:
        # Set time range based on duration
        end_time = datetime.now()

        if duration == "hour":
            start_time = end_time - timedelta(hours=1)
        elif duration == "week":
            start_time = end_time - timedelta(days=7)
        elif duration == "month":
            start_time = end_time - timedelta(days=30)
        elif duration == "year":
            start_time = end_time - timedelta(days=365)
        else:  # default to day
            start_time = end_time - timedelta(days=1)

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get account metrics
        account_metrics = ["account_count", "account_active_count", "account_locked_count"]

        metrics_data = {}

        for metric_name in account_metrics:
            # Get latest value
            latest = get_latest_metric_value(
                metric_name=metric_name,
                entity_type="system",
                entity_id="system",
                owner_id=owner_id
            )

            # Get statistics
            stats = get_metric_statistics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                entity_type="system",
                entity_id="system",
                owner_id=owner_id
            )

            # Get time series data
            if period in ["hourly", "daily", "weekly", "monthly"]:
                data = get_metric_aggregates(
                    metric_name=metric_name,
                    period_type=period,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=1000,
                    offset=0
                )

                # Format data for response
                formatted_data = []
                for point in data:
                    formatted_data.append({
                        "timestamp": point["period_start"],
                        "value": point["avg"]  # Use average for time series
                    })
            else:
                # Get raw data
                data = get_metric_data(
                    metric_name=metric_name,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=1000,
                    offset=0
                )

                # Format data for response
                formatted_data = []
                for point in data:
                    formatted_data.append({
                        "timestamp": point["timestamp"],
                        "value": point["value"]
                    })

            metrics_data[metric_name] = {
                "latest": latest["value"] if latest else None,
                "timestamp": latest["timestamp"] if latest else None,
                "statistics": stats,
                "data": formatted_data
            }

        return {
            "period": period,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "metrics": metrics_data
        }
    except Exception as e:
        logger.error(f"Error getting account overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting account overview: {str(e)}")

@router.get("/job/overview")
async def get_job_overview(
    period: Optional[str] = "hourly",
    duration: Optional[str] = "day",
    current_user = Depends(get_current_active_user)
):
    """
    Get job overview metrics.

    Args:
        period: The aggregation period (raw, hourly, daily, weekly, monthly)
        duration: The time duration (hour, day, week, month, year)
    """
    try:
        # Set time range based on duration
        end_time = datetime.now()

        if duration == "hour":
            start_time = end_time - timedelta(hours=1)
        elif duration == "week":
            start_time = end_time - timedelta(days=7)
        elif duration == "month":
            start_time = end_time - timedelta(days=30)
        elif duration == "year":
            start_time = end_time - timedelta(days=365)
        else:  # default to day
            start_time = end_time - timedelta(days=1)

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get job metrics
        job_metrics = ["job_count", "job_active_count", "job_completed_count", "job_failed_count", "job_execution_time"]

        metrics_data = {}

        for metric_name in job_metrics:
            # Get latest value
            latest = get_latest_metric_value(
                metric_name=metric_name,
                entity_type="system",
                entity_id="system",
                owner_id=owner_id
            )

            # Get statistics
            stats = get_metric_statistics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                entity_type="system",
                entity_id="system",
                owner_id=owner_id
            )

            # Get time series data
            if period in ["hourly", "daily", "weekly", "monthly"]:
                data = get_metric_aggregates(
                    metric_name=metric_name,
                    period_type=period,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=1000,
                    offset=0
                )

                # Format data for response
                formatted_data = []
                for point in data:
                    formatted_data.append({
                        "timestamp": point["period_start"],
                        "value": point["avg"]  # Use average for time series
                    })
            else:
                # Get raw data
                data = get_metric_data(
                    metric_name=metric_name,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=1000,
                    offset=0
                )

                # Format data for response
                formatted_data = []
                for point in data:
                    formatted_data.append({
                        "timestamp": point["timestamp"],
                        "value": point["value"]
                    })

            metrics_data[metric_name] = {
                "latest": latest["value"] if latest else None,
                "timestamp": latest["timestamp"] if latest else None,
                "statistics": stats,
                "data": formatted_data
            }

        return {
            "period": period,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "metrics": metrics_data
        }
    except Exception as e:
        logger.error(f"Error getting job overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting job overview: {str(e)}")

@router.get("/data/vm_status_distribution")
async def get_vm_status_distribution(
    period: Optional[str] = "hourly",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_active_user)
):
    """
    Get VM status distribution data.

    Args:
        period: The aggregation period (raw, hourly, daily, weekly, monthly)
        start_time: The start time of the range (defaults to 24 hours ago)
        end_time: The end time of the range (defaults to now)
        limit: The maximum number of data points to return
        offset: The offset for pagination
    """
    try:
        # Set default time range if not provided
        if end_time is None:
            end_time = datetime.now()

        if start_time is None:
            # Default to different time ranges based on period
            if period == "monthly":
                start_time = end_time - timedelta(days=365)
            elif period == "weekly":
                start_time = end_time - timedelta(days=90)
            elif period == "daily":
                start_time = end_time - timedelta(days=30)
            elif period == "hourly":
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(days=1)

        # Get owner ID for RLS
        owner_id = current_user["id"] if current_user["role"] != "admin" else None

        # Get VM status counts from database
        with get_db_connection() as conn:
            if not conn:
                logger.error("Failed to get database connection for retrieving VM status distribution")
                raise HTTPException(status_code=500, detail="Database connection error")

            cursor = conn.cursor()

            # Get VM status counts over time
            if period in ["hourly", "daily", "weekly", "monthly"]:
                # For aggregated data, we need to use a different approach
                # We'll get the VM counts from the timeseries_aggregates table
                running_data = get_metric_aggregates(
                    metric_name="vm_running_count",
                    period_type=period,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=limit,
                    offset=offset
                )

                stopped_data = get_metric_aggregates(
                    metric_name="vm_stopped_count",
                    period_type=period,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=limit,
                    offset=offset
                )

                error_data = get_metric_aggregates(
                    metric_name="vm_error_count",
                    period_type=period,
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=limit,
                    offset=offset
                )

                # Combine the data
                result_data = []
                timestamps = set()

                # Collect all timestamps
                for data in running_data:
                    timestamps.add(data["period_start"].isoformat())
                for data in stopped_data:
                    timestamps.add(data["period_start"].isoformat())
                for data in error_data:
                    timestamps.add(data["period_start"].isoformat())

                # Sort timestamps
                sorted_timestamps = sorted(timestamps)

                # Create a map for quick lookup
                running_map = {data["period_start"].isoformat(): data["avg"] for data in running_data}
                stopped_map = {data["period_start"].isoformat(): data["avg"] for data in stopped_data}
                error_map = {data["period_start"].isoformat(): data["avg"] for data in error_data}

                # Create the combined data
                for timestamp in sorted_timestamps:
                    result_data.append({
                        "timestamp": timestamp,
                        "running": running_map.get(timestamp, 0),
                        "stopped": stopped_map.get(timestamp, 0),
                        "error": error_map.get(timestamp, 0)
                    })
            else:
                # For raw data, we'll get the VM counts from the timeseries_data table
                running_data = get_metric_data(
                    metric_name="vm_running_count",
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=limit,
                    offset=offset
                )

                stopped_data = get_metric_data(
                    metric_name="vm_stopped_count",
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=limit,
                    offset=offset
                )

                error_data = get_metric_data(
                    metric_name="vm_error_count",
                    start_time=start_time,
                    end_time=end_time,
                    entity_type="system",
                    entity_id="system",
                    owner_id=owner_id,
                    limit=limit,
                    offset=offset
                )

                # Combine the data
                result_data = []
                timestamps = set()

                # Collect all timestamps
                for data in running_data:
                    timestamps.add(data["timestamp"].isoformat())
                for data in stopped_data:
                    timestamps.add(data["timestamp"].isoformat())
                for data in error_data:
                    timestamps.add(data["timestamp"].isoformat())

                # Sort timestamps
                sorted_timestamps = sorted(timestamps)

                # Create a map for quick lookup
                running_map = {data["timestamp"].isoformat(): data["value"] for data in running_data}
                stopped_map = {data["timestamp"].isoformat(): data["value"] for data in stopped_data}
                error_map = {data["timestamp"].isoformat(): data["value"] for data in error_data}

                # Create the combined data
                for timestamp in sorted_timestamps:
                    result_data.append({
                        "timestamp": timestamp,
                        "running": running_map.get(timestamp, 0),
                        "stopped": stopped_map.get(timestamp, 0),
                        "error": error_map.get(timestamp, 0)
                    })

            cursor.close()

            return {
                "metric": "vm_status_distribution",
                "period": period,
                "start_time": start_time,
                "end_time": end_time,
                "data": result_data,
                "count": len(result_data)
            }
    except Exception as e:
        logger.error(f"Error getting VM status distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting VM status distribution: {str(e)}")

@router.post("/generate-sample-data")
async def generate_sample_data(
    days: int = 7,
    current_user = Depends(get_current_active_user)
):
    """
    Generate sample timeseries data for testing.

    Args:
        days: Number of days of data to generate
    """
    try:
        # Only allow admins to generate sample data
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can generate sample data")

        logger.info(f"Generating sample data for {days} days")

        # Generate data for each day
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        logger.info(f"Generating sample data from {start_time} to {end_time}")

        # Generate hourly data points
        current_time = start_time
        metrics_batch = []

        # System metrics
        system_metrics = {
            "cpu_usage": (10, 90),  # min, max values
            "memory_usage": (20, 80),
            "disk_usage": (30, 70),
            "vm_count": (5, 15),
            "vm_running_count": (3, 10),
            "vm_stopped_count": (1, 5),
            "vm_error_count": (0, 2),
            "account_count": (10, 20),
            "account_active_count": (8, 18),
            "account_locked_count": (0, 3),
            "job_count": (5, 15),
            "job_active_count": (2, 8),
            "job_completed_count": (10, 30),
            "job_failed_count": (0, 5),
            "job_execution_time": (30, 300)
        }

        # Generate data for each hour
        while current_time < end_time:
            for metric_name, (min_val, max_val) in system_metrics.items():
                # Generate random value
                import random
                value = random.uniform(min_val, max_val)

                # Add to batch
                metrics_batch.append({
                    "metric_name": metric_name,
                    "value": value,
                    "entity_type": "system",
                    "entity_id": "system",
                    "owner_id": current_user["id"],  # Use current user as owner
                    "timestamp": current_time
                })

            # Move to next hour
            current_time += timedelta(hours=1)

            # Store batch if it's large enough
            if len(metrics_batch) >= 100:
                success_count, failure_count = store_metrics_batch(
                    metrics=metrics_batch,
                    user_id=current_user["id"],
                    user_role=current_user["role"]
                )
                logger.info(f"Stored {success_count} metrics, {failure_count} failures")
                metrics_batch = []

        # Store any remaining metrics
        if metrics_batch:
            success_count, failure_count = store_metrics_batch(
                metrics=metrics_batch,
                user_id=current_user["id"],
                user_role=current_user["role"]
            )
            logger.info(f"Stored {success_count} metrics, {failure_count} failures")

        return {
            "status": "success",
            "message": f"Generated sample data for {days} days",
            "start_time": start_time,
            "end_time": end_time
        }
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating sample data: {str(e)}")

@router.post("/collect-metrics")
async def collect_metrics(
    current_user = Depends(get_current_active_user)
):
    """
    Manually trigger metrics collection.
    """
    try:
        # Only allow admins to trigger collection
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can trigger metrics collection")

        logger.info(f"Manually triggering metrics collection for user {current_user['username']} (id={current_user['id']})")

        # Import the collector functions
        from timeseries.collector import collect_system_metrics, collect_vm_metrics, collect_account_metrics
        from timeseries.storage import store_metrics_batch
        from timeseries.vm_status import collect_vm_status_distribution

        all_metrics = []

        # Collect system metrics
        logger.info("Collecting system metrics...")
        system_metrics = collect_system_metrics()

        # Add owner_id to system metrics
        for metric in system_metrics:
            metric['owner_id'] = current_user['id']

        all_metrics.extend(system_metrics)

        # Collect VM metrics
        logger.info("Collecting VM metrics...")
        vm_metrics = collect_vm_metrics()

        # Add owner_id to VM metrics if not present
        for metric in vm_metrics:
            if 'owner_id' not in metric:
                metric['owner_id'] = current_user['id']

        all_metrics.extend(vm_metrics)

        # Collect VM status distribution
        logger.info("Collecting VM status distribution...")
        vm_status_metrics = collect_vm_status_distribution()
        all_metrics.extend(vm_status_metrics)

        # Collect account metrics
        logger.info("Collecting account metrics...")
        account_metrics = collect_account_metrics()

        # Add owner_id to account metrics
        for metric in account_metrics:
            metric['owner_id'] = current_user['id']

        all_metrics.extend(account_metrics)

        # Store metrics
        logger.info(f"Storing {len(all_metrics)} metrics...")
        success_count, failure_count = store_metrics_batch(
            metrics=all_metrics,
            user_id=current_user['id'],
            user_role=current_user['role']
        )

        logger.info(f"Stored {success_count} metrics, {failure_count} failures")

        return {
            "status": "success",
            "message": f"Metrics collection triggered successfully. Stored {success_count} metrics, {failure_count} failures",
            "metrics_count": len(all_metrics),
            "success_count": success_count,
            "failure_count": failure_count
        }
    except Exception as e:
        logger.error(f"Error triggering metrics collection: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering metrics collection: {str(e)}")

"""
Monitoring router for the AccountDB API.

This module provides endpoints for monitoring database performance and health.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import JSONResponse

from routers.auth import get_current_active_user, get_current_admin_user
from db.monitoring import get_monitoring_data, get_alerts, get_monitoring_report
from db.health_checks import get_health_check_data, get_health_check_report
from db.query_analyzer import get_query_stats, get_recent_slow_queries, get_slow_query_report
from db.query_cache import get_cache_stats, get_cache_report

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

@router.get("/health")
async def health_check():
    """
    Check the health of the database.

    This endpoint is public and does not require authentication.
    It returns a simple health check status.
    """
    health_data = get_health_check_data()

    # Return a 503 status code if the database is not healthy
    if not health_data.get("healthy", True):
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Database is not healthy"}
        )

    return {"status": "healthy", "message": "Database is healthy"}

@router.get("/health/details")
async def health_check_details(current_user = Depends(get_current_admin_user)):
    """
    Get detailed health check information.

    This endpoint requires admin authentication.
    """
    health_data = get_health_check_data()
    return health_data

@router.get("/health/report")
async def health_check_report(current_user = Depends(get_current_admin_user)):
    """
    Get a health check report.

    This endpoint requires admin authentication.
    """
    report = get_health_check_report()
    return {"report": report}

@router.get("/database")
async def database_monitoring(current_user = Depends(get_current_admin_user)):
    """
    Get database monitoring data.

    This endpoint requires admin authentication.
    """
    monitoring_data = get_monitoring_data()
    return monitoring_data

@router.get("/database/report")
async def database_monitoring_report(current_user = Depends(get_current_admin_user)):
    """
    Get a database monitoring report.

    This endpoint requires admin authentication.
    """
    report = get_monitoring_report()
    return {"report": report}

@router.get("/alerts")
async def get_monitoring_alerts(
    level: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_admin_user)
):
    """
    Get monitoring alerts.

    This endpoint requires admin authentication.

    Args:
        level (Optional[str], optional): Alert level. Defaults to None.
        component (Optional[str], optional): Alert component. Defaults to None.
        limit (int, optional): Maximum number of alerts to return. Defaults to 100.
    """
    alerts = get_alerts(level, component, limit)
    return {"alerts": alerts}

@router.get("/queries")
async def query_stats(current_user = Depends(get_current_admin_user)):
    """
    Get query statistics.

    This endpoint requires admin authentication.
    """
    stats = get_query_stats()
    return stats

@router.get("/queries/slow")
async def slow_queries(current_user = Depends(get_current_admin_user)):
    """
    Get slow queries.

    This endpoint requires admin authentication.
    """
    queries = get_recent_slow_queries()
    return {"queries": queries}

@router.get("/queries/report")
async def query_report(current_user = Depends(get_current_admin_user)):
    """
    Get a query performance report.

    This endpoint requires admin authentication.
    """
    report = get_slow_query_report()
    return {"report": report}

@router.get("/cache")
async def cache_stats(current_user = Depends(get_current_admin_user)):
    """
    Get cache statistics.

    This endpoint requires admin authentication.
    """
    stats = get_cache_stats()
    return stats

@router.get("/cache/report")
async def cache_report(current_user = Depends(get_current_admin_user)):
    """
    Get a cache report.

    This endpoint requires admin authentication.
    """
    report = get_cache_report()
    return {"report": report}

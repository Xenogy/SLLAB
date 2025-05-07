"""
Logs API router.

This module provides endpoints for log management, including storing and retrieving logs.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta

from db.repositories.logs import LogRepository
from routers.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)

# Models
class LogLevel(BaseModel):
    """Model for log level."""
    id: int
    name: str
    severity: int
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LogCategory(BaseModel):
    """Model for log category."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LogSource(BaseModel):
    """Model for log source."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LogRetentionPolicy(BaseModel):
    """Model for log retention policy."""
    id: int
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    level_id: Optional[int] = None
    level_name: Optional[str] = None
    retention_days: int
    created_at: datetime
    updated_at: datetime

class LogEntry(BaseModel):
    """Model for log entry."""
    id: int
    timestamp: datetime
    category: Optional[str] = None
    source: Optional[str] = None
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[int] = None
    owner_id: Optional[int] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    created_at: datetime

class LogEntryCreate(BaseModel):
    """Model for creating a log entry."""
    message: str = Field(..., description="The log message")
    level: str = Field("INFO", description="The log level")
    category: Optional[str] = Field(None, description="The log category")
    source: Optional[str] = Field(None, description="The log source")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    entity_type: Optional[str] = Field(None, description="The entity type")
    entity_id: Optional[str] = Field(None, description="The entity ID")
    user_id: Optional[int] = Field(None, description="The user ID")
    owner_id: Optional[int] = Field(None, description="The owner ID")
    trace_id: Optional[str] = Field(None, description="The trace ID")
    span_id: Optional[str] = Field(None, description="The span ID")
    parent_span_id: Optional[str] = Field(None, description="The parent span ID")
    timestamp: Optional[datetime] = Field(None, description="The timestamp")

class LogsResponse(BaseModel):
    """Model for logs response."""
    logs: List[LogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int

class LogStatistic(BaseModel):
    """Model for log statistic."""
    time_period: datetime
    level: str
    count: int
    severity: Optional[int] = None

# Endpoints
@router.post("/", response_model=None)
async def create_log(
    log_data: LogEntryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new log entry.

    This endpoint allows creating a new log entry with the specified details.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Set user_id to current user if not provided
        if log_data.user_id is None:
            log_data.user_id = current_user["id"]

        # Set owner_id to current user if not provided
        if log_data.owner_id is None:
            log_data.owner_id = current_user["id"]

        # Add log entry
        log = log_repo.add_log(
            message=log_data.message,
            level=log_data.level,
            category=log_data.category,
            source=log_data.source,
            details=log_data.details,
            entity_type=log_data.entity_type,
            entity_id=log_data.entity_id,
            user_id=log_data.user_id,
            owner_id=log_data.owner_id,
            trace_id=log_data.trace_id,
            span_id=log_data.span_id,
            parent_span_id=log_data.parent_span_id,
            timestamp=log_data.timestamp
        )

        if not log:
            raise HTTPException(status_code=500, detail="Failed to create log entry")

        # If log is a dictionary with log_id, return just the log_id
        if isinstance(log, dict) and 'log_id' in log:
            return {"log_id": log['log_id']}

        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating log entry: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating log entry: {str(e)}")

@router.get("/", response_model=LogsResponse)
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    start_time: Optional[datetime] = Query(None, description="Filter logs after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter logs before this time"),
    levels: Optional[List[str]] = Query(None, description="Filter by log levels"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    sources: Optional[List[str]] = Query(None, description="Filter by sources"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    search: Optional[str] = Query(None, description="Search in message text"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get logs with filtering and pagination.

    This endpoint allows retrieving logs with various filters and pagination.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Calculate offset
        offset = (page - 1) * page_size

        # Get logs
        logs, total = log_repo.get_logs(
            limit=page_size,
            offset=offset,
            start_time=start_time,
            end_time=end_time,
            levels=levels,
            categories=categories,
            sources=sources,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            trace_id=trace_id,
            search_query=search
        )

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size

        return {
            "logs": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@router.get("/categories/", response_model=List[LogCategory])
async def get_log_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all log categories.

    This endpoint allows retrieving all available log categories.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get categories
        categories = log_repo.get_log_categories()

        return categories
    except Exception as e:
        logger.error(f"Error getting log categories: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting log categories: {str(e)}")

@router.get("/sources/", response_model=List[LogSource])
async def get_log_sources(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all log sources.

    This endpoint allows retrieving all available log sources.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get sources
        sources = log_repo.get_log_sources()

        return sources
    except Exception as e:
        logger.error(f"Error getting log sources: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting log sources: {str(e)}")

@router.get("/levels/", response_model=List[LogLevel])
async def get_log_levels(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all log levels.

    This endpoint allows retrieving all available log levels.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get levels
        levels = log_repo.get_log_levels()

        return levels
    except Exception as e:
        logger.error(f"Error getting log levels: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting log levels: {str(e)}")

@router.get("/retention-policies/", response_model=List[LogRetentionPolicy])
async def get_retention_policies(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all log retention policies.

    This endpoint allows retrieving all available log retention policies.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get retention policies
        policies = log_repo.get_retention_policies()

        return policies
    except Exception as e:
        logger.error(f"Error getting retention policies: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting retention policies: {str(e)}")

@router.get("/statistics/", response_model=List[LogStatistic])
async def get_log_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to include"),
    group_by: str = Query("day", description="Grouping interval ('hour', 'day', 'week', 'month')"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get log statistics for the specified time period.

    This endpoint allows retrieving log statistics grouped by time period and log level.
    """
    try:
        # Validate group_by parameter
        valid_group_by = ["hour", "day", "week", "month"]
        if group_by not in valid_group_by:
            raise HTTPException(status_code=400, detail=f"Invalid group_by parameter. Must be one of: {', '.join(valid_group_by)}")

        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get statistics
        statistics = log_repo.get_log_statistics(days=days, group_by=group_by)

        return statistics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting log statistics: {str(e)}")

@router.get("/{log_id}", response_model=LogEntry)
async def get_log(
    log_id: int = Path(..., description="The ID of the log to retrieve"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a log entry by ID.

    This endpoint allows retrieving a specific log entry by its ID.
    """
    try:
        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get log
        log = log_repo.get_log_by_id(log_id)

        if not log:
            raise HTTPException(status_code=404, detail="Log entry not found")

        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting log: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting log: {str(e)}")

@router.post("/cleanup/", response_model=Dict[str, Any])
async def cleanup_logs(
    dry_run: bool = Query(False, description="If True, only show what would be deleted without actually deleting"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Clean up old logs based on retention policies.

    This endpoint allows cleaning up old logs based on the configured retention policies.
    Only administrators can trigger this operation.

    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    try:
        # Check if user is admin
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can clean up logs")

        # Create log repository
        log_repo = LogRepository(user_id=current_user["id"], user_role=current_user["role"])

        if dry_run:
            # Get count of logs that would be deleted
            count_by_level = log_repo.get_logs_to_delete_count()
            total_count = sum(count["count"] for count in count_by_level)

            return {
                "dry_run": True,
                "would_delete_count": total_count,
                "counts_by_level": count_by_level
            }
        else:
            # Clean up logs
            deleted_count = log_repo.cleanup_old_logs()

            return {
                "dry_run": False,
                "deleted_count": deleted_count
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up logs: {str(e)}")

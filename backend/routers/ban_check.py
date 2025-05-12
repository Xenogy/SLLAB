"""
Steam Ban Check API router.

This module provides endpoints for checking Steam profiles for bans, with proxy and retry support.
It is based on the BanCheck API and adapted to work within the AccountDB system.
"""

import logging
import uuid
import json
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

from db.repositories.ban_check import BanCheckRepository
from routers.auth import get_current_user
from utils.proxy_utils import validate_proxy_string
from utils.ban_check_utils import (
    generate_urls_from_steamids,
    generate_urls_from_csv_content,
    run_checks_background_task
)

# In-memory storage for public tasks (not stored in database)
public_tasks: Dict[str, Dict[str, Any]] = {}

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ban-check",
    tags=["ban-check"],
    responses={404: {"description": "Not found"}},
)

# Models
class TaskStatus(BaseModel):
    """Model for task status."""
    task_id: str
    status: str  # "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    message: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    results: Optional[List[Dict[str, Any]]] = None
    proxy_stats: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None

class TaskListResponse(BaseModel):
    """Response model for listing tasks."""
    tasks: List[TaskStatus]
    total: int
    limit: int
    offset: int

# In-memory store for task statuses and results (temporary until DB implementation)
tasks_db: Dict[str, Dict[str, Any]] = {}

# Endpoints
@router.post("/check/steamids", response_model=TaskStatus, status_code=202)
async def check_steamids_endpoint(
    background_tasks: BackgroundTasks,
    steam_ids: List[str] = Form(..., description="List of SteamIDs to check"),
    proxy_file: Optional[UploadFile] = File(None, description="File containing proxy list, one per line"),
    proxy_list_str: Optional[str] = Form(None, description="Multiline string of proxies, one per line"),
    logical_batch_size: int = Form(20, ge=1, description="URLs per processing unit/task"),
    max_concurrent_batches: int = Form(3, ge=1, description="How many batch tasks run in parallel"),
    max_workers_per_batch: int = Form(3, ge=1, description="Threads for URLs within one batch"),
    inter_request_submit_delay: float = Form(0.1, ge=0, description="Delay (s) submitting requests"),
    max_retries_per_url: int = Form(2, ge=0, description="Retries per URL on failure"),
    retry_delay_seconds: float = Form(5.0, ge=0, description="Delay (s) between retries"),
    current_user: dict = Depends(get_current_user)
):
    """
    Check a list of Steam IDs for bans.

    This endpoint accepts a list of Steam IDs and checks them for bans using the Steam profile pages.
    It supports proxy usage and various concurrency and retry parameters.
    """
    try:
        # Create a unique task ID
        task_id = str(uuid.uuid4())

        # Initialize task in database
        ban_check_repo = BanCheckRepository(user_id=current_user["id"], user_role=current_user["role"])
        task = ban_check_repo.create_task(
            task_id=task_id,
            status="PENDING",
            message="Task received, processing Steam IDs",
            progress=0,
            owner_id=current_user["id"]
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create task")

        # Process proxies
        proxies_list = []

        # Process proxy file if provided
        if proxy_file:
            content = await proxy_file.read()
            proxy_lines = content.decode("utf-8").splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Process proxy list string if provided
        if proxy_list_str:
            proxy_lines = proxy_list_str.splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Generate URLs from Steam IDs
        generated_urls = generate_urls_from_steamids(steam_ids)

        # Prepare parameters
        params = {
            "logical_batch_size": logical_batch_size,
            "max_concurrent_batches": max_concurrent_batches,
            "max_workers_per_batch": max_workers_per_batch,
            "inter_request_submit_delay": inter_request_submit_delay,
            "max_retries_per_url": max_retries_per_url,
            "retry_delay_seconds": retry_delay_seconds
        }

        # Start background task
        background_tasks.add_task(
            run_checks_background_task,
            task_id=task_id,
            generated_urls=generated_urls,
            proxies_list=proxies_list,
            params=params,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )

        return task

    except Exception as e:
        logger.error(f"Error processing Steam IDs: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing Steam IDs: {str(e)}")

@router.post("/check/csv", response_model=TaskStatus, status_code=202)
async def check_csv_endpoint(
    background_tasks: BackgroundTasks,
    csv_file: UploadFile = File(..., description="CSV file containing Steam IDs"),
    steam_id_column: str = Form("steam64_id", description="Column name containing Steam IDs"),
    proxy_file: Optional[UploadFile] = File(None, description="File containing proxy list, one per line"),
    proxy_list_str: Optional[str] = Form(None, description="Multiline string of proxies, one per line"),
    logical_batch_size: int = Form(20, ge=1, description="URLs per processing unit/task"),
    max_concurrent_batches: int = Form(3, ge=1, description="How many batch tasks run in parallel"),
    max_workers_per_batch: int = Form(3, ge=1, description="Threads for URLs within one batch"),
    inter_request_submit_delay: float = Form(0.1, ge=0, description="Delay (s) submitting requests"),
    max_retries_per_url: int = Form(2, ge=0, description="Retries per URL on failure"),
    retry_delay_seconds: float = Form(5.0, ge=0, description="Delay (s) between retries"),
    current_user: dict = Depends(get_current_user)
):
    """
    Check Steam IDs from a CSV file for bans.

    This endpoint accepts a CSV file containing Steam IDs and checks them for bans.
    It supports proxy usage and various concurrency and retry parameters.
    """
    try:
        # Create a unique task ID
        task_id = str(uuid.uuid4())

        # Initialize task in database
        ban_check_repo = BanCheckRepository(user_id=current_user["id"], user_role=current_user["role"])
        task = ban_check_repo.create_task(
            task_id=task_id,
            status="PENDING",
            message="Task received, processing CSV file",
            progress=0,
            owner_id=current_user["id"]
        )

        if not task:
            raise HTTPException(status_code=500, detail="Failed to create task")

        # Process proxies
        proxies_list = []

        # Process proxy file if provided
        if proxy_file:
            content = await proxy_file.read()
            proxy_lines = content.decode("utf-8").splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Process proxy list string if provided
        if proxy_list_str:
            proxy_lines = proxy_list_str.splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Read CSV file
        csv_content = await csv_file.read()

        # Generate URLs from CSV content
        generated_urls = generate_urls_from_csv_content(csv_content.decode("utf-8"), steam_id_column)

        # Prepare parameters
        params = {
            "logical_batch_size": logical_batch_size,
            "max_concurrent_batches": max_concurrent_batches,
            "max_workers_per_batch": max_workers_per_batch,
            "inter_request_submit_delay": inter_request_submit_delay,
            "max_retries_per_url": max_retries_per_url,
            "retry_delay_seconds": retry_delay_seconds
        }

        # Start background task
        background_tasks.add_task(
            run_checks_background_task,
            task_id=task_id,
            generated_urls=generated_urls,
            proxies_list=proxies_list,
            params=params,
            user_id=current_user["id"],
            user_role=current_user["role"]
        )

        return task

    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of ban check tasks with pagination and filtering.

    This endpoint returns a list of ban check tasks with pagination and filtering options.
    """
    try:
        # Get tasks from database
        ban_check_repo = BanCheckRepository(user_id=current_user["id"], user_role=current_user["role"])
        result = ban_check_repo.get_tasks(limit, offset, status)

        # Ensure the tasks array is valid for the response model
        # If there are no tasks, return an empty list instead of any other structure
        if not result.get("tasks") or not isinstance(result["tasks"], list):
            result["tasks"] = []

        # Check if there's a count object instead of a proper task (happens when no tasks exist)
        if result["tasks"] and any(isinstance(task, dict) and "count" in task for task in result["tasks"]):
            # Replace with an empty list to avoid validation errors
            result["tasks"] = []

        return result

    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        # Return a valid empty response instead of raising an exception
        return {
            "tasks": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }

@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific ban check task by ID.

    This endpoint returns a specific ban check task by its ID.
    """
    try:
        # Get task from database
        ban_check_repo = BanCheckRepository(user_id=current_user["id"], user_role=current_user["role"])
        task = ban_check_repo.get_task_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")

# Public endpoints (no authentication required)
@router.post("/public/check/steamids", response_model=TaskStatus, status_code=202)
async def check_steamids_public_endpoint(
    background_tasks: BackgroundTasks,
    steam_ids: List[str] = Form(..., description="List of SteamIDs to check"),
    proxy_file: Optional[UploadFile] = File(None, description="File containing proxy list, one per line"),
    proxy_list_str: Optional[str] = Form(None, description="Multiline string of proxies, one per line"),
    logical_batch_size: int = Form(20, ge=1, description="URLs per processing unit/task"),
    max_concurrent_batches: int = Form(3, ge=1, description="How many batch tasks run in parallel"),
    max_workers_per_batch: int = Form(3, ge=1, description="Threads for URLs within one batch"),
    inter_request_submit_delay: float = Form(0.1, ge=0, description="Delay (s) submitting requests"),
    max_retries_per_url: int = Form(2, ge=0, description="Retries per URL on failure"),
    retry_delay_seconds: float = Form(5.0, ge=0, description="Delay (s) between retries")
):
    """
    Check a list of Steam IDs for bans (public endpoint, no authentication required).

    This endpoint accepts a list of Steam IDs and checks them for bans using the Steam profile pages.
    It supports proxy usage and various concurrency and retry parameters.
    Results are stored in memory only and not persisted to the database.
    """
    try:
        # Create a unique task ID
        task_id = str(uuid.uuid4())

        # Initialize task in memory (not in database)
        task = {
            "task_id": task_id,
            "status": "PENDING",
            "message": "Task received, processing Steam IDs",
            "progress": 0,
            "results": None,
            "proxy_stats": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "owner_id": None  # No owner for public tasks
        }

        # Store task in memory
        public_tasks[task_id] = task

        # Process proxies
        proxies_list = []

        # Process proxy file if provided
        if proxy_file:
            content = await proxy_file.read()
            proxy_lines = content.decode("utf-8").splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Process proxy list string if provided
        if proxy_list_str:
            proxy_lines = proxy_list_str.splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Generate URLs from Steam IDs
        generated_urls = generate_urls_from_steamids(steam_ids)

        # Prepare parameters
        params = {
            "logical_batch_size": logical_batch_size,
            "max_concurrent_batches": max_concurrent_batches,
            "max_workers_per_batch": max_workers_per_batch,
            "inter_request_submit_delay": inter_request_submit_delay,
            "max_retries_per_url": max_retries_per_url,
            "retry_delay_seconds": retry_delay_seconds
        }

        # Start background task with no user context
        background_tasks.add_task(
            run_checks_background_task,
            task_id=task_id,
            generated_urls=generated_urls,
            proxies_list=proxies_list,
            params=params,
            user_id=None,  # No user ID for public tasks
            user_role=None,  # No user role for public tasks
            is_public=True,  # Mark as public task
            public_tasks_dict=public_tasks  # Pass the public tasks dictionary
        )

        return task

    except Exception as e:
        logger.error(f"Error processing public Steam IDs: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing Steam IDs: {str(e)}")

@router.post("/public/check/csv", response_model=TaskStatus, status_code=202)
async def check_csv_public_endpoint(
    background_tasks: BackgroundTasks,
    csv_file: UploadFile = File(..., description="CSV file containing Steam IDs"),
    steam_id_column: str = Form("steam64_id", description="Column name containing Steam IDs"),
    proxy_file: Optional[UploadFile] = File(None, description="File containing proxy list, one per line"),
    proxy_list_str: Optional[str] = Form(None, description="Multiline string of proxies, one per line"),
    logical_batch_size: int = Form(20, ge=1, description="URLs per processing unit/task"),
    max_concurrent_batches: int = Form(3, ge=1, description="How many batch tasks run in parallel"),
    max_workers_per_batch: int = Form(3, ge=1, description="Threads for URLs within one batch"),
    inter_request_submit_delay: float = Form(0.1, ge=0, description="Delay (s) submitting requests"),
    max_retries_per_url: int = Form(2, ge=0, description="Retries per URL on failure"),
    retry_delay_seconds: float = Form(5.0, ge=0, description="Delay (s) between retries")
):
    """
    Check Steam IDs from a CSV file for bans (public endpoint, no authentication required).

    This endpoint accepts a CSV file containing Steam IDs and checks them for bans.
    It supports proxy usage and various concurrency and retry parameters.
    Results are stored in memory only and not persisted to the database.
    """
    try:
        # Create a unique task ID
        task_id = str(uuid.uuid4())

        # Initialize task in memory (not in database)
        task = {
            "task_id": task_id,
            "status": "PENDING",
            "message": "Task received, processing CSV file",
            "progress": 0,
            "results": None,
            "proxy_stats": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "owner_id": None  # No owner for public tasks
        }

        # Store task in memory
        public_tasks[task_id] = task

        # Process proxies
        proxies_list = []

        # Process proxy file if provided
        if proxy_file:
            content = await proxy_file.read()
            proxy_lines = content.decode("utf-8").splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Process proxy list string if provided
        if proxy_list_str:
            proxy_lines = proxy_list_str.splitlines()
            for line in proxy_lines:
                proxy = validate_proxy_string(line.strip())
                if proxy:
                    proxies_list.append(proxy)

        # Read CSV file
        csv_content = await csv_file.read()

        # Generate URLs from CSV content
        generated_urls = generate_urls_from_csv_content(csv_content.decode("utf-8"), steam_id_column)

        # Prepare parameters
        params = {
            "logical_batch_size": logical_batch_size,
            "max_concurrent_batches": max_concurrent_batches,
            "max_workers_per_batch": max_workers_per_batch,
            "inter_request_submit_delay": inter_request_submit_delay,
            "max_retries_per_url": max_retries_per_url,
            "retry_delay_seconds": retry_delay_seconds
        }

        # Start background task with no user context
        background_tasks.add_task(
            run_checks_background_task,
            task_id=task_id,
            generated_urls=generated_urls,
            proxies_list=proxies_list,
            params=params,
            user_id=None,  # No user ID for public tasks
            user_role=None,  # No user role for public tasks
            is_public=True,  # Mark as public task
            public_tasks_dict=public_tasks  # Pass the public tasks dictionary
        )

        return task

    except Exception as e:
        logger.error(f"Error processing public CSV file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV file: {str(e)}")

@router.get("/public/tasks/{task_id}", response_model=TaskStatus)
async def get_public_task(
    task_id: str
):
    """
    Get a specific public ban check task by ID.

    This endpoint returns a specific public ban check task by its ID.
    """
    try:
        # Get task from in-memory storage
        task = public_tasks.get(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Public task not found")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving public task: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving public task: {str(e)}")

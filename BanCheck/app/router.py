from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional, Union
import uuid
import math

from app.models import CheckSteamIDsRequest, TaskStatus, CheckRequestBase
from app.tasks import run_checks_background_task, tasks_db
from app.utils import (
    generate_urls_from_steamids,
    generate_urls_from_csv_content,
    load_proxies_from_str,
    load_proxies_from_file,
    load_default_proxies,
    ScriptConfig
)

router = APIRouter()
cfg = ScriptConfig() # For default values

async def handle_proxy_file(proxy_file: Optional[Union[UploadFile, str]], task_id: str) -> List[str]:
    """
    Handle the proxy_file parameter, which can be an UploadFile, None, or a string.

    Args:
        proxy_file: The proxy_file parameter from the request
        task_id: The task ID for logging purposes

    Returns:
        A list of proxy strings
    """
    # If proxy_file is None or an empty string, return an empty list
    if proxy_file is None or (isinstance(proxy_file, str) and not proxy_file):
        return []

    # If proxy_file is a non-empty string, it's likely an error from the client
    if isinstance(proxy_file, str):
        print(f"[API Task {task_id}] Warning: proxy_file parameter received as string: '{proxy_file}'. Expected UploadFile. Ignoring.")
        return []

    # If proxy_file is an UploadFile, read it and load the proxies
    try:
        proxy_file_content = await proxy_file.read()
        proxies = await load_proxies_from_file(proxy_file_content)
        return proxies
    except Exception as e:
        print(f"[API Task {task_id}] Error reading proxy file: {e}")
        return []
    finally:
        await proxy_file.close()

@router.post("/check/steamids", response_model=TaskStatus, status_code=202)
async def check_steamids_endpoint(
    background_tasks: BackgroundTasks,
    steam_ids: List[str] = Form(..., description="List of SteamIDs to check"),
    proxy_file: Optional[Union[UploadFile, str]] = File(None, description="File containing proxy list, one per line"),
    proxy_list_str: Optional[str] = Form(None, description="Multiline string of proxies, one per line")
):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "PENDING", "results": None, "progress": 0, "message": "Task received."}

    # Generate URLs from SteamIDs
    generated_urls, problems = generate_urls_from_steamids(steam_ids)
    if problems:
        # Log problems but continue with valid URLs
        print(f"[API Task {task_id}] Problems generating URLs from SteamIDs: {problems}")

    # Load proxies with priority: 1) proxy_file, 2) proxy_list_str, 3) default proxies
    proxies = []

    # Try to load proxies from file first
    if proxy_file:
        proxies = await handle_proxy_file(proxy_file, task_id)
        if proxies:
            print(f"[API Task {task_id}] Using {len(proxies)} proxies from uploaded file")

    # If no proxies from file, try proxy_list_str
    if not proxies and proxy_list_str:
        proxies = load_proxies_from_str(proxy_list_str)
        if proxies:
            print(f"[API Task {task_id}] Using {len(proxies)} proxies from provided string")

    # If still no proxies, use default proxies
    if not proxies:
        proxies = load_default_proxies()
        print(f"[API Task {task_id}] Using {len(proxies)} default proxies from test_data/proxies.txt")

    # Get optimized parameters based on account list size
    params = ScriptConfig.get_optimized_params(len(generated_urls))

    # Log the optimized parameters
    print(f"[API Task {task_id}] Using optimized parameters for {len(generated_urls)} accounts: {params}")

    background_tasks.add_task(
        run_checks_background_task,
        task_id,
        generated_urls,
        proxies,
        params
    )
    return TaskStatus(task_id=task_id, status="PENDING", message="Task accepted and processing in background.")


@router.post("/check/csv", response_model=TaskStatus, status_code=202)
async def check_csv_endpoint(
    background_tasks: BackgroundTasks,
    csv_file: UploadFile = File(...),
    steam_id_column: Optional[str] = Form("steam64_id"),
    proxy_file: Optional[Union[UploadFile, str]] = File(None, description="File containing proxy list, one per line"),
    proxy_list_str: Optional[str] = Form(None)
):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "PENDING", "results": None, "progress": 0, "message": "Task received from CSV."}

    try:
        csv_content_bytes = await csv_file.read()
        csv_content_str = csv_content_bytes.decode('utf-8-sig') # Handle BOM
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded CSV file: {e}")
    finally:
        await csv_file.close()

    generated_urls, problems = generate_urls_from_csv_content(csv_content_str, steam_id_column)
    if problems and not generated_urls : # If only problems and no URLs, fail early
         tasks_db[task_id] = {"status": "FAILED", "message": f"CSV processing failed: {problems}", "results": None, "progress": 100}
         # Not raising HTTPException here as task is "created" but then immediately fails. Client can check status.
         return TaskStatus(task_id=task_id, status="FAILED", message=f"CSV processing errors: {problems}")

    if problems:
        print(f"[API Task {task_id}] Problems generating URLs from CSV: {problems}")

    # Load proxies with priority: 1) proxy_file, 2) proxy_list_str, 3) default proxies
    proxies = []

    # Try to load proxies from file first
    if proxy_file:
        proxies = await handle_proxy_file(proxy_file, task_id)
        if proxies:
            print(f"[API Task {task_id}] Using {len(proxies)} proxies from uploaded file")

    # If no proxies from file, try proxy_list_str
    if not proxies and proxy_list_str:
        proxies = load_proxies_from_str(proxy_list_str)
        if proxies:
            print(f"[API Task {task_id}] Using {len(proxies)} proxies from provided string")

    # If still no proxies, use default proxies
    if not proxies:
        proxies = load_default_proxies()
        print(f"[API Task {task_id}] Using {len(proxies)} default proxies from test_data/proxies.txt")

    # Get optimized parameters based on account list size
    params = ScriptConfig.get_optimized_params(len(generated_urls))

    # Log the optimized parameters
    print(f"[API Task {task_id}] Using optimized parameters for {len(generated_urls)} accounts: {params}")

    background_tasks.add_task(
        run_checks_background_task,
        task_id,
        generated_urls,
        proxies,
        params
    )
    return TaskStatus(task_id=task_id, status="PENDING", message="CSV task accepted and processing in background.")

@router.get("/check/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    print(f"[API] Returning task status for {task_id}: {task}")
    return TaskStatus(task_id=task_id, **task)

@router.get("/debug/tasks")
async def debug_tasks():
    """Debug endpoint to view all tasks in the tasks_db"""
    return {"tasks": tasks_db}
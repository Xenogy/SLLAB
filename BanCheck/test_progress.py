"""
Test script to verify progress tracking in the BanCheck API.
"""

import time
import uuid
import requests
from typing import List, Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1/steam"
# Generate 50 test Steam IDs
TEST_STEAM_IDS = [f"7656119800000{i:04d}" for i in range(1, 51)]

def submit_check_task() -> str:
    """Submit a check task and return the task ID."""
    url = f"{API_BASE_URL}/check/steamids"
    data = {
        "steam_ids": TEST_STEAM_IDS,
    }

    response = requests.post(url, data={"steam_ids": TEST_STEAM_IDS})
    if response.status_code != 202:
        print(f"Error submitting task: {response.status_code} - {response.text}")
        return None

    task_data = response.json()
    task_id = task_data.get("task_id")
    print(f"Task submitted successfully. Task ID: {task_id}")
    return task_id

def check_task_progress(task_id: str) -> Dict[str, Any]:
    """Check the progress of a task."""
    url = f"{API_BASE_URL}/check/status/{task_id}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error checking task progress: {response.status_code} - {response.text}")
        return None

    task_data = response.json()
    print(f"Raw task data: {json.dumps(task_data, indent=2)}")
    return task_data

def monitor_task_progress(task_id: str, check_interval: float = 0.2, max_checks: int = 300) -> None:
    """Monitor the progress of a task until it completes or max_checks is reached."""
    checks = 0
    last_progress = -1

    print(f"Monitoring task {task_id}...")
    print(f"{'Time (s)':<10} {'Progress':<10} {'Status':<15} {'Message'}")
    print("-" * 60)

    start_time = time.time()

    while checks < max_checks:
        task_data = check_task_progress(task_id)
        if not task_data:
            print("Failed to get task data. Exiting.")
            return

        progress = task_data.get("progress", 0)
        status = task_data.get("status", "UNKNOWN")
        message = task_data.get("message", "")

        elapsed = time.time() - start_time

        # Print every time we check
        if True:
            print(f"{elapsed:<10.2f} {progress:<10.2f} {status:<15} {message}")
            last_progress = progress

        if status in ["COMPLETED", "FAILED"]:
            print(f"\nTask {status} after {elapsed:.2f} seconds.")
            if status == "COMPLETED":
                print(f"Results: {len(task_data.get('results', []))} items")
            break

        time.sleep(check_interval)
        checks += 1

    if checks >= max_checks:
        print(f"\nReached maximum number of checks ({max_checks}). Task may still be running.")

def main():
    """Main function to test progress tracking."""
    print("Starting BanCheck API progress test...")

    # Submit a task
    task_id = submit_check_task()
    if not task_id:
        print("Failed to submit task. Exiting.")
        return

    # Monitor the task progress
    monitor_task_progress(task_id)

    print("Test completed.")

if __name__ == "__main__":
    main()

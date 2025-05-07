"""
Simple test script to verify progress tracking in the BanCheck API.
"""

import time
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1/steam"
TEST_STEAM_IDS = [f"7656119800000{i:04d}" for i in range(1, 51)]

def main():
    """Main function to test progress tracking."""
    print("Starting BanCheck API simple test...")
    
    # Submit a task
    url = f"{API_BASE_URL}/check/steamids"
    response = requests.post(url, data={"steam_ids": TEST_STEAM_IDS})
    
    if response.status_code != 202:
        print(f"Error submitting task: {response.status_code} - {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data.get("task_id")
    print(f"Task submitted successfully. Task ID: {task_id}")
    
    # Monitor the task progress
    print(f"Monitoring task {task_id}...")
    print(f"{'Time (s)':<10} {'Progress':<10} {'Status':<15} {'Message'}")
    print("-" * 60)
    
    start_time = time.time()
    completed = False
    
    while not completed and time.time() - start_time < 60:
        # Check task progress
        status_url = f"{API_BASE_URL}/check/status/{task_id}"
        status_response = requests.get(status_url)
        
        if status_response.status_code != 200:
            print(f"Error checking task status: {status_response.status_code} - {status_response.text}")
            time.sleep(1)
            continue
        
        status_data = status_response.json()
        progress = status_data.get("progress", 0)
        status = status_data.get("status", "UNKNOWN")
        message = status_data.get("message", "")
        
        elapsed = time.time() - start_time
        print(f"{elapsed:<10.2f} {progress:<10.2f} {status:<15} {message}")
        
        if status in ["COMPLETED", "FAILED"]:
            print(f"\nTask {status} after {elapsed:.2f} seconds.")
            if status == "COMPLETED":
                print(f"Results: {len(status_data.get('results', []))} items")
            completed = True
        else:
            time.sleep(0.5)
    
    if not completed:
        print("\nTimeout waiting for task to complete.")
    
    print("Test completed.")

if __name__ == "__main__":
    main()

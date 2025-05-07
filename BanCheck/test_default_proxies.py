"""
Test script to verify that the test proxy list is being used as a default.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1/steam"
# Using real Steam IDs for better testing
TEST_STEAM_IDS = [
    "76561198037414410",  # Valid Steam ID example
    "76561197960287930",  # Valid Steam ID example
    "76561197960435530"   # Valid Steam ID example
]

def main():
    """Main function to test default proxy list."""
    print("Starting test to verify default proxy list...")

    # Submit a task without providing any proxies
    url = f"{API_BASE_URL}/check/steamids"
    print(f"Sending request to {url} with steam_ids: {TEST_STEAM_IDS}")
    response = requests.post(url, data={"steam_ids": TEST_STEAM_IDS})
    print(f"Response status code: {response.status_code}")

    if response.status_code != 202:
        print(f"Error submitting task: {response.status_code} - {response.text}")
        return

    task_data = response.json()
    task_id = task_data.get("task_id")
    print(f"Task submitted successfully. Task ID: {task_id}")

    # Wait for the task to complete
    print("Waiting for task to complete...")
    completed = False
    start_time = time.time()

    while not completed and time.time() - start_time < 30:
        # Check task status
        status_url = f"{API_BASE_URL}/check/status/{task_id}"
        status_response = requests.get(status_url)

        if status_response.status_code != 200:
            print(f"Error checking task status: {status_response.status_code} - {status_response.text}")
            time.sleep(1)
            continue

        status_data = status_response.json()
        status = status_data.get("status", "UNKNOWN")

        if status in ["COMPLETED", "FAILED"]:
            completed = True
            print(f"Task {status}.")

            # Check if proxy_stats is in the response
            if "proxy_stats" in status_data:
                print("\nProxy Statistics:")
                print(json.dumps(status_data["proxy_stats"], indent=2))

                # Check if the test proxies were used
                if status_data["proxy_stats"]["total_proxies"] > 0:
                    print("\nTest proxies were successfully used as default!")
                else:
                    print("\nNo proxies were used.")
            else:
                print("\nNo proxy statistics in the response.")

            # Print the results
            if "results" in status_data and status_data["results"]:
                print("\nResults:")
                for result in status_data["results"]:
                    print(f"Steam ID: {result['steam_id']}, Status: {result['status_summary']}, Proxy: {result['proxy_used']}")
        else:
            print(f"Task status: {status}, Progress: {status_data.get('progress', 0)}%")
            time.sleep(1)

    if not completed:
        print("Timeout waiting for task to complete.")

    print("Test completed.")

if __name__ == "__main__":
    main()

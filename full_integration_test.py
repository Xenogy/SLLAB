"""
Full integration test for the Windows VM Agent.

This script tests the complete agent workflow from log monitoring to action execution.
"""
import os
import sys
import time
import logging
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import agent components
from windows_vm_agent.config.config_loader import ConfigLoader
from windows_vm_agent.api.api_client import APIClient
from windows_vm_agent.scripts.script_executor import ScriptExecutor
from windows_vm_agent.agent.action_manager import ActionManager
from windows_vm_agent.monitors.log_file_monitor import LogFileMonitor

def main():
    """Run a full integration test."""
    print("\n===== STARTING FULL INTEGRATION TEST =====\n")
    
    # Step 1: Load configuration
    print("Step 1: Loading configuration...")
    config_loader = ConfigLoader("windows_vm_agent/config.yaml")
    config = config_loader.load()
    
    # Step 2: Create API client
    print("\nStep 2: Creating API client...")
    api_client = APIClient(
        config['General']['ManagerBaseURL'],
        config['General']['APIKey'],
        config['General']['VMIdentifier']
    )
    
    # Step 3: Create script executor
    print("\nStep 3: Creating script executor...")
    script_executor = ScriptExecutor(config['General']['ScriptsPath'])
    
    # Step 4: Create action manager
    print("\nStep 4: Creating action manager...")
    action_manager = ActionManager(config, api_client, script_executor)
    
    # Step 5: Create test log file
    print("\nStep 5: Creating test log file...")
    test_log_path = "test_logs/integration_test.log"
    with open(test_log_path, 'w') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO Starting integration test\n")
    
    # Step 6: Create monitor configuration
    print("\nStep 6: Creating monitor configuration...")
    monitor_config = {
        'Name': 'IntegrationTestMonitor',
        'Type': 'LogFileTail',
        'LogFilePath': test_log_path,
        'CheckIntervalSeconds': 0.5,
        'EventTriggers': [
            {
                'EventName': 'LoginEvent',
                'Regex': 'User logged in: (?P<account_id>\\w+)',
                'Action': 'UpdateProxyForAccount'
            },
            {
                'EventName': 'ErrorEvent',
                'Regex': 'Error code: (?P<error_code>\\d+)',
                'Action': 'NotifyError'
            }
        ]
    }
    
    # Step 7: Create event callback function
    print("\nStep 7: Setting up event callback...")
    event_results = {}
    event_triggered = threading.Event()
    
    def event_callback(action_name, event_data):
        print(f"\n*** EVENT TRIGGERED: {action_name} with data: {event_data} ***")
        
        # Let the action manager handle the event
        result = action_manager.handle_event(action_name, event_data)
        
        # Store the result
        event_key = f"{action_name}_{next(iter(event_data.values()))}"
        event_results[event_key] = result
        
        # Signal that an event was triggered
        event_triggered.set()
    
    # Step 8: Create and start the monitor
    print("\nStep 8: Creating and starting monitor...")
    monitor = LogFileMonitor(monitor_config, event_callback)
    monitor.start()
    
    # Step 9: Add test events to the log file
    print("\nStep 9: Adding test events to log file...")
    time.sleep(2)  # Wait for monitor to start
    
    # Add login event
    print("Adding login event...")
    with open(test_log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO User logged in: testuser123\n")
    
    # Wait for event to be processed
    if event_triggered.wait(timeout=5):
        print("Login event was processed")
        event_triggered.clear()
    else:
        print("Login event was not processed within timeout period")
    
    time.sleep(2)
    
    # Add error event
    print("\nAdding error event...")
    with open(test_log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR Error code: 5001\n")
    
    # Wait for event to be processed
    if event_triggered.wait(timeout=5):
        print("Error event was processed")
    else:
        print("Error event was not processed within timeout period")
    
    # Step 10: Stop the monitor
    print("\nStep 10: Stopping monitor...")
    monitor.stop()
    
    # Step 11: Print results
    print("\n===== TEST RESULTS =====")
    if event_results:
        for event_key, result in event_results.items():
            print(f"{event_key}: {'SUCCESS' if result else 'FAILED'}")
        
        all_success = all(event_results.values())
        if all_success:
            print("\nALL EVENTS PROCESSED SUCCESSFULLY!")
        else:
            print("\nSOME EVENTS FAILED TO PROCESS")
    else:
        print("No events were processed")
    
    print("\n===== FULL INTEGRATION TEST COMPLETED =====")

if __name__ == "__main__":
    main()

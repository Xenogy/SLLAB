"""
Simple test script for the log file monitor.
"""
import os
import sys
import time
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import the log file monitor
from windows_vm_agent.monitors.log_file_monitor import LogFileMonitor

def main():
    """Run a simple test of the log file monitor."""
    print("Starting simple log file monitor test...")
    
    # Create a test log file
    test_log_path = "test_logs/simple_test.log"
    print(f"Creating test log file: {test_log_path}")
    with open(test_log_path, 'w') as f:
        f.write("Initial log entry\n")
    
    # Create a monitor configuration
    monitor_config = {
        'Name': 'SimpleTestMonitor',
        'Type': 'LogFileTail',
        'LogFilePath': test_log_path,
        'CheckIntervalSeconds': 1.0,
        'EventTriggers': [
            {
                'EventName': 'SimpleTestEvent',
                'Regex': 'Test: (?P<value>\\w+)',
                'Action': 'SimpleTestAction'
            }
        ]
    }
    
    # Event callback function
    def event_callback(action_name, event_data):
        print(f"EVENT TRIGGERED: {action_name} with data: {event_data}")
    
    # Create and start the monitor
    print("Creating and starting monitor...")
    monitor = LogFileMonitor(monitor_config, event_callback)
    monitor.start()
    
    # Wait a moment for the monitor to start
    time.sleep(2)
    
    # Add test entries to the log file
    print("Adding test entries to log file...")
    for i in range(3):
        with open(test_log_path, 'a') as f:
            f.write(f"Test: value{i}\n")
        print(f"Added entry {i+1}/3")
        time.sleep(2)
    
    # Wait a bit longer to ensure all events are processed
    print("Waiting for events to be processed...")
    time.sleep(5)
    
    # Stop the monitor
    print("Stopping monitor...")
    monitor.stop()
    
    print("Test completed.")

if __name__ == "__main__":
    main()

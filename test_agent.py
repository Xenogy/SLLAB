"""
Test script for the Windows VM Agent.

This script tests the core functionality of the agent.
"""
import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import agent components
from windows_vm_agent.config.config_loader import ConfigLoader
from windows_vm_agent.api.api_client import APIClient
from windows_vm_agent.scripts.script_executor import ScriptExecutor
from windows_vm_agent.monitors.log_file_monitor import LogFileMonitor

def test_config_loader():
    """Test the configuration loader."""
    print("\n=== Testing ConfigLoader ===")
    try:
        config_loader = ConfigLoader("windows_vm_agent/config.yaml")
        config = config_loader.load()
        print(f"Configuration loaded successfully: {config}")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None

def test_api_client(config):
    """Test the API client."""
    print("\n=== Testing APIClient ===")
    try:
        api_client = APIClient(
            config['General']['ManagerBaseURL'],
            config['General']['APIKey'],
            config['General']['VMIdentifier']
        )
        
        # Test API request
        endpoint = "/account-config?vm_id={VMIdentifier}&account_id=test123"
        data = api_client.get_data(endpoint, {})
        print(f"API response: {data}")
        return api_client
    except Exception as e:
        print(f"Error testing API client: {e}")
        return None

def test_script_executor(config):
    """Test the script executor."""
    print("\n=== Testing ScriptExecutor ===")
    try:
        script_executor = ScriptExecutor(config['General']['ScriptsPath'])
        
        # List available scripts
        scripts_path = config['General']['ScriptsPath']
        if os.path.exists(scripts_path):
            scripts = [f for f in os.listdir(scripts_path) if f.endswith('.ps1')]
            print(f"Available scripts: {scripts}")
        else:
            print(f"Scripts directory not found: {scripts_path}")
        
        return script_executor
    except Exception as e:
        print(f"Error testing script executor: {e}")
        return None

def test_log_monitor(config):
    """Test the log file monitor."""
    print("\n=== Testing LogFileMonitor ===")
    try:
        # Create a test log file
        test_log_path = "test_logs/test_monitor.log"
        with open(test_log_path, 'w') as f:
            f.write("2023-05-01 12:00:00 INFO Test log entry\n")
        
        # Create a monitor configuration
        monitor_config = {
            'Name': 'TestMonitor',
            'Type': 'LogFileTail',
            'LogFilePath': test_log_path,
            'CheckIntervalSeconds': 0.5,
            'EventTriggers': [
                {
                    'EventName': 'TestEvent',
                    'Regex': 'Test event: (?P<event_id>\\d+)',
                    'Action': 'TestAction'
                }
            ]
        }
        
        # Event callback function
        def event_callback(action_name, event_data):
            print(f"Event triggered: {action_name} with data: {event_data}")
        
        # Create and start the monitor
        monitor = LogFileMonitor(monitor_config, event_callback)
        monitor.start()
        
        # Wait a moment for the monitor to start
        time.sleep(1)
        
        # Append a test event to the log file
        print("Adding test event to log file...")
        with open(test_log_path, 'a') as f:
            f.write("2023-05-01 12:01:00 INFO Test event: 12345\n")
        
        # Wait for the monitor to detect the event
        time.sleep(2)
        
        # Stop the monitor
        monitor.stop()
        return True
    except Exception as e:
        print(f"Error testing log monitor: {e}")
        return False

def main():
    """Run the tests."""
    print("Starting Windows VM Agent tests...")
    
    # Test configuration loader
    config = test_config_loader()
    if not config:
        print("Configuration test failed, aborting.")
        return
    
    # Test API client
    api_client = test_api_client(config)
    
    # Test script executor
    script_executor = test_script_executor(config)
    
    # Test log monitor
    log_monitor_success = test_log_monitor(config)
    
    print("\n=== Test Results ===")
    print(f"Configuration: {'SUCCESS' if config else 'FAILED'}")
    print(f"API Client: {'SUCCESS' if api_client else 'FAILED'}")
    print(f"Script Executor: {'SUCCESS' if script_executor else 'FAILED'}")
    print(f"Log Monitor: {'SUCCESS' if log_monitor_success else 'FAILED'}")

if __name__ == "__main__":
    main()

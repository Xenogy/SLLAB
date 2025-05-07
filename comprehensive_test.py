"""
Comprehensive test script for the Windows VM Agent.

This script tests each component of the agent individually and together.
"""
import os
import sys
import time
import logging
import threading
import traceback
from datetime import datetime

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
from windows_vm_agent.agent.action_manager import ActionManager
from windows_vm_agent.monitors.log_file_monitor import LogFileMonitor
from windows_vm_agent.monitors.base_monitor import BaseMonitor

class TestRunner:
    """Test runner for the Windows VM Agent."""

    def __init__(self):
        """Initialize the test runner."""
        self.config = None
        self.api_client = None
        self.script_executor = None
        self.action_manager = None
        self.monitors = []
        self.test_results = {}

    def run_all_tests(self):
        """Run all tests."""
        print("\n===== STARTING COMPREHENSIVE TESTS =====\n")

        try:
            # Test configuration loader
            self.test_config_loader()

            # Test API client
            self.test_api_client()

            # Test script executor
            self.test_script_executor()

            # Test action manager
            self.test_action_manager()

            # Test log file monitor
            self.test_log_monitor()

            # Test full integration
            self.test_full_integration()

            # Print test results
            self.print_results()

        except Exception as e:
            print(f"Error running tests: {e}")
            traceback.print_exc()

    def test_config_loader(self):
        """Test the configuration loader."""
        print("\n=== Testing ConfigLoader ===")
        try:
            config_loader = ConfigLoader("windows_vm_agent/config.yaml")
            self.config = config_loader.load()
            print(f"Configuration loaded successfully")
            print(f"General settings: {self.config['General']}")
            print(f"Number of monitors: {len(self.config['EventMonitors'])}")
            print(f"Number of actions: {len(self.config['Actions'])}")
            self.test_results['ConfigLoader'] = "SUCCESS"
        except Exception as e:
            print(f"Error loading configuration: {e}")
            traceback.print_exc()
            self.test_results['ConfigLoader'] = f"FAILED: {str(e)}"

    def test_api_client(self):
        """Test the API client."""
        print("\n=== Testing APIClient ===")
        if not self.config:
            print("Configuration not loaded, skipping API client test")
            self.test_results['APIClient'] = "SKIPPED"
            return

        try:
            self.api_client = APIClient(
                self.config['General']['ManagerBaseURL'],
                self.config['General']['APIKey'],
                self.config['General']['VMIdentifier']
            )

            # Test API request
            print("Making test API request...")
            endpoint = "/account-config?vm_id={VMIdentifier}&account_id=test123"
            data = self.api_client.get_data(endpoint, {})

            if data:
                print(f"API request successful")
                print(f"Response data: {data}")
                self.test_results['APIClient'] = "SUCCESS"
            else:
                print("API request failed, no data returned")
                self.test_results['APIClient'] = "FAILED: No data returned"
        except Exception as e:
            print(f"Error testing API client: {e}")
            traceback.print_exc()
            self.test_results['APIClient'] = f"FAILED: {str(e)}"

    def test_script_executor(self):
        """Test the script executor."""
        print("\n=== Testing ScriptExecutor ===")
        if not self.config:
            print("Configuration not loaded, skipping script executor test")
            self.test_results['ScriptExecutor'] = "SKIPPED"
            return

        try:
            scripts_path = self.config['General']['ScriptsPath']
            self.script_executor = ScriptExecutor(scripts_path)

            # List available scripts
            if os.path.exists(scripts_path):
                scripts = [f for f in os.listdir(scripts_path) if f.endswith('.ps1')]
                print(f"Available scripts: {scripts}")

                if scripts:
                    self.test_results['ScriptExecutor'] = "SUCCESS"
                else:
                    print("No scripts found in scripts directory")
                    self.test_results['ScriptExecutor'] = "WARNING: No scripts found"
            else:
                print(f"Scripts directory not found: {scripts_path}")
                self.test_results['ScriptExecutor'] = f"WARNING: Scripts directory not found"
        except Exception as e:
            print(f"Error testing script executor: {e}")
            traceback.print_exc()
            self.test_results['ScriptExecutor'] = f"FAILED: {str(e)}"

    def test_action_manager(self):
        """Test the action manager."""
        print("\n=== Testing ActionManager ===")
        if not self.config or not self.api_client or not self.script_executor:
            print("Prerequisites not met, skipping action manager test")
            self.test_results['ActionManager'] = "SKIPPED"
            return

        try:
            self.action_manager = ActionManager(
                self.config,
                self.api_client,
                self.script_executor
            )

            # Check if actions were loaded
            action_count = len(self.action_manager.actions)
            print(f"Loaded {action_count} actions")

            if action_count > 0:
                print("Actions loaded successfully:")
                for name, action in self.action_manager.actions.items():
                    print(f"  - {name}: Script={action.script}, API Endpoint={action.api_data_endpoint}")
                self.test_results['ActionManager'] = "SUCCESS"
            else:
                print("No actions were loaded")
                self.test_results['ActionManager'] = "WARNING: No actions loaded"
        except Exception as e:
            print(f"Error testing action manager: {e}")
            traceback.print_exc()
            self.test_results['ActionManager'] = f"FAILED: {str(e)}"

    def test_log_monitor(self):
        """Test the log file monitor."""
        print("\n=== Testing LogFileMonitor ===")
        try:
            # Create a test log file
            test_log_path = "test_logs/test_monitor.log"
            with open(test_log_path, 'w') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO Test log entry\n")

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
            event_triggered = threading.Event()
            event_data_captured = {}

            def event_callback(action_name, event_data):
                print(f"Event triggered: {action_name} with data: {event_data}")
                event_data_captured.update(event_data)
                event_triggered.set()

            # Create and start the monitor
            monitor = LogFileMonitor(monitor_config, event_callback)
            monitor.start()

            # Wait a moment for the monitor to start
            time.sleep(1)

            # Append a test event to the log file
            print("Adding test event to log file...")
            with open(test_log_path, 'a') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO Test event: 12345\n")

            # Wait for the event to be triggered (with timeout)
            if event_triggered.wait(timeout=5):
                print(f"Event was triggered successfully with data: {event_data_captured}")
                if 'event_id' in event_data_captured and event_data_captured['event_id'] == '12345':
                    print("Event data was captured correctly")
                    self.test_results['LogFileMonitor'] = "SUCCESS"
                else:
                    print(f"Event data was not captured correctly: {event_data_captured}")
                    self.test_results['LogFileMonitor'] = "FAILED: Event data incorrect"
            else:
                print("Event was not triggered within timeout period")
                self.test_results['LogFileMonitor'] = "FAILED: Event not triggered"

            # Stop the monitor
            monitor.stop()
        except Exception as e:
            print(f"Error testing log monitor: {e}")
            traceback.print_exc()
            self.test_results['LogFileMonitor'] = f"FAILED: {str(e)}"

    def test_full_integration(self):
        """Test full integration of all components."""
        print("\n=== Testing Full Integration ===")
        if not self.config or not self.api_client or not self.script_executor or not self.action_manager:
            print("Prerequisites not met, skipping full integration test")
            self.test_results['FullIntegration'] = "SKIPPED"
            return

        try:
            # Create a test log file for the integration test
            test_log_path = "test_logs/integration_test.log"
            with open(test_log_path, 'w') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO Starting integration test\n")

            # Create a monitor configuration that matches an action in the config
            action_name = next(iter(self.action_manager.actions.keys()))
            print(f"Using action '{action_name}' for integration test")

            monitor_config = {
                'Name': 'IntegrationTestMonitor',
                'Type': 'LogFileTail',
                'LogFilePath': test_log_path,
                'CheckIntervalSeconds': 0.5,
                'EventTriggers': [
                    {
                        'EventName': 'IntegrationTestEvent',
                        'Regex': 'Integration test: (?P<account_id>\\w+)',
                        'Action': action_name
                    }
                ]
            }

            # Event callback function
            event_triggered = threading.Event()

            def event_callback(action_name, event_data):
                print(f"Integration event triggered: {action_name} with data: {event_data}")
                # Let the action manager handle the event
                result = self.action_manager.handle_event(action_name, event_data)
                print(f"Action manager result: {result}")
                event_triggered.set()

            # Create and start the monitor
            monitor = LogFileMonitor(monitor_config, event_callback)
            monitor.start()

            # Wait a moment for the monitor to start
            time.sleep(1)

            # Append a test event to the log file
            print("Adding integration test event to log file...")
            with open(test_log_path, 'a') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO Integration test: testuser123\n")

            # Wait for the event to be triggered (with timeout)
            if event_triggered.wait(timeout=10):
                print("Integration test event was triggered successfully")
                self.test_results['FullIntegration'] = "SUCCESS"
            else:
                print("Integration test event was not triggered within timeout period")
                self.test_results['FullIntegration'] = "FAILED: Event not triggered"

            # Stop the monitor
            monitor.stop()
        except Exception as e:
            print(f"Error in full integration test: {e}")
            traceback.print_exc()
            self.test_results['FullIntegration'] = f"FAILED: {str(e)}"

    def print_results(self):
        """Print test results."""
        print("\n===== TEST RESULTS =====")
        for test_name, result in self.test_results.items():
            print(f"{test_name}: {result}")

        # Check if all tests passed
        all_passed = all(result.startswith("SUCCESS") for result in self.test_results.values())
        if all_passed:
            print("\nALL TESTS PASSED!")
        else:
            print("\nSOME TESTS FAILED OR WERE SKIPPED")

if __name__ == "__main__":
    print("Starting comprehensive test script...")
    try:
        runner = TestRunner()
        print("Test runner created, starting tests...")
        runner.run_all_tests()
    except Exception as e:
        print(f"Unhandled exception in main: {e}")
        traceback.print_exc()

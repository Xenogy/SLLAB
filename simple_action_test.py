"""
Simple test script for the action manager.
"""
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import the necessary components
from windows_vm_agent.config.config_loader import ConfigLoader
from windows_vm_agent.api.api_client import APIClient
from windows_vm_agent.scripts.script_executor import ScriptExecutor
from windows_vm_agent.agent.action_manager import ActionManager

def main():
    """Run a simple test of the action manager."""
    print("Starting simple action manager test...")
    
    # Load configuration
    print("Loading configuration...")
    config_loader = ConfigLoader("windows_vm_agent/config.yaml")
    config = config_loader.load()
    
    # Create API client
    print("Creating API client...")
    api_client = APIClient(
        config['General']['ManagerBaseURL'],
        config['General']['APIKey'],
        config['General']['VMIdentifier']
    )
    
    # Create script executor
    print("Creating script executor...")
    script_executor = ScriptExecutor(config['General']['ScriptsPath'])
    
    # Create action manager
    print("Creating action manager...")
    action_manager = ActionManager(config, api_client, script_executor)
    
    # Print loaded actions
    print("Loaded actions:")
    for name, action in action_manager.actions.items():
        print(f"  - {name}: Script={action.script}, API Endpoint={action.api_data_endpoint}")
    
    # Test handling an event
    print("\nTesting event handling...")
    action_name = "UpdateProxyForAccount"
    event_data = {"account_id": "test123"}
    
    print(f"Handling event: {action_name} with data: {event_data}")
    result = action_manager.handle_event(action_name, event_data)
    
    print(f"Event handling result: {result}")
    
    print("Test completed.")

if __name__ == "__main__":
    main()

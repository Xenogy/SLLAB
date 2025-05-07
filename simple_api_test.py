"""
Simple test script for the API client.
"""
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import the API client and config loader
from windows_vm_agent.config.config_loader import ConfigLoader
from windows_vm_agent.api.api_client import APIClient

def main():
    """Run a simple test of the API client."""
    print("Starting simple API client test...")
    
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
    
    # Test API request
    print("Making test API request...")
    endpoint = "/account-config?vm_id={VMIdentifier}&account_id=test123"
    data = api_client.get_data(endpoint, {})
    
    print(f"API response: {data}")
    
    print("Test completed.")

if __name__ == "__main__":
    main()

"""
Test script for the Windows VM Agent API endpoints.

This script tests the Windows VM Agent API endpoints by making requests to them.
"""
import requests
import json
import sys
import logging
import argparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_register_agent(base_url: str) -> dict:
    """
    Test the register agent endpoint.
    
    Args:
        base_url: Base URL of the API.
        
    Returns:
        dict: Response data from the API.
    """
    logger.info("Testing register agent endpoint...")
    
    # Generate a unique VM ID
    vm_id = f"test-vm-{int(time.time())}"
    
    # Make the request
    url = f"{base_url}/windows-vm-agent/register"
    params = {
        "vm_id": vm_id,
        "vm_name": "Test VM",
        "owner_id": 1  # Admin user ID
    }
    
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Register agent response: {data}")
        
        # Verify the response
        assert "vm_id" in data, "Response missing vm_id"
        assert "api_key" in data, "Response missing api_key"
        assert data["vm_id"] == vm_id, f"VM ID mismatch: {data['vm_id']} != {vm_id}"
        
        logger.info("Register agent test passed")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Assertion error: {e}")
        sys.exit(1)

def test_account_config(base_url: str, vm_id: str, api_key: str) -> dict:
    """
    Test the account config endpoint.
    
    Args:
        base_url: Base URL of the API.
        vm_id: VM ID to use for the request.
        api_key: API key to use for the request.
        
    Returns:
        dict: Response data from the API.
    """
    logger.info("Testing account config endpoint...")
    
    # Make the request
    url = f"{base_url}/windows-vm-agent/account-config"
    params = {
        "vm_id": vm_id,
        "account_id": "test-account",  # This should be a valid account ID
        "api_key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Account config response: {data}")
        
        # Verify the response
        assert "account_id" in data, "Response missing account_id"
        assert "vm_id" in data, "Response missing vm_id"
        assert data["vm_id"] == vm_id, f"VM ID mismatch: {data['vm_id']} != {vm_id}"
        
        logger.info("Account config test passed")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Assertion error: {e}")
        sys.exit(1)

def test_update_status(base_url: str, vm_id: str, api_key: str) -> dict:
    """
    Test the update status endpoint.
    
    Args:
        base_url: Base URL of the API.
        vm_id: VM ID to use for the request.
        api_key: API key to use for the request.
        
    Returns:
        dict: Response data from the API.
    """
    logger.info("Testing update status endpoint...")
    
    # Make the request
    url = f"{base_url}/windows-vm-agent/status"
    params = {
        "api_key": api_key
    }
    data = {
        "vm_id": vm_id,
        "status": "running",
        "ip_address": "192.168.1.100",
        "cpu_usage_percent": 25.5,
        "memory_usage_percent": 50.2,
        "disk_usage_percent": 75.8,
        "uptime_seconds": 3600
    }
    
    try:
        response = requests.post(url, params=params, json=data)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Update status response: {data}")
        
        # Verify the response
        assert "success" in data, "Response missing success"
        assert data["success"] is True, "Update status failed"
        
        logger.info("Update status test passed")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Assertion error: {e}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Windows VM Agent API endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    args = parser.parse_args()
    
    logger.info(f"Using base URL: {args.base_url}")
    
    # Test register agent
    register_data = test_register_agent(args.base_url)
    
    # Extract VM ID and API key
    vm_id = register_data["vm_id"]
    api_key = register_data["api_key"]
    
    # Test account config
    test_account_config(args.base_url, vm_id, api_key)
    
    # Test update status
    test_update_status(args.base_url, vm_id, api_key)
    
    logger.info("All tests passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())

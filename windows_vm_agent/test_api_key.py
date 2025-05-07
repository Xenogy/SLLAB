#!/usr/bin/env python3
"""
Test script for verifying the API key in the Windows VM Agent configuration.

This script loads the configuration file and tests the API key by making a request
to the server. It can be used to diagnose API key issues.
"""
import argparse
import logging
import sys
from config.config_loader import ConfigLoader
from api.api_client import APIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the API key in the Windows VM Agent configuration")
    parser.add_argument("--config", default=None, help="Path to the configuration file")
    parser.add_argument("--api-key", default=None, help="Override the API key in the configuration file")
    parser.add_argument("--vm-id", default=None, help="Override the VM ID in the configuration file")
    parser.add_argument("--base-url", default=None, help="Override the Manager Base URL in the configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config_loader = ConfigLoader(args.config)
        config = config_loader.load()
        
        # Get configuration values
        vm_id = args.vm_id or config['General']['VMIdentifier']
        api_key = args.api_key or config['General']['APIKey']
        base_url = args.base_url or config['General']['ManagerBaseURL']
        
        logger.info(f"Using VM ID: {vm_id}")
        logger.info(f"Using API Key: {api_key}")
        logger.info(f"Using Base URL: {base_url}")
        
        # Create API client
        logger.info("Creating API client...")
        api_client = APIClient(base_url, api_key, vm_id)
        
        # Test API key
        logger.info("Testing API key...")
        if api_client.test_api_key():
            logger.info("API key test PASSED! The API key is valid.")
            return 0
        else:
            logger.error("API key test FAILED! The API key is not valid.")
            return 1
    
    except Exception as e:
        logger.error(f"Error testing API key: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

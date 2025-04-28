"""
Test script to verify that the refactored endpoints are working correctly.
This script doesn't execute HTTP requests but checks the structure of the endpoint functions.
"""

import inspect
import sys
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import router modules
from routers.proxmox_nodes import router as proxmox_nodes_router
from routers.vms import router as vms_router
from routers.accounts import router as accounts_router

def check_endpoint_structure(router, endpoint_path: str, expected_repo_class: str) -> bool:
    """
    Check if an endpoint function uses the repository pattern.
    
    Args:
        router: The router containing the endpoint
        endpoint_path: The path of the endpoint
        expected_repo_class: The name of the repository class that should be used
        
    Returns:
        bool: True if the endpoint uses the repository pattern, False otherwise
    """
    # Find the endpoint function
    endpoint_function = None
    for route in router.routes:
        if route.path == endpoint_path:
            endpoint_function = route.endpoint
            break
    
    if not endpoint_function:
        logger.error(f"Endpoint {endpoint_path} not found in router")
        return False
    
    # Get the source code of the endpoint function
    try:
        source_code = inspect.getsource(endpoint_function)
    except Exception as e:
        logger.error(f"Error getting source code for endpoint {endpoint_path}: {e}")
        return False
    
    # Check if the source code contains the repository class instantiation
    repo_instantiation = f"{expected_repo_class}(user_id=current_user"
    if repo_instantiation not in source_code:
        logger.error(f"Endpoint {endpoint_path} does not use {expected_repo_class}")
        return False
    
    # Check if the source code contains direct SQL queries
    sql_indicators = ["cursor.execute", "SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM "]
    for indicator in sql_indicators:
        if indicator in source_code:
            logger.warning(f"Endpoint {endpoint_path} contains direct SQL query: {indicator}")
            # Don't fail the test for this, just warn
    
    logger.info(f"Endpoint {endpoint_path} uses {expected_repo_class}")
    return True

def main():
    """Main function."""
    success = True
    
    # Check proxmox_nodes endpoints
    proxmox_nodes_endpoints = [
        ("/", "ProxmoxNodeRepository"),
        ("/{node_id}", "ProxmoxNodeRepository"),
        ("/{node_id}/regenerate-api-key", "ProxmoxNodeRepository"),
        ("/verify", "ProxmoxNodeRepository"),
        ("/heartbeat", "ProxmoxNodeRepository"),
        ("/agent-node/{node_id}", "ProxmoxNodeRepository"),
        ("/agent-vms/{node_id}", "ProxmoxNodeRepository"),
        ("/agent-whitelist/{node_id}", "ProxmoxNodeRepository"),
        ("/whitelist/{node_id}", "ProxmoxNodeRepository")
    ]
    
    for endpoint_path, repo_class in proxmox_nodes_endpoints:
        if not check_endpoint_structure(proxmox_nodes_router, endpoint_path, repo_class):
            success = False
    
    # Check vms endpoints
    vms_endpoints = [
        ("/", "VMRepository"),
        ("/{vm_id}", "VMRepository"),
        ("/proxmox", "VMRepository"),
        ("/proxmox/{node_id}", "VMRepository")
    ]
    
    for endpoint_path, repo_class in vms_endpoints:
        if not check_endpoint_structure(vms_router, endpoint_path, repo_class):
            success = False
    
    # Check accounts endpoints
    accounts_endpoints = [
        ("/", "AccountRepository"),
        ("/{acc_id}", "AccountRepository"),
        ("/info", "AccountRepository")
    ]
    
    for endpoint_path, repo_class in accounts_endpoints:
        if not check_endpoint_structure(accounts_router, endpoint_path, repo_class):
            success = False
    
    if success:
        logger.info("All endpoints use the repository pattern")
        return 0
    else:
        logger.error("Some endpoints do not use the repository pattern")
        return 1

if __name__ == "__main__":
    sys.exit(main())

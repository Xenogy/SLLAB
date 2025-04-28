"""
Test script to verify that the repository pattern implementation is working correctly.
This script doesn't execute database operations but checks the structure and methods of repository classes.
"""

import inspect
import sys
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import repository classes
from db.repositories.base import BaseRepository
from db.repositories.accounts import AccountRepository
from db.repositories.proxmox_nodes import ProxmoxNodeRepository
from db.repositories.vms import VMRepository
from db.repositories.hardware import HardwareRepository
from db.repositories.users import UserRepository

def check_repository_structure(repo_class, expected_methods: List[str]) -> bool:
    """
    Check if a repository class has the expected structure.
    
    Args:
        repo_class: The repository class to check
        expected_methods: List of method names that should be present
        
    Returns:
        bool: True if the repository has the expected structure, False otherwise
    """
    # Check if the class inherits from BaseRepository
    if not issubclass(repo_class, BaseRepository):
        logger.error(f"{repo_class.__name__} does not inherit from BaseRepository")
        return False
    
    # Check if the class has the expected methods
    missing_methods = []
    for method_name in expected_methods:
        if not hasattr(repo_class, method_name) or not callable(getattr(repo_class, method_name)):
            missing_methods.append(method_name)
    
    if missing_methods:
        logger.error(f"{repo_class.__name__} is missing the following methods: {', '.join(missing_methods)}")
        return False
    
    # Check if the class has the required attributes
    required_attributes = ["table_name", "id_column", "default_columns", "default_order_by"]
    missing_attributes = []
    
    # Create an instance to check instance attributes
    repo_instance = repo_class()
    
    for attr_name in required_attributes:
        if not hasattr(repo_instance, attr_name):
            missing_attributes.append(attr_name)
    
    if missing_attributes:
        logger.error(f"{repo_class.__name__} is missing the following attributes: {', '.join(missing_attributes)}")
        return False
    
    logger.info(f"{repo_class.__name__} has the expected structure")
    return True

def check_method_signature(repo_class, method_name: str, expected_params: List[str]) -> bool:
    """
    Check if a method has the expected signature.
    
    Args:
        repo_class: The repository class to check
        method_name: The name of the method to check
        expected_params: List of parameter names that should be present
        
    Returns:
        bool: True if the method has the expected signature, False otherwise
    """
    if not hasattr(repo_class, method_name) or not callable(getattr(repo_class, method_name)):
        logger.error(f"{repo_class.__name__}.{method_name} does not exist")
        return False
    
    method = getattr(repo_class, method_name)
    signature = inspect.signature(method)
    
    # Check if all expected parameters are present
    missing_params = []
    for param_name in expected_params:
        if param_name not in signature.parameters:
            missing_params.append(param_name)
    
    if missing_params:
        logger.error(f"{repo_class.__name__}.{method_name} is missing the following parameters: {', '.join(missing_params)}")
        return False
    
    logger.info(f"{repo_class.__name__}.{method_name} has the expected signature")
    return True

def main():
    """Main function."""
    success = True
    
    # Check BaseRepository structure
    base_repo_methods = [
        "__init__", "execute_query", "execute_query_single", "execute_command",
        "execute_insert", "execute_update", "execute_delete", "get_count",
        "get_all", "get_by_id", "insert", "update", "delete"
    ]
    if not check_repository_structure(BaseRepository, base_repo_methods):
        success = False
    
    # Check AccountRepository structure
    account_repo_methods = [
        "get_accounts", "get_account_by_id", "get_account_by_username",
        "create_account", "update_account", "delete_account", "get_account_info"
    ]
    if not check_repository_structure(AccountRepository, account_repo_methods):
        success = False
    
    # Check ProxmoxNodeRepository structure
    proxmox_node_repo_methods = [
        "get_nodes", "get_node_by_id", "create_node", "update_node",
        "delete_node", "update_node_status", "get_agent_whitelist", "get_agent_vms"
    ]
    if not check_repository_structure(ProxmoxNodeRepository, proxmox_node_repo_methods):
        success = False
    
    # Check VMRepository structure
    vm_repo_methods = [
        "get_vms", "get_vm_by_id", "get_vm_by_vmid", "create_vm",
        "update_vm", "delete_vm", "get_vms_by_proxmox_node"
    ]
    if not check_repository_structure(VMRepository, vm_repo_methods):
        success = False
    
    # Check method signatures
    if not check_method_signature(AccountRepository, "get_accounts", ["limit", "offset"]):
        success = False
    
    if not check_method_signature(ProxmoxNodeRepository, "get_node_by_id", ["node_id"]):
        success = False
    
    if not check_method_signature(VMRepository, "get_vm_by_id", ["vm_id"]):
        success = False
    
    if success:
        logger.info("All repository classes have the expected structure")
        return 0
    else:
        logger.error("Some repository classes do not have the expected structure")
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Test script for Windows VM agent registration.

This script tests the Windows VM agent registration process by directly calling
the repository methods, bypassing the API endpoints.
"""

import logging
import sys
import secrets
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import the repository classes
from db.repositories.vms import VMRepository
from db.repositories.windows_vm_agent import WindowsVMAgentRepository

def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)

def test_register_agent(vm_id: str, vm_name: str, owner_id: int) -> Optional[Dict[str, Any]]:
    """
    Test the register agent functionality.

    Args:
        vm_id: The VM ID.
        vm_name: The VM name.
        owner_id: The owner ID.

    Returns:
        The registered agent data or None if registration failed.
    """
    logger.info(f"Testing register agent functionality for VM ID: {vm_id}, VM Name: {vm_name}, Owner ID: {owner_id}")

    # First, check if the user owns the VM
    vm_repo = VMRepository(user_id=owner_id, user_role="user")
    if not vm_repo.check_vm_ownership(vm_id, owner_id):
        logger.error(f"User {owner_id} does not own VM {vm_id}")
        return None

    # Generate API key
    api_key = generate_api_key()
    logger.info(f"Generated API key: {api_key}")

    # Register the agent
    agent_repo = WindowsVMAgentRepository(user_id=owner_id, user_role="user")
    agent = agent_repo.register_agent(vm_id, api_key, vm_name, owner_id)

    if not agent:
        logger.error(f"Failed to register agent for VM ID: {vm_id}")
        return None

    logger.info(f"Successfully registered agent for VM ID: {vm_id}")
    return agent

if __name__ == "__main__":
    # Test with the VM we created earlier
    vm_id = "1"  # Database ID of the VM (from the 'id' column)
    vm_name = "Test VM"
    owner_id = 2  # User ID

    # Print all VMs in the database for debugging
    logger.info("Listing all VMs in the database:")
    vm_repo = VMRepository(user_id=1, user_role="admin")
    vms = vm_repo.get_all()
    for vm in vms:
        logger.info(f"VM: id={vm['id']}, vmid={vm['vmid']}, name={vm['name']}, owner_id={vm['owner_id']}")

    result = test_register_agent(vm_id, vm_name, owner_id)

    if result:
        logger.info(f"Test successful! Agent registered: {result}")
    else:
        logger.error("Test failed! Could not register agent.")

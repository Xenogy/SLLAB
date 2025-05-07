"""
Windows VM Agent API endpoints.

This module provides API endpoints for Windows VM agents to retrieve configuration
and report status.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
import secrets

from db.repositories.vms import VMRepository
from db.repositories.accounts import AccountRepository
from db.repositories.windows_vm_agent import WindowsVMAgentRepository
from routers.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/windows-vm-agent",
    tags=["windows-vm-agent"],
    responses={404: {"description": "Not found"}},
)

# Models
class AccountConfigResponse(BaseModel):
    """Response model for account configuration."""
    account_id: str
    vm_id: str
    proxy_server: Optional[str] = None
    proxy_bypass: Optional[str] = None
    additional_settings: Optional[Dict[str, Any]] = None

class AgentStatusUpdate(BaseModel):
    """Model for agent status updates."""
    vm_id: str
    status: str
    ip_address: Optional[str] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    uptime_seconds: Optional[int] = None

class AgentStatusResponse(BaseModel):
    """Response model for agent status updates."""
    success: bool
    message: str

class AgentInfoResponse(BaseModel):
    """Response model for agent information."""
    vm_id: str
    vm_name: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    uptime_seconds: Optional[int] = None
    last_seen: Optional[str] = None
    created_at: str
    updated_at: str

# Helper functions
def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)

# Endpoints
@router.get("/account-config", response_model=AccountConfigResponse)
async def get_account_config(
    vm_id: str = Query(..., description="The VM identifier"),
    account_id: str = Query(..., description="The account identifier"),
    api_key: str = Query(..., description="API key for authentication")
):
    """
    Get account configuration for a Windows VM agent.

    This endpoint is called by the Windows VM agent to get account-specific configuration
    such as proxy settings.
    """
    logger.info(f"Getting account config for VM: {vm_id}, Account: {account_id}")

    # Validate input parameters
    if not vm_id:
        raise HTTPException(status_code=400, detail="Missing required parameter: vm_id")

    if not account_id:
        raise HTTPException(status_code=400, detail="Missing required parameter: account_id")

    if not api_key:
        raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

    # Use the repository pattern with admin role to verify API key
    agent_repo = WindowsVMAgentRepository(user_id=1, user_role="admin")

    try:
        # Verify API key
        agent = agent_repo.verify_api_key(vm_id, api_key)

        if not agent:
            logger.warning(f"Invalid API key for VM: {vm_id}")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update last_seen timestamp
        agent_repo.update_last_seen(vm_id)

        # Get the VM to check ownership
        vm_repo = VMRepository(user_id=agent["owner_id"], user_role="user")
        vm = vm_repo.get_vm_by_vmid(vm_id)

        if not vm:
            logger.warning(f"VM not found: {vm_id}")
            raise HTTPException(status_code=404, detail=f"VM not found: {vm_id}")

        # Check if the account belongs to the agent's owner
        # Use the agent's owner context to get the account
        account_repo = AccountRepository(user_id=agent["owner_id"], user_role="user")
        account = account_repo.get_account_by_id(account_id)

        if not account:
            logger.warning(f"Account not found: {account_id}")
            raise HTTPException(status_code=404, detail="Account not found")

        # Get proxy settings for the account
        # This is a placeholder - implement actual logic to get proxy settings
        proxy_settings = account_repo.get_account_proxy_settings(account_id)

        # Return the configuration
        return {
            "account_id": account_id,
            "vm_id": vm_id,
            "proxy_server": proxy_settings.get("proxy_server"),
            "proxy_bypass": proxy_settings.get("proxy_bypass"),
            "additional_settings": proxy_settings.get("additional_settings")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account config: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting account config: {str(e)}")

@router.post("/status", response_model=AgentStatusResponse)
async def update_agent_status(
    status_update: AgentStatusUpdate,
    api_key: str = Query(..., description="API key for authentication")
):
    """
    Update the status of a Windows VM agent.

    This endpoint is called by the Windows VM agent to report its status.
    """
    logger.info(f"Updating agent status for VM: {status_update.vm_id}")

    # Validate input parameters
    if not status_update.vm_id:
        raise HTTPException(status_code=400, detail="Missing required parameter: vm_id")

    if not api_key:
        raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

    # Use the repository pattern with admin role to verify API key
    agent_repo = WindowsVMAgentRepository(user_id=1, user_role="admin")

    try:
        # Verify API key
        agent = agent_repo.verify_api_key(status_update.vm_id, api_key)

        if not agent:
            logger.warning(f"Invalid API key for VM: {status_update.vm_id}")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Use the agent's owner context for updating status
        owner_agent_repo = WindowsVMAgentRepository(user_id=agent["owner_id"], user_role="user")

        # Update agent status
        success = owner_agent_repo.update_status(
            status_update.vm_id,
            status_update.status,
            status_update.ip_address,
            status_update.cpu_usage_percent,
            status_update.memory_usage_percent,
            status_update.disk_usage_percent,
            status_update.uptime_seconds
        )

        if not success:
            logger.warning(f"Failed to update status for VM: {status_update.vm_id}")
            raise HTTPException(status_code=500, detail="Failed to update agent status")

        return {
            "success": True,
            "message": "Agent status updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating agent status: {str(e)}")

@router.post("/register", response_model=Dict[str, Any])
async def register_agent(
    vm_id: str = Query(..., description="The VM identifier"),
    vm_name: Optional[str] = Query(None, description="The VM name"),
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new Windows VM agent and generate an API key.

    This endpoint requires authentication and ensures users can only register VM IDs they own.
    """
    logger.info(f"Registering new Windows VM agent for VM: {vm_id}, requested by user: {current_user['id']}")

    # Validate input parameters
    if not vm_id:
        raise HTTPException(status_code=400, detail="Missing required parameter: vm_id")

    # Check if the user owns the VM or is an admin
    if current_user["role"] != "admin":
        # Use VM repository to check ownership
        vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])
        # The vm_id could be either a database ID or a Proxmox VMID
        if not vm_repo.check_vm_ownership(vm_id, current_user["id"]):
            logger.warning(f"User {current_user['id']} attempted to register agent for VM {vm_id} they don't own")
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to register an agent for this VM"
            )

    # Use the repository pattern with the current user's context
    agent_repo = WindowsVMAgentRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if agent already exists
        existing_agent = agent_repo.get_agent_by_vm_id(vm_id)

        # Get VM name if not provided
        if not vm_name:
            try:
                vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])
                vm = vm_repo.get_vm_by_id(int(vm_id))
                if vm:
                    vm_name = vm["name"]
            except:
                # If we can't get the VM name, use a default
                vm_name = f"VM {vm_id}"

        # Import the agent utils
        from utils.agent_utils import generate_powershell_command, generate_powershell_script

        if existing_agent:
            logger.info(f"Agent already exists for VM: {vm_id}")

            # Check if the user owns the existing agent or is an admin
            if current_user["role"] != "admin" and existing_agent["owner_id"] != current_user["id"]:
                logger.warning(f"User {current_user['id']} attempted to regenerate API key for VM {vm_id} owned by user {existing_agent['owner_id']}")
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to regenerate the API key for this VM agent"
                )

            # Generate a new API key
            api_key = generate_api_key()

            # Update the agent with the new API key
            updated_agent = agent_repo.update_api_key(vm_id, api_key)

            if not updated_agent:
                raise HTTPException(status_code=500, detail="Failed to update API key")

            # Generate PowerShell command and script
            powershell_command = generate_powershell_command(vm_id, vm_name or "", api_key)
            powershell_script = generate_powershell_script(vm_id, vm_name or "", api_key)

            return {
                "vm_id": vm_id,
                "api_key": api_key,
                "message": "Agent API key regenerated successfully",
                "powershell_command": powershell_command,
                "powershell_script": powershell_script
            }

        # Generate API key
        api_key = generate_api_key()

        # Register the agent with the current user as the owner
        agent = agent_repo.register_agent(vm_id, api_key, vm_name, current_user["id"])

        if not agent:
            raise HTTPException(status_code=500, detail="Failed to register agent")

        # Generate PowerShell command and script
        powershell_command = generate_powershell_command(vm_id, vm_name or "", api_key)
        powershell_script = generate_powershell_script(vm_id, vm_name or "", api_key)

        return {
            "vm_id": vm_id,
            "api_key": api_key,
            "message": "Agent registered successfully",
            "powershell_command": powershell_command,
            "powershell_script": powershell_script
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error registering agent: {str(e)}")

@router.post("/logs", response_model=Dict[str, Any])
async def create_log(
    log_data: dict = Body(..., description="Log data"),
    api_key: str = Query(..., description="API key for authentication")
):
    """
    Create a log entry from a Windows VM agent.

    This endpoint allows Windows VM agents to send logs to the central log storage system.
    """
    try:
        # Validate input parameters
        if not api_key:
            raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

        # Use the repository pattern with admin role to verify API key
        agent_repo = WindowsVMAgentRepository(user_id=1, user_role="admin")

        # Extract VM ID from log data if available, otherwise use a placeholder
        vm_id = log_data.get("details", {}).get("vm_info", {}).get("vm_identifier", "unknown")

        # Verify API key
        agent = agent_repo.verify_api_key(vm_id, api_key)

        if not agent:
            logger.warning(f"Invalid API key for VM: {vm_id}")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update last_seen timestamp
        agent_repo.update_last_seen(vm_id)

        # Import the log repository
        from db.repositories.logs import LogRepository

        # Create log repository with the agent's owner context
        log_repo = LogRepository(user_id=agent["owner_id"], user_role="user")

        # Extract log data
        message = log_data.get("message", "No message provided")
        level = log_data.get("level", "INFO")
        category = log_data.get("category", "windows_vm_agent")
        source = log_data.get("source", "windows_vm_agent")
        details = log_data.get("details", {})
        entity_type = log_data.get("entity_type", "vm")
        entity_id = log_data.get("entity_id", vm_id)
        timestamp = log_data.get("timestamp")

        # Add log entry
        log = log_repo.add_log(
            message=message,
            level=level,
            category=category,
            source=source,
            details=details,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=agent["owner_id"],
            owner_id=agent["owner_id"],
            timestamp=timestamp
        )

        if not log:
            raise HTTPException(status_code=500, detail="Failed to create log entry")

        return {"success": True, "message": "Log entry created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating log entry: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating log entry: {str(e)}")

@router.get("/status/{vm_id}", response_model=AgentInfoResponse)
async def get_agent_status(
    vm_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of a Windows VM agent.

    This endpoint returns the current status and information about a Windows VM agent.
    Uses Row-Level Security to ensure users can only see their own agents.
    """
    logger.info(f"Getting agent status for VM: {vm_id}")

    # Use the repository pattern with the current user's context
    agent_repo = WindowsVMAgentRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get the agent
        agent = agent_repo.get_agent_by_vm_id(vm_id)

        if not agent:
            logger.warning(f"Agent not found for VM: {vm_id}")
            raise HTTPException(status_code=404, detail=f"Agent not found for VM: {vm_id}")

        # Return the agent information
        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting agent status: {str(e)}")

@router.get("/agents", response_model=Dict[str, Any])
async def get_agents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of Windows VM agents with pagination and filtering.
    Uses Row-Level Security to ensure users can only see their own agents.
    """
    logger.info(f"Getting agents with limit={limit}, offset={offset}, search={search}, status={status}")

    # Use the repository pattern with the current user's context
    agent_repo = WindowsVMAgentRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get agents with pagination and filtering
        result = agent_repo.get_agents(limit, offset, search, status)
        return result

    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting agents: {str(e)}")

@router.get("/test-register/{vm_id}", response_model=Dict[str, Any])
async def test_register_agent(
    vm_id: str,
    vm_name: Optional[str] = Query(None, description="The VM name"),
    current_user: dict = Depends(get_current_user)
):
    """
    Test endpoint for registering a Windows VM agent.
    This is for debugging purposes only.
    """
    logger.info(f"TEST: Registering agent for VM: {vm_id}, VM Name: {vm_name}, User: {current_user['id']}")

    # Check if the user is an admin
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can use this test endpoint")

    # First, check if the VM exists
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    # List all VMs for debugging
    logger.info("Listing all VMs in the database:")
    vms = vm_repo.get_all()
    for vm in vms:
        logger.info(f"VM: id={vm['id']}, vmid={vm['vmid']}, name={vm['name']}, owner_id={vm['owner_id']}")

    # Check VM ownership
    if not vm_repo.check_vm_ownership(vm_id, 2):  # Hardcoded to user ID 2 for testing
        logger.warning(f"User 2 does not own VM {vm_id}")
        raise HTTPException(status_code=403, detail="User 2 does not own this VM")

    # Generate API key
    api_key = generate_api_key()
    logger.info(f"Generated API key: {api_key}")

    # Register the agent
    agent_repo = WindowsVMAgentRepository(user_id=2, user_role="user")  # Hardcoded to user ID 2 for testing
    agent = agent_repo.register_agent(vm_id, api_key, vm_name or "Test VM", 2)

    if not agent:
        raise HTTPException(status_code=500, detail="Failed to register agent")

    logger.info(f"Successfully registered agent for VM ID: {vm_id}")
    return {
        "vm_id": vm_id,
        "api_key": api_key,
        "message": "Agent registered successfully",
        "agent": agent
    }

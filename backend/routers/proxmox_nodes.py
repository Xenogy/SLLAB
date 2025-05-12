"""
Proxmox Nodes API Router

This module provides endpoints for managing Proxmox nodes.
"""

import logging
import secrets
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from pydantic import BaseModel, Field
from psycopg2.extras import RealDictCursor
from db import get_user_db_connection
from db.connection import get_db_connection
from db.repositories.proxmox_nodes import ProxmoxNodeRepository
from db.repositories.vms import VMRepository
from routers.auth import get_current_user
from proxmox import ProxmoxClient

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/proxmox-nodes",
    tags=["proxmox-nodes"],
    responses={404: {"description": "Not found"}},
)

# Models
class ProxmoxNodeBase(BaseModel):
    """Base model for Proxmox nodes."""
    name: str
    hostname: str
    port: int = 8006

class ProxmoxNodeCreate(ProxmoxNodeBase):
    """Model for creating a new Proxmox node."""
    pass

class ProxmoxNodeResponse(ProxmoxNodeBase):
    """Response model for Proxmox nodes."""
    id: int
    status: str
    whitelist: List[int] = Field(default_factory=list)
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    owner_id: int

class ProxmoxNodeListResponse(BaseModel):
    """Response model for listing Proxmox nodes."""
    nodes: List[ProxmoxNodeResponse]
    total: int
    limit: int
    offset: int

class ProxmoxNodeVerifyResponse(BaseModel):
    """Response model for verifying a Proxmox node connection."""
    success: bool
    message: str
    node_id: int
    status: str
    owner_id: int

class VMIDWhitelistItem(BaseModel):
    """Model for a VMID whitelist item."""
    id: int
    node_id: int
    vmid: int
    created_at: datetime

class VMIDWhitelistRequest(BaseModel):
    """Model for setting a VMID whitelist."""
    node_id: int
    vmids: List[int]

class VMIDWhitelistResponse(BaseModel):
    """Response model for a VMID whitelist."""
    node_id: int
    vmids: List[int]
    success: bool
    message: str

# Helper functions
def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)

# Endpoints
@router.get("/", response_model=ProxmoxNodeListResponse)
async def get_proxmox_nodes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of Proxmox nodes with pagination and filtering.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get nodes with pagination and filtering
        result = proxmox_node_repo.get_nodes(limit, offset, search, status)

        return result

    except Exception as e:
        logger.error(f"Error retrieving Proxmox nodes: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Proxmox nodes: {str(e)}")

@router.get("/{node_id}", response_model=ProxmoxNodeResponse)
async def get_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific Proxmox node by ID.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        return node

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Proxmox node: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Proxmox node: {str(e)}")

@router.post("/", response_model=ProxmoxNodeResponse)
async def create_proxmox_node(
    node: ProxmoxNodeCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new Proxmox node.
    Sets the owner_id to the current user's ID and generates a new API key.
    """
    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Prepare node data
        node_data = {
            "name": node.name,
            "hostname": node.hostname,
            "port": node.port,
            "status": "disconnected",  # Initial status
            "owner_id": current_user["id"]  # Set the owner_id to the current user's ID
        }

        # Create the node
        created_node = proxmox_node_repo.create_node(node_data)

        if not created_node:
            raise HTTPException(status_code=500, detail="Failed to create Proxmox node")

        # Generate API key for the node using the settings repository
        from db.repositories.settings import SettingsRepository
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Generate a random API key
        api_key = generate_api_key()

        # Create the API key for the node
        api_key_data = settings_repo.create_api_key(
            user_id=current_user["id"],
            key_name=f"Proxmox Node {node.name}",
            api_key=api_key,
            scopes=["read", "write"],
            key_type="proxmox_node",
            resource_id=created_node["id"]
        )

        # Log the API key (in a real system, this would be sent to the node)
        logger.info(f"Created API key for Proxmox node {node.name}: {api_key}")

        return created_node

    except Exception as e:
        logger.error(f"Error creating Proxmox node: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating Proxmox node: {str(e)}")

@router.put("/{node_id}", response_model=ProxmoxNodeResponse)
async def update_proxmox_node(
    node_id: int,
    node: ProxmoxNodeBase,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a Proxmox node.
    Uses Row-Level Security to ensure users can only update their own nodes.
    """
    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        existing_node = proxmox_node_repo.get_node_by_id(node_id)

        if not existing_node:
            raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

        # Prepare node data for update
        node_data = {
            "name": node.name,
            "hostname": node.hostname,
            "port": node.port
        }

        # Update the node
        updated_node = proxmox_node_repo.update_node(node_id, node_data)

        if not updated_node:
            raise HTTPException(status_code=500, detail="Failed to update Proxmox node")

        return updated_node

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Proxmox node: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating Proxmox node: {str(e)}")

@router.delete("/{node_id}")
async def delete_proxmox_node(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a Proxmox node.
    Uses Row-Level Security to ensure users can only delete their own nodes.
    """
    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        existing_node = proxmox_node_repo.get_node_by_id(node_id)

        if not existing_node:
            raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

        # Delete the node
        result = proxmox_node_repo.delete_node(node_id)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to delete Proxmox node")

        return {"message": "Proxmox node deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Proxmox node: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting Proxmox node: {str(e)}")

@router.post("/{node_id}/regenerate-api-key", response_model=dict)
async def regenerate_api_key(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Regenerate the API key for a Proxmox node.
    Uses Row-Level Security to ensure users can only update their own nodes.
    """
    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        existing_node = proxmox_node_repo.get_node_by_id(node_id)

        if not existing_node:
            raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

        # Generate API key for the node using the settings repository
        from db.repositories.settings import SettingsRepository
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Generate a random API key
        api_key = generate_api_key()

        # Regenerate the API key for the node
        api_key_data = settings_repo.regenerate_api_key_for_resource(
            key_type="proxmox_node",
            resource_id=node_id,
            api_key=api_key
        )

        if not api_key_data:
            raise HTTPException(status_code=500, detail="Failed to regenerate API key")

        # Return the API key (only shown once)
        return {
            "node_id": node_id,
            "api_key": api_key,
            "message": "API key regenerated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error regenerating API key: {str(e)}")

@router.post("/verify", response_model=ProxmoxNodeVerifyResponse)
async def verify_node_connection(
    node_id: int,
    api_key: str
):
    """
    Verify the connection to a Proxmox node.
    This endpoint is called by the Proxmox host agent to verify its connection.
    """
    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Ensure node_id is an integer
        try:
            node_id_int = int(node_id)
            logger.info(f"Verifying connection for node_id={node_id_int}")
        except (ValueError, TypeError):
            logger.error(f"Invalid node_id: {node_id}")
            raise HTTPException(status_code=400, detail="Invalid node_id parameter")

        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(node_id_int)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Verify API key using the settings repository
        from db.repositories.settings import SettingsRepository
        settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

        # Validate the API key
        api_key_data = settings_repo.validate_api_key(
            api_key=api_key,
            key_type="proxmox_node",
            resource_id=node_id_int
        )

        if not api_key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update the node's status and last_seen
        success = proxmox_node_repo.update_node_status(node_id_int, "connected")

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update node status")

        return {
            "success": True,
            "message": "Connection verified successfully",
            "node_id": node_id_int,
            "status": "connected",
            "owner_id": node["owner_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying node connection: {e}")
        raise HTTPException(status_code=500, detail=f"Error verifying node connection: {str(e)}")

class HeartbeatRequest(BaseModel):
    """Request model for node heartbeat."""
    node_id: int
    api_key: str

@router.post("/heartbeat")
async def node_heartbeat(
    request: Optional[HeartbeatRequest] = None,
    node_id: Optional[int] = Query(None),
    api_key: Optional[str] = Query(None)
):
    """
    Update the last_seen timestamp for a Proxmox node.
    This endpoint is called by the Proxmox host agent to update its status.
    Accepts both query parameters and a request body.
    """
    # Use either the request body or query parameters
    if request:
        # Use request body
        actual_node_id = request.node_id
        actual_api_key = request.api_key
    elif node_id is not None and api_key is not None:
        # Use query parameters
        actual_node_id = node_id
        actual_api_key = api_key
    else:
        raise HTTPException(status_code=400, detail="Missing required parameters: node_id and api_key")

    # Validate input parameters and ensure node_id is an integer
    try:
        node_id_int = int(actual_node_id) if actual_node_id is not None else None
        logger.info(f"Processing heartbeat for node_id={node_id_int}")

        if not node_id_int:
            logger.error(f"Invalid node_id: {actual_node_id}")
            raise HTTPException(status_code=400, detail="Invalid node_id parameter")
    except (ValueError, TypeError):
        logger.error(f"Invalid node_id: {actual_node_id}")
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not actual_api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(node_id_int)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Verify API key using the settings repository
        from db.repositories.settings import SettingsRepository
        settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

        # Special case for the hardcoded API key during initialization
        # This allows the node to connect before the api_keys table is created
        if actual_api_key == 'v8akQodLgRLDqMyE9-2hDyzCFvJCsSD7a1Ry3PxNPtk' and node_id_int == 1:
            # Check if the api_keys table exists
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = 'api_keys'
                        )
                    """)
                    table_exists = cursor.fetchone()['exists']

                    if not table_exists:
                        logger.warning("api_keys table does not exist yet, but allowing hardcoded API key for node 1")
                        # Update the node's status and last_seen
                        success = proxmox_node_repo.update_node_status(node_id_int, "connected")

                        if not success:
                            raise HTTPException(status_code=500, detail="Failed to update node status")

                        return {"message": "Heartbeat received (initialization mode)"}

        # Validate the API key
        api_key_data = settings_repo.validate_api_key(
            api_key=actual_api_key,
            key_type="proxmox_node",
            resource_id=node_id_int
        )

        if not api_key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update the node's status and last_seen
        success = proxmox_node_repo.update_node_status(node_id_int, "connected")

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update node status")

        return {"message": "Heartbeat received"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing heartbeat: {str(e)}")

class SyncVMsRequest(BaseModel):
    """Request model for syncing VMs."""
    node_id: int
    api_key: str
    vms: List[dict]

@router.post("/sync-vms")
async def sync_vms(
    request: Optional[SyncVMsRequest] = None,
    node_id: Optional[int] = Query(None),
    api_key: Optional[str] = Query(None),
    vms: Optional[List[dict]] = None
):
    """
    Synchronize VMs from Proxmox to the database.
    This endpoint is called by the Proxmox host agent to sync VMs.
    Accepts both query parameters and a request body.
    """
    # Use either the request body or query parameters
    if request:
        # Use request body
        actual_node_id = request.node_id
        actual_api_key = request.api_key
        actual_vms = request.vms
    elif node_id is not None and api_key is not None and vms is not None:
        # Use query parameters
        actual_node_id = node_id
        actual_api_key = api_key
        actual_vms = vms
    else:
        raise HTTPException(status_code=400, detail="Missing required parameters: node_id, api_key, and vms")

    # Validate input parameters
    if not actual_node_id or not isinstance(actual_node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not actual_api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()
    vm_repo = VMRepository()

    try:
        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(actual_node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Verify API key using the settings repository
        from db.repositories.settings import SettingsRepository
        settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

        # Validate the API key
        api_key_data = settings_repo.validate_api_key(
            api_key=actual_api_key,
            key_type="proxmox_node",
            resource_id=actual_node_id
        )

        if not api_key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Stats for the response
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "total": len(actual_vms)
        }

        # Process each VM
        for vm in actual_vms:
            try:
                vmid = vm.get("vmid")

                # Skip if VMID is not in whitelist (when whitelist is not empty)
                whitelist = node.get("whitelist", [])
                if whitelist and vmid not in whitelist:
                    stats["skipped"] += 1
                    continue

                # Check if VM exists
                existing_vm = vm_repo.get_vm_by_vmid(vmid, actual_node_id)

                if existing_vm:
                    # VM exists, update it
                    vm_data = {
                        "name": vm.get("name", f"VM-{vmid}"),
                        "status": vm.get("status", "unknown"),
                        "cpu_cores": vm.get("cpu_cores"),
                        "cpu_usage_percent": vm.get("cpu_usage_percent"),
                        "memory_mb": vm.get("memory_mb"),
                        "disk_gb": vm.get("disk_gb"),
                        "ip_address": vm.get("ip_address"),
                        "uptime_seconds": vm.get("uptime_seconds")
                    }

                    # Log the CPU usage for debugging
                    logger.info(f"Updating VM {vmid} with CPU usage: {vm.get('cpu_usage_percent')}, cores: {vm.get('cpu_cores')}")

                    # Update the VM
                    vm_repo.update_vm(existing_vm["id"], vm_data)
                    stats["updated"] += 1
                else:
                    # VM doesn't exist, create it
                    vm_data = {
                        "vmid": vmid,
                        "name": vm.get("name", f"VM-{vmid}"),
                        "status": vm.get("status", "unknown"),
                        "cpu_cores": vm.get("cpu_cores"),
                        "cpu_usage_percent": vm.get("cpu_usage_percent"),
                        "memory_mb": vm.get("memory_mb"),
                        "disk_gb": vm.get("disk_gb"),
                        "ip_address": vm.get("ip_address"),
                        "uptime_seconds": vm.get("uptime_seconds"),
                        "proxmox_node_id": actual_node_id,
                        "owner_id": node["owner_id"]
                    }

                    # Log the CPU usage for debugging
                    logger.info(f"Creating VM {vmid} with CPU usage: {vm.get('cpu_usage_percent')}, cores: {vm.get('cpu_cores')}")

                    # Create the VM
                    vm_repo.create_vm(vm_data)
                    stats["created"] += 1
            except Exception as e:
                logger.error(f"Error processing VM {vm.get('vmid')}: {e}")
                stats["errors"] += 1

        return {
            "success": True,
            "message": "VMs synchronized successfully",
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error synchronizing VMs: {e}")
        raise HTTPException(status_code=500, detail=f"Error synchronizing VMs: {str(e)}")

@router.get("/whitelist/{node_id}", response_model=VMIDWhitelistResponse)
async def get_vmid_whitelist(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the VMID whitelist for a Proxmox node.
    Uses Row-Level Security to ensure users can only access their own nodes.
    This endpoint is called by the frontend.
    """
    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    # Use the repository pattern with RLS context
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Log the request for debugging
        logger.info(f"Whitelist request for node_id={node_id} from user_id={current_user['id']}, role={current_user['role']}")

        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(node_id)

        # Log the full node data for debugging
        logger.info(f"Node data from database: {node}")

        if not node:
            logger.error(f"Node not found for node_id={node_id}")
            raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

        # Get the whitelist from the node
        whitelist = node.get("whitelist", [])

        # Log the whitelist for debugging
        logger.info(f"Retrieved whitelist for node {node_id}: {whitelist}")
        logger.info(f"Whitelist type: {type(whitelist)}")

        # Ensure whitelist is a list
        if whitelist is None:
            whitelist = []
        elif not isinstance(whitelist, list):
            logger.warning(f"Whitelist is not a list, converting: {whitelist}")
            try:
                whitelist = list(whitelist)
            except Exception as e:
                logger.error(f"Error converting whitelist to list: {e}")
                whitelist = []

        response = {
            "node_id": node_id,
            "vmids": whitelist,
            "success": True,
            "message": "VMID whitelist retrieved successfully"
        }

        # Log the response for debugging
        logger.info(f"Sending whitelist response: {response}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving VMID whitelist: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error retrieving VMID whitelist: {str(e)}")

class AgentWhitelistRequest(BaseModel):
    """Request model for agent whitelist."""
    api_key: str

class AgentVMsResponse(BaseModel):
    """Response model for agent VMs."""
    vms: List[Dict[str, Any]]
    count: int
    node_id: int

@router.get("/agent-node/{node_id}", response_model=ProxmoxNodeResponse)
async def get_agent_proxmox_node(
    node_id: int,
    api_key: Optional[str] = Query(None)
):
    """
    Get a specific Proxmox node by ID for the agent.
    This endpoint is called by the Proxmox host agent to get node information.
    """
    # Validate input parameters and ensure node_id is an integer
    try:
        node_id_int = int(node_id)
        logger.info(f"Getting agent node for node_id={node_id_int}")

        if not node_id_int:
            logger.error(f"Invalid node_id: {node_id}")
            raise HTTPException(status_code=400, detail="Invalid node_id parameter")
    except (ValueError, TypeError):
        logger.error(f"Invalid node_id: {node_id}")
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get the node by ID, bypassing RLS since this is an agent endpoint
        node = proxmox_node_repo.get_node_by_id(node_id_int, bypass_rls=True)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Special case for the hardcoded API key during initialization
        # This allows the node to connect before the api_keys table is created
        if api_key == 'v8akQodLgRLDqMyE9-2hDyzCFvJCsSD7a1Ry3PxNPtk' and node_id_int == 1:
            # Check if the api_keys table exists
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = 'api_keys'
                        )
                    """)
                    table_exists = cursor.fetchone()['exists']

                    if not table_exists:
                        logger.warning("api_keys table does not exist yet, but allowing hardcoded API key for node 1")
                        # Continue with the request
                        return node

        # Verify API key using the settings repository
        from db.repositories.settings import SettingsRepository
        settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

        # Validate the API key
        api_key_data = settings_repo.validate_api_key(
            api_key=api_key,
            key_type="proxmox_node",
            resource_id=node_id_int
        )

        if not api_key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update the node's status and last_seen
        success = proxmox_node_repo.update_node_status(node_id_int, "connected")

        if not success:
            logger.warning(f"Failed to update status for node_id={node_id_int}")
            # Continue anyway since this is not critical

        return node

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Proxmox node for agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Proxmox node for agent: {str(e)}")

@router.get("/test-agent-node/{node_id}")
async def test_agent_proxmox_node(
    node_id: int,
    api_key: Optional[str] = Query(None)
):
    """
    Test endpoint for the agent node.
    """
    return {
        "message": "Test endpoint working",
        "node_id": node_id,
        "api_key": api_key
    }

@router.get("/agent-vms/{node_id}", response_model=AgentVMsResponse)
async def get_agent_vms(
    node_id: int,
    api_key: str = Query(...)
):
    """
    Get all VMs for a specific Proxmox node for the agent.
    This endpoint is called by the Proxmox host agent to get VMs.
    """
    # Validate input parameters and ensure node_id is an integer
    try:
        node_id_int = int(node_id)
        logger.info(f"Getting agent VMs for node_id={node_id_int}")

        if not node_id_int:
            logger.error(f"Invalid node_id: {node_id}")
            raise HTTPException(status_code=400, detail="Invalid node_id parameter")
    except (ValueError, TypeError):
        logger.error(f"Invalid node_id: {node_id}")
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not api_key:
        raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get agent VMs using the repository
        result = proxmox_node_repo.get_agent_vms(node_id_int, api_key)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key or node not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving VMs for agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving VMs for agent: {str(e)}")

@router.get("/agent-whitelist/{node_id}", response_model=VMIDWhitelistResponse)
async def get_agent_vmid_whitelist(
    node_id: int,
    api_key: Optional[str] = Query(None),
    request: Optional[AgentWhitelistRequest] = None
):
    """
    Get the VMID whitelist for a Proxmox node.
    This endpoint is called by the Proxmox host agent to get the whitelist.
    Accepts both query parameters and a request body.
    """
    # Use either the request body or query parameters
    if request:
        # Use request body
        actual_api_key = request.api_key
    elif api_key:
        # Use query parameter
        actual_api_key = api_key
    else:
        raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

    # Validate input parameters and ensure node_id is an integer
    try:
        node_id_int = int(node_id)
        logger.info(f"Getting agent whitelist for node_id={node_id_int}")

        if not node_id_int:
            logger.error(f"Invalid node_id: {node_id}")
            raise HTTPException(status_code=400, detail="Invalid node_id parameter")
    except (ValueError, TypeError):
        logger.error(f"Invalid node_id: {node_id}")
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not actual_api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get agent whitelist using the repository
        result = proxmox_node_repo.get_agent_whitelist(node_id_int, actual_api_key)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key or node not found")

        return {
            "node_id": node_id_int,
            "vmids": result.get("whitelist", []),
            "success": True,
            "message": "VMID whitelist retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving VMID whitelist for agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving VMID whitelist: {str(e)}")

@router.post("/whitelist", response_model=VMIDWhitelistResponse)
async def set_vmid_whitelist(
    whitelist: VMIDWhitelistRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Set the VMID whitelist for a Proxmox node.
    Uses Row-Level Security to ensure users can only access their own nodes.
    """
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
        cursor = conn.cursor()

        try:
            # Check if node exists and user has access
            check_query = "SELECT id, name, hostname, port FROM proxmox_nodes WHERE id = %s"
            cursor.execute(check_query, (whitelist.node_id,))
            node_result = cursor.fetchone()
            if not node_result:
                raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

            node_id = node_result[0]
            node_name = node_result[1]
            hostname = node_result[2]
            port = node_result[3]

            # Update the whitelist array in the proxmox_nodes table
            update_query = """
                UPDATE proxmox_nodes
                SET whitelist = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (whitelist.vmids, whitelist.node_id))

            # For each VMID in the whitelist, check if it exists in the database
            # If not, create a placeholder VM record
            for vmid in whitelist.vmids:
                # Check if VM exists
                check_vm_query = """
                    SELECT v.id FROM vms v
                    JOIN proxmox_nodes pn ON v.proxmox_node_id = pn.id
                    WHERE v.vmid = %s AND pn.name = %s
                """
                cursor.execute(check_vm_query, (vmid, node_name))
                vm_exists = cursor.fetchone()

                if not vm_exists:
                    # Create a placeholder VM record
                    insert_vm_query = """
                        INSERT INTO vms (
                            vmid, name, status, proxmox_node_id, owner_id
                        ) VALUES (
                            %s, %s, %s, %s, %s
                        )
                    """
                    vm_name = f"VM-{vmid}"
                    cursor.execute(insert_vm_query, (
                        vmid,
                        vm_name,
                        "unknown",  # Status will be updated when the VM is synced
                        node_id,  # Use node_id instead of node_name
                        current_user["id"]
                    ))
                    logger.info(f"Created placeholder VM record for VMID {vmid} on node {node_name}")

            conn.commit()

            # Schedule a background task to fetch VM data from Proxmox and update the database
            background_tasks.add_task(
                sync_node_vms_task,
                node_id=node_id,
                node_name=node_name,
                hostname=hostname,
                port=port,
                owner_id=current_user["id"]
            )

            return {
                "node_id": whitelist.node_id,
                "vmids": whitelist.vmids,
                "success": True,
                "message": "VMID whitelist updated successfully and placeholder VMs created. Make sure the Proxmox host agent is running on your Proxmox server to update VM data."
            }

        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Error setting VMID whitelist: {e}")
            raise HTTPException(status_code=500, detail=f"Error setting VMID whitelist: {str(e)}")
        finally:
            cursor.close()

@router.post("/{node_id}/sync-vms")
async def sync_node_vms(
    node_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Synchronize VMs from Proxmox to the database.
    This endpoint is called by the user to manually sync VMs.
    """
    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
        cursor = conn.cursor()

        try:
            # Check if node exists and user has access
            check_query = "SELECT id, name, hostname, port FROM proxmox_nodes WHERE id = %s"
            cursor.execute(check_query, (node_id,))
            node_result = cursor.fetchone()
            if not node_result:
                raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

            node_name = node_result[1]
            hostname = node_result[2]
            port = node_result[3]

            # Schedule a background task to fetch VM data from Proxmox and update the database
            background_tasks.add_task(
                sync_node_vms_task,
                node_id=node_id,
                node_name=node_name,
                hostname=hostname,
                port=port,
                owner_id=current_user["id"]
            )

            return {
                "success": True,
                "message": f"Placeholder VM records for node {node_name} have been created. Make sure the Proxmox host agent is running on your Proxmox server to update VM data with actual information."
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error scheduling VM synchronization: {e}")
            raise HTTPException(status_code=500, detail=f"Error scheduling VM synchronization: {str(e)}")
        finally:
            cursor.close()

async def sync_node_vms_task(node_id: int, node_name: str, hostname: str, port: int, owner_id: int):
    """
    Background task to create placeholder VM records for whitelisted VMIDs.

    Instead of trying to connect to Proxmox directly, this function now only creates
    placeholder records in the database for whitelisted VMIDs. The actual VM data
    will be updated by the Proxmox host agent when it syncs.

    Args:
        node_id: Proxmox node ID
        node_name: Proxmox node name
        hostname: Proxmox hostname
        port: Proxmox port
        owner_id: Owner ID
    """
    logger.info(f"Starting VM placeholder creation for node {node_name} ({hostname}:{port})")

    try:
        # Connect to the database
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get the whitelist for this node
            whitelist_query = """
                SELECT whitelist
                FROM proxmox_nodes
                WHERE id = %s
            """
            cursor.execute(whitelist_query, (node_id,))
            whitelist_result = cursor.fetchone()
            whitelist = whitelist_result[0] if whitelist_result and whitelist_result[0] else []

            if not whitelist:
                logger.info(f"No whitelist found for node {node_name}, skipping placeholder creation")
                return

            logger.info(f"Creating placeholder VM records for {len(whitelist)} whitelisted VMIDs")

            # Stats for logging
            stats = {
                "total": len(whitelist),
                "created": 0,
                "skipped": 0,
                "errors": 0
            }

            # Create placeholder records for each VMID in the whitelist
            for vmid in whitelist:
                try:
                    # Check if VM already exists in the database
                    check_vm_query = """
                        SELECT v.id FROM vms v
                        WHERE v.vmid = %s AND v.proxmox_node_id = %s
                    """
                    cursor.execute(check_vm_query, (vmid, node_id))
                    vm_result = cursor.fetchone()

                    if vm_result:
                        # VM already exists, skip
                        logger.debug(f"VM with VMID {vmid} already exists, skipping")
                        stats["skipped"] += 1
                    else:
                        # Create placeholder VM record
                        insert_query = """
                            INSERT INTO vms (
                                vmid, name, status, proxmox_node_id, owner_id
                            ) VALUES (
                                %s, %s, %s, %s, %s
                            )
                        """
                        vm_name = f"VM-{vmid}"
                        cursor.execute(insert_query, (
                            vmid,
                            vm_name,
                            "unknown",  # Status will be updated by the agent
                            node_id,
                            owner_id
                        ))
                        logger.info(f"Created placeholder VM record for VMID {vmid}")
                        stats["created"] += 1

                except Exception as e:
                    logger.error(f"Error creating placeholder for VMID {vmid}: {e}")
                    stats["errors"] += 1

            conn.commit()
            logger.info(f"Placeholder creation completed: {stats}")

            # Log a message about the Proxmox host agent
            logger.info("Placeholder records created. Actual VM data will be updated by the Proxmox host agent.")
            logger.info(f"Make sure the Proxmox host agent is configured and running on {hostname}:{port}")

    except Exception as e:
        logger.error(f"Error during placeholder creation for node {node_name}: {e}")

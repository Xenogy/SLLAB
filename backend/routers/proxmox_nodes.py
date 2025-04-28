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
    api_key: str
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
        # Generate API key
        api_key = generate_api_key()

        # Prepare node data
        node_data = {
            "name": node.name,
            "hostname": node.hostname,
            "port": node.port,
            "status": "disconnected",  # Initial status
            "api_key": api_key,
            "owner_id": current_user["id"]  # Set the owner_id to the current user's ID
        }

        # Create the node
        created_node = proxmox_node_repo.create_node(node_data)

        if not created_node:
            raise HTTPException(status_code=500, detail="Failed to create Proxmox node")

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

@router.post("/{node_id}/regenerate-api-key", response_model=ProxmoxNodeResponse)
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

        # Generate new API key
        api_key = generate_api_key()

        # Prepare node data for update
        node_data = {
            "api_key": api_key
        }

        # Update the node
        updated_node = proxmox_node_repo.update_node(node_id, node_data)

        if not updated_node:
            raise HTTPException(status_code=500, detail="Failed to regenerate API key")

        return updated_node

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
        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Verify API key
        if api_key != node["api_key"]:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update the node's status and last_seen
        success = proxmox_node_repo.update_node_status(node_id, "connected")

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update node status")

        return {
            "success": True,
            "message": "Connection verified successfully",
            "node_id": node_id,
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

    # Validate input parameters
    if not actual_node_id or not isinstance(actual_node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not actual_api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(actual_node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Verify API key
        if actual_api_key != node["api_key"]:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update the node's status and last_seen
        success = proxmox_node_repo.update_node_status(actual_node_id, "connected")

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

        # Verify API key
        if actual_api_key != node["api_key"]:
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
                        "memory_mb": vm.get("memory_mb"),
                        "disk_gb": vm.get("disk_gb"),
                        "ip_address": vm.get("ip_address")
                    }

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
                        "memory_mb": vm.get("memory_mb"),
                        "disk_gb": vm.get("disk_gb"),
                        "ip_address": vm.get("ip_address"),
                        "proxmox_node_id": actual_node_id,
                        "owner_id": node["owner_id"]
                    }

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
        # Get the node by ID
        node = proxmox_node_repo.get_node_by_id(node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

        # Get the whitelist from the node
        whitelist = node.get("whitelist", [])

        return {
            "node_id": node_id,
            "vmids": whitelist,
            "success": True,
            "message": "VMID whitelist retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving VMID whitelist: {e}")
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
    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get the node by ID, bypassing RLS since this is an agent endpoint
        node = proxmox_node_repo.get_node_by_id(node_id, bypass_rls=True)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found")

        # Verify API key
        if api_key != node["api_key"]:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update the node's status and last_seen
        proxmox_node_repo.update_node_status(node_id, "connected")

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
    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not api_key:
        raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get agent VMs using the repository
        result = proxmox_node_repo.get_agent_vms(node_id, api_key)

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

    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not actual_api_key:
        raise HTTPException(status_code=400, detail="Invalid api_key parameter")

    # Use the repository pattern
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Get agent whitelist using the repository
        result = proxmox_node_repo.get_agent_whitelist(node_id, actual_api_key)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key or node not found")

        return {
            "node_id": node_id,
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
                "message": "VMID whitelist updated successfully and placeholder VMs created. VM data will be updated in the background."
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
                "message": f"VM synchronization for node {node_name} has been scheduled. VM data will be updated in the background."
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
    Background task to fetch VM data from Proxmox and update the database.

    Args:
        node_id: Proxmox node ID
        node_name: Proxmox node name
        hostname: Proxmox hostname
        port: Proxmox port
        owner_id: Owner ID
    """
    logger.info(f"Starting VM synchronization for node {node_name} ({hostname}:{port})")

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
                logger.info(f"No whitelist found for node {node_name}, skipping synchronization")
                return

            # We don't store credentials in the database anymore
            # The Proxmox host agent should use its own credentials from the .env file
            # For the backend sync, we'll use dummy credentials since we can't actually connect
            username = "dummy_user"
            password = "dummy_password"
            realm = "pam"

            logger.info("Using dummy credentials for Proxmox connection attempt")
            logger.info("Note: Actual synchronization should be done by the Proxmox host agent")

            # Create a Proxmox client
            client = ProxmoxClient(hostname=hostname, port=port, verify_ssl=False)

            # Login to Proxmox
            logger.info(f"Logging in to Proxmox node {node_name} as {username}@{realm}")
            login_success = await client.login(username=username, password=password, realm=realm)
            if not login_success:
                logger.error(f"Failed to login to Proxmox node {node_name}")
                return

            # Get nodes from Proxmox
            proxmox_nodes = await client.get_nodes()

            # Get VMs from all Proxmox nodes
            vms = []
            for proxmox_node in proxmox_nodes:
                proxmox_node_name = proxmox_node.get("node")
                if proxmox_node_name:
                    logger.info(f"Getting VMs from Proxmox node {proxmox_node_name}")
                    node_vms = await client.get_vms(node=proxmox_node_name)
                    vms.extend(node_vms)

            # Filter VMs by whitelist
            whitelisted_vms = [vm for vm in vms if vm.get("vmid") in whitelist]

            # Stats for logging
            stats = {
                "total": len(whitelisted_vms),
                "updated": 0,
                "errors": 0
            }

            # Update each VM in the database
            for vm in whitelisted_vms:
                try:
                    vmid = vm.get("vmid")

                    # Map Proxmox status to our status format
                    status = "unknown"
                    if "status" in vm:
                        if vm["status"] == "running":
                            status = "running"
                        elif vm["status"] == "stopped":
                            status = "stopped"

                    # Get VM details
                    name = vm.get("name", f"VM-{vmid}")
                    cpu_cores = vm.get("cpu_cores")
                    memory_mb = vm.get("memory_mb")
                    disk_gb = vm.get("disk_gb")
                    ip_address = vm.get("ip_address")

                    # Check if VM exists in the database
                    check_vm_query = """
                        SELECT v.id FROM vms v
                        JOIN proxmox_nodes pn ON v.proxmox_node_id = pn.id
                        WHERE v.vmid = %s AND pn.name = %s
                    """
                    cursor.execute(check_vm_query, (vmid, node_name))
                    vm_result = cursor.fetchone()

                    if vm_result:
                        # Update existing VM
                        vm_id = vm_result[0]
                        update_query = """
                            UPDATE vms
                            SET
                                name = %s,
                                status = %s,
                                cpu_cores = %s,
                                memory_mb = %s,
                                disk_gb = %s,
                                ip_address = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """
                        cursor.execute(update_query, (
                            name,
                            status,
                            cpu_cores,
                            memory_mb,
                            disk_gb,
                            ip_address,
                            vm_id
                        ))
                    else:
                        # Create new VM
                        insert_query = """
                            INSERT INTO vms (
                                vmid, name, status, cpu_cores, memory_mb,
                                disk_gb, ip_address, proxmox_node_id, owner_id
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        cursor.execute(insert_query, (
                            vmid,
                            name,
                            status,
                            cpu_cores,
                            memory_mb,
                            disk_gb,
                            ip_address,
                            node_id,  # Use node_id instead of node_name
                            owner_id
                        ))

                    stats["updated"] += 1

                except Exception as e:
                    logger.error(f"Error updating VM {vm.get('vmid')}: {e}")
                    stats["errors"] += 1

            conn.commit()
            logger.info(f"VM synchronization completed for node {node_name}: {stats}")

    except Exception as e:
        logger.error(f"Error during VM synchronization for node {node_name}: {e}")

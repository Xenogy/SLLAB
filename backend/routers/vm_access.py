"""
VM Access Control API Router

This module provides endpoints for managing VM access control.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from db.repositories.vms import VMRepository
from db.repositories.proxmox_nodes import ProxmoxNodeRepository
from routers.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/vm-access",
    tags=["vm-access"],
    responses={404: {"description": "Not found"}},
)

# Models
class VMAccessVM(BaseModel):
    """Model for a VM with access information."""
    id: int
    vmid: int
    name: str
    status: str
    proxmox_node_id: int
    proxmox_node_name: Optional[str] = None
    owner_id: int

class VMAccessResponse(BaseModel):
    """Response model for VM access operations."""
    success: bool
    message: str

class UserVMsResponse(BaseModel):
    """Response model for listing VMs a user has access to."""
    user_id: int
    username: str
    vms: List[VMAccessVM]

# Endpoints
@router.get("/user/{user_id}/vms", response_model=UserVMsResponse)
async def get_user_vms(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all VMs that a user owns.
    Uses Row-Level Security to ensure users can only see their own VMs or admin can see all.
    """
    # Check if current user is admin or the requested user
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this user's VMs"
        )

    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get user's VMs
        result = vm_repo.get_vms_with_proxmox_node_name(limit=100, offset=0)
        vms = result["vms"]

        # Get username
        username = current_user["username"] if current_user["id"] == user_id else None
        if not username:
            # Get username from database
            query = "SELECT username FROM users WHERE id = %s"
            user_result = vm_repo.execute_query_single(query, (user_id,))
            if user_result:
                username = user_result["username"]
            else:
                username = f"User {user_id}"

        return {
            "user_id": user_id,
            "username": username,
            "vms": vms
        }
    except Exception as e:
        logger.error(f"Error retrieving user VMs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user VMs: {str(e)}"
        )

@router.get("/node/{node_id}/whitelist", response_model=List[int])
async def get_node_whitelist(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the whitelist for a specific Proxmox node.
    Uses Row-Level Security to ensure users can only see their own nodes or admin can see all.
    """
    # Use the repository pattern with RLS context
    node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        node = node_repo.get_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=404,
                detail="Proxmox node not found or you don't have access"
            )

        # Get whitelist
        whitelist = node.get("whitelist", [])

        return whitelist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving node whitelist: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving node whitelist: {str(e)}"
        )

@router.get("/node/{node_id}/whitelist/agent", response_model=List[int])
async def get_node_whitelist_for_agent(
    node_id: int,
    api_key: str = Query(..., description="API key for authentication")
):
    """
    Get the whitelist for a specific Proxmox node.
    This endpoint is for the Proxmox agent and uses API key authentication.
    """
    # Use the repository pattern without RLS context
    node_repo = ProxmoxNodeRepository()

    try:
        # Get agent whitelist using the repository
        result = node_repo.get_agent_whitelist(node_id, api_key)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid API key or node not found")

        # Return just the whitelist array
        return result.get("whitelist", [])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving node whitelist for agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving node whitelist for agent: {str(e)}"
        )

@router.post("/node/{node_id}/whitelist", response_model=VMAccessResponse)
async def set_node_whitelist(
    node_id: int,
    vmids: List[int],
    current_user: dict = Depends(get_current_user)
):
    """
    Set the whitelist for a specific Proxmox node.
    Uses Row-Level Security to ensure users can only update their own nodes or admin can update all.
    """
    # Use the repository pattern with RLS context
    node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        node = node_repo.get_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=404,
                detail="Proxmox node not found or you don't have access"
            )

        # Set whitelist
        update_query = """
            UPDATE proxmox_nodes
            SET whitelist = %s
            WHERE id = %s
        """
        result = node_repo.execute_command(update_query, (vmids, node_id))

        if result <= 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to set node whitelist"
            )

        return {
            "success": True,
            "message": "Node whitelist set successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting node whitelist: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error setting node whitelist: {str(e)}"
        )

@router.post("/node/{node_id}/whitelist/add/{vmid}", response_model=VMAccessResponse)
async def add_to_node_whitelist(
    node_id: int,
    vmid: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a VMID to a node's whitelist.
    Uses Row-Level Security to ensure users can only update their own nodes or admin can update all.
    """
    # Use the repository pattern with RLS context
    node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        node = node_repo.get_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=404,
                detail="Proxmox node not found or you don't have access"
            )

        # Get current whitelist
        current_whitelist = node.get("whitelist", [])

        # Check if VMID is already in whitelist
        if vmid in current_whitelist:
            return {
                "success": True,
                "message": f"VMID {vmid} is already in the whitelist"
            }

        # Add to whitelist
        new_whitelist = current_whitelist + [vmid]

        # Update whitelist
        update_query = """
            UPDATE proxmox_nodes
            SET whitelist = %s
            WHERE id = %s
        """
        result = node_repo.execute_command(update_query, (new_whitelist, node_id))

        if result <= 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to add to node whitelist"
            )

        return {
            "success": True,
            "message": f"VMID {vmid} added to node whitelist successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to node whitelist: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding to node whitelist: {str(e)}"
        )

@router.post("/node/{node_id}/whitelist/remove/{vmid}", response_model=VMAccessResponse)
async def remove_from_node_whitelist(
    node_id: int,
    vmid: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a VMID from a node's whitelist.
    Uses Row-Level Security to ensure users can only update their own nodes or admin can update all.
    """
    # Use the repository pattern with RLS context
    node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if node exists and user has access
        node = node_repo.get_node_by_id(node_id)
        if not node:
            raise HTTPException(
                status_code=404,
                detail="Proxmox node not found or you don't have access"
            )

        # Get current whitelist
        current_whitelist = node.get("whitelist", [])

        # Check if VMID is in whitelist
        if vmid not in current_whitelist:
            return {
                "success": True,
                "message": f"VMID {vmid} is not in the whitelist"
            }

        # Remove from whitelist
        new_whitelist = [v for v in current_whitelist if v != vmid]

        # Update whitelist
        update_query = """
            UPDATE proxmox_nodes
            SET whitelist = %s
            WHERE id = %s
        """
        result = node_repo.execute_command(update_query, (new_whitelist, node_id))

        if result <= 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to remove from node whitelist"
            )

        return {
            "success": True,
            "message": f"VMID {vmid} removed from node whitelist successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from node whitelist: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error removing from node whitelist: {str(e)}"
        )

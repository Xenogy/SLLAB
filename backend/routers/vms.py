"""
Virtual Machines API router.
"""

import logging
import httpx
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from db import get_db_connection, get_user_db_connection
from db.rls_context import rls_context
from db.repositories.vms import VMRepository
from db.repositories.proxmox_nodes import ProxmoxNodeRepository
from routers.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/vms",
    tags=["vms"],
    responses={404: {"description": "Not found"}},
)

# VM models
class VMBase(BaseModel):
    vmid: int
    name: str
    ip_address: Optional[str] = None
    status: str = "stopped"
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    disk_gb: Optional[int] = None
    proxmox_node_id: Optional[int] = None
    proxmox_node: Optional[str] = None  # For backward compatibility
    template_id: Optional[int] = None
    notes: Optional[str] = None

class VMCreate(VMBase):
    pass

class VMResponse(VMBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

class VMListResponse(BaseModel):
    vms: List[VMResponse]
    total: int
    limit: int
    offset: int

@router.get("/", response_model=VMListResponse)
async def get_vms(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of virtual machines with pagination and filtering.
    Uses Row-Level Security to ensure users can only see their own VMs.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get VMs with Proxmox node names
        result = vm_repo.get_vms_with_proxmox_node_name(limit, offset, search, status)

        return result

    except Exception as e:
        logger.error(f"Error retrieving VMs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving VMs: {str(e)}")

@router.get("/proxmox", response_model=List[VMResponse])
async def get_proxmox_vms(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all VMs from all connected Proxmox nodes.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get all connected Proxmox nodes owned by the user
        nodes = proxmox_node_repo.get_nodes_by_status("connected")

        if not nodes:
            return []

        # Get all VMs from all nodes
        all_vms = []
        for node in nodes["nodes"]:
            node_id = node["id"]

            try:
                # Get the whitelist for this node
                whitelist = node.get("whitelist", [])

                # Get VMs for this node
                node_vms = vm_repo.get_vms_by_proxmox_node(node_id, whitelist)

                # Add node name to VMs
                for vm in node_vms:
                    vm["proxmox_node"] = node["name"]

                all_vms.extend(node_vms)

            except Exception as e:
                logger.error(f"Error getting VMs from Proxmox node {node_id}: {e}")
                # Continue with the next node

        return all_vms

    except Exception as e:
        logger.error(f"Error retrieving Proxmox VMs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Proxmox VMs: {str(e)}")

@router.get("/proxmox/{node_id}", response_model=List[VMResponse])
async def get_proxmox_node_vms(
    node_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all VMs from a specific Proxmox node.
    Uses Row-Level Security to ensure users can only see their own nodes.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])
    proxmox_node_repo = ProxmoxNodeRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get the Proxmox node
        node = proxmox_node_repo.get_node_by_id(node_id)

        if not node:
            raise HTTPException(status_code=404, detail="Proxmox node not found or you don't have access")

        # Get the whitelist for this node
        whitelist = node.get("whitelist", [])

        # Get VMs for this node
        vms = vm_repo.get_vms_by_proxmox_node(node_id, whitelist)

        # Add node name to VMs
        for vm in vms:
            vm["proxmox_node"] = node["name"]

        return vms

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Proxmox node VMs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving Proxmox node VMs: {str(e)}")

@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific virtual machine by ID.
    Uses Row-Level Security to ensure users can only see their own VMs.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get the VM with Proxmox node name
        vm = vm_repo.get_vm_with_proxmox_node_name(vm_id)

        if not vm:
            raise HTTPException(status_code=404, detail="VM not found")

        return vm

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving VM: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving VM: {str(e)}")

@router.post("/", response_model=VMResponse)
async def create_vm(
    vm: VMCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new virtual machine.
    Sets the owner_id to the current user's ID.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Prepare VM data
        vm_data = {
            "vmid": vm.vmid,
            "name": vm.name,
            "ip_address": vm.ip_address,
            "status": vm.status,
            "cpu_cores": vm.cpu_cores,
            "memory_mb": vm.memory_mb,
            "disk_gb": vm.disk_gb,
            "proxmox_node_id": vm.proxmox_node_id,
            "template_id": vm.template_id,
            "notes": vm.notes,
            "owner_id": current_user["id"]  # Set the owner_id to the current user's ID
        }

        # Create the VM
        created_vm = vm_repo.create_vm(vm_data)

        if not created_vm:
            raise HTTPException(status_code=500, detail="Failed to create VM")

        return created_vm

    except Exception as e:
        logger.error(f"Error creating VM: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating VM: {str(e)}")

@router.put("/{vm_id}", response_model=VMResponse)
async def update_vm(
    vm_id: int,
    vm: VMBase,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a virtual machine.
    Uses Row-Level Security to ensure users can only update their own VMs.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if VM exists and user has access
        existing_vm = vm_repo.get_vm_by_id(vm_id)

        if not existing_vm:
            raise HTTPException(status_code=404, detail="VM not found or you don't have access")

        # Prepare VM data
        vm_data = {
            "vmid": vm.vmid,
            "name": vm.name,
            "ip_address": vm.ip_address,
            "status": vm.status,
            "cpu_cores": vm.cpu_cores,
            "memory_mb": vm.memory_mb,
            "disk_gb": vm.disk_gb,
            "proxmox_node_id": vm.proxmox_node_id,
            "template_id": vm.template_id,
            "notes": vm.notes
        }

        # Update the VM
        updated_vm = vm_repo.update_vm(vm_id, vm_data)

        if not updated_vm:
            raise HTTPException(status_code=500, detail="Failed to update VM")

        return updated_vm

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating VM: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating VM: {str(e)}")

@router.delete("/{vm_id}")
async def delete_vm(
    vm_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a virtual machine.
    Uses Row-Level Security to ensure users can only delete their own VMs.
    """
    # Use the repository pattern with RLS context
    vm_repo = VMRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if VM exists and user has access
        existing_vm = vm_repo.get_vm_by_id(vm_id)

        if not existing_vm:
            raise HTTPException(status_code=404, detail="VM not found or you don't have access")

        # Delete the VM
        success = vm_repo.delete_vm(vm_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete VM")

        return {"message": "VM deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting VM: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting VM: {str(e)}")

@router.put("/agent/{vm_id}", response_model=VMResponse)
async def update_vm_agent(
    vm_id: int,
    vm: VMBase,
    node_id: int = Query(..., description="The ID of the Proxmox node"),
    api_key: str = Query(..., description="API key for authentication")
):
    """
    Update a virtual machine from the Proxmox agent.
    Uses API key authentication instead of JWT token.
    """
    # Validate input parameters
    if not node_id or not isinstance(node_id, int):
        raise HTTPException(status_code=400, detail="Invalid node_id parameter")

    if not api_key:
        raise HTTPException(status_code=400, detail="Missing required parameter: api_key")

    # Use the repository pattern without RLS context
    vm_repo = VMRepository()
    proxmox_node_repo = ProxmoxNodeRepository()

    try:
        # Verify the node and API key
        # Use direct database connection to avoid caching issues
        import psycopg2
        import psycopg2.extras
        import os

        # Connect directly to the database using the postgres user to bypass RLS
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'postgres'),
            port=os.getenv('PG_PORT', '5432'),
            dbname='accountdb',  # Hardcode the database name
            user='postgres',  # Use postgres user to bypass RLS
            password='CHANGEME_ULTRASECURE'  # Use the actual postgres password
        )

        # Create a cursor
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Execute the query to verify the node and API key
        node_query = """
            SELECT id, api_key
            FROM proxmox_nodes
            WHERE id = %s
        """
        logger.info(f"Executing direct query: {node_query} with params: {node_id}")
        cursor.execute(node_query, (node_id,))

        # Fetch the result
        result = cursor.fetchone()
        logger.info(f"Fetch result: {result}")

        # Close the cursor and connection
        cursor.close()
        conn.close()

        if not result:
            logger.info(f"No node found with id={node_id}")
            raise HTTPException(status_code=401, detail="Invalid API key or node not found")

        node_result = dict(result)
        stored_api_key = node_result['api_key']

        # Verify API key
        if api_key != stored_api_key:
            logger.info(f"API key mismatch for node_id={node_id}")
            raise HTTPException(status_code=401, detail="Invalid API key or node not found")

        logger.info(f"API key verified for node_id={node_id}")

        # Check if VM exists using direct database connection
        # Use direct database connection to avoid caching issues
        import psycopg2
        import psycopg2.extras
        import os

        # Connect directly to the database using the postgres user to bypass RLS
        conn = psycopg2.connect(
            host=os.getenv('PG_HOST', 'postgres'),
            port=os.getenv('PG_PORT', '5432'),
            dbname='accountdb',  # Hardcode the database name
            user='postgres',  # Use postgres user to bypass RLS
            password='CHANGEME_ULTRASECURE'  # Use the actual postgres password
        )

        # Create a cursor
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Execute the query to check if VM exists
        vm_query = """
            SELECT id, vmid, name, status, cpu_cores, memory_mb,
                disk_gb, ip_address, proxmox_node_id, owner_id,
                created_at, updated_at
            FROM vms
            WHERE id = %s
        """
        logger.info(f"Executing direct query: {vm_query} with params: {vm_id}")
        cursor.execute(vm_query, (vm_id,))

        # Fetch the result
        result = cursor.fetchone()
        logger.info(f"Fetch result: {result}")

        # Close the cursor and connection
        cursor.close()
        conn.close()

        existing_vm = dict(result) if result else None

        if not existing_vm:
            # If VM doesn't exist, create it
            logger.info(f"VM with id={vm_id} not found, creating new VM")

            # Prepare VM data
            vm_data = {
                "vmid": vm.vmid,
                "name": vm.name,
                "ip_address": vm.ip_address,
                "status": vm.status,
                "cpu_cores": vm.cpu_cores,
                "memory_mb": vm.memory_mb,
                "disk_gb": vm.disk_gb,
                "proxmox_node_id": node_id,  # Use the node_id from the query parameter
                "template_id": vm.template_id,
                "notes": vm.notes,
                "owner_id": 1  # Default to admin user for agent-created VMs
            }

            # Create the VM using direct database connection
            # Use direct database connection to avoid caching issues
            import psycopg2
            import psycopg2.extras
            import os

            # Connect directly to the database using the postgres user to bypass RLS
            conn = psycopg2.connect(
                host=os.getenv('PG_HOST', 'postgres'),
                port=os.getenv('PG_PORT', '5432'),
                dbname='accountdb',  # Hardcode the database name
                user='postgres',  # Use postgres user to bypass RLS
                password='CHANGEME_ULTRASECURE'  # Use the actual postgres password
            )

            # Create a cursor
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Execute the query to create the VM
            create_query = """
                INSERT INTO vms (
                    vmid, name, ip_address, status, cpu_cores, memory_mb,
                    disk_gb, proxmox_node_id, template_id, notes, owner_id
                ) VALUES (
                    %(vmid)s, %(name)s, %(ip_address)s, %(status)s, %(cpu_cores)s, %(memory_mb)s,
                    %(disk_gb)s, %(proxmox_node_id)s, %(template_id)s, %(notes)s, %(owner_id)s
                ) RETURNING
                    id, vmid, name, ip_address, status, cpu_cores, memory_mb,
                    disk_gb, proxmox_node_id, template_id, notes, created_at, updated_at, owner_id
            """
            logger.info(f"Executing direct query: {create_query}")
            cursor.execute(create_query, vm_data)

            # Fetch the result
            result = cursor.fetchone()
            logger.info(f"Fetch result: {result}")

            # Commit the transaction
            conn.commit()

            # Close the cursor and connection
            cursor.close()
            conn.close()

            if not result:
                raise HTTPException(status_code=500, detail="Failed to create VM")

            # Convert the result to a dictionary
            created_vm = dict(result)

            # Get the Proxmox node name
            if created_vm.get("proxmox_node_id"):
                # Connect directly to the database using the postgres user to bypass RLS
                conn = psycopg2.connect(
                    host=os.getenv('PG_HOST', 'postgres'),
                    port=os.getenv('PG_PORT', '5432'),
                    dbname='accountdb',  # Hardcode the database name
                    user='postgres',  # Use postgres user to bypass RLS
                    password='CHANGEME_ULTRASECURE'  # Use the actual postgres password
                )

                # Create a cursor
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # Execute the query to get the Proxmox node name
                node_query = "SELECT name FROM proxmox_nodes WHERE id = %s"
                cursor.execute(node_query, (created_vm["proxmox_node_id"],))

                # Fetch the result
                node_result = cursor.fetchone()

                # Close the cursor and connection
                cursor.close()
                conn.close()

                if node_result:
                    created_vm["proxmox_node"] = node_result["name"]

            return created_vm
        else:
            # If VM exists, update it
            logger.info(f"Updating VM with id={vm_id}")

            # Prepare VM data
            vm_data = {
                "vmid": vm.vmid,
                "name": vm.name,
                "ip_address": vm.ip_address,
                "status": vm.status,
                "cpu_cores": vm.cpu_cores,
                "memory_mb": vm.memory_mb,
                "disk_gb": vm.disk_gb,
                "proxmox_node_id": node_id,  # Use the node_id from the query parameter
                "template_id": vm.template_id,
                "notes": vm.notes
            }

            # Update the VM using direct database connection
            # Use direct database connection to avoid caching issues
            import psycopg2
            import psycopg2.extras
            import os

            # Connect directly to the database using the postgres user to bypass RLS
            conn = psycopg2.connect(
                host=os.getenv('PG_HOST', 'postgres'),
                port=os.getenv('PG_PORT', '5432'),
                dbname='accountdb',  # Hardcode the database name
                user='postgres',  # Use postgres user to bypass RLS
                password='CHANGEME_ULTRASECURE'  # Use the actual postgres password
            )

            # Create a cursor
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Execute the query to update the VM
            update_query = """
                UPDATE vms
                SET
                    vmid = COALESCE(%(vmid)s, vmid),
                    name = COALESCE(%(name)s, name),
                    ip_address = COALESCE(%(ip_address)s, ip_address),
                    status = COALESCE(%(status)s, status),
                    cpu_cores = COALESCE(%(cpu_cores)s, cpu_cores),
                    memory_mb = COALESCE(%(memory_mb)s, memory_mb),
                    disk_gb = COALESCE(%(disk_gb)s, disk_gb),
                    proxmox_node_id = COALESCE(%(proxmox_node_id)s, proxmox_node_id),
                    template_id = COALESCE(%(template_id)s, template_id),
                    notes = COALESCE(%(notes)s, notes),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(id)s
                RETURNING
                    id, vmid, name, ip_address, status, cpu_cores, memory_mb,
                    disk_gb, proxmox_node_id, template_id, notes, created_at, updated_at, owner_id
            """
            # Add vm_id to vm_data
            vm_data["id"] = vm_id

            logger.info(f"Executing direct query: {update_query}")
            cursor.execute(update_query, vm_data)

            # Fetch the result
            result = cursor.fetchone()
            logger.info(f"Fetch result: {result}")

            # Commit the transaction
            conn.commit()

            # Close the cursor and connection
            cursor.close()
            conn.close()

            if not result:
                raise HTTPException(status_code=500, detail="Failed to update VM")

            # Convert the result to a dictionary
            updated_vm = dict(result)

            # Get the Proxmox node name
            if updated_vm.get("proxmox_node_id"):
                # Connect directly to the database using the postgres user to bypass RLS
                conn = psycopg2.connect(
                    host=os.getenv('PG_HOST', 'postgres'),
                    port=os.getenv('PG_PORT', '5432'),
                    dbname='accountdb',  # Hardcode the database name
                    user='postgres',  # Use postgres user to bypass RLS
                    password='CHANGEME_ULTRASECURE'  # Use the actual postgres password
                )

                # Create a cursor
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # Execute the query to get the Proxmox node name
                node_query = "SELECT name FROM proxmox_nodes WHERE id = %s"
                cursor.execute(node_query, (updated_vm["proxmox_node_id"],))

                # Fetch the result
                node_result = cursor.fetchone()

                # Close the cursor and connection
                cursor.close()
                conn.close()

                if node_result:
                    updated_vm["proxmox_node"] = node_result["name"]

            return updated_vm

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating VM from agent: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating VM from agent: {str(e)}")

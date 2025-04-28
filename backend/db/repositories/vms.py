"""
VM repository for database access.

This module provides a repository class for accessing VM data in the database.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from .base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class VMRepository(BaseRepository):
    """Repository for VM data."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the VMRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "vms"
        self.id_column = "id"
        self.default_columns = """
            id, vmid, name, status, cpu_cores, memory_mb,
            disk_gb, ip_address, proxmox_node_id, owner_id,
            created_at, updated_at
        """
        self.default_order_by = "id DESC"
        self.search_columns = ["name", "vmid", "ip_address"]

    def get_vms(self, limit: int = 10, offset: int = 0, search: Optional[str] = None,
               status: Optional[str] = None, proxmox_node_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a list of VMs with pagination and filtering.

        Args:
            limit (int, optional): Maximum number of VMs to return. Defaults to 10.
            offset (int, optional): Number of VMs to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter VMs. Defaults to None.
            status (Optional[str], optional): Filter by status. Defaults to None.
            proxmox_node_id (Optional[int], optional): Filter by Proxmox node ID. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary with VMs and pagination info.
        """
        # Build filter conditions
        condition = "1=1"
        params = []

        if status:
            condition += " AND status = %s"
            params.append(status)

        if proxmox_node_id:
            condition += " AND proxmox_node_id = %s"
            params.append(proxmox_node_id)

        # Add search condition if provided
        if search:
            search_condition = " OR ".join([f"{column} ILIKE %s" for column in self.search_columns])
            condition += f" AND ({search_condition})"
            search_term = f"%{search}%"
            params.extend([search_term] * len(self.search_columns))

        # Get total count
        total = self.get_count(condition, tuple(params) if params else None)

        # Get VMs
        vms = self.get_all(condition, tuple(params) if params else None,
                          self.default_columns, self.default_order_by, limit, offset)

        return {
            "vms": vms,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def get_vm_by_id(self, vm_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific VM by ID.

        Args:
            vm_id (int): The ID of the VM.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the VM or None if not found.
        """
        return self.get_by_id(vm_id)

    def get_vm_by_vmid(self, vmid: str, proxmox_node_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific VM by VMID.

        Args:
            vmid (str): The VMID of the VM.
            proxmox_node_id (Optional[int], optional): The ID of the Proxmox node. Defaults to None.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the VM or None if not found.
        """
        condition = "vmid = %s"
        params = [vmid]

        if proxmox_node_id:
            condition += " AND proxmox_node_id = %s"
            params.append(proxmox_node_id)

        vms = self.get_all(condition, tuple(params), self.default_columns)
        return vms[0] if vms else None

    def create_vm(self, vm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new VM.

        Args:
            vm_data (Dict[str, Any]): The VM data.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created VM or None if creation failed.
        """
        return self.create(vm_data)

    def update_vm(self, vm_id: int, vm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a VM.

        Args:
            vm_id (int): The ID of the VM.
            vm_data (Dict[str, Any]): The VM data to update.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated VM or None if update failed.
        """
        return self.update(vm_id, vm_data, returning=True)

    def delete_vm(self, vm_id: int) -> bool:
        """
        Delete a VM.

        Args:
            vm_id (int): The ID of the VM.

        Returns:
            bool: True if the VM was deleted, False otherwise.
        """
        return self.delete(vm_id) > 0

    def get_vms_by_proxmox_node(self, proxmox_node_id: int, whitelist: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Get all VMs for a specific Proxmox node.

        Args:
            proxmox_node_id (int): The ID of the Proxmox node.
            whitelist (Optional[List[int]], optional): List of VMIDs to filter by. Defaults to None.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with VMs.
        """
        condition = "proxmox_node_id = %s"
        params = [proxmox_node_id]

        # Get VMs
        vms = self.get_all(condition, tuple(params), self.default_columns)

        # Filter by whitelist if provided
        if whitelist:
            vms = [vm for vm in vms if vm["vmid"] in whitelist]

        return vms

    def get_vms_with_proxmox_node_name(self, limit: int = 10, offset: int = 0, search: Optional[str] = None,
                                      status: Optional[str] = None, proxmox_node_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a list of VMs with Proxmox node names.

        Args:
            limit (int, optional): Maximum number of VMs to return. Defaults to 10.
            offset (int, optional): Number of VMs to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter VMs. Defaults to None.
            status (Optional[str], optional): Filter by status. Defaults to None.
            proxmox_node_id (Optional[int], optional): Filter by Proxmox node ID. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary with VMs and pagination info.
        """
        try:
            # Build the query
            query = """
                SELECT
                    v.id, v.vmid, v.name, v.ip_address, v.status, v.cpu_cores, v.memory_mb,
                    v.disk_gb, v.proxmox_node_id, pn.name as proxmox_node, v.template_id, v.notes, v.created_at, v.updated_at, v.owner_id
                FROM vms v
                LEFT JOIN proxmox_nodes pn ON v.proxmox_node_id = pn.id
                WHERE 1=1
            """
            params = []

            # Add search filter if provided
            if search:
                query += " AND (v.name ILIKE %s OR v.ip_address ILIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param])

            # Add status filter if provided
            if status:
                query += " AND v.status = %s"
                params.append(status)

            # Add proxmox_node_id filter if provided
            if proxmox_node_id:
                query += " AND v.proxmox_node_id = %s"
                params.append(proxmox_node_id)

            # Convert params to tuple for database query
            params_tuple = tuple(params) if params else None

            # Disable cache for this query to avoid serialization issues
            from ..query_cache import cache_context

            # Execute queries with cache disabled
            with cache_context(enable=False):
                # Count total records
                count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_vms"
                total_result = self.execute_query_single(count_query, params_tuple)
                total = total_result["count"] if total_result else 0

                # Add pagination
                paginated_query = f"{query} ORDER BY v.id DESC LIMIT %s OFFSET %s"
                paginated_params = list(params) if params else []
                paginated_params.extend([limit, offset])
                paginated_params_tuple = tuple(paginated_params)

                # Execute the query
                vms = self.execute_query(paginated_query, paginated_params_tuple)

            return {
                "vms": vms,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Error in get_vms_with_proxmox_node_name: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_vm_with_proxmox_node_name(self, vm_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific VM with Proxmox node name.

        Args:
            vm_id (int): The ID of the VM.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the VM or None if not found.
        """
        try:
            query = """
                SELECT
                    v.id, v.vmid, v.name, v.ip_address, v.status, v.cpu_cores, v.memory_mb,
                    v.disk_gb, v.proxmox_node_id, pn.name as proxmox_node, v.template_id, v.notes, v.created_at, v.updated_at, v.owner_id
                FROM vms v
                LEFT JOIN proxmox_nodes pn ON v.proxmox_node_id = pn.id
                WHERE v.id = %s
            """

            # Disable cache for this query to avoid serialization issues
            from ..query_cache import cache_context

            # Execute query with cache disabled
            with cache_context(enable=False):
                return self.execute_query_single(query, (vm_id,))
        except Exception as e:
            logger.error(f"Error in get_vm_with_proxmox_node_name: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def create_vm(self, vm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new VM.

        Args:
            vm_data (Dict[str, Any]): The VM data.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created VM or None if creation failed.
        """
        # Set owner_id if not provided
        if "owner_id" not in vm_data and self.user_id:
            vm_data["owner_id"] = self.user_id

        # Insert the VM
        query = """
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
        created_vm = self.execute_query_single(query, vm_data)

        if not created_vm:
            return None

        # Get the Proxmox node name
        if created_vm.get("proxmox_node_id"):
            query = "SELECT name FROM proxmox_nodes WHERE id = %s"
            node = self.execute_query_single(query, (created_vm["proxmox_node_id"],))
            if node:
                created_vm["proxmox_node"] = node["name"]

        return created_vm

    def update_vm(self, vm_id: int, vm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a VM.

        Args:
            vm_id (int): The ID of the VM to update.
            vm_data (Dict[str, Any]): The VM data to update.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated VM or None if update failed.
        """
        # Update the VM
        query = """
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

        # Update the VM
        updated_vm = self.execute_query_single(query, vm_data)

        if not updated_vm:
            return None

        # Get the Proxmox node name
        if updated_vm.get("proxmox_node_id"):
            query = "SELECT name FROM proxmox_nodes WHERE id = %s"
            node = self.execute_query_single(query, (updated_vm["proxmox_node_id"],))
            if node:
                updated_vm["proxmox_node"] = node["name"]

        return updated_vm

    def delete_vm(self, vm_id: int) -> bool:
        """
        Delete a VM.

        Args:
            vm_id (int): The ID of the VM to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Delete the VM
        query = "DELETE FROM vms WHERE id = %s"
        affected_rows = self.execute_command(query, (vm_id,))

        return affected_rows > 0

    def get_vms_by_owner(self, owner_id: int) -> List[Dict[str, Any]]:
        """
        Get all VMs for a specific owner.

        Args:
            owner_id (int): The ID of the owner.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with VMs.
        """
        condition = "owner_id = %s"
        return self.get_all(condition, (owner_id,), self.default_columns)

    def get_vm_with_whitelist(self, vm_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a VM with its whitelist.

        Args:
            vm_id (int): The ID of the VM.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the VM and its whitelist or None if not found.
        """
        # Get the VM
        vm = self.get_by_id(vm_id)

        if not vm:
            return None

        # Get the whitelist
        whitelist_query = """
            SELECT
                w.id, w.vm_id, w.user_id, w.created_at,
                u.username as user_username
            FROM whitelist w
            JOIN users u ON w.user_id = u.id
            WHERE w.vm_id = %s
        """
        whitelist = self.execute_query(whitelist_query, (vm_id,))

        # Add whitelist to VM
        vm["whitelist"] = whitelist

        return vm

    def add_to_whitelist(self, vm_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Add a user to a VM's whitelist.

        Args:
            vm_id (int): The ID of the VM.
            user_id (int): The ID of the user.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the whitelist entry or None if addition failed.
        """
        # Check if the whitelist entry already exists
        check_query = """
            SELECT 1 FROM whitelist
            WHERE vm_id = %s AND user_id = %s
        """
        check_result = self.execute_query(check_query, (vm_id, user_id))

        if check_result:
            return None  # Already exists

        # Add to whitelist
        insert_query = """
            INSERT INTO whitelist (vm_id, user_id)
            VALUES (%s, %s)
            RETURNING id, vm_id, user_id, created_at
        """
        return self.execute_insert(insert_query, (vm_id, user_id))

    def remove_from_whitelist(self, vm_id: int, user_id: int) -> bool:
        """
        Remove a user from a VM's whitelist.

        Args:
            vm_id (int): The ID of the VM.
            user_id (int): The ID of the user.

        Returns:
            bool: True if the user was removed, False otherwise.
        """
        delete_query = """
            DELETE FROM whitelist
            WHERE vm_id = %s AND user_id = %s
        """
        result = self.execute_command(delete_query, (vm_id, user_id))
        return result > 0

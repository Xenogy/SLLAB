"""
AccountDB API client for sending VM information.
"""

from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from config import config

class AccountDBClient:
    """Client for interacting with the AccountDB API."""

    def __init__(self):
        """Initialize the AccountDB client."""
        self.base_url = config.accountdb.url
        self.api_key = config.accountdb.api_key
        self.node_id = config.accountdb.node_id
        self.owner_id = None  # Will be retrieved from the server
        self.headers = {
            "Content-Type": "application/json",
        }
        self.access_token = None
        logger.info(f"Initialized AccountDB client for URL: {self.base_url}, Node ID: {self.node_id}")

    async def login(self) -> bool:
        """
        Login to the AccountDB API to get an access token.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        # For now, we'll skip the login process and use the API key directly
        # This is a temporary solution until we implement proper authentication
        logger.info("Using API key for authentication instead of JWT token")
        return True

    def get_auth_headers(self) -> dict:
        """
        Get headers with authentication token.

        Returns:
            dict: Headers with authentication token if available
        """
        headers = self.headers.copy()
        # We're not using JWT tokens for now, just returning the headers
        return headers

    async def get_node_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about this Proxmox node from AccountDB.
        This includes the owner_id which is needed for VM synchronization.

        Returns:
            Optional[Dict[str, Any]]: Node information or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Fetching node information from AccountDB API")
                response = await client.get(
                    f"{self.base_url}/proxmox-nodes/agent-node/{self.node_id}",
                    params={"api_key": self.api_key},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully retrieved node information")
                    return data
                else:
                    error_text = response.text
                    logger.error(f"Error getting node information: HTTP {response.status_code} - {error_text}")
                    return None
        except httpx.HTTPError as e:
            logger.error(f"Network error getting node information: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving node information: {e}")
            return None

    async def verify_connection(self) -> bool:
        """
        Verify the connection to the AccountDB API and retrieve the owner_id.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            # Get node information which includes the owner_id
            node_info = await self.get_node_info()

            if node_info and 'owner_id' in node_info:
                self.owner_id = node_info['owner_id']
                logger.info(f"Connection verified successfully. Owner ID: {self.owner_id}")
                return True
            else:
                logger.error("Failed to retrieve owner_id from node information")
                return False
        except Exception as e:
            logger.error(f"Error verifying connection to AccountDB: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """
        Send a heartbeat to the AccountDB API.

        Returns:
            bool: True if the heartbeat is successful, False otherwise.
        """
        try:
            # Make sure we have a valid token
            if not self.access_token:
                login_success = await self.login()
                if not login_success:
                    logger.error("Failed to login to AccountDB")
                    return False

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/proxmox-nodes/heartbeat",
                    params={"node_id": self.node_id, "api_key": self.api_key},
                    headers=self.get_auth_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                logger.debug("Heartbeat sent successfully")
                return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Authentication failed, trying to login again")
                # Token might be expired, try to login again
                login_success = await self.login()
                if login_success:
                    # Try heartbeat again with new token
                    return await self.send_heartbeat()
            logger.error(f"HTTP error sending heartbeat to AccountDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending heartbeat to AccountDB: {e}")
            return False

    async def get_vms(self) -> List[Dict[str, Any]]:
        """
        Get all VMs from AccountDB.

        Returns:
            List[Dict[str, Any]]: List of VM information dictionaries.
        """
        try:
            # Make sure we have a valid token
            if not self.access_token:
                login_success = await self.login()
                if not login_success:
                    logger.error("Failed to login to AccountDB")
                    return []

            async with httpx.AsyncClient() as client:
                # Use the agent-specific endpoint that doesn't require authentication
                url = f"{self.base_url}/proxmox-nodes/agent-vms/{self.node_id}"
                logger.info(f"Request URL: {url}")

                # Add API key as query parameter
                params = {"api_key": self.api_key}
                logger.info(f"Request params: {params}")

                response = await client.get(
                    url,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Retrieved {len(data.get('vms', []))} VMs from AccountDB")
                return data.get("vms", [])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Authentication failed, trying to login again")
                # Token might be expired, try to login again
                login_success = await self.login()
                if login_success:
                    # Try getting VMs again with new token
                    return await self.get_vms()
            logger.error(f"HTTP error retrieving VMs from AccountDB: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving VMs from AccountDB: {e}")
            return []

    async def get_vm(self, vm_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific VM from AccountDB.

        Args:
            vm_id: VM ID

        Returns:
            Optional[Dict[str, Any]]: VM information or None if not found
        """
        try:
            # For now, we'll get all VMs and filter by ID
            # This is not the most efficient approach, but it works with our current API
            vms = await self.get_vms()

            # Find the VM with the specified ID
            for vm in vms:
                if vm.get('id') == vm_id:
                    logger.debug(f"Found VM with ID {vm_id} in AccountDB")
                    return vm

            logger.debug(f"VM with ID {vm_id} not found in AccountDB")
            return None
        except Exception as e:
            logger.error(f"Error retrieving VM with ID {vm_id} from AccountDB: {e}")
            return None

    async def create_vm(self, vm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new VM in AccountDB.

        Args:
            vm_data: VM information dictionary

        Returns:
            Optional[Dict[str, Any]]: Created VM information or None if failed
        """
        try:
            # Use the agent-specific endpoint that accepts API key authentication
            # For creating a VM, we'll use the same endpoint as updating, but with a non-existent ID
            # The endpoint will create a new VM if it doesn't exist
            async with httpx.AsyncClient() as client:
                # Use a high ID that's unlikely to exist
                vm_id = 999999
                logger.debug(f"Creating VM with VMID {vm_data.get('vmid')} using agent endpoint")
                response = await client.put(
                    f"{self.base_url}/vms/agent/{vm_id}",
                    params={"node_id": self.node_id, "api_key": self.api_key},
                    json=vm_data,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    logger.info(f"Created VM with VMID {vm_data.get('vmid')} in AccountDB")
                    return response.json()
                else:
                    error_text = response.text
                    logger.error(f"Error creating VM with VMID {vm_data.get('vmid')} in AccountDB: HTTP {response.status_code} - {error_text}")
                    return None
        except httpx.HTTPError as e:
            logger.error(f"Network error creating VM in AccountDB: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating VM in AccountDB: {e}")
            return None

    async def update_vm(self, vm_id: int, vm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing VM in AccountDB.

        Args:
            vm_id: VM ID
            vm_data: VM information dictionary

        Returns:
            Optional[Dict[str, Any]]: Updated VM information or None if failed
        """
        try:
            # Use the agent-specific endpoint that accepts API key authentication
            async with httpx.AsyncClient() as client:
                logger.debug(f"Updating VM with ID {vm_id} using agent endpoint")
                response = await client.put(
                    f"{self.base_url}/vms/agent/{vm_id}",
                    params={"node_id": self.node_id, "api_key": self.api_key},
                    json=vm_data,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    logger.info(f"Updated VM with ID {vm_id} in AccountDB")
                    return response.json()
                else:
                    error_text = response.text
                    logger.error(f"Error updating VM with ID {vm_id} in AccountDB: HTTP {response.status_code} - {error_text}")
                    return None
        except httpx.HTTPError as e:
            logger.error(f"Network error updating VM with ID {vm_id} in AccountDB: {e}")
            return None
        except Exception as e:
            logger.error(f"Error updating VM with ID {vm_id} in AccountDB: {e}")
            return None

    async def delete_vm(self, vm_id: int) -> bool:
        """
        Delete a VM from AccountDB.

        Args:
            vm_id: VM ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # For now, we'll just update the VM status to 'deleted'
            # This is not a true deletion, but it will mark the VM as deleted in the UI
            vm_data = {
                "status": "deleted"
            }

            # Update the VM using our agent endpoint
            result = await self.update_vm(vm_id, vm_data)

            if result:
                logger.info(f"Marked VM with ID {vm_id} as deleted in AccountDB")
                return True
            else:
                logger.error(f"Failed to mark VM with ID {vm_id} as deleted in AccountDB")
                return False
        except Exception as e:
            logger.error(f"Error deleting VM with ID {vm_id} from AccountDB: {e}")
            return False

    async def get_vmid_whitelist(self) -> List[int]:
        """
        Get the VMID whitelist for this node.

        Returns:
            List[int]: List of whitelisted VMIDs

        Raises:
            Exception: If there's an error retrieving the whitelist
        """
        try:
            # Try the new endpoint first
            async with httpx.AsyncClient() as client:
                logger.debug(f"Fetching whitelist from new AccountDB API endpoint")
                response = await client.get(
                    f"{self.base_url}/vm-access/node/{self.node_id}/whitelist/agent",
                    params={"api_key": self.api_key},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    vmids = response.json()
                    logger.info(f"Successfully retrieved whitelist with {len(vmids)} whitelisted VMIDs from new endpoint")
                    # The response is already a list of VMIDs
                    return vmids
                elif response.status_code == 404:
                    # New endpoint not found, try the legacy endpoint
                    logger.warning("New whitelist endpoint not found, trying legacy endpoint")
                    return await self._get_vmid_whitelist_legacy()
                else:
                    error_text = response.text
                    logger.error(f"Error getting VMID whitelist from new endpoint: HTTP {response.status_code} - {error_text}")
                    # Try the legacy endpoint as a fallback
                    return await self._get_vmid_whitelist_legacy()
        except httpx.HTTPError as e:
            logger.error(f"Network error getting VMID whitelist from new endpoint: {e}")
            # Try the legacy endpoint as a fallback
            return await self._get_vmid_whitelist_legacy()
        except Exception as e:
            logger.error(f"Error retrieving VMID whitelist from new endpoint: {e}")
            # Try the legacy endpoint as a fallback
            return await self._get_vmid_whitelist_legacy()

    async def _get_vmid_whitelist_legacy(self) -> List[int]:
        """
        Get the VMID whitelist for this node using the legacy endpoint.

        Returns:
            List[int]: List of whitelisted VMIDs

        Raises:
            Exception: If there's an error retrieving the whitelist
        """
        try:
            # Use the agent-specific endpoint that doesn't require authentication
            async with httpx.AsyncClient() as client:
                logger.debug(f"Fetching whitelist from legacy AccountDB API endpoint")
                response = await client.get(
                    f"{self.base_url}/proxmox-nodes/agent-whitelist/{self.node_id}",
                    params={"api_key": self.api_key},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    vmids = data.get("vmids", [])
                    logger.info(f"Successfully retrieved whitelist with {len(vmids)} whitelisted VMIDs from legacy endpoint")
                    return vmids
                else:
                    error_text = response.text
                    logger.error(f"Error getting VMID whitelist from legacy endpoint: HTTP {response.status_code} - {error_text}")
                    # In sync_vms, we catch and handle this exception
                    raise Exception(f"HTTP {response.status_code} - {error_text}")
        except httpx.HTTPError as e:
            logger.error(f"Network error getting VMID whitelist from legacy endpoint: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving VMID whitelist from legacy endpoint: {e}")
            # Return empty list as fallback for backward compatibility
            # This will be caught in sync_vms and handled appropriately
            return []

    async def sync_vms(self, proxmox_vms: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Synchronize VMs between Proxmox and AccountDB.

        Args:
            proxmox_vms: List of VM information dictionaries from Proxmox
            (already filtered by whitelist if whitelist is enabled)

        Returns:
            Dict[str, int]: Statistics about the synchronization
        """
        stats = {
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "unchanged": 0,
            "filtered": 0,
            "errors": 0,
            "total_proxmox_vms": len(proxmox_vms),
            "whitelist_enabled": False,
            "whitelist_count": 0,
            "online_vms": 0,
        }

        try:
            # Get the current whitelist for stats
            whitelist = await self.get_vmid_whitelist()
            stats["whitelist_enabled"] = len(whitelist) > 0
            stats["whitelist_count"] = len(whitelist)

            # Get existing VMs from the database for this node
            existing_vms = await self.get_vms()

            # Create a map of existing VMs by VMID for quick lookup
            existing_vm_map = {vm.get('vmid'): vm for vm in existing_vms if vm.get('vmid')}

            # Process each VM from Proxmox
            for vm in proxmox_vms:
                vmid = vm.get('vmid')
                if not vmid:
                    logger.warning(f"Skipping VM without VMID: {vm}")
                    stats["filtered"] += 1
                    continue

                # Check if VM is online/running
                is_online = vm.get('status') == 'running'
                if is_online:
                    stats["online_vms"] += 1

                # Check if VM already exists in the database
                if vmid in existing_vm_map:
                    # VM exists, check if it needs to be updated
                    existing_vm = existing_vm_map[vmid]

                    # Check if any fields have changed
                    needs_update = (
                        vm.get('name') != existing_vm.get('name') or
                        vm.get('status') != existing_vm.get('status') or
                        vm.get('cpu_cores') != existing_vm.get('cpu_cores') or
                        vm.get('memory_mb') != existing_vm.get('memory_mb') or
                        vm.get('disk_gb') != existing_vm.get('disk_gb') or
                        vm.get('ip_address') != existing_vm.get('ip_address')
                    )

                    if needs_update:
                        # Update the VM in the database
                        try:
                            await self.update_vm(existing_vm.get('id'), vm)
                            stats["updated"] += 1
                            logger.info(f"Updated VM with VMID {vmid} in AccountDB")
                        except Exception as e:
                            logger.error(f"Error updating VM with VMID {vmid}: {e}")
                            stats["errors"] += 1
                    else:
                        stats["unchanged"] += 1
                else:
                    # VM doesn't exist, create it if it's whitelisted and online
                    if vmid in whitelist and is_online:
                        try:
                            # Set owner_id to the configured owner
                            vm['owner_id'] = self.owner_id

                            # Set proxmox_node_id to the node_id
                            vm['proxmox_node_id'] = self.node_id

                            # Create the VM in the database
                            await self.create_vm(vm)
                            stats["created"] += 1
                            logger.info(f"Created VM with VMID {vmid} in AccountDB")
                        except Exception as e:
                            logger.error(f"Error creating VM with VMID {vmid}: {e}")
                            stats["errors"] += 1
                    else:
                        # VM is not whitelisted or not online, skip it
                        if vmid not in whitelist:
                            logger.debug(f"Skipping VM with VMID {vmid}: Not in whitelist")
                        elif not is_online:
                            logger.debug(f"Skipping VM with VMID {vmid}: Not online")
                        stats["filtered"] += 1

            logger.info(f"VM synchronization completed: {stats}")

        except Exception as e:
            logger.error(f"Error during VM synchronization: {e}")
            stats["errors"] += 1

        return stats

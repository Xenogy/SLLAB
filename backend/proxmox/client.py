"""
Proxmox API Client

This module provides a client for interacting with the Proxmox API.
"""

import logging
import httpx
import json
import ssl
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

# Configure logging
logger = logging.getLogger(__name__)

class ProxmoxClient:
    """Client for interacting with the Proxmox API."""

    def __init__(self, hostname: str, port: int = 8006, verify_ssl: bool = False):
        """
        Initialize the Proxmox client.

        Args:
            hostname: Hostname or IP address of the Proxmox server
            port: Port number (default: 8006)
            verify_ssl: Whether to verify SSL certificates (default: False)
        """
        self.base_url = f"https://{hostname}:{port}/api2/json"
        self.verify_ssl = verify_ssl
        self.token = None
        self.csrf_token = None
        self.ticket = None

        # Create SSL context that doesn't verify certificates if verify_ssl is False
        if not verify_ssl:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    async def login(self, username: str, password: str, realm: str = "pam") -> bool:
        """
        Log in to the Proxmox API.

        Args:
            username: Username
            password: Password
            realm: Authentication realm (default: pam)

        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.post(
                    urljoin(self.base_url, "access/ticket"),
                    data={
                        "username": username,
                        "password": password,
                        "realm": realm
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        self.token = data["data"]["ticket"]
                        self.csrf_token = data["data"]["CSRFPreventionToken"]
                        self.ticket = data["data"]["ticket"]
                        return True

                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False

    async def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get a list of nodes in the Proxmox cluster.

        Returns:
            List[Dict[str, Any]]: List of nodes
        """
        return await self._get("nodes")

    async def get_vms(self, node: str) -> List[Dict[str, Any]]:
        """
        Get a list of VMs on a specific node.

        Args:
            node: Node name

        Returns:
            List[Dict[str, Any]]: List of VMs
        """
        enriched_vms = []

        try:
            # Get the list of VMs
            vms = await self._get(f"nodes/{node}/qemu")

            # Process each VM
            for vm in vms:
                try:
                    vmid = vm.get("vmid")
                    if not vmid:
                        continue

                    # Get VM status
                    status = await self._get(f"nodes/{node}/qemu/{vmid}/status/current")
                    if status:
                        vm.update(status)

                    # Get VM config
                    config = await self._get(f"nodes/{node}/qemu/{vmid}/config")
                    if config:
                        vm.update(config)

                        # Extract CPU cores and memory
                        if "data" in config:
                            config_data = config.get("data", {})
                            vm["cpu_cores"] = int(config_data.get("cores", 1))
                            vm["memory_mb"] = int(config_data.get("memory", 1024))

                            # Extract disk size
                            disk_size = 0
                            for key, value in config_data.items():
                                if key.startswith("scsi") or key.startswith("virtio") or key.startswith("ide") or key.startswith("sata"):
                                    if "size" in value:
                                        size_str = value.split(",")[0].split("=")[1]
                                        if size_str.endswith("G"):
                                            disk_size += int(size_str[:-1])
                            vm["disk_gb"] = disk_size

                    # Get VM IP address
                    try:
                        agent_info = await self._get(f"nodes/{node}/qemu/{vmid}/agent/network-get-interfaces")
                        if "data" in agent_info and "result" in agent_info["data"]:
                            interfaces = agent_info["data"]["result"]
                            for interface in interfaces:
                                if "ip-addresses" in interface:
                                    for ip in interface["ip-addresses"]:
                                        if ip["ip-address-type"] == "ipv4":
                                            vm["ip_address"] = ip["ip-address"]
                                            break
                    except Exception as e:
                        # Agent might not be running or VM might be stopped
                        logger.debug(f"Error getting IP address for VM {vmid}: {e}")

                    # Add the VM to the list
                    enriched_vms.append(vm)

                except Exception as e:
                    logger.error(f"Error processing VM {vm.get('vmid')}: {e}")

        except Exception as e:
            logger.error(f"Error getting VMs on node {node}: {e}")

        return enriched_vms

    async def get_vm(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific VM.

        Args:
            node: Node name
            vmid: VM ID

        Returns:
            Optional[Dict[str, Any]]: VM information or None if not found
        """
        try:
            vm = await self._get(f"nodes/{node}/qemu/{vmid}/status/current")

            if vm:
                # Get VM config
                config = await self._get(f"nodes/{node}/qemu/{vmid}/config")
                if config and "data" in config:
                    vm.update(config)

                    # Extract CPU cores and memory
                    config_data = config.get("data", {})
                    vm["cpu_cores"] = int(config_data.get("cores", 1))
                    vm["memory_mb"] = int(config_data.get("memory", 1024))

                    # Extract disk size
                    disk_size = 0
                    for key, value in config_data.items():
                        if key.startswith("scsi") or key.startswith("virtio") or key.startswith("ide") or key.startswith("sata"):
                            if "size" in value:
                                size_str = value.split(",")[0].split("=")[1]
                                if size_str.endswith("G"):
                                    disk_size += int(size_str[:-1])
                    vm["disk_gb"] = disk_size

                # Get VM IP address
                try:
                    agent_info = await self._get(f"nodes/{node}/qemu/{vmid}/agent/network-get-interfaces")
                    if "data" in agent_info and "result" in agent_info["data"]:
                        interfaces = agent_info["data"]["result"]
                        for interface in interfaces:
                            if "ip-addresses" in interface:
                                for ip in interface["ip-addresses"]:
                                    if ip["ip-address-type"] == "ipv4":
                                        vm["ip_address"] = ip["ip-address"]
                                        break
                except Exception as e:
                    # Agent might not be running or VM might be stopped
                    logger.debug(f"Error getting IP address for VM {vmid}: {e}")

                return vm

            return None
        except Exception as e:
            logger.error(f"Error getting VM {vmid} on node {node}: {e}")
            return None

    async def _get(self, path: str) -> Any:
        """
        Make a GET request to the Proxmox API.

        Args:
            path: API path

        Returns:
            Any: Response data
        """
        try:
            url = urljoin(self.base_url, path)
            headers = {}

            if self.token:
                cookies = {"PVEAuthCookie": self.token}
            else:
                cookies = {}

            async with httpx.AsyncClient(verify=self.verify_ssl, cookies=cookies) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json().get("data", [])

                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error during API request: {e}")
            return []

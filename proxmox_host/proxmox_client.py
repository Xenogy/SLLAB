"""
Proxmox API client for fetching VM information.
"""

import time
from typing import List, Dict, Any, Optional
from proxmoxer import ProxmoxAPI
from loguru import logger
from config import config

class ProxmoxClient:
    """Client for interacting with the Proxmox API."""

    def __init__(self):
        """Initialize the Proxmox client."""
        # Extract hostname from URL if needed
        host = config.proxmox.host
        if host.startswith("http://") or host.startswith("https://"):
            # Parse the URL to extract just the hostname
            from urllib.parse import urlparse
            parsed_url = urlparse(host)
            host = parsed_url.netloc

        self.node_name = config.proxmox.node_name
        logger.info(f"Initializing Proxmox client for node: {self.node_name}")

        try:
            self.proxmox = ProxmoxAPI(
                host=host,
                user=config.proxmox.user,
                password=config.proxmox.password,
                verify_ssl=config.proxmox.verify_ssl,
            )
            self.connected = True
            logger.info(f"Successfully connected to Proxmox API at {host}")
        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect to Proxmox API: {e}")
            # Create a dummy proxmox object
            self.proxmox = None

    def get_vms(self) -> List[Dict[str, Any]]:
        """
        Get all VMs from the Proxmox node.

        Returns:
            List[Dict[str, Any]]: List of VM information dictionaries.
        """
        # If not connected, return empty list
        if not self.connected or self.proxmox is None:
            logger.warning("Not connected to Proxmox API, returning empty VM list")
            return []

        try:
            # Get all VMs (QEMU)
            vms = self.proxmox.nodes(self.node_name).qemu.get()
            logger.info(f"Retrieved {len(vms)} VMs from Proxmox")

            # Enrich VM data with additional information
            enriched_vms = []
            for vm in vms:
                vm_id = vm['vmid']
                try:
                    # Get VM config for additional details
                    config = self.proxmox.nodes(self.node_name).qemu(vm_id).config.get()

                    # Get VM status for runtime information
                    status = self.proxmox.nodes(self.node_name).qemu(vm_id).status.current.get()

                    # Combine all information
                    enriched_vm = {
                        'vmid': vm_id,
                        'name': vm.get('name', f"VM-{vm_id}"),
                        'status': vm.get('status', 'unknown'),
                        'cpu_cores': vm.get('cpus', 0),
                        'memory_mb': vm.get('maxmem', 0) // (1024 * 1024),  # Convert to MB
                        'disk_gb': self._calculate_disk_size(vm, config),
                        'ip_address': self._get_ip_address(vm_id, config, status),
                        'proxmox_node': self.node_name,
                        'template_id': config.get('template', None),
                        'notes': config.get('description', ''),
                    }
                    enriched_vms.append(enriched_vm)
                    logger.debug(f"Enriched VM data for VMID {vm_id}")
                except Exception as e:
                    logger.error(f"Error enriching VM data for VMID {vm_id}: {e}")

            return enriched_vms
        except Exception as e:
            logger.error(f"Error retrieving VMs from Proxmox: {e}")
            return []

    def _calculate_disk_size(self, vm: Dict[str, Any], config: Dict[str, Any]) -> int:
        """
        Calculate the total disk size in GB.

        Args:
            vm: VM information dictionary
            config: VM configuration dictionary

        Returns:
            int: Total disk size in GB
        """
        try:
            # Try to get disk size from VM info
            if 'maxdisk' in vm:
                return vm['maxdisk'] // (1024 * 1024 * 1024)  # Convert to GB

            # If not available, calculate from config
            total_size = 0
            for key, value in config.items():
                if key.startswith('scsi') or key.startswith('ide') or key.startswith('sata'):
                    if 'size' in value:
                        # Parse size string (e.g., "20G")
                        size_str = value.split(',')[0].split('=')[1]
                        if size_str.endswith('G'):
                            total_size += int(size_str[:-1])
                        elif size_str.endswith('M'):
                            total_size += int(size_str[:-1]) / 1024
                        elif size_str.endswith('T'):
                            total_size += int(size_str[:-1]) * 1024

            return total_size
        except Exception as e:
            logger.error(f"Error calculating disk size: {e}")
            return 0

    def _get_ip_address(self, vm_id: int, config: Dict[str, Any], status: Dict[str, Any]) -> Optional[str]:
        """
        Get the IP address of a VM.

        Args:
            vm_id: VM ID
            config: VM configuration dictionary
            status: VM status dictionary

        Returns:
            Optional[str]: IP address or None if not available
        """
        try:
            # Try to get IP from agent info if VM is running
            if status.get('status') == 'running':
                try:
                    agent_info = self.proxmox.nodes(self.node_name).qemu(vm_id).agent.get('network-get-interfaces')
                    for interface in agent_info.get('result', []):
                        for ip_info in interface.get('ip-addresses', []):
                            if ip_info.get('ip-address-type') == 'ipv4' and not ip_info.get('ip-address').startswith('127.'):
                                return ip_info.get('ip-address')
                except Exception:
                    # Agent might not be available, continue with other methods
                    pass

            # Try to get IP from config (if using DHCP with MAC)
            for key, value in config.items():
                if key.startswith('net') and 'ip=' in value:
                    parts = value.split(',')
                    for part in parts:
                        if part.startswith('ip='):
                            return part.split('=')[1]

            # No IP found
            return None
        except Exception as e:
            logger.error(f"Error getting IP address for VMID {vm_id}: {e}")
            return None

    def get_vm_status(self, vm_id: int) -> Dict[str, Any]:
        """
        Get detailed status of a specific VM.

        Args:
            vm_id: VM ID

        Returns:
            Dict[str, Any]: VM status information
        """
        # If not connected, return empty dict
        if not self.connected or self.proxmox is None:
            logger.warning(f"Not connected to Proxmox API, returning empty status for VMID {vm_id}")
            return {}

        try:
            status = self.proxmox.nodes(self.node_name).qemu(vm_id).status.current.get()
            logger.debug(f"Retrieved status for VMID {vm_id}")
            return status
        except Exception as e:
            logger.error(f"Error retrieving status for VMID {vm_id}: {e}")
            return {}

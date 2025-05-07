"""
Repository for Windows VM Agent data.

This module provides database operations for Windows VM agents.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from db.repositories.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class WindowsVMAgentRepository(BaseRepository):
    """Repository for Windows VM Agent data."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the WindowsVMAgentRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "windows_vm_agents"
        self.id_column = "vm_id"
        self.default_columns = """
            vm_id, vm_name, status, ip_address, cpu_usage_percent,
            memory_usage_percent, disk_usage_percent, uptime_seconds,
            owner_id, last_seen, created_at, updated_at
        """
        self.default_order_by = "vm_id ASC"
        self.search_columns = ["vm_id", "vm_name", "ip_address"]

    def get_agent_by_vm_id(self, vm_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a Windows VM agent by VM ID.

        Args:
            vm_id (str): The VM ID.

        Returns:
            Optional[Dict[str, Any]]: The agent data or None if not found.
        """
        try:
            query = f"""
                SELECT {self.default_columns}
                FROM {self.table_name}
                WHERE vm_id = %s
            """
            return self.execute_query_single(query, (vm_id,))
        except Exception as e:
            logger.error(f"Error getting agent by VM ID: {e}")
            return None

    def verify_api_key(self, vm_id: str, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify an API key for a Windows VM agent.

        Args:
            vm_id (str): The VM ID.
            api_key (str): The API key to verify.

        Returns:
            Optional[Dict[str, Any]]: The agent data if the API key is valid, None otherwise.
        """
        try:
            logger.info(f"Verifying API key for VM ID: {vm_id}")

            # First, get the agent to check if it exists
            query = f"""
                SELECT {self.default_columns}
                FROM {self.table_name}
                WHERE vm_id = %s
            """
            agent = self.execute_query_single(query, (vm_id,))

            if not agent:
                logger.info(f"Agent not found for VM ID: {vm_id}")
                return None

            # Verify API key using the settings repository
            from ..repositories.settings import SettingsRepository
            settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

            # Convert vm_id to integer for the API key validation
            # The resource_id in the API keys table is an integer
            vm_id_int = None
            try:
                # Try to convert to integer if it's a numeric string
                if str(vm_id).isdigit():
                    vm_id_int = int(vm_id)
                    logger.info(f"Converted VM ID {vm_id} to integer: {vm_id_int}")
                else:
                    # If not numeric, use a hash of the string as the resource_id
                    # This allows non-numeric VM IDs to still work with the API key system
                    import hashlib
                    vm_id_hash = int(hashlib.md5(vm_id.encode()).hexdigest(), 16) % (10 ** 10)
                    vm_id_int = vm_id_hash
                    logger.info(f"Using hash for non-numeric VM ID {vm_id}: {vm_id_int}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting VM ID to integer: {vm_id}, error: {e}")
                # Use a fallback value
                vm_id_int = abs(hash(vm_id)) % (10 ** 10)
                logger.info(f"Using fallback hash for VM ID {vm_id}: {vm_id_int}")

            # Validate the API key
            api_key_data = settings_repo.validate_api_key(
                api_key=api_key,
                key_type="windows_vm",
                resource_id=vm_id_int
            )

            if not api_key_data:
                logger.info(f"API key validation failed for VM ID: {vm_id}")
                return None

            logger.info(f"API key validation successful for VM ID: {vm_id}")
            return agent
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def update_last_seen(self, vm_id: str) -> bool:
        """
        Update the last_seen timestamp for a Windows VM agent.

        Args:
            vm_id (str): The VM ID.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            query = f"""
                UPDATE {self.table_name}
                SET last_seen = NOW()
                WHERE vm_id = %s
            """
            self.execute_query(query, (vm_id,))
            return True
        except Exception as e:
            logger.error(f"Error updating last_seen: {e}")
            return False

    def update_status(
        self,
        vm_id: str,
        status: str,
        ip_address: Optional[str] = None,
        cpu_usage_percent: Optional[float] = None,
        memory_usage_percent: Optional[float] = None,
        disk_usage_percent: Optional[float] = None,
        uptime_seconds: Optional[int] = None
    ) -> bool:
        """
        Update the status of a Windows VM agent.

        Args:
            vm_id (str): The VM ID.
            status (str): The agent status.
            ip_address (Optional[str], optional): The IP address. Defaults to None.
            cpu_usage_percent (Optional[float], optional): The CPU usage percentage. Defaults to None.
            memory_usage_percent (Optional[float], optional): The memory usage percentage. Defaults to None.
            disk_usage_percent (Optional[float], optional): The disk usage percentage. Defaults to None.
            uptime_seconds (Optional[int], optional): The uptime in seconds. Defaults to None.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            query = f"""
                UPDATE {self.table_name}
                SET status = %s,
                    ip_address = COALESCE(%s, ip_address),
                    cpu_usage_percent = COALESCE(%s, cpu_usage_percent),
                    memory_usage_percent = COALESCE(%s, memory_usage_percent),
                    disk_usage_percent = COALESCE(%s, disk_usage_percent),
                    uptime_seconds = COALESCE(%s, uptime_seconds),
                    last_seen = NOW(),
                    updated_at = NOW()
                WHERE vm_id = %s
            """
            self.execute_query(
                query,
                (
                    status,
                    ip_address,
                    cpu_usage_percent,
                    memory_usage_percent,
                    disk_usage_percent,
                    uptime_seconds,
                    vm_id
                )
            )
            return True
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False

    def register_agent(
        self,
        vm_id: str,
        api_key: str,
        vm_name: Optional[str] = None,
        owner_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Register a new Windows VM agent.

        Args:
            vm_id (str): The VM ID (database ID from the vms table).
            api_key (str): The API key.
            vm_name (Optional[str], optional): The VM name. Defaults to None.
            owner_id (Optional[int], optional): The owner ID. Defaults to None.

        Returns:
            Optional[Dict[str, Any]]: The registered agent data or None if registration failed.
        """
        try:
            logger.info(f"Registering agent for VM ID: {vm_id}, VM Name: {vm_name}, Owner ID: {owner_id}")

            # Verify that the VM exists in the vms table
            from ..repositories.vms import VMRepository
            vm_repo = VMRepository(user_id=owner_id, user_role="user")

            # Convert vm_id to integer if it's a numeric string
            vm_id_int = None
            if str(vm_id).isdigit():
                vm_id_int = int(vm_id)

            # First check if the VM exists by ID
            vm = None
            if vm_id_int is not None:
                vm = vm_repo.get_vm_by_id(vm_id_int)

            if not vm:
                logger.error(f"VM with ID {vm_id} not found in the database")
                return None

            logger.info(f"Found VM in database: {vm['name']} (ID: {vm['id']}, VMID: {vm['vmid']})")

            # Use the VM name from the database if not provided
            if not vm_name:
                vm_name = vm['name']

            # First, register the agent in the windows_vm_agents table
            try:
                # The api_key column is required in the windows_vm_agents table
                # Use direct connection to bypass RLS
                from db.connection import get_db_connection

                logger.info(f"Using direct connection to insert agent for VM ID: {vm_id}")
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    try:
                        insert_query = f"""
                            INSERT INTO {self.table_name} (
                                vm_id, vm_name, status, owner_id, api_key
                            ) VALUES (
                                %s, %s, 'registered', %s, %s
                            )
                            RETURNING {self.default_columns}
                        """
                        logger.info(f"Executing query: {insert_query} with params: ({vm_id}, {vm_name}, {owner_id}, {api_key})")
                        cursor.execute(insert_query, (vm_id, vm_name, owner_id, api_key))

                        # Get the result
                        result = cursor.fetchone()
                        conn.commit()

                        if result:
                            # Convert to dict
                            columns = [desc[0] for desc in cursor.description]
                            agent = dict(zip(columns, result))
                            logger.info(f"Successfully inserted agent: {agent}")
                        else:
                            logger.error(f"Failed to insert agent for VM ID: {vm_id} - No rows returned")
                            return None
                    except Exception as e:
                        conn.rollback()
                        logger.error(f"Exception during direct SQL insert for VM ID {vm_id}: {e}")
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        return None

                # If we got here, the insert was successful
                logger.info(f"Successfully registered agent for VM ID: {vm_id}")
                return agent
            except Exception as e:
                logger.error(f"Exception during agent registration for VM ID {vm_id}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None

            # Now, create an API key for the agent
            from ..repositories.settings import SettingsRepository
            settings_repo = SettingsRepository(user_id=owner_id, user_role="user")

            # For the API key, we need to use the VM's database ID as the resource_id
            # This is required by the trigger that validates the resource_id in the api_keys table
            resource_id = vm['id']
            logger.info(f"Using VM database ID {resource_id} as resource_id for API key")

            # Create the API key
            api_key_data = settings_repo.create_api_key(
                user_id=owner_id,
                key_name=f"Windows VM {vm_name}",
                api_key=api_key,
                scopes=["read", "write"],
                key_type="windows_vm",
                resource_id=resource_id
            )

            if not api_key_data:
                logger.error(f"Failed to create API key for VM ID: {vm_id}")
                return None

            logger.info(f"Successfully registered agent for VM ID: {vm_id}")
            return agent
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def update_api_key(self, vm_id: str, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Update the API key for a Windows VM agent.

        Args:
            vm_id (str): The VM ID (database ID from the vms table).
            api_key (str): The new API key.

        Returns:
            Optional[Dict[str, Any]]: The updated agent data or None if the update failed.
        """
        try:
            logger.info(f"Updating API key for VM ID: {vm_id}")

            # First, get the agent to check if it exists and get the owner_id
            query = f"""
                SELECT {self.default_columns}
                FROM {self.table_name}
                WHERE vm_id = %s
            """
            agent = self.execute_query_single(query, (vm_id,))

            if not agent:
                logger.error(f"Agent not found for VM ID: {vm_id}")
                return None

            # Update the agent's updated_at timestamp
            update_query = f"""
                UPDATE {self.table_name}
                SET updated_at = NOW()
                WHERE vm_id = %s
                RETURNING {self.default_columns}
            """
            updated_agent = self.execute_query_single(update_query, (vm_id,))

            if not updated_agent:
                logger.error(f"Failed to update agent for VM ID: {vm_id}")
                return None

            # Verify that the VM exists in the vms table
            from ..repositories.vms import VMRepository
            vm_repo = VMRepository(user_id=agent["owner_id"], user_role="user")

            # Convert vm_id to integer if it's a numeric string
            vm_id_int = None
            if str(vm_id).isdigit():
                vm_id_int = int(vm_id)

            # First check if the VM exists by ID
            vm = None
            if vm_id_int is not None:
                vm = vm_repo.get_vm_by_id(vm_id_int)

            if not vm:
                logger.error(f"VM with ID {vm_id} not found in the database")
                return None

            logger.info(f"Found VM in database: {vm['name']} (ID: {vm['id']}, VMID: {vm['vmid']})")

            # Now, regenerate the API key
            from ..repositories.settings import SettingsRepository
            settings_repo = SettingsRepository(user_id=agent["owner_id"], user_role="user")

            # For the API key, we need to use the VM's database ID as the resource_id
            # This is required by the trigger that validates the resource_id in the api_keys table
            resource_id = vm['id']
            logger.info(f"Using VM database ID {resource_id} as resource_id for API key")

            # Regenerate the API key
            api_key_data = settings_repo.regenerate_api_key_for_resource(
                key_type="windows_vm",
                resource_id=resource_id,
                api_key=api_key
            )

            if not api_key_data:
                logger.error(f"Failed to regenerate API key for VM ID: {vm_id}")
                return None

            logger.info(f"Successfully updated API key for VM ID: {vm_id}")
            return updated_agent
        except Exception as e:
            logger.error(f"Error updating API key: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def get_agents(
        self,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a list of Windows VM agents with pagination and filtering.

        Args:
            limit (int, optional): The maximum number of agents to return. Defaults to 100.
            offset (int, optional): The number of agents to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter agents. Defaults to None.
            status (Optional[str], optional): Status to filter agents. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary with agents and pagination info.
        """
        try:
            # Build the condition
            condition = "1=1"
            params = []

            # Add search filter if provided
            if search:
                search_conditions = []
                for column in self.search_columns:
                    search_conditions.append(f"{column} ILIKE %s")
                    params.append(f"%{search}%")

                condition += f" AND ({' OR '.join(search_conditions)})"

            # Add status filter if provided
            if status:
                condition += " AND status = %s"
                params.append(status)

            # Get total count
            total = self.get_count(condition, tuple(params) if params else None)

            # Get agents
            agents = self.get_all(
                condition,
                tuple(params) if params else None,
                self.default_columns,
                self.default_order_by,
                limit,
                offset
            )

            return {
                "agents": agents,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Error getting agents: {e}")
            return {"agents": [], "total": 0, "limit": limit, "offset": offset}

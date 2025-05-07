"""
Proxmox node repository for database access.

This module provides a repository class for accessing Proxmox node data in the database.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from .base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class ProxmoxNodeRepository(BaseRepository):
    """Repository for Proxmox node data."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the ProxmoxNodeRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "proxmox_nodes"
        self.id_column = "id"
        self.default_columns = """
            id, name, hostname, port, status, whitelist, last_seen,
            created_at, updated_at, owner_id
        """
        self.default_order_by = "id DESC"
        self.search_columns = ["name", "hostname"]

    def get_nodes(self, limit: int = 10, offset: int = 0, search: Optional[str] = None,
                 status: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a list of Proxmox nodes with pagination and filtering.

        Args:
            limit (int, optional): Maximum number of nodes to return. Defaults to 10.
            offset (int, optional): Number of nodes to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter nodes. Defaults to None.
            status (Optional[str], optional): Filter by status. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary with nodes and pagination info.
        """
        try:
            # Build filter conditions
            condition = "1=1"
            params = []

            if status:
                condition += " AND status = %s"
                params.append(status)

            # Add search condition if provided
            if search:
                search_conditions = []
                for column in self.search_columns:
                    search_conditions.append(f"{column} ILIKE %s")
                search_condition = " OR ".join(search_conditions)
                condition += f" AND ({search_condition})"
                search_term = f"%{search}%"
                params.extend([search_term] * len(self.search_columns))

            # Convert params to tuple for database query
            params_tuple = tuple(params) if params else None

            # Disable cache for this query to avoid serialization issues
            from ..query_cache import cache_context

            # Get total count and nodes with cache disabled
            with cache_context(enable=False):
                # Get total count
                total = self.get_count(condition, params_tuple)

                # Get nodes
                nodes = self.get_all(condition, params_tuple,
                                    self.default_columns, self.default_order_by, limit, offset)

            return {
                "nodes": nodes,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Error in get_nodes: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_node_by_id(self, node_id: int, bypass_rls: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a specific Proxmox node by ID.

        Args:
            node_id (int): The ID of the node.
            bypass_rls (bool, optional): Whether to bypass RLS. Defaults to False.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the node or None if not found.
        """
        try:
            # Validate node_id is a valid integer
            try:
                node_id_int = int(node_id)
                if str(node_id_int) != str(node_id):
                    logger.error(f"Invalid node_id: {node_id} (not a valid integer)")
                    return None
            except (ValueError, TypeError):
                logger.error(f"Invalid node_id: {node_id} (not a valid integer)")
                return None

            # Disable cache for this query to avoid serialization issues
            from ..query_cache import cache_context

            logger.info(f"get_node_by_id called with node_id={node_id_int}, bypass_rls={bypass_rls}")

            if bypass_rls:
                # Use direct SQL query to bypass RLS
                query = f"""
                    SELECT
                        id, name, hostname, port, status, whitelist,
                        last_seen, created_at, updated_at, owner_id
                    FROM {self.table_name}
                    WHERE {self.id_column} = %s
                """

                logger.info(f"Executing direct SQL query: {query} with params: {(node_id,)}")

                # Use a direct connection without RLS and without cache
                try:
                    # Use a direct connection to the database
                    import psycopg2
                    from config import Config

                    # Create a direct connection to the database
                    logger.info(f"Connecting to database: host={Config.DB_HOST}, port={Config.DB_PORT}, dbname={Config.DB_NAME}, user=postgres")
                    conn = psycopg2.connect(
                        host=Config.DB_HOST,
                        port=Config.DB_PORT,
                        dbname=Config.DB_NAME,
                        user="postgres",
                        password="CHANGEME_ULTRASECURE"
                    )
                    logger.info("Database connection established")

                    try:
                        cursor = conn.cursor()
                        try:
                            logger.info(f"Executing query: {query} with params: {(node_id_int,)}")
                            cursor.execute(query, (node_id_int,))
                            logger.info("Query executed successfully")

                            if not cursor.description:
                                logger.info("No description returned from cursor")
                                return None

                            columns = [desc[0] for desc in cursor.description]
                            logger.info(f"Columns: {columns}")

                            result = cursor.fetchone()
                            logger.info(f"Raw result: {result}")

                            if result:
                                node = dict(zip(columns, result))
                                logger.info(f"Direct SQL query result: {node}")
                                return node
                            else:
                                logger.info("Direct SQL query result: None")
                                return None
                        except Exception as e:
                            logger.error(f"Error executing direct query: {e}")
                            return None
                        finally:
                            cursor.close()
                    finally:
                        conn.close()
                except Exception as e:
                    logger.error(f"Error getting database connection: {e}")
                    return None
            else:
                # Execute query with cache disabled
                logger.info(f"Using get_by_id with node_id={node_id_int}")
                with cache_context(enable=False):
                    result = self.get_by_id(node_id_int)
                    logger.info(f"get_by_id result: {result}")
                    return result
        except Exception as e:
            logger.error(f"Error in get_node_by_id: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def create_node(self, node_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new Proxmox node.

        Args:
            node_data (Dict[str, Any]): The node data.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created node or None if creation failed.
        """
        return self.create(node_data)

    def update_node(self, node_id: int, node_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a Proxmox node.

        Args:
            node_id (int): The ID of the node.
            node_data (Dict[str, Any]): The node data to update.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated node or None if update failed.
        """
        return self.update(node_id, node_data, returning=True)

    def delete_node(self, node_id: int) -> bool:
        """
        Delete a Proxmox node.

        Args:
            node_id (int): The ID of the node.

        Returns:
            bool: True if the node was deleted, False otherwise.
        """
        return self.delete(node_id) > 0

    def get_agent_vms(self, node_id: int, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Get all VMs for a specific Proxmox node for the agent.

        Args:
            node_id (int): The ID of the node.
            api_key (str): The API key for authentication.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with VMs or None if authentication failed.
        """
        try:
            # Validate node_id is a valid integer
            try:
                node_id_int = int(node_id)
                if str(node_id_int) != str(node_id):
                    logger.error(f"Invalid node_id: {node_id} (not a valid integer)")
                    return None
            except (ValueError, TypeError):
                logger.error(f"Invalid node_id: {node_id} (not a valid integer)")
                return None

            logger.info(f"Getting agent VMs for node_id={node_id_int}")

            # First, verify the node exists
            node_query = """
                SELECT id
                FROM proxmox_nodes
                WHERE id = %s
            """
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

            # Execute the query
            logger.info(f"Executing direct query: {node_query} with params: {node_id}")
            cursor.execute(node_query, (node_id,))
            logger.info(f"Direct query executed successfully")

            # Fetch the result
            result = cursor.fetchone()
            logger.info(f"Fetch result: {result}")

            # Close the cursor and connection
            cursor.close()
            conn.close()

            if result:
                node_result = [dict(result)]
                logger.info(f"Node result: {node_result}")
            else:
                node_result = []
                logger.info(f"No result found for node_id={node_id_int}")

            if not node_result:
                logger.info(f"No node found with id={node_id_int}")
                return None

            # Verify API key using the settings repository
            from ..repositories.settings import SettingsRepository
            settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

            # Validate the API key
            api_key_data = settings_repo.validate_api_key(
                api_key=api_key,
                key_type="proxmox_node",
                resource_id=node_id_int
            )

            if not api_key_data:
                logger.info(f"API key validation failed for node_id={node_id_int}")
                return None

            logger.info(f"API key verified for node_id={node_id_int}")

            # Get all VMs for this node
            vms_query = """
                SELECT
                    id, vmid, name, status, cpu_cores, cpu_usage_percent, memory_mb,
                    disk_gb, ip_address, proxmox_node_id, owner_id,
                    created_at, updated_at
                FROM vms
                WHERE proxmox_node_id = %s
            """
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

            # Execute the query
            logger.info(f"Executing direct query: {vms_query} with params: {node_id_int}")
            cursor.execute(vms_query, (node_id_int,))
            logger.info(f"Direct query executed successfully")

            # Fetch the results
            results = cursor.fetchall()
            logger.info(f"Fetch results: {len(results)} rows")

            # Convert the results to a list of dictionaries
            vms = [dict(row) for row in results]

            # Close the cursor and connection
            cursor.close()
            conn.close()

            logger.info(f"Found {len(vms)} VMs for node_id={node_id_int}")

            return {
                "vms": vms,
                "count": len(vms),
                "node_id": node_id_int
            }
        except Exception as e:
            logger.error(f"Error in get_agent_vms: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_agent_whitelist(self, node_id: int, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Get the whitelist for a specific Proxmox node for the agent.

        Args:
            node_id (int): The ID of the node.
            api_key (str): The API key for authentication.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with whitelist or None if authentication failed.
        """
        try:
            # Validate node_id is a valid integer
            try:
                node_id_int = int(node_id)
                if str(node_id_int) != str(node_id):
                    logger.error(f"Invalid node_id: {node_id} (not a valid integer)")
                    return None
            except (ValueError, TypeError):
                logger.error(f"Invalid node_id: {node_id} (not a valid integer)")
                return None

            logger.info(f"Getting agent whitelist for node_id={node_id_int}")

            # First, verify the node exists
            node_query = """
                SELECT id, whitelist
                FROM proxmox_nodes
                WHERE id = %s
            """
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

            # Execute the query
            logger.info(f"Executing direct query: {node_query} with params: {node_id}")
            cursor.execute(node_query, (node_id,))
            logger.info(f"Direct query executed successfully")

            # Fetch the result
            result = cursor.fetchone()
            logger.info(f"Fetch result: {result}")

            # Close the cursor and connection
            cursor.close()
            conn.close()

            if result:
                node_result = [dict(result)]
                logger.info(f"Node result: {node_result}")
            else:
                node_result = []
                logger.info(f"No result found for node_id={node_id_int}")

            if not node_result:
                logger.info(f"No node found with id={node_id_int}")
                return None

            whitelist = node_result[0]['whitelist'] or []

            logger.info(f"Node id={node_id_int} has whitelist with {len(whitelist)} items")
            logger.info(f"Provided api_key={api_key[:5]}...")

            # Verify API key using the settings repository
            from ..repositories.settings import SettingsRepository
            settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

            # Validate the API key
            api_key_data = settings_repo.validate_api_key(
                api_key=api_key,
                key_type="proxmox_node",
                resource_id=node_id_int
            )

            if not api_key_data:
                logger.info(f"API key validation failed for node_id={node_id_int}")
                return None

            logger.info(f"API key verified for node_id={node_id_int}")
            return {
                "whitelist": whitelist,
                "count": len(whitelist),
                "node_id": node_id_int
            }
        except Exception as e:
            logger.error(f"Error in get_agent_whitelist: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def update_node_status(self, node_id: int, status: str) -> bool:
        """
        Update the status of a Proxmox node.

        Args:
            node_id (int): The ID of the node.
            status (str): The new status.

        Returns:
            bool: True if the status was updated, False otherwise.
        """
        try:
            # Ensure node_id is a valid integer
            if node_id is None or node_id == "" or node_id == 0:
                logger.error(f"Invalid node_id: {node_id}")
                return False

            # Convert to integer if it's not already
            if not isinstance(node_id, int):
                try:
                    node_id_int = int(node_id)
                except (ValueError, TypeError):
                    logger.error(f"Cannot convert node_id to integer: {node_id}")
                    return False
            else:
                node_id_int = node_id

            logger.info(f"Updating node status: node_id={node_id_int}, status={status}")

            update_query = """
                UPDATE proxmox_nodes
                SET status = %s, last_seen = NOW()
                WHERE id = %s
            """
            # Ensure both parameters are properly typed
            logger.debug(f"Executing update query with params: status={status} (type: {type(status)}), node_id={node_id_int} (type: {type(node_id_int)})")
            result = self.execute_command(update_query, (status, node_id_int), with_rls=False)

            if result > 0:
                logger.info(f"Successfully updated status for node_id={node_id_int}")
                return True
            else:
                logger.warning(f"No rows affected when updating status for node_id={node_id_int}")
                return False
        except Exception as e:
            logger.error(f"Error in update_node_status: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def get_nodes_by_status(self, status: str) -> Dict[str, Any]:
        """
        Get a list of Proxmox nodes filtered by status.

        Args:
            status (str): The status to filter by.

        Returns:
            Dict[str, Any]: A dictionary with nodes and pagination info.
        """
        try:
            # Call the existing get_nodes method with the status parameter
            return self.get_nodes(limit=100, offset=0, status=status)
        except Exception as e:
            logger.error(f"Error in get_nodes_by_status: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

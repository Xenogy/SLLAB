"""
Direct test script for Windows VM agent registration.

This script directly tests the Windows VM agent registration process by
bypassing the API endpoints and directly calling the repository methods.
"""

import logging
import sys
import secrets
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import the repository classes
from db.repositories.vms import VMRepository
from db.repositories.windows_vm_agent import WindowsVMAgentRepository

def generate_api_key() -> str:
    """Generate a random API key."""
    return secrets.token_urlsafe(32)

def test_direct_register():
    """
    Test the Windows VM agent registration directly.
    """
    try:
        # Use admin role to bypass RLS
        vm_repo = VMRepository(user_id=1, user_role="admin")

        # List all VMs in the database
        logger.info("Listing all VMs in the database:")
        vms = vm_repo.get_all()

        if not vms:
            logger.error("No VMs found in the database")
            return

        for vm in vms:
            logger.info(f"VM: id={vm['id']}, vmid={vm['vmid']}, name={vm['name']}, owner_id={vm['owner_id']}")

        # Use the first VM for testing
        test_vm = vms[0]
        vm_id = str(test_vm['id'])
        vm_name = test_vm['name']
        owner_id = test_vm['owner_id']

        logger.info(f"Testing with VM: id={vm_id}, name={vm_name}, owner_id={owner_id}")

        # Generate API key
        api_key = generate_api_key()
        logger.info(f"Generated API key: {api_key}")

        # Register the agent
        agent_repo = WindowsVMAgentRepository(user_id=owner_id, user_role="user")

        # First, check if an agent already exists for this VM
        existing_agent = agent_repo.get_agent_by_vm_id(vm_id)
        if existing_agent:
            logger.info(f"Agent already exists for VM ID: {vm_id}")

            # Update the API key
            updated_agent = agent_repo.update_api_key(vm_id, api_key)
            if updated_agent:
                logger.info(f"Successfully updated API key for VM ID: {vm_id}")
                return
            else:
                logger.error(f"Failed to update API key for VM ID: {vm_id}")
                return

        # Try to register a new agent using direct SQL
        try:
            from db.access import DatabaseAccess
            db_access = DatabaseAccess(user_id=1, user_role="admin")

            # First, check if an agent already exists
            query = "SELECT vm_id FROM windows_vm_agents WHERE vm_id = %s"
            result = db_access.execute_query_single(query, (vm_id,))

            if result:
                logger.info(f"Agent already exists for VM ID: {vm_id}")

                # Update the agent
                update_query = """
                    UPDATE windows_vm_agents
                    SET api_key = %s, updated_at = NOW()
                    WHERE vm_id = %s
                    RETURNING vm_id, vm_name, status
                """
                updated = db_access.execute_query_single(update_query, (api_key, vm_id))

                if updated:
                    logger.info(f"Successfully updated agent for VM ID: {vm_id}")
                    logger.info(f"Updated agent: {updated}")
                else:
                    logger.error(f"Failed to update agent for VM ID: {vm_id}")
            else:
                # Insert a new agent
                try:
                    # Try with execute_insert method
                    logger.info("Trying with execute_insert method...")
                    insert_data = {
                        "vm_id": vm_id,
                        "vm_name": vm_name,
                        "status": "registered",
                        "owner_id": owner_id,
                        "api_key": api_key
                    }
                    inserted = db_access.execute_insert("windows_vm_agents", insert_data, True, True)

                    if inserted:
                        logger.info(f"Successfully inserted agent for VM ID: {vm_id}")
                        logger.info(f"Inserted agent: {inserted}")
                    else:
                        logger.error(f"Failed to insert agent with execute_insert for VM ID: {vm_id}")

                        # Try with direct execute_query method
                        logger.info("Trying with direct execute_query method...")
                        insert_query = """
                            INSERT INTO windows_vm_agents (vm_id, vm_name, status, owner_id, api_key)
                            VALUES (%s, %s, 'registered', %s, %s)
                            RETURNING vm_id, vm_name, status
                        """
                        inserted = db_access.execute_query_single(insert_query, (vm_id, vm_name, owner_id, api_key))

                        if inserted:
                            logger.info(f"Successfully inserted agent for VM ID: {vm_id}")
                            logger.info(f"Inserted agent: {inserted}")
                        else:
                            logger.error(f"Failed to insert agent with execute_query_single for VM ID: {vm_id}")

                            # Try with direct SQL through psycopg2
                            logger.info("Trying with direct psycopg2 connection...")
                            from db.connection import get_db_connection
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    """
                                    INSERT INTO windows_vm_agents (vm_id, vm_name, status, owner_id, api_key)
                                    VALUES (%s, %s, 'registered', %s, %s)
                                    """,
                                    (vm_id, vm_name, owner_id, api_key)
                                )
                                conn.commit()
                                logger.info(f"Direct SQL insert completed with rowcount: {cursor.rowcount}")
                except Exception as e:
                    logger.error(f"Error inserting agent: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

        except Exception as e:
            logger.error(f"Error executing direct SQL: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    except Exception as e:
        logger.error(f"Error in test_direct_register: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_direct_register()

"""
Script to standardize RLS policies across all tables.

This script creates or updates RLS policies for all tables that should have RLS.
It ensures that each table has policies for admin users and regular users.
"""

import logging
import argparse
import psycopg2
from typing import List, Dict, Any, Optional
from config import Config
from db.connection import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_tables_with_rls() -> List[str]:
    """
    Get a list of tables that should have RLS.
    
    Returns:
        List[str]: A list of table names.
    """
    return [
        "accounts",
        "hardware",
        "cards",
        "vms",
        "proxmox_nodes",
        "whitelist",
        # Add more tables as needed
    ]

def check_rls_enabled(cursor, table: str) -> bool:
    """
    Check if RLS is enabled for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if RLS is enabled, False otherwise
    """
    try:
        cursor.execute(f"""
            SELECT relrowsecurity
            FROM pg_class
            WHERE relname = %s AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
        """, (table,))
        result = cursor.fetchone()
        return result and result[0]
    except Exception as e:
        logger.error(f"Error checking if RLS is enabled for table {table}: {e}")
        return False

def enable_rls(cursor, table: str) -> bool:
    """
    Enable RLS for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        logger.info(f"Enabled RLS for table {table}")
        return True
    except Exception as e:
        logger.error(f"Error enabling RLS for table {table}: {e}")
        return False

def check_owner_id_column(cursor, table: str) -> bool:
    """
    Check if a table has an owner_id column.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if the column exists, False otherwise
    """
    try:
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                AND column_name = 'owner_id'
            );
        """, (table,))
        result = cursor.fetchone()
        return result and result[0]
    except Exception as e:
        logger.error(f"Error checking if owner_id column exists for table {table}: {e}")
        return False

def get_existing_policies(cursor, table: str) -> List[str]:
    """
    Get a list of existing RLS policies for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        List[str]: A list of policy names
    """
    try:
        cursor.execute(f"""
            SELECT polname
            FROM pg_policy
            WHERE polrelid = %s::regclass;
        """, (table,))
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting existing policies for table {table}: {e}")
        return []

def create_admin_policy(cursor, table: str) -> bool:
    """
    Create an admin policy for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if successful, False otherwise
    """
    policy_name = f"{table}_admin_policy"
    try:
        cursor.execute(f"""
            CREATE POLICY {policy_name} ON {table}
            FOR ALL
            TO PUBLIC
            USING (current_setting('app.current_user_role', TRUE) = 'admin');
        """)
        logger.info(f"Created admin policy for table {table}")
        return True
    except Exception as e:
        logger.error(f"Error creating admin policy for table {table}: {e}")
        return False

def create_user_select_policy(cursor, table: str) -> bool:
    """
    Create a user SELECT policy for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if successful, False otherwise
    """
    policy_name = f"{table}_user_select_policy"
    try:
        cursor.execute(f"""
            CREATE POLICY {policy_name} ON {table}
            FOR SELECT
            TO PUBLIC
            USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        logger.info(f"Created user SELECT policy for table {table}")
        return True
    except Exception as e:
        logger.error(f"Error creating user SELECT policy for table {table}: {e}")
        return False

def create_user_insert_policy(cursor, table: str) -> bool:
    """
    Create a user INSERT policy for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if successful, False otherwise
    """
    policy_name = f"{table}_user_insert_policy"
    try:
        cursor.execute(f"""
            CREATE POLICY {policy_name} ON {table}
            FOR INSERT
            TO PUBLIC
            WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        logger.info(f"Created user INSERT policy for table {table}")
        return True
    except Exception as e:
        logger.error(f"Error creating user INSERT policy for table {table}: {e}")
        return False

def create_user_update_policy(cursor, table: str) -> bool:
    """
    Create a user UPDATE policy for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if successful, False otherwise
    """
    policy_name = f"{table}_user_update_policy"
    try:
        cursor.execute(f"""
            CREATE POLICY {policy_name} ON {table}
            FOR UPDATE
            TO PUBLIC
            USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER)
            WITH CHECK (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        logger.info(f"Created user UPDATE policy for table {table}")
        return True
    except Exception as e:
        logger.error(f"Error creating user UPDATE policy for table {table}: {e}")
        return False

def create_user_delete_policy(cursor, table: str) -> bool:
    """
    Create a user DELETE policy for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        
    Returns:
        bool: True if successful, False otherwise
    """
    policy_name = f"{table}_user_delete_policy"
    try:
        cursor.execute(f"""
            CREATE POLICY {policy_name} ON {table}
            FOR DELETE
            TO PUBLIC
            USING (owner_id = current_setting('app.current_user_id', TRUE)::INTEGER);
        """)
        logger.info(f"Created user DELETE policy for table {table}")
        return True
    except Exception as e:
        logger.error(f"Error creating user DELETE policy for table {table}: {e}")
        return False

def drop_policy(cursor, table: str, policy_name: str) -> bool:
    """
    Drop a policy from a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        policy_name (str): Policy name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table};")
        logger.info(f"Dropped policy {policy_name} from table {table}")
        return True
    except Exception as e:
        logger.error(f"Error dropping policy {policy_name} from table {table}: {e}")
        return False

def standardize_table_policies(cursor, table: str, drop_existing: bool = False) -> bool:
    """
    Standardize RLS policies for a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        drop_existing (bool, optional): Whether to drop existing policies. Defaults to False.
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if the table exists
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        );
    """, (table,))
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        logger.warning(f"Table {table} does not exist")
        return False
    
    # Check if the table has an owner_id column
    has_owner_id = check_owner_id_column(cursor, table)
    
    if not has_owner_id:
        logger.warning(f"Table {table} does not have an owner_id column")
        return False
    
    # Enable RLS if not already enabled
    if not check_rls_enabled(cursor, table):
        if not enable_rls(cursor, table):
            return False
    
    # Get existing policies
    existing_policies = get_existing_policies(cursor, table)
    
    # Drop existing policies if requested
    if drop_existing:
        for policy in existing_policies:
            drop_policy(cursor, table, policy)
        existing_policies = []
    
    # Create admin policy if it doesn't exist
    admin_policy = f"{table}_admin_policy"
    if admin_policy not in existing_policies:
        if not create_admin_policy(cursor, table):
            return False
    
    # Create user SELECT policy if it doesn't exist
    user_select_policy = f"{table}_user_select_policy"
    if user_select_policy not in existing_policies:
        if not create_user_select_policy(cursor, table):
            return False
    
    # Create user INSERT policy if it doesn't exist
    user_insert_policy = f"{table}_user_insert_policy"
    if user_insert_policy not in existing_policies:
        if not create_user_insert_policy(cursor, table):
            return False
    
    # Create user UPDATE policy if it doesn't exist
    user_update_policy = f"{table}_user_update_policy"
    if user_update_policy not in existing_policies:
        if not create_user_update_policy(cursor, table):
            return False
    
    # Create user DELETE policy if it doesn't exist
    user_delete_policy = f"{table}_user_delete_policy"
    if user_delete_policy not in existing_policies:
        if not create_user_delete_policy(cursor, table):
            return False
    
    return True

def standardize_all_policies(drop_existing: bool = False) -> Dict[str, bool]:
    """
    Standardize RLS policies for all tables.
    
    Args:
        drop_existing (bool, optional): Whether to drop existing policies. Defaults to False.
        
    Returns:
        Dict[str, bool]: A dictionary with table names as keys and success status as values
    """
    results = {}
    
    with get_db_connection() as conn:
        if not conn:
            logger.error("No database connection available")
            return results
        
        cursor = conn.cursor()
        try:
            # Get tables with RLS
            tables = get_tables_with_rls()
            
            # Standardize policies for each table
            for table in tables:
                results[table] = standardize_table_policies(cursor, table, drop_existing)
            
            # Commit changes
            conn.commit()
        except Exception as e:
            logger.error(f"Error standardizing RLS policies: {e}")
            conn.rollback()
        finally:
            cursor.close()
    
    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Standardize RLS policies across all tables.')
    parser.add_argument('--drop-existing', action='store_true', help='Drop existing policies before creating new ones')
    args = parser.parse_args()
    
    results = standardize_all_policies(args.drop_existing)
    
    # Print results
    logger.info("RLS policy standardization results:")
    for table, success in results.items():
        logger.info(f"  {table}: {'Success' if success else 'Failed'}")

if __name__ == "__main__":
    main()

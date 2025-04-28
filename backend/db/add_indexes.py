"""
Script to add indexes to improve database performance.

This script adds indexes to tables to improve query performance.
"""

import logging
import argparse
from typing import List, Dict, Any, Optional
from db.connection import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_indexes_to_add() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get a dictionary of indexes to add.
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary with table names as keys and lists of indexes as values.
    """
    return {
        "accounts": [
            {"name": "idx_accounts_owner_id", "columns": ["owner_id"]},
            {"name": "idx_accounts_acc_username", "columns": ["acc_username"]},
            {"name": "idx_accounts_acc_email_address", "columns": ["acc_email_address"]},
            {"name": "idx_accounts_prime", "columns": ["prime"]},
            {"name": "idx_accounts_lock", "columns": ["lock"]},
            {"name": "idx_accounts_perm_lock", "columns": ["perm_lock"]}
        ],
        "hardware": [
            {"name": "idx_hardware_owner_id", "columns": ["owner_id"]},
            {"name": "idx_hardware_account_id", "columns": ["account_id"]},
            {"name": "idx_hardware_type", "columns": ["type"]}
        ],
        "vms": [
            {"name": "idx_vms_owner_id", "columns": ["owner_id"]},
            {"name": "idx_vms_proxmox_node_id", "columns": ["proxmox_node_id"]},
            {"name": "idx_vms_vmid", "columns": ["vmid"]},
            {"name": "idx_vms_status", "columns": ["status"]}
        ],
        "proxmox_nodes": [
            {"name": "idx_proxmox_nodes_owner_id", "columns": ["owner_id"]},
            {"name": "idx_proxmox_nodes_status", "columns": ["status"]}
        ],
        "whitelist": [
            {"name": "idx_whitelist_vm_id", "columns": ["vm_id"]},
            {"name": "idx_whitelist_user_id", "columns": ["user_id"]}
        ],
        "users": [
            {"name": "idx_users_username", "columns": ["username"]},
            {"name": "idx_users_email", "columns": ["email"]},
            {"name": "idx_users_is_admin", "columns": ["is_admin"]}
        ],
        "cards": [
            {"name": "idx_cards_owner_id", "columns": ["owner_id"]},
            {"name": "idx_cards_account_id", "columns": ["account_id"]}
        ]
    }

def check_index_exists(cursor, table: str, index_name: str) -> bool:
    """
    Check if an index exists.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        index_name (str): Index name
        
    Returns:
        bool: True if the index exists, False otherwise
    """
    try:
        cursor.execute("""
            SELECT 1
            FROM pg_indexes
            WHERE tablename = %s AND indexname = %s;
        """, (table, index_name))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking if index {index_name} exists on table {table}: {e}")
        return False

def add_index(cursor, table: str, index: Dict[str, Any]) -> bool:
    """
    Add an index to a table.
    
    Args:
        cursor: Database cursor
        table (str): Table name
        index (Dict[str, Any]): Index definition
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        index_name = index["name"]
        columns = index["columns"]
        
        # Check if index already exists
        if check_index_exists(cursor, table, index_name):
            logger.info(f"Index {index_name} already exists on table {table}")
            return True
        
        # Create the index
        columns_str = ", ".join(columns)
        cursor.execute(f"CREATE INDEX {index_name} ON {table} ({columns_str});")
        logger.info(f"Created index {index_name} on table {table}")
        return True
    except Exception as e:
        logger.error(f"Error adding index to table {table}: {e}")
        return False

def add_all_indexes() -> Dict[str, Dict[str, int]]:
    """
    Add all indexes.
    
    Returns:
        Dict[str, Dict[str, int]]: A dictionary with table names as keys and dictionaries of stats as values.
    """
    results = {}
    
    with get_db_connection() as conn:
        if not conn:
            logger.error("No database connection available")
            return results
        
        cursor = conn.cursor()
        try:
            # Get indexes to add
            indexes_to_add = get_indexes_to_add()
            
            # Add indexes for each table
            for table, indexes in indexes_to_add.items():
                table_results = {
                    "total": len(indexes),
                    "added": 0,
                    "skipped": 0,
                    "failed": 0
                }
                
                for index in indexes:
                    if check_index_exists(cursor, table, index["name"]):
                        table_results["skipped"] += 1
                    elif add_index(cursor, table, index):
                        table_results["added"] += 1
                    else:
                        table_results["failed"] += 1
                
                results[table] = table_results
            
            # Commit changes
            conn.commit()
        except Exception as e:
            logger.error(f"Error adding indexes: {e}")
            conn.rollback()
        finally:
            cursor.close()
    
    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Add indexes to improve database performance.')
    args = parser.parse_args()
    
    results = add_all_indexes()
    
    # Print results
    logger.info("Index addition results:")
    for table, stats in results.items():
        logger.info(f"  {table}: {stats['added']} added, {stats['skipped']} skipped, {stats['failed']} failed, {stats['total']} total")

if __name__ == "__main__":
    main()

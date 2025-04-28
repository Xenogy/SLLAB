"""
Test script for Row-Level Security (RLS) implementation.

This script tests the RLS implementation by:
1. Verifying that RLS is set up correctly
2. Testing RLS policies for different users
3. Testing the SecureDatabase class with RLS enforcement
"""

import logging
import sys
import os
import json
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db_connection
from db.rls_context import verify_rls_setup, test_rls_policies, set_rls_context, clear_rls_context
from db.secure_access import get_secure_db, secure_db_context, with_secure_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_rls_setup():
    """
    Test that RLS is set up correctly.
    """
    logger.info("Testing RLS setup...")
    
    with get_db_connection() as conn:
        if not conn:
            logger.error("No database connection available")
            return False
        
        results = verify_rls_setup(conn)
        
        if not results["success"]:
            logger.error(f"RLS setup verification failed: {results.get('error', 'Unknown error')}")
            return False
        
        # Check if app schema exists
        if not results.get("app_schema_exists", False):
            logger.error("App schema does not exist")
            return False
        
        # Check if set_rls_context function exists
        if not results.get("set_rls_context_exists", False):
            logger.error("set_rls_context function does not exist")
            return False
        
        # Check if tables exist and have RLS enabled
        for table, table_info in results.get("tables", {}).items():
            if not table_info.get("exists", False):
                logger.warning(f"Table {table} does not exist")
                continue
            
            if not table_info.get("rls_enabled", False):
                logger.error(f"RLS is not enabled for table {table}")
                return False
            
            if not table_info.get("owner_id_exists", False):
                logger.error(f"owner_id column does not exist for table {table}")
                return False
        
        # Check if RLS policies exist
        for table, policy_info in results.get("policies", {}).items():
            if policy_info.get("count", 0) < 2:
                logger.error(f"Not enough RLS policies for table {table}: {policy_info.get('count', 0)}")
                return False
        
        # Check if RLS views exist
        for table, view_info in results.get("views", {}).items():
            if not view_info.get("exists", False):
                logger.error(f"RLS view does not exist for table {table}")
                return False
        
        logger.info("RLS setup verification successful")
        return True

def test_rls_policies_for_users():
    """
    Test RLS policies for different users.
    """
    logger.info("Testing RLS policies for different users...")
    
    with get_db_connection() as conn:
        if not conn:
            logger.error("No database connection available")
            return False
        
        # Test admin user
        admin_results = test_rls_policies(conn, 1, "admin")
        if not admin_results["success"]:
            logger.error(f"RLS policy test failed for admin user: {admin_results.get('error', 'Unknown error')}")
            return False
        
        # Test regular user
        user_results = test_rls_policies(conn, 2, "user")
        if not user_results["success"]:
            logger.error(f"RLS policy test failed for regular user: {user_results.get('error', 'Unknown error')}")
            return False
        
        # Check if RLS is working correctly
        for table, table_info in admin_results.get("tables", {}).items():
            if "error" in table_info:
                logger.error(f"Error testing RLS for table {table} (admin): {table_info['error']}")
                return False
            
            if not table_info.get("rls_working", False):
                logger.error(f"RLS is not working correctly for table {table} (admin)")
                return False
        
        for table, table_info in user_results.get("tables", {}).items():
            if "error" in table_info:
                logger.error(f"Error testing RLS for table {table} (user): {table_info['error']}")
                return False
            
            if not table_info.get("rls_working", False):
                logger.error(f"RLS is not working correctly for table {table} (user)")
                return False
        
        logger.info("RLS policy tests successful")
        return True

def test_secure_database():
    """
    Test the SecureDatabase class with RLS enforcement.
    """
    logger.info("Testing SecureDatabase class...")
    
    # Test admin user
    with get_secure_db(user_id=1, user_role="admin") as db:
        # Test query execution
        accounts = db.get_all("accounts")
        logger.info(f"Admin user can see {len(accounts)} accounts")
        
        # Test command execution
        count = db.count("accounts")
        logger.info(f"Admin user can see {count} accounts (count)")
        
        # Test transaction
        with db.transaction():
            # Insert a test account
            db.insert("accounts", {
                "acc_id": "test_admin",
                "acc_username": "test_admin",
                "acc_password": "password",
                "owner_id": 1
            })
            
            # Verify the account was inserted
            test_account = db.get_by_id("accounts", "acc_id", "test_admin")
            if not test_account:
                logger.error("Failed to insert test account (admin)")
                return False
            
            # Delete the test account
            db.delete("accounts", "acc_id = %s", ("test_admin",))
            
            # Verify the account was deleted
            test_account = db.get_by_id("accounts", "acc_id", "test_admin")
            if test_account:
                logger.error("Failed to delete test account (admin)")
                return False
    
    # Test regular user
    with get_secure_db(user_id=2, user_role="user") as db:
        # Test query execution
        accounts = db.get_all("accounts")
        logger.info(f"Regular user can see {len(accounts)} accounts")
        
        # Test command execution
        count = db.count("accounts")
        logger.info(f"Regular user can see {count} accounts (count)")
        
        # Test transaction
        with db.transaction():
            # Insert a test account
            db.insert("accounts", {
                "acc_id": "test_user",
                "acc_username": "test_user",
                "acc_password": "password",
                "owner_id": 2
            })
            
            # Verify the account was inserted
            test_account = db.get_by_id("accounts", "acc_id", "test_user")
            if not test_account:
                logger.error("Failed to insert test account (user)")
                return False
            
            # Delete the test account
            db.delete("accounts", "acc_id = %s", ("test_user",))
            
            # Verify the account was deleted
            test_account = db.get_by_id("accounts", "acc_id", "test_user")
            if test_account:
                logger.error("Failed to delete test account (user)")
                return False
    
    # Test context manager
    with secure_db_context(user_id=1, user_role="admin") as db:
        accounts = db.get_all("accounts")
        logger.info(f"Admin user can see {len(accounts)} accounts (context manager)")
    
    # Test decorator
    @with_secure_db()
    def get_accounts(db, user_id=None, user_role=None):
        return db.get_all("accounts")
    
    admin_accounts = get_accounts(user_id=1, user_role="admin")
    logger.info(f"Admin user can see {len(admin_accounts)} accounts (decorator)")
    
    user_accounts = get_accounts(user_id=2, user_role="user")
    logger.info(f"Regular user can see {len(user_accounts)} accounts (decorator)")
    
    logger.info("SecureDatabase tests successful")
    return True

def main():
    """
    Main function.
    """
    logger.info("Starting RLS tests...")
    
    # Test RLS setup
    if not test_rls_setup():
        logger.error("RLS setup test failed")
        return 1
    
    # Test RLS policies
    if not test_rls_policies_for_users():
        logger.error("RLS policy test failed")
        return 1
    
    # Test SecureDatabase
    if not test_secure_database():
        logger.error("SecureDatabase test failed")
        return 1
    
    logger.info("All RLS tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
Test script for Phase 1 of the Database and RLS Improvements.

This script tests the database access layer, repository pattern, and RLS implementation.
"""

import logging
import sys
from typing import Dict, Any, List, Optional

from db.access import DatabaseAccess
from db.repositories.accounts import AccountRepository
from db.repositories.proxmox_nodes import ProxmoxNodeRepository
from db.repositories.vms import VMRepository
from db.repositories.hardware import HardwareRepository
from db.repositories.users import UserRepository
from db.connection import get_db_connection
from db.user_connection import get_user_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_access():
    """Test the DatabaseAccess class."""
    logger.info("Testing DatabaseAccess class...")
    
    # Create a DatabaseAccess instance without RLS context
    db_access = DatabaseAccess()
    
    # Test execute_query
    results = db_access.execute_query("SELECT 1 as test")
    assert results and len(results) == 1 and results[0]["test"] == 1, "execute_query failed"
    logger.info("execute_query test passed")
    
    # Test execute_query_single
    result = db_access.execute_query_single("SELECT 1 as test")
    assert result and result["test"] == 1, "execute_query_single failed"
    logger.info("execute_query_single test passed")
    
    # Test execute_command with a temporary table
    db_access.execute_command("CREATE TEMPORARY TABLE test_table (id SERIAL PRIMARY KEY, name TEXT)")
    affected_rows = db_access.execute_command("INSERT INTO test_table (name) VALUES (%s)", ("test",))
    assert affected_rows == 1, "execute_command failed"
    logger.info("execute_command test passed")
    
    # Test execute_insert
    result = db_access.execute_insert("INSERT INTO test_table (name) VALUES (%s) RETURNING id, name", ("test2",))
    assert result and result["name"] == "test2", "execute_insert failed"
    logger.info("execute_insert test passed")
    
    # Test execute_update
    affected_rows = db_access.execute_update("UPDATE test_table SET name = %s WHERE name = %s", ("updated", "test"))
    assert affected_rows == 1, "execute_update failed"
    logger.info("execute_update test passed")
    
    # Test execute_delete
    affected_rows = db_access.execute_delete("DELETE FROM test_table WHERE name = %s", ("updated",))
    assert affected_rows == 1, "execute_delete failed"
    logger.info("execute_delete test passed")
    
    # Test get_count
    count = db_access.get_count("test_table")
    assert count == 1, "get_count failed"
    logger.info("get_count test passed")
    
    # Test get_all
    results = db_access.get_all("test_table")
    assert results and len(results) == 1, "get_all failed"
    logger.info("get_all test passed")
    
    # Test get_by_id
    result = db_access.get_by_id("test_table", "id", results[0]["id"])
    assert result and result["id"] == results[0]["id"], "get_by_id failed"
    logger.info("get_by_id test passed")
    
    # Test insert
    result = db_access.insert("test_table", {"name": "test3"})
    assert result and result["name"] == "test3", "insert failed"
    logger.info("insert test passed")
    
    # Test update
    affected_rows = db_access.update("test_table", {"name": "updated3"}, "id = %s", (result["id"],))
    assert affected_rows == 1, "update failed"
    logger.info("update test passed")
    
    # Test delete
    affected_rows = db_access.delete("test_table", "id = %s", (result["id"],))
    assert affected_rows == 1, "delete failed"
    logger.info("delete test passed")
    
    # Clean up
    db_access.execute_command("DROP TABLE test_table")
    
    logger.info("All DatabaseAccess tests passed")

def test_repository_pattern():
    """Test the repository pattern."""
    logger.info("Testing repository pattern...")
    
    # Create repository instances
    account_repo = AccountRepository()
    proxmox_node_repo = ProxmoxNodeRepository()
    vm_repo = VMRepository()
    hardware_repo = HardwareRepository()
    user_repo = UserRepository()
    
    # Test that repositories are created successfully
    assert account_repo is not None, "AccountRepository creation failed"
    assert proxmox_node_repo is not None, "ProxmoxNodeRepository creation failed"
    assert vm_repo is not None, "VMRepository creation failed"
    assert hardware_repo is not None, "HardwareRepository creation failed"
    assert user_repo is not None, "UserRepository creation failed"
    
    logger.info("Repository creation tests passed")
    
    # Test repository methods with a test user
    with get_db_connection() as conn:
        if not conn:
            logger.error("No database connection available")
            return
        
        cursor = conn.cursor()
        try:
            # Create a test user
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin)
                VALUES ('test_user', crypt('password', gen_salt('bf')), 'test@example.com', FALSE)
                RETURNING id
            """)
            user_id = cursor.fetchone()[0]
            
            # Create a test account
            cursor.execute("""
                INSERT INTO accounts (acc_id, acc_username, acc_password, acc_email_address, acc_email_password, owner_id)
                VALUES ('test_acc', 'test_acc_user', 'password', 'test_acc@example.com', 'email_password', %s)
                RETURNING acc_id
            """, (user_id,))
            acc_id = cursor.fetchone()[0]
            
            # Create a test Proxmox node
            cursor.execute("""
                INSERT INTO proxmox_nodes (name, hostname, port, status, api_key, owner_id)
                VALUES ('test_node', 'test.example.com', 8006, 'online', 'test_api_key', %s)
                RETURNING id
            """, (user_id,))
            node_id = cursor.fetchone()[0]
            
            # Create a test VM
            cursor.execute("""
                INSERT INTO vms (vmid, name, status, proxmox_node_id, owner_id)
                VALUES ('100', 'test_vm', 'running', %s, %s)
                RETURNING id
            """, (node_id, user_id))
            vm_id = cursor.fetchone()[0]
            
            # Create a test hardware
            cursor.execute("""
                INSERT INTO hardware (name, type, specs, account_id, owner_id)
                VALUES ('test_hw', 'CPU', 'Intel i7', NULL, %s)
                RETURNING id
            """, (user_id,))
            hw_id = cursor.fetchone()[0]
            
            conn.commit()
            
            # Test repository methods
            
            # Test AccountRepository
            account = account_repo.get_account_by_id(acc_id)
            assert account and account["acc_id"] == acc_id, "AccountRepository.get_account_by_id failed"
            logger.info("AccountRepository.get_account_by_id test passed")
            
            # Test ProxmoxNodeRepository
            node = proxmox_node_repo.get_node_by_id(node_id)
            assert node and node["id"] == node_id, "ProxmoxNodeRepository.get_node_by_id failed"
            logger.info("ProxmoxNodeRepository.get_node_by_id test passed")
            
            # Test VMRepository
            vm = vm_repo.get_vm_by_id(vm_id)
            assert vm and vm["id"] == vm_id, "VMRepository.get_vm_by_id failed"
            logger.info("VMRepository.get_vm_by_id test passed")
            
            # Test HardwareRepository
            hw = hardware_repo.get_hardware_by_id(hw_id)
            assert hw and hw["id"] == hw_id, "HardwareRepository.get_hardware_by_id failed"
            logger.info("HardwareRepository.get_hardware_by_id test passed")
            
            # Test UserRepository
            user = user_repo.get_user_by_id(user_id)
            assert user and user["id"] == user_id, "UserRepository.get_user_by_id failed"
            logger.info("UserRepository.get_user_by_id test passed")
            
            # Clean up
            cursor.execute("DELETE FROM hardware WHERE id = %s", (hw_id,))
            cursor.execute("DELETE FROM vms WHERE id = %s", (vm_id,))
            cursor.execute("DELETE FROM proxmox_nodes WHERE id = %s", (node_id,))
            cursor.execute("DELETE FROM accounts WHERE acc_id = %s", (acc_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error testing repository pattern: {e}")
            raise
        finally:
            cursor.close()
    
    logger.info("All repository pattern tests passed")

def test_rls_implementation():
    """Test the RLS implementation."""
    logger.info("Testing RLS implementation...")
    
    # Create test users and data
    with get_db_connection() as conn:
        if not conn:
            logger.error("No database connection available")
            return
        
        cursor = conn.cursor()
        try:
            # Create test users
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin)
                VALUES 
                    ('test_user1', crypt('password1', gen_salt('bf')), 'test1@example.com', FALSE),
                    ('test_user2', crypt('password2', gen_salt('bf')), 'test2@example.com', FALSE),
                    ('test_admin', crypt('admin_password', gen_salt('bf')), 'admin@example.com', TRUE)
                RETURNING id, username, is_admin
            """)
            users = cursor.fetchall()
            user1_id = users[0][0]
            user2_id = users[1][0]
            admin_id = users[2][0]
            
            # Create test accounts
            cursor.execute("""
                INSERT INTO accounts (acc_id, acc_username, acc_password, acc_email_address, acc_email_password, owner_id)
                VALUES 
                    ('test_acc1', 'test_acc1_user', 'password1', 'test1@example.com', 'email_password1', %s),
                    ('test_acc2', 'test_acc2_user', 'password2', 'test2@example.com', 'email_password2', %s)
                RETURNING acc_id, owner_id
            """, (user1_id, user2_id))
            accounts = cursor.fetchall()
            acc1_id = accounts[0][0]
            acc2_id = accounts[1][0]
            
            conn.commit()
            
            # Test RLS with user1
            with get_user_db_connection(user_id=user1_id, user_role="user") as user1_conn:
                if not user1_conn:
                    logger.error("No user1 database connection available")
                    return
                
                user1_cursor = user1_conn.cursor()
                try:
                    # User1 should see only their own account
                    user1_cursor.execute("SELECT acc_id FROM accounts")
                    user1_accounts = user1_cursor.fetchall()
                    assert len(user1_accounts) == 1, f"User1 should see only their own account, but saw {len(user1_accounts)}"
                    assert user1_accounts[0][0] == acc1_id, f"User1 should see account {acc1_id}, but saw {user1_accounts[0][0]}"
                    logger.info("User1 RLS test passed")
                finally:
                    user1_cursor.close()
            
            # Test RLS with user2
            with get_user_db_connection(user_id=user2_id, user_role="user") as user2_conn:
                if not user2_conn:
                    logger.error("No user2 database connection available")
                    return
                
                user2_cursor = user2_conn.cursor()
                try:
                    # User2 should see only their own account
                    user2_cursor.execute("SELECT acc_id FROM accounts")
                    user2_accounts = user2_cursor.fetchall()
                    assert len(user2_accounts) == 1, f"User2 should see only their own account, but saw {len(user2_accounts)}"
                    assert user2_accounts[0][0] == acc2_id, f"User2 should see account {acc2_id}, but saw {user2_accounts[0][0]}"
                    logger.info("User2 RLS test passed")
                finally:
                    user2_cursor.close()
            
            # Test RLS with admin
            with get_user_db_connection(user_id=admin_id, user_role="admin") as admin_conn:
                if not admin_conn:
                    logger.error("No admin database connection available")
                    return
                
                admin_cursor = admin_conn.cursor()
                try:
                    # Admin should see all accounts
                    admin_cursor.execute("SELECT acc_id FROM accounts WHERE acc_id IN (%s, %s)", (acc1_id, acc2_id))
                    admin_accounts = admin_cursor.fetchall()
                    assert len(admin_accounts) == 2, f"Admin should see all accounts, but saw {len(admin_accounts)}"
                    logger.info("Admin RLS test passed")
                finally:
                    admin_cursor.close()
            
            # Test repository pattern with RLS
            
            # User1 repository
            user1_account_repo = AccountRepository(user_id=user1_id, user_role="user")
            user1_accounts = user1_account_repo.get_accounts()
            assert len(user1_accounts["accounts"]) == 1, f"User1 should see only their own account, but saw {len(user1_accounts['accounts'])}"
            assert user1_accounts["accounts"][0]["acc_id"] == acc1_id, f"User1 should see account {acc1_id}, but saw {user1_accounts['accounts'][0]['acc_id']}"
            logger.info("User1 repository RLS test passed")
            
            # User2 repository
            user2_account_repo = AccountRepository(user_id=user2_id, user_role="user")
            user2_accounts = user2_account_repo.get_accounts()
            assert len(user2_accounts["accounts"]) == 1, f"User2 should see only their own account, but saw {len(user2_accounts['accounts'])}"
            assert user2_accounts["accounts"][0]["acc_id"] == acc2_id, f"User2 should see account {acc2_id}, but saw {user2_accounts['accounts'][0]['acc_id']}"
            logger.info("User2 repository RLS test passed")
            
            # Admin repository
            admin_account_repo = AccountRepository(user_id=admin_id, user_role="admin")
            admin_accounts = admin_account_repo.get_accounts()
            assert len(admin_accounts["accounts"]) >= 2, f"Admin should see all accounts, but saw {len(admin_accounts['accounts'])}"
            logger.info("Admin repository RLS test passed")
            
            # Clean up
            cursor.execute("DELETE FROM accounts WHERE acc_id IN (%s, %s)", (acc1_id, acc2_id))
            cursor.execute("DELETE FROM users WHERE id IN (%s, %s, %s)", (user1_id, user2_id, admin_id))
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error testing RLS implementation: {e}")
            raise
        finally:
            cursor.close()
    
    logger.info("All RLS implementation tests passed")

def main():
    """Main function."""
    try:
        # Test database access
        test_database_access()
        
        # Test repository pattern
        test_repository_pattern()
        
        # Test RLS implementation
        test_rls_implementation()
        
        logger.info("All tests passed")
        return 0
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

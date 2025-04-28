"""
Integration tests for Row-Level Security (RLS).

This module contains tests to verify that RLS is working correctly.
"""

import pytest
import psycopg2
import logging
from typing import Dict, Any, List, Tuple
from db.connection import get_db_connection
from db.user_connection import get_user_db_connection
from db.access import DatabaseAccess
from db.repositories.accounts import AccountRepository
from db.repositories.hardware import HardwareRepository
from db.repositories.vms import VMRepository
from db.repositories.proxmox_nodes import ProxmoxNodeRepository

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture
def setup_test_data():
    """
    Set up test data for RLS tests.
    
    This fixture creates test users, accounts, hardware, VMs, and Proxmox nodes.
    It returns a dictionary with the created data.
    """
    test_data = {
        "users": [],
        "accounts": [],
        "hardware": [],
        "vms": [],
        "proxmox_nodes": []
    }
    
    with get_db_connection() as conn:
        if not conn:
            pytest.skip("No database connection available")
        
        cursor = conn.cursor()
        try:
            # Create test users
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin)
                VALUES 
                    ('test_user1', crypt('password1', gen_salt('bf')), 'test1@example.com', FALSE),
                    ('test_user2', crypt('password2', gen_salt('bf')), 'test2@example.com', FALSE),
                    ('test_admin', crypt('admin_password', gen_salt('bf')), 'admin@example.com', TRUE)
                RETURNING id, username, email, is_admin;
            """)
            test_data["users"] = [dict(zip(["id", "username", "email", "is_admin"], row)) for row in cursor.fetchall()]
            
            # Create test accounts
            cursor.execute("""
                INSERT INTO accounts (acc_id, acc_username, acc_password, acc_email_address, acc_email_password, owner_id)
                VALUES 
                    ('test_acc1', 'test_acc1_user', 'password1', 'test1@example.com', 'email_password1', %s),
                    ('test_acc2', 'test_acc2_user', 'password2', 'test2@example.com', 'email_password2', %s)
                RETURNING acc_id, acc_username, acc_email_address, owner_id;
            """, (test_data["users"][0]["id"], test_data["users"][1]["id"]))
            test_data["accounts"] = [dict(zip(["acc_id", "acc_username", "acc_email_address", "owner_id"], row)) for row in cursor.fetchall()]
            
            # Create test hardware
            cursor.execute("""
                INSERT INTO hardware (name, type, specs, owner_id)
                VALUES 
                    ('test_hw1', 'CPU', 'Intel i7', %s),
                    ('test_hw2', 'RAM', '16GB', %s)
                RETURNING id, name, type, specs, owner_id;
            """, (test_data["users"][0]["id"], test_data["users"][1]["id"]))
            test_data["hardware"] = [dict(zip(["id", "name", "type", "specs", "owner_id"], row)) for row in cursor.fetchall()]
            
            # Create test Proxmox nodes
            cursor.execute("""
                INSERT INTO proxmox_nodes (name, hostname, port, status, api_key, owner_id)
                VALUES 
                    ('test_node1', 'node1.example.com', 8006, 'online', 'api_key1', %s),
                    ('test_node2', 'node2.example.com', 8006, 'online', 'api_key2', %s)
                RETURNING id, name, hostname, port, status, owner_id;
            """, (test_data["users"][0]["id"], test_data["users"][1]["id"]))
            test_data["proxmox_nodes"] = [dict(zip(["id", "name", "hostname", "port", "status", "owner_id"], row)) for row in cursor.fetchall()]
            
            # Create test VMs
            cursor.execute("""
                INSERT INTO vms (vmid, name, status, proxmox_node_id, owner_id)
                VALUES 
                    ('100', 'test_vm1', 'running', %s, %s),
                    ('101', 'test_vm2', 'stopped', %s, %s)
                RETURNING id, vmid, name, status, proxmox_node_id, owner_id;
            """, (test_data["proxmox_nodes"][0]["id"], test_data["users"][0]["id"], 
                  test_data["proxmox_nodes"][1]["id"], test_data["users"][1]["id"]))
            test_data["vms"] = [dict(zip(["id", "vmid", "name", "status", "proxmox_node_id", "owner_id"], row)) for row in cursor.fetchall()]
            
            # Commit changes
            conn.commit()
        except Exception as e:
            logger.error(f"Error setting up test data: {e}")
            conn.rollback()
            pytest.skip(f"Error setting up test data: {e}")
        finally:
            cursor.close()
    
    yield test_data
    
    # Clean up test data
    with get_db_connection() as conn:
        if not conn:
            return
        
        cursor = conn.cursor()
        try:
            # Delete test data
            cursor.execute("DELETE FROM vms WHERE id IN %s", (tuple([vm["id"] for vm in test_data["vms"]]),))
            cursor.execute("DELETE FROM proxmox_nodes WHERE id IN %s", (tuple([node["id"] for node in test_data["proxmox_nodes"]]),))
            cursor.execute("DELETE FROM hardware WHERE id IN %s", (tuple([hw["id"] for hw in test_data["hardware"]]),))
            cursor.execute("DELETE FROM accounts WHERE acc_id IN %s", (tuple([acc["acc_id"] for acc in test_data["accounts"]]),))
            cursor.execute("DELETE FROM users WHERE id IN %s", (tuple([user["id"] for user in test_data["users"]]),))
            
            # Commit changes
            conn.commit()
        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")
            conn.rollback()
        finally:
            cursor.close()

def test_rls_admin_access(setup_test_data):
    """
    Test that admin users can access all data.
    
    Args:
        setup_test_data: Test data fixture
    """
    test_data = setup_test_data
    admin_id = next(user["id"] for user in test_data["users"] if user["is_admin"])
    
    # Test admin access to accounts
    account_repo = AccountRepository(user_id=admin_id, user_role="admin")
    accounts = account_repo.get_accounts()
    assert len(accounts["accounts"]) == 2, "Admin should see all accounts"
    
    # Test admin access to hardware
    hardware_repo = HardwareRepository(user_id=admin_id, user_role="admin")
    hardware = hardware_repo.get_hardware()
    assert len(hardware["hardware"]) == 2, "Admin should see all hardware"
    
    # Test admin access to VMs
    vm_repo = VMRepository(user_id=admin_id, user_role="admin")
    vms = vm_repo.get_vms()
    assert len(vms["vms"]) == 2, "Admin should see all VMs"
    
    # Test admin access to Proxmox nodes
    node_repo = ProxmoxNodeRepository(user_id=admin_id, user_role="admin")
    nodes = node_repo.get_nodes()
    assert len(nodes["nodes"]) == 2, "Admin should see all Proxmox nodes"

def test_rls_user_access(setup_test_data):
    """
    Test that regular users can only access their own data.
    
    Args:
        setup_test_data: Test data fixture
    """
    test_data = setup_test_data
    user1_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user1")
    user2_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user2")
    
    # Test user1 access to accounts
    account_repo = AccountRepository(user_id=user1_id, user_role="user")
    accounts = account_repo.get_accounts()
    assert len(accounts["accounts"]) == 1, "User1 should only see their own accounts"
    assert accounts["accounts"][0]["owner_id"] == user1_id, "User1 should only see their own accounts"
    
    # Test user2 access to accounts
    account_repo = AccountRepository(user_id=user2_id, user_role="user")
    accounts = account_repo.get_accounts()
    assert len(accounts["accounts"]) == 1, "User2 should only see their own accounts"
    assert accounts["accounts"][0]["owner_id"] == user2_id, "User2 should only see their own accounts"
    
    # Test user1 access to hardware
    hardware_repo = HardwareRepository(user_id=user1_id, user_role="user")
    hardware = hardware_repo.get_hardware()
    assert len(hardware["hardware"]) == 1, "User1 should only see their own hardware"
    assert hardware["hardware"][0]["owner_id"] == user1_id, "User1 should only see their own hardware"
    
    # Test user2 access to hardware
    hardware_repo = HardwareRepository(user_id=user2_id, user_role="user")
    hardware = hardware_repo.get_hardware()
    assert len(hardware["hardware"]) == 1, "User2 should only see their own hardware"
    assert hardware["hardware"][0]["owner_id"] == user2_id, "User2 should only see their own hardware"
    
    # Test user1 access to VMs
    vm_repo = VMRepository(user_id=user1_id, user_role="user")
    vms = vm_repo.get_vms()
    assert len(vms["vms"]) == 1, "User1 should only see their own VMs"
    assert vms["vms"][0]["owner_id"] == user1_id, "User1 should only see their own VMs"
    
    # Test user2 access to VMs
    vm_repo = VMRepository(user_id=user2_id, user_role="user")
    vms = vm_repo.get_vms()
    assert len(vms["vms"]) == 1, "User2 should only see their own VMs"
    assert vms["vms"][0]["owner_id"] == user2_id, "User2 should only see their own VMs"
    
    # Test user1 access to Proxmox nodes
    node_repo = ProxmoxNodeRepository(user_id=user1_id, user_role="user")
    nodes = node_repo.get_nodes()
    assert len(nodes["nodes"]) == 1, "User1 should only see their own Proxmox nodes"
    assert nodes["nodes"][0]["owner_id"] == user1_id, "User1 should only see their own Proxmox nodes"
    
    # Test user2 access to Proxmox nodes
    node_repo = ProxmoxNodeRepository(user_id=user2_id, user_role="user")
    nodes = node_repo.get_nodes()
    assert len(nodes["nodes"]) == 1, "User2 should only see their own Proxmox nodes"
    assert nodes["nodes"][0]["owner_id"] == user2_id, "User2 should only see their own Proxmox nodes"

def test_rls_insert(setup_test_data):
    """
    Test that users can only insert data with their own owner_id.
    
    Args:
        setup_test_data: Test data fixture
    """
    test_data = setup_test_data
    user1_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user1")
    user2_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user2")
    
    # Test user1 inserting an account with their own owner_id
    account_repo = AccountRepository(user_id=user1_id, user_role="user")
    account_data = {
        "acc_id": "test_acc_insert1",
        "acc_username": "test_acc_insert1_user",
        "acc_password": "password",
        "acc_email_address": "test_insert1@example.com",
        "acc_email_password": "email_password",
        "owner_id": user1_id
    }
    account = account_repo.create_account(account_data)
    assert account is not None, "User1 should be able to insert an account with their own owner_id"
    
    # Test user1 inserting an account with user2's owner_id
    account_data = {
        "acc_id": "test_acc_insert2",
        "acc_username": "test_acc_insert2_user",
        "acc_password": "password",
        "acc_email_address": "test_insert2@example.com",
        "acc_email_password": "email_password",
        "owner_id": user2_id
    }
    account = account_repo.create_account(account_data)
    assert account is None, "User1 should not be able to insert an account with user2's owner_id"
    
    # Clean up test data
    with get_db_connection() as conn:
        if not conn:
            return
        
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM accounts WHERE acc_id = 'test_acc_insert1'")
            conn.commit()
        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")
            conn.rollback()
        finally:
            cursor.close()

def test_rls_update(setup_test_data):
    """
    Test that users can only update their own data.
    
    Args:
        setup_test_data: Test data fixture
    """
    test_data = setup_test_data
    user1_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user1")
    user2_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user2")
    
    # Get user1's account
    user1_account = next(acc for acc in test_data["accounts"] if acc["owner_id"] == user1_id)
    
    # Get user2's account
    user2_account = next(acc for acc in test_data["accounts"] if acc["owner_id"] == user2_id)
    
    # Test user1 updating their own account
    account_repo = AccountRepository(user_id=user1_id, user_role="user")
    update_data = {"acc_username": "updated_username1"}
    updated_account = account_repo.update_account(user1_account["acc_id"], update_data)
    assert updated_account is not None, "User1 should be able to update their own account"
    assert updated_account["acc_username"] == "updated_username1", "User1's account should be updated"
    
    # Test user1 updating user2's account
    update_data = {"acc_username": "updated_username2"}
    updated_account = account_repo.update_account(user2_account["acc_id"], update_data)
    assert updated_account is None, "User1 should not be able to update user2's account"
    
    # Test admin updating any account
    admin_id = next(user["id"] for user in test_data["users"] if user["is_admin"])
    account_repo = AccountRepository(user_id=admin_id, user_role="admin")
    update_data = {"acc_username": "admin_updated_username"}
    updated_account = account_repo.update_account(user2_account["acc_id"], update_data)
    assert updated_account is not None, "Admin should be able to update any account"
    assert updated_account["acc_username"] == "admin_updated_username", "Admin should be able to update user2's account"

def test_rls_delete(setup_test_data):
    """
    Test that users can only delete their own data.
    
    Args:
        setup_test_data: Test data fixture
    """
    test_data = setup_test_data
    user1_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user1")
    user2_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user2")
    
    # Create test accounts for deletion
    with get_db_connection() as conn:
        if not conn:
            pytest.skip("No database connection available")
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO accounts (acc_id, acc_username, acc_password, acc_email_address, acc_email_password, owner_id)
                VALUES 
                    ('test_acc_delete1', 'test_acc_delete1_user', 'password1', 'test_delete1@example.com', 'email_password1', %s),
                    ('test_acc_delete2', 'test_acc_delete2_user', 'password2', 'test_delete2@example.com', 'email_password2', %s)
                RETURNING acc_id, owner_id;
            """, (user1_id, user2_id))
            delete_accounts = [dict(zip(["acc_id", "owner_id"], row)) for row in cursor.fetchall()]
            conn.commit()
        except Exception as e:
            logger.error(f"Error creating test accounts for deletion: {e}")
            conn.rollback()
            pytest.skip(f"Error creating test accounts for deletion: {e}")
        finally:
            cursor.close()
    
    # Test user1 deleting their own account
    account_repo = AccountRepository(user_id=user1_id, user_role="user")
    user1_delete_account = next(acc for acc in delete_accounts if acc["owner_id"] == user1_id)
    result = account_repo.delete_account(user1_delete_account["acc_id"])
    assert result, "User1 should be able to delete their own account"
    
    # Test user1 deleting user2's account
    user2_delete_account = next(acc for acc in delete_accounts if acc["owner_id"] == user2_id)
    result = account_repo.delete_account(user2_delete_account["acc_id"])
    assert not result, "User1 should not be able to delete user2's account"
    
    # Test admin deleting any account
    admin_id = next(user["id"] for user in test_data["users"] if user["is_admin"])
    account_repo = AccountRepository(user_id=admin_id, user_role="admin")
    result = account_repo.delete_account(user2_delete_account["acc_id"])
    assert result, "Admin should be able to delete any account"
    
    # Clean up any remaining test accounts
    with get_db_connection() as conn:
        if not conn:
            return
        
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM accounts WHERE acc_id LIKE 'test_acc_delete%'")
            conn.commit()
        except Exception as e:
            logger.error(f"Error cleaning up test accounts for deletion: {e}")
            conn.rollback()
        finally:
            cursor.close()

def test_rls_whitelist_access(setup_test_data):
    """
    Test that users can access VMs they have whitelist access to.
    
    Args:
        setup_test_data: Test data fixture
    """
    test_data = setup_test_data
    user1_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user1")
    user2_id = next(user["id"] for user in test_data["users"] if user["username"] == "test_user2")
    
    # Get user2's VM
    user2_vm = next(vm for vm in test_data["vms"] if vm["owner_id"] == user2_id)
    
    # Add user1 to the whitelist for user2's VM
    vm_repo = VMRepository(user_id=user2_id, user_role="user")
    whitelist_entry = vm_repo.add_to_whitelist(user2_vm["id"], user1_id)
    assert whitelist_entry is not None, "User2 should be able to add user1 to the whitelist for their VM"
    
    # Test user1 access to user2's VM through whitelist
    vm_repo = VMRepository(user_id=user1_id, user_role="user")
    vm = vm_repo.get_vm_by_id(user2_vm["id"])
    assert vm is not None, "User1 should be able to access user2's VM through whitelist"
    
    # Remove user1 from the whitelist
    vm_repo = VMRepository(user_id=user2_id, user_role="user")
    result = vm_repo.remove_from_whitelist(user2_vm["id"], user1_id)
    assert result, "User2 should be able to remove user1 from the whitelist for their VM"
    
    # Test user1 access to user2's VM after whitelist removal
    vm_repo = VMRepository(user_id=user1_id, user_role="user")
    vm = vm_repo.get_vm_by_id(user2_vm["id"])
    assert vm is None, "User1 should not be able to access user2's VM after whitelist removal"

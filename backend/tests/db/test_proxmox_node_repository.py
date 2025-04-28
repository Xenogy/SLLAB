"""
Integration tests for ProxmoxNodeRepository.

This module contains tests for the ProxmoxNodeRepository class.
"""

import pytest
import os
from datetime import datetime, timedelta
from db.repositories.proxmox_nodes import ProxmoxNodeRepository

# Use test database
os.environ["DB_NAME"] = "accountdb_test"

@pytest.fixture
def setup_test_data():
    """Set up test data in the database."""
    # Connect to test database
    from db.connection import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM proxmox_nodes")
        
        # Insert test data
        cursor.execute("""
            INSERT INTO proxmox_nodes (
                name, hostname, port, status, api_key, owner_id
            ) VALUES (
                'test_node', 'test.example.com', 8006, 'connected', 'test_key', 1
            )
        """)
        
        conn.commit()
    
    yield
    
    # Clean up
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proxmox_nodes")
        conn.commit()

@pytest.mark.integration
@pytest.mark.db
class TestProxmoxNodeRepository:
    """Tests for ProxmoxNodeRepository."""
    
    def test_get_nodes(self, setup_test_data):
        """Test getting nodes from the repository."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Get nodes
        result = repo.get_nodes()
        
        # Check result
        assert result["total"] == 1
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["name"] == "test_node"
        assert result["nodes"][0]["hostname"] == "test.example.com"
    
    def test_get_node_by_id(self, setup_test_data):
        """Test getting a node by ID."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Get nodes to find the ID
        nodes = repo.get_nodes()
        node_id = nodes["nodes"][0]["id"]
        
        # Get node by ID
        node = repo.get_node_by_id(node_id)
        
        # Check result
        assert node is not None
        assert node["name"] == "test_node"
        assert node["hostname"] == "test.example.com"
    
    def test_create_node(self):
        """Test creating a node."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Create node
        node_data = {
            "name": "new_node",
            "hostname": "new.example.com",
            "port": 8006,
            "status": "disconnected",
            "api_key": "new_key",
            "owner_id": 1
        }
        
        created_node = repo.create_node(node_data)
        
        # Check result
        assert created_node is not None
        assert created_node["name"] == "new_node"
        assert created_node["hostname"] == "new.example.com"
        assert created_node["port"] == 8006
        assert created_node["status"] == "disconnected"
        assert created_node["api_key"] == "new_key"
        assert created_node["owner_id"] == 1
        
        # Clean up
        repo.delete_node(created_node["id"])
    
    def test_update_node(self, setup_test_data):
        """Test updating a node."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Get nodes to find the ID
        nodes = repo.get_nodes()
        node_id = nodes["nodes"][0]["id"]
        
        # Update node
        node_data = {
            "name": "updated_node",
            "hostname": "updated.example.com",
            "port": 8007
        }
        
        updated_node = repo.update_node(node_id, node_data)
        
        # Check result
        assert updated_node is not None
        assert updated_node["name"] == "updated_node"
        assert updated_node["hostname"] == "updated.example.com"
        assert updated_node["port"] == 8007
    
    def test_delete_node(self):
        """Test deleting a node."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Create node
        node_data = {
            "name": "delete_node",
            "hostname": "delete.example.com",
            "port": 8006,
            "status": "disconnected",
            "api_key": "delete_key",
            "owner_id": 1
        }
        
        created_node = repo.create_node(node_data)
        node_id = created_node["id"]
        
        # Delete node
        result = repo.delete_node(node_id)
        
        # Check result
        assert result is True
        
        # Verify node is deleted
        node = repo.get_node_by_id(node_id)
        assert node is None
    
    def test_update_node_status(self, setup_test_data):
        """Test updating a node's status."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Get nodes to find the ID
        nodes = repo.get_nodes()
        node_id = nodes["nodes"][0]["id"]
        
        # Update node status
        result = repo.update_node_status(node_id, "disconnected")
        
        # Check result
        assert result is True
        
        # Verify status is updated
        node = repo.get_node_by_id(node_id)
        assert node["status"] == "disconnected"
    
    def test_rls_user_can_only_see_own_nodes(self, setup_test_data):
        """Test that a user can only see their own nodes with RLS."""
        # Create repositories for different users
        admin_repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        user_repo = ProxmoxNodeRepository(user_id=2, user_role="user")
        
        # Admin should see the test node
        admin_result = admin_repo.get_nodes()
        assert admin_result["total"] == 1
        
        # User should not see any nodes
        user_result = user_repo.get_nodes()
        assert user_result["total"] == 0
        
        # Create a node for user 2
        node_data = {
            "name": "user2_node",
            "hostname": "user2.example.com",
            "port": 8006,
            "status": "disconnected",
            "api_key": "user2_key",
            "owner_id": 2
        }
        
        created_node = admin_repo.create(node_data, with_rls=False)  # Bypass RLS to create node for user 2
        
        # Now user should see their node
        user_result = user_repo.get_nodes()
        assert user_result["total"] == 1
        assert user_result["nodes"][0]["name"] == "user2_node"
        
        # Admin should see both nodes
        admin_result = admin_repo.get_nodes()
        assert admin_result["total"] == 2
        
        # Clean up
        admin_repo.delete(created_node["id"], with_rls=False)  # Bypass RLS to delete node

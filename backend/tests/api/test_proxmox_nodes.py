"""
Unit tests for Proxmox Nodes API endpoints.

This module contains tests for the Proxmox Nodes API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

@pytest.mark.unit
@pytest.mark.api
class TestProxmoxNodesAPI:
    """Tests for Proxmox Nodes API endpoints."""
    
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_get_proxmox_nodes(self, mock_get_current_user, mock_repo_class):
        """Test getting a list of Proxmox nodes."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository response
        mock_repo_instance.get_nodes.return_value = {
            "nodes": [
                {
                    "id": 1,
                    "name": "pve1",
                    "hostname": "proxmox.example.com",
                    "port": 8006,
                    "status": "connected",
                    "api_key": "test_key",
                    "last_seen": "2023-04-26T12:34:56",
                    "created_at": "2023-04-25T10:20:30",
                    "updated_at": "2023-04-26T12:34:56",
                    "owner_id": 1
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
        
        # Make the request
        response = client.get("/proxmox-nodes/")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["name"] == "pve1"
        
        # Verify the mock was called correctly
        mock_repo_instance.get_nodes.assert_called_once_with(
            limit=10,
            offset=0,
            search=None,
            status=None
        )
    
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_get_proxmox_node(self, mock_get_current_user, mock_repo_class):
        """Test getting a specific Proxmox node by ID."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository response
        mock_repo_instance.get_node_by_id.return_value = {
            "id": 1,
            "name": "pve1",
            "hostname": "proxmox.example.com",
            "port": 8006,
            "status": "connected",
            "api_key": "test_key",
            "last_seen": "2023-04-26T12:34:56",
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-26T12:34:56",
            "owner_id": 1
        }
        
        # Make the request
        response = client.get("/proxmox-nodes/1")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "pve1"
        
        # Verify the mock was called correctly
        mock_repo_instance.get_node_by_id.assert_called_once_with(1)
    
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_get_proxmox_node_not_found(self, mock_get_current_user, mock_repo_class):
        """Test getting a non-existent Proxmox node."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository response
        mock_repo_instance.get_node_by_id.return_value = None
        
        # Make the request
        response = client.get("/proxmox-nodes/999")
        
        # Check the response
        assert response.status_code == 404
        assert response.json()["detail"] == "Proxmox node not found"
        
        # Verify the mock was called correctly
        mock_repo_instance.get_node_by_id.assert_called_once_with(999)
    
    @patch('routers.proxmox_nodes.generate_api_key')
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_create_proxmox_node(self, mock_get_current_user, mock_repo_class, mock_generate_api_key):
        """Test creating a new Proxmox node."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        mock_generate_api_key.return_value = "new_api_key"
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository response
        mock_repo_instance.create_node.return_value = {
            "id": 1,
            "name": "new-node",
            "hostname": "new.example.com",
            "port": 8006,
            "status": "disconnected",
            "api_key": "new_api_key",
            "last_seen": None,
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-25T10:20:30",
            "owner_id": 1
        }
        
        # Make the request
        response = client.post(
            "/proxmox-nodes/",
            json={
                "name": "new-node",
                "hostname": "new.example.com",
                "port": 8006
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "new-node"
        assert data["hostname"] == "new.example.com"
        assert data["port"] == 8006
        assert data["status"] == "disconnected"
        assert data["api_key"] == "new_api_key"
        assert data["owner_id"] == 1
        
        # Verify the mocks were called correctly
        mock_generate_api_key.assert_called_once()
        mock_repo_instance.create_node.assert_called_once_with({
            "name": "new-node",
            "hostname": "new.example.com",
            "port": 8006,
            "status": "disconnected",
            "api_key": "new_api_key",
            "owner_id": 1
        })
    
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_update_proxmox_node(self, mock_get_current_user, mock_repo_class):
        """Test updating a Proxmox node."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository responses
        mock_repo_instance.get_node_by_id.return_value = {
            "id": 1,
            "name": "pve1",
            "hostname": "proxmox.example.com",
            "port": 8006,
            "status": "connected",
            "api_key": "test_key",
            "last_seen": "2023-04-26T12:34:56",
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-26T12:34:56",
            "owner_id": 1
        }
        
        mock_repo_instance.update_node.return_value = {
            "id": 1,
            "name": "updated-node",
            "hostname": "updated.example.com",
            "port": 8006,
            "status": "connected",
            "api_key": "test_key",
            "last_seen": "2023-04-26T12:34:56",
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-26T12:34:56",
            "owner_id": 1
        }
        
        # Make the request
        response = client.put(
            "/proxmox-nodes/1",
            json={
                "name": "updated-node",
                "hostname": "updated.example.com",
                "port": 8006
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "updated-node"
        assert data["hostname"] == "updated.example.com"
        
        # Verify the mocks were called correctly
        mock_repo_instance.get_node_by_id.assert_called_once_with(1)
        mock_repo_instance.update_node.assert_called_once_with(1, {
            "name": "updated-node",
            "hostname": "updated.example.com",
            "port": 8006
        })
    
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_delete_proxmox_node(self, mock_get_current_user, mock_repo_class):
        """Test deleting a Proxmox node."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository responses
        mock_repo_instance.get_node_by_id.return_value = {
            "id": 1,
            "name": "pve1",
            "hostname": "proxmox.example.com",
            "port": 8006,
            "status": "connected",
            "api_key": "test_key",
            "last_seen": "2023-04-26T12:34:56",
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-26T12:34:56",
            "owner_id": 1
        }
        
        mock_repo_instance.delete_node.return_value = True
        
        # Make the request
        response = client.delete("/proxmox-nodes/1")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Proxmox node deleted successfully"
        
        # Verify the mocks were called correctly
        mock_repo_instance.get_node_by_id.assert_called_once_with(1)
        mock_repo_instance.delete_node.assert_called_once_with(1)
    
    @patch('routers.proxmox_nodes.generate_api_key')
    @patch('routers.proxmox_nodes.ProxmoxNodeRepository')
    @patch('routers.auth.get_current_user')
    def test_regenerate_api_key(self, mock_get_current_user, mock_repo_class, mock_generate_api_key):
        """Test regenerating the API key for a Proxmox node."""
        # Set up the mocks
        mock_get_current_user.return_value = {"id": 1, "role": "admin"}
        mock_generate_api_key.return_value = "new_api_key"
        
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Mock the repository responses
        mock_repo_instance.get_node_by_id.return_value = {
            "id": 1,
            "name": "pve1",
            "hostname": "proxmox.example.com",
            "port": 8006,
            "status": "connected",
            "api_key": "test_key",
            "last_seen": "2023-04-26T12:34:56",
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-26T12:34:56",
            "owner_id": 1
        }
        
        mock_repo_instance.update_node.return_value = {
            "id": 1,
            "name": "pve1",
            "hostname": "proxmox.example.com",
            "port": 8006,
            "status": "connected",
            "api_key": "new_api_key",
            "last_seen": "2023-04-26T12:34:56",
            "created_at": "2023-04-25T10:20:30",
            "updated_at": "2023-04-26T12:34:56",
            "owner_id": 1
        }
        
        # Make the request
        response = client.post("/proxmox-nodes/1/regenerate-api-key")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["api_key"] == "new_api_key"
        
        # Verify the mocks were called correctly
        mock_repo_instance.get_node_by_id.assert_called_once_with(1)
        mock_generate_api_key.assert_called_once()
        mock_repo_instance.update_node.assert_called_once_with(1, {"api_key": "new_api_key"})

"""
Test script for the ban check functionality.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from utils.ban_check_utils import (
    generate_urls_from_steamids,
    generate_urls_from_csv_content,
    check_single_url_for_ban_info,
    interpret_status
)

class TestBanCheck(unittest.TestCase):
    """Test case for the ban check functionality."""
    
    def setUp(self):
        """Set up the test case."""
        self.client = TestClient(app)
        
        # Mock authentication
        self.auth_patch = patch('routers.auth.get_current_user', return_value={
            "id": 1,
            "username": "admin",
            "role": "admin"
        })
        self.mock_auth = self.auth_patch.start()
    
    def tearDown(self):
        """Tear down the test case."""
        self.auth_patch.stop()
    
    def test_generate_urls_from_steamids(self):
        """Test generating URLs from Steam IDs."""
        steam_ids = ["76561198000000001", "76561198000000002"]
        urls = generate_urls_from_steamids(steam_ids)
        
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://steamcommunity.com/profiles/76561198000000001")
        self.assertEqual(urls[1], "https://steamcommunity.com/profiles/76561198000000002")
    
    def test_generate_urls_from_csv_content(self):
        """Test generating URLs from CSV content."""
        csv_content = "steam64_id,name\n76561198000000001,User1\n76561198000000002,User2"
        urls = generate_urls_from_csv_content(csv_content)
        
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://steamcommunity.com/profiles/76561198000000001")
        self.assertEqual(urls[1], "https://steamcommunity.com/profiles/76561198000000002")
    
    @patch('utils.ban_check_utils.requests.get')
    def test_check_single_url_for_ban_info_not_banned(self, mock_get):
        """Test checking a single URL for ban info (not banned)."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<html><div class="profile_header_centered_persona"></div></html>'
        mock_get.return_value = mock_response
        
        # Check URL
        result = check_single_url_for_ban_info("https://steamcommunity.com/profiles/76561198000000001")
        
        # Verify result
        self.assertEqual(result, "NOT_BANNED_PUBLIC")
    
    @patch('utils.ban_check_utils.requests.get')
    def test_check_single_url_for_ban_info_banned(self, mock_get):
        """Test checking a single URL for ban info (banned)."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<html><span class="profile_ban_info">VAC ban on record</span></html>'
        mock_get.return_value = mock_response
        
        # Check URL
        result = check_single_url_for_ban_info("https://steamcommunity.com/profiles/76561198000000001")
        
        # Verify result
        self.assertEqual(result, "BANNED: VAC ban on record")
    
    @patch('utils.ban_check_utils.requests.get')
    def test_check_single_url_for_ban_info_private(self, mock_get):
        """Test checking a single URL for ban info (private profile)."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<html><div class="profile_private_info"></div></html>'
        mock_get.return_value = mock_response
        
        # Check URL
        result = check_single_url_for_ban_info("https://steamcommunity.com/profiles/76561198000000001")
        
        # Verify result
        self.assertEqual(result, "PRIVATE_PROFILE")
    
    def test_interpret_status(self):
        """Test interpreting status strings."""
        # Test banned status
        result = interpret_status("BANNED: VAC ban on record")
        self.assertEqual(result["status_summary"], "BANNED")
        self.assertEqual(result["details"], "VAC ban on record")
        
        # Test not banned status
        result = interpret_status("NOT_BANNED_PUBLIC")
        self.assertEqual(result["status_summary"], "NOT_BANNED")
        self.assertEqual(result["details"], "No bans detected")
        
        # Test private profile status
        result = interpret_status("PRIVATE_PROFILE")
        self.assertEqual(result["status_summary"], "PRIVATE")
        self.assertEqual(result["details"], "Profile is private")
        
        # Test error status
        result = interpret_status("ERROR_TIMEOUT")
        self.assertEqual(result["status_summary"], "ERROR")
        self.assertEqual(result["details"], "ERROR_TIMEOUT")
    
    @patch('routers.ban_check.BanCheckRepository')
    def test_check_steamids_endpoint(self, mock_repo_class):
        """Test the check_steamids endpoint."""
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.create_task.return_value = {
            "task_id": "test-task-id",
            "status": "PENDING",
            "message": "Task received, processing Steam IDs",
            "progress": 0,
            "owner_id": 1
        }
        mock_repo_class.return_value = mock_repo
        
        # Make request
        response = self.client.post(
            "/ban-check/check/steamids",
            data={
                "steam_ids": ["76561198000000001", "76561198000000002"],
                "logical_batch_size": 10,
                "max_concurrent_batches": 3,
                "max_workers_per_batch": 3,
                "inter_request_submit_delay": 0.1,
                "max_retries_per_url": 2,
                "retry_delay_seconds": 5.0
            }
        )
        
        # Verify response
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["status"], "PENDING")
        self.assertEqual(response.json()["progress"], 0)
    
    @patch('routers.ban_check.BanCheckRepository')
    def test_get_tasks_endpoint(self, mock_repo_class):
        """Test the get_tasks endpoint."""
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_tasks.return_value = {
            "tasks": [
                {
                    "task_id": "test-task-id",
                    "status": "COMPLETED",
                    "message": "Task completed",
                    "progress": 100,
                    "owner_id": 1
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
        mock_repo_class.return_value = mock_repo
        
        # Make request
        response = self.client.get("/ban-check/tasks")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["tasks"]), 1)
        self.assertEqual(response.json()["total"], 1)
    
    @patch('routers.ban_check.BanCheckRepository')
    def test_get_task_endpoint(self, mock_repo_class):
        """Test the get_task endpoint."""
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_task_by_id.return_value = {
            "task_id": "test-task-id",
            "status": "COMPLETED",
            "message": "Task completed",
            "progress": 100,
            "owner_id": 1
        }
        mock_repo_class.return_value = mock_repo
        
        # Make request
        response = self.client.get("/ban-check/tasks/test-task-id")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], "test-task-id")
        self.assertEqual(response.json()["status"], "COMPLETED")

if __name__ == '__main__':
    unittest.main()

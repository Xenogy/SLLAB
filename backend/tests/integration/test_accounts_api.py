"""
Integration tests for accounts API.
"""

import pytest
import json
from fastapi.testclient import TestClient
from tests.utils.test_utils import (
    create_test_user, create_test_account, create_test_token,
    get_auth_headers, clean_test_data
)
from tests.fixtures.test_data import (
    get_test_account_create_data, get_test_account_update_data
)

@pytest.mark.integration
@pytest.mark.api
class TestAccountsAPI:
    """Tests for accounts API."""
    
    @pytest.fixture(scope="function")
    def setup_test_data(self, db_connection):
        """Set up test data."""
        # Create test users
        admin_user = create_test_user(db_connection, role="admin")
        regular_user = create_test_user(db_connection)
        
        # Create test accounts
        admin_account = create_test_account(db_connection, admin_user["id"])
        user_account = create_test_account(db_connection, regular_user["id"])
        
        # Create test tokens
        admin_token = create_test_token(admin_user["id"], admin_user["username"], "admin")
        user_token = create_test_token(regular_user["id"], regular_user["username"], "user")
        
        # Return the test data
        yield {
            "admin_user": admin_user,
            "regular_user": regular_user,
            "admin_account": admin_account,
            "user_account": user_account,
            "admin_token": admin_token,
            "user_token": user_token
        }
        
        # Clean up test data
        clean_test_data(db_connection)
    
    def test_get_accounts(self, client, setup_test_data):
        """Test GET /accounts endpoint."""
        # Get the test data
        admin_token = setup_test_data["admin_token"]
        user_token = setup_test_data["user_token"]
        
        # Test as admin
        response = client.get("/accounts", headers=get_auth_headers(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
        assert len(data["accounts"]) >= 2  # At least the two test accounts
        
        # Test as regular user
        response = client.get("/accounts", headers=get_auth_headers(user_token))
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
        assert len(data["accounts"]) >= 1  # At least the user's account
        
        # Test without authentication
        response = client.get("/accounts")
        assert response.status_code == 401
    
    def test_get_account(self, client, setup_test_data):
        """Test GET /accounts/{acc_id} endpoint."""
        # Get the test data
        admin_token = setup_test_data["admin_token"]
        user_token = setup_test_data["user_token"]
        admin_account = setup_test_data["admin_account"]
        user_account = setup_test_data["user_account"]
        
        # Test as admin getting admin account
        response = client.get(f"/accounts/{admin_account['acc_id']}", headers=get_auth_headers(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert data["acc_id"] == admin_account["acc_id"]
        
        # Test as admin getting user account
        response = client.get(f"/accounts/{user_account['acc_id']}", headers=get_auth_headers(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert data["acc_id"] == user_account["acc_id"]
        
        # Test as regular user getting own account
        response = client.get(f"/accounts/{user_account['acc_id']}", headers=get_auth_headers(user_token))
        assert response.status_code == 200
        data = response.json()
        assert data["acc_id"] == user_account["acc_id"]
        
        # Test as regular user getting admin account (should fail)
        response = client.get(f"/accounts/{admin_account['acc_id']}", headers=get_auth_headers(user_token))
        assert response.status_code == 403
        
        # Test getting non-existent account
        response = client.get("/accounts/nonexistent", headers=get_auth_headers(admin_token))
        assert response.status_code == 404
        
        # Test without authentication
        response = client.get(f"/accounts/{admin_account['acc_id']}")
        assert response.status_code == 401
    
    def test_create_account(self, client, setup_test_data):
        """Test POST /accounts endpoint."""
        # Get the test data
        admin_token = setup_test_data["admin_token"]
        user_token = setup_test_data["user_token"]
        
        # Get test account data
        account_data = get_test_account_create_data()
        
        # Test as admin
        response = client.post("/accounts", headers=get_auth_headers(admin_token), json=account_data)
        assert response.status_code == 201
        data = response.json()
        assert data["acc_id"] == account_data["acc_id"]
        assert data["acc_username"] == account_data["acc_username"]
        
        # Test as regular user
        account_data = get_test_account_create_data()  # Get new data
        response = client.post("/accounts", headers=get_auth_headers(user_token), json=account_data)
        assert response.status_code == 201
        data = response.json()
        assert data["acc_id"] == account_data["acc_id"]
        assert data["acc_username"] == account_data["acc_username"]
        
        # Test without authentication
        account_data = get_test_account_create_data()  # Get new data
        response = client.post("/accounts", json=account_data)
        assert response.status_code == 401
    
    def test_update_account(self, client, setup_test_data):
        """Test PUT /accounts/{acc_id} endpoint."""
        # Get the test data
        admin_token = setup_test_data["admin_token"]
        user_token = setup_test_data["user_token"]
        admin_account = setup_test_data["admin_account"]
        user_account = setup_test_data["user_account"]
        
        # Get test account update data
        update_data = get_test_account_update_data()
        
        # Test as admin updating admin account
        response = client.put(
            f"/accounts/{admin_account['acc_id']}",
            headers=get_auth_headers(admin_token),
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["acc_id"] == admin_account["acc_id"]
        assert data["acc_username"] == update_data["acc_username"]
        
        # Test as admin updating user account
        update_data = get_test_account_update_data()  # Get new data
        response = client.put(
            f"/accounts/{user_account['acc_id']}",
            headers=get_auth_headers(admin_token),
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["acc_id"] == user_account["acc_id"]
        assert data["acc_username"] == update_data["acc_username"]
        
        # Test as regular user updating own account
        update_data = get_test_account_update_data()  # Get new data
        response = client.put(
            f"/accounts/{user_account['acc_id']}",
            headers=get_auth_headers(user_token),
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["acc_id"] == user_account["acc_id"]
        assert data["acc_username"] == update_data["acc_username"]
        
        # Test as regular user updating admin account (should fail)
        update_data = get_test_account_update_data()  # Get new data
        response = client.put(
            f"/accounts/{admin_account['acc_id']}",
            headers=get_auth_headers(user_token),
            json=update_data
        )
        assert response.status_code == 403
        
        # Test updating non-existent account
        update_data = get_test_account_update_data()  # Get new data
        response = client.put(
            "/accounts/nonexistent",
            headers=get_auth_headers(admin_token),
            json=update_data
        )
        assert response.status_code == 404
        
        # Test without authentication
        update_data = get_test_account_update_data()  # Get new data
        response = client.put(
            f"/accounts/{admin_account['acc_id']}",
            json=update_data
        )
        assert response.status_code == 401
    
    def test_delete_account(self, client, setup_test_data):
        """Test DELETE /accounts/{acc_id} endpoint."""
        # Get the test data
        admin_token = setup_test_data["admin_token"]
        user_token = setup_test_data["user_token"]
        admin_account = setup_test_data["admin_account"]
        user_account = setup_test_data["user_account"]
        
        # Create additional accounts for deletion
        admin_user = setup_test_data["admin_user"]
        regular_user = setup_test_data["regular_user"]
        admin_account_to_delete = create_test_account(db_connection, admin_user["id"])
        user_account_to_delete = create_test_account(db_connection, regular_user["id"])
        
        # Test as admin deleting admin account
        response = client.delete(
            f"/accounts/{admin_account_to_delete['acc_id']}",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 204
        
        # Test as admin deleting user account
        response = client.delete(
            f"/accounts/{user_account_to_delete['acc_id']}",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 204
        
        # Create a new account for the user to delete
        user_account_to_delete = create_test_account(db_connection, regular_user["id"])
        
        # Test as regular user deleting own account
        response = client.delete(
            f"/accounts/{user_account_to_delete['acc_id']}",
            headers=get_auth_headers(user_token)
        )
        assert response.status_code == 204
        
        # Create a new account for the admin
        admin_account_to_delete = create_test_account(db_connection, admin_user["id"])
        
        # Test as regular user deleting admin account (should fail)
        response = client.delete(
            f"/accounts/{admin_account_to_delete['acc_id']}",
            headers=get_auth_headers(user_token)
        )
        assert response.status_code == 403
        
        # Test deleting non-existent account
        response = client.delete(
            "/accounts/nonexistent",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 404
        
        # Test without authentication
        response = client.delete(
            f"/accounts/{admin_account_to_delete['acc_id']}"
        )
        assert response.status_code == 401

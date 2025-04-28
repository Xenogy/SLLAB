"""
Test configuration and fixtures for pytest.
"""

import os
import sys
import pytest
import logging
from typing import Dict, Any, Generator, List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
import random
import string
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import from the backend package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import application modules
from main import app
from config import Config
from db.connection import get_connection, return_connection, get_db_connection
from db.user_connection import get_user_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database configuration
TEST_DB_HOST = os.getenv('TEST_DB_HOST', Config.DB_HOST)
TEST_DB_PORT = os.getenv('TEST_DB_PORT', Config.DB_PORT)
TEST_DB_NAME = os.getenv('TEST_DB_NAME', 'accountdb_test')
TEST_DB_USER = os.getenv('TEST_DB_USER', Config.DB_USER)
TEST_DB_PASS = os.getenv('TEST_DB_PASS', Config.DB_PASS)

# Test database URL
TEST_DB_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASS}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

# Mock authentication
@pytest.fixture(scope="function")
def mock_auth():
    """Mock the authentication for tests."""
    # Mock the get_current_user function
    with patch("routers.auth.get_current_user", return_value={"id": 1, "username": "test_user", "role": "admin", "is_active": True}):
        # Mock the get_current_active_user function
        with patch("routers.auth.get_current_active_user", return_value={"id": 1, "username": "test_user", "role": "admin", "is_active": True}):
            yield

# Test client
@pytest.fixture(scope="module")
def client() -> Generator:
    """
    Create a FastAPI TestClient for testing API endpoints.

    Returns:
        Generator: A FastAPI TestClient
    """
    with TestClient(app) as test_client:
        yield test_client

# Test client with authentication
@pytest.fixture(scope="function")
def authenticated_client(mock_auth):
    """Create a test client with authentication."""
    with TestClient(app) as test_client:
        yield test_client

# Mock database connection
@pytest.fixture(scope="function")
def mock_db_connection():
    """Mock the database connection for tests."""
    # Create a mock connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock the get_db_connection function
    with patch("db.connection.get_db_connection", return_value=mock_conn):
        # Mock the get_secure_db function
        with patch("db.connection.get_secure_db", return_value=mock_conn):
            yield mock_conn

# Test database connection
@pytest.fixture(scope="session")
def db_connection() -> Generator[PsycopgConnection, None, None]:
    """
    Create a database connection for testing.

    Returns:
        Generator[PsycopgConnection, None, None]: A database connection
    """
    # Connect to the test database
    conn = psycopg2.connect(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        dbname=TEST_DB_NAME,
        user=TEST_DB_USER,
        password=TEST_DB_PASS
    )

    # Set autocommit to True to avoid transaction issues
    conn.autocommit = True

    yield conn

    # Close the connection
    conn.close()

# Test database cursor
@pytest.fixture(scope="function")
def db_cursor(db_connection: PsycopgConnection) -> Generator:
    """
    Create a database cursor for testing.

    Args:
        db_connection (PsycopgConnection): A database connection

    Returns:
        Generator: A database cursor
    """
    # Create a cursor
    cursor = db_connection.cursor()

    yield cursor

    # Close the cursor
    cursor.close()

# Test user
@pytest.fixture(scope="function")
def test_user() -> Dict[str, Any]:
    """
    Create a test user.

    Returns:
        Dict[str, Any]: A test user
    """
    return {
        "id": 999,
        "username": f"test_user_{random_string(8)}",
        "email": f"test_user_{random_string(8)}@example.com",
        "role": "user",
        "is_active": True,
        "created_at": datetime.now().timestamp()
    }

# Test admin user
@pytest.fixture(scope="function")
def test_admin() -> Dict[str, Any]:
    """
    Create a test admin user.

    Returns:
        Dict[str, Any]: A test admin user
    """
    return {
        "id": 998,
        "username": f"test_admin_{random_string(8)}",
        "email": f"test_admin_{random_string(8)}@example.com",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now().timestamp()
    }

# Test account
@pytest.fixture(scope="function")
def test_account(test_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a test account.

    Args:
        test_user (Dict[str, Any]): A test user

    Returns:
        Dict[str, Any]: A test account
    """
    return {
        "acc_id": f"76561199{random_string(9, digits_only=True)}",
        "acc_username": f"test_account_{random_string(8)}",
        "acc_password": f"password_{random_string(8)}",
        "acc_email_address": f"test_account_{random_string(8)}@example.com",
        "acc_email_password": f"email_password_{random_string(8)}",
        "acc_created_at": datetime.now().timestamp(),
        "prime": False,
        "lock": False,
        "perm_lock": False,
        "owner_id": test_user["id"]
    }

# Test accounts
@pytest.fixture(scope="function")
def test_accounts(test_user: Dict[str, Any], test_admin: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create test accounts.

    Args:
        test_user (Dict[str, Any]): A test user
        test_admin (Dict[str, Any]): A test admin user

    Returns:
        List[Dict[str, Any]]: A list of test accounts
    """
    accounts = []

    # Create accounts for the test user
    for i in range(3):
        accounts.append({
            "acc_id": f"76561199{random_string(9, digits_only=True)}",
            "acc_username": f"test_user_account_{i}_{random_string(8)}",
            "acc_password": f"password_{random_string(8)}",
            "acc_email_address": f"test_user_account_{i}_{random_string(8)}@example.com",
            "acc_email_password": f"email_password_{random_string(8)}",
            "acc_created_at": datetime.now().timestamp(),
            "prime": i % 2 == 0,
            "lock": i % 3 == 0,
            "perm_lock": False,
            "owner_id": test_user["id"]
        })

    # Create accounts for the test admin
    for i in range(2):
        accounts.append({
            "acc_id": f"76561199{random_string(9, digits_only=True)}",
            "acc_username": f"test_admin_account_{i}_{random_string(8)}",
            "acc_password": f"password_{random_string(8)}",
            "acc_email_address": f"test_admin_account_{i}_{random_string(8)}@example.com",
            "acc_email_password": f"email_password_{random_string(8)}",
            "acc_created_at": datetime.now().timestamp(),
            "prime": i % 2 == 0,
            "lock": i % 3 == 0,
            "perm_lock": False,
            "owner_id": test_admin["id"]
        })

    return accounts

# Test token
@pytest.fixture(scope="function")
def test_token(test_user: Dict[str, Any]) -> str:
    """
    Create a test token.

    Args:
        test_user (Dict[str, Any]): A test user

    Returns:
        str: A test token
    """
    from jose import jwt

    # Create a token that expires in 30 minutes
    expires = datetime.now() + timedelta(minutes=30)

    # Create the token payload
    payload = {
        "sub": test_user["username"],
        "user_id": test_user["id"],
        "user_role": test_user["role"],
        "exp": expires.timestamp()
    }

    # Create the token
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

    return token

# Test admin token
@pytest.fixture(scope="function")
def test_admin_token(test_admin: Dict[str, Any]) -> str:
    """
    Create a test admin token.

    Args:
        test_admin (Dict[str, Any]): A test admin user

    Returns:
        str: A test admin token
    """
    from jose import jwt

    # Create a token that expires in 30 minutes
    expires = datetime.now() + timedelta(minutes=30)

    # Create the token payload
    payload = {
        "sub": test_admin["username"],
        "user_id": test_admin["id"],
        "user_role": test_admin["role"],
        "exp": expires.timestamp()
    }

    # Create the token
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

    return token

# Utility functions
def random_string(length: int = 8, digits_only: bool = False) -> str:
    """
    Generate a random string.

    Args:
        length (int, optional): The length of the string. Defaults to 8.
        digits_only (bool, optional): Whether to use only digits. Defaults to False.

    Returns:
        str: A random string
    """
    if digits_only:
        return ''.join(random.choices(string.digits, k=length))
    else:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

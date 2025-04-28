"""
Test script for the secure database access layer.

This script tests the secure database access layer by:
1. Testing the SecureDatabase class
2. Testing the secure_db_context context manager
3. Testing the with_secure_db decorator
"""

import logging
import sys
import os
import json
from typing import Dict, Any, List, Optional
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.secure_access import SecureDatabase, get_secure_db, secure_db_context, with_secure_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestSecureDatabase(unittest.TestCase):
    """Test the SecureDatabase class."""

    def setUp(self):
        """Set up the test case."""
        # Create a mock connection
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Create a mock for get_connection_with_retries
        self.get_connection_patcher = patch('db.secure_access.get_connection_with_retries')
        self.mock_get_connection = self.get_connection_patcher.start()
        self.mock_get_connection.return_value = self.mock_conn

        # Create a mock for set_rls_context
        self.set_rls_context_patcher = patch('db.secure_access.set_rls_context')
        self.mock_set_rls_context = self.set_rls_context_patcher.start()
        self.mock_set_rls_context.return_value = True

        # Create a mock for clear_rls_context
        self.clear_rls_context_patcher = patch('db.secure_access.clear_rls_context')
        self.mock_clear_rls_context = self.clear_rls_context_patcher.start()

        # Create a SecureDatabase instance
        self.db = SecureDatabase(user_id=1, user_role="admin")

    def tearDown(self):
        """Tear down the test case."""
        # Stop the patchers
        self.get_connection_patcher.stop()
        self.set_rls_context_patcher.stop()
        self.clear_rls_context_patcher.stop()

        # Close the database connection
        if self.db.conn is not None:
            self.db.close()

    def test_connect(self):
        """Test the connect method."""
        # Test successful connection
        result = self.db.connect()
        self.assertTrue(result)
        self.assertEqual(self.db.conn, self.mock_conn)

        # Test that set_rls_context was called
        self.mock_set_rls_context.assert_called_once()

        # Test connection failure
        self.mock_get_connection.return_value = None
        db = SecureDatabase(user_id=1, user_role="admin")
        result = db.connect()
        self.assertFalse(result)

    def test_close(self):
        """Test the close method."""
        # Connect first
        self.db.connect()

        # Test close
        self.db.close()
        self.assertIsNone(self.db.conn)

        # Test that clear_rls_context was called
        self.mock_clear_rls_context.assert_called_once()

    def test_transaction(self):
        """Test the transaction context manager."""
        # Connect first
        self.db.connect()

        # Test successful transaction
        with self.db.transaction():
            self.assertTrue(self.db._in_transaction)

        # Test that commit was called
        self.mock_conn.commit.assert_called_once()
        self.assertFalse(self.db._in_transaction)

        # Test transaction with exception
        self.mock_conn.commit.reset_mock()
        try:
            with self.db.transaction():
                self.assertTrue(self.db._in_transaction)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Test that rollback was called
        self.mock_conn.rollback.assert_called_once()
        self.assertFalse(self.db._in_transaction)

    def test_execute_query(self):
        """Test the execute_query method."""
        # Connect first
        self.db.connect()

        # Mock cursor.description and fetchall
        self.mock_cursor.description = [("id",), ("name",)]
        self.mock_cursor.fetchall.return_value = [(1, "test"), (2, "test2")]

        # Create a mock for psycopg2.extras.DictCursor
        with patch('psycopg2.extras.DictCursor') as mock_dict_cursor:
            # Make the mock return our mock cursor
            self.mock_conn.cursor.return_value = self.mock_cursor

            # Test execute_query
            with patch.object(self.db, 'connect', return_value=True):
                # Mock the dict conversion
                self.db.execute_query = MagicMock(return_value=[
                    {"id": 1, "name": "test"},
                    {"id": 2, "name": "test2"}
                ])

                # Test execute_query
                results = self.db.execute_query("SELECT * FROM test")

                # Test that the results are correct
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0]["id"], 1)
                self.assertEqual(results[0]["name"], "test")
                self.assertEqual(results[1]["id"], 2)
                self.assertEqual(results[1]["name"], "test2")

    def test_execute_command(self):
        """Test the execute_command method."""
        # Connect first
        self.db.connect()

        # Mock cursor.rowcount
        self.mock_cursor.rowcount = 1

        # Test execute_command
        result = self.db.execute_command("INSERT INTO test (name) VALUES (%s)", ("test",))

        # Test that cursor.execute was called
        self.mock_cursor.execute.assert_called()

        # Test that the result is correct
        self.assertEqual(result, 1)

        # Test that commit was called
        self.mock_conn.commit.assert_called_once()

    def test_get_by_id(self):
        """Test the get_by_id method."""
        # Connect first
        self.db.connect()

        # Mock execute_query
        with patch.object(self.db, 'execute_query') as mock_execute_query:
            mock_execute_query.return_value = [{"id": 1, "name": "test"}]

            # Test get_by_id
            result = self.db.get_by_id("test", "id", 1)

            # Test that execute_query was called
            mock_execute_query.assert_called_with("SELECT * FROM test WHERE id = %s", (1,))

            # Test that the result is correct
            self.assertEqual(result["id"], 1)
            self.assertEqual(result["name"], "test")

    def test_get_all(self):
        """Test the get_all method."""
        # Connect first
        self.db.connect()

        # Mock execute_query
        with patch.object(self.db, 'execute_query') as mock_execute_query:
            mock_execute_query.return_value = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]

            # Test get_all
            results = self.db.get_all("test", "id = %s", (1,), "id", 10, 0)

            # Test that execute_query was called
            mock_execute_query.assert_called_with("SELECT * FROM test WHERE id = %s ORDER BY id LIMIT 10 OFFSET 0", (1,))

            # Test that the results are correct
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["id"], 1)
            self.assertEqual(results[0]["name"], "test")
            self.assertEqual(results[1]["id"], 2)
            self.assertEqual(results[1]["name"], "test2")

    def test_insert(self):
        """Test the insert method."""
        # Connect first
        self.db.connect()

        # Mock execute_command
        with patch.object(self.db, 'execute_command') as mock_execute_command:
            mock_execute_command.return_value = 1

            # Test insert
            result = self.db.insert("test", {"name": "test"})

            # Test that execute_command was called
            mock_execute_command.assert_called_with("INSERT INTO test (name) VALUES (%s)", ("test",))

            # Test that the result is correct
            self.assertEqual(result, 1)

    def test_update(self):
        """Test the update method."""
        # Connect first
        self.db.connect()

        # Mock execute_command
        with patch.object(self.db, 'execute_command') as mock_execute_command:
            mock_execute_command.return_value = 1

            # Test update
            result = self.db.update("test", {"name": "test2"}, "id = %s", (1,))

            # Test that execute_command was called
            mock_execute_command.assert_called_with("UPDATE test SET name = %s WHERE id = %s", ("test2", 1))

            # Test that the result is correct
            self.assertEqual(result, 1)

    def test_delete(self):
        """Test the delete method."""
        # Connect first
        self.db.connect()

        # Mock execute_command
        with patch.object(self.db, 'execute_command') as mock_execute_command:
            mock_execute_command.return_value = 1

            # Test delete
            result = self.db.delete("test", "id = %s", (1,))

            # Test that execute_command was called
            mock_execute_command.assert_called_with("DELETE FROM test WHERE id = %s", (1,))

            # Test that the result is correct
            self.assertEqual(result, 1)

    def test_count(self):
        """Test the count method."""
        # Connect first
        self.db.connect()

        # Mock execute_query
        with patch.object(self.db, 'execute_query') as mock_execute_query:
            mock_execute_query.return_value = [{"count": 2}]

            # Test count
            result = self.db.count("test", "id = %s", (1,))

            # Test that execute_query was called
            mock_execute_query.assert_called_with("SELECT COUNT(*) FROM test WHERE id = %s", (1,))

            # Test that the result is correct
            self.assertEqual(result, 2)

    def test_exists(self):
        """Test the exists method."""
        # Connect first
        self.db.connect()

        # Mock execute_query
        with patch.object(self.db, 'execute_query') as mock_execute_query:
            mock_execute_query.return_value = [{"exists": True}]

            # Test exists
            result = self.db.exists("test", "id = %s", (1,))

            # Test that execute_query was called
            mock_execute_query.assert_called_with("SELECT EXISTS (SELECT 1 FROM test WHERE id = %s)", (1,))

            # Test that the result is correct
            self.assertTrue(result)

class TestSecureDatabaseContextManager(unittest.TestCase):
    """Test the secure_db_context context manager."""

    def setUp(self):
        """Set up the test case."""
        # Create a mock for get_secure_db
        self.get_secure_db_patcher = patch('db.secure_access.get_secure_db')
        self.mock_get_secure_db = self.get_secure_db_patcher.start()

        # Create a mock SecureDatabase
        self.mock_db = MagicMock()
        self.mock_get_secure_db.return_value = self.mock_db

    def tearDown(self):
        """Tear down the test case."""
        # Stop the patchers
        self.get_secure_db_patcher.stop()

    def test_secure_db_context(self):
        """Test the secure_db_context context manager."""
        # Test successful context
        with secure_db_context(user_id=1, user_role="admin") as db:
            self.assertEqual(db, self.mock_db)

        # Test that close was called
        self.mock_db.close.assert_called_once()

        # Test context with exception
        self.mock_db.close.reset_mock()
        try:
            with secure_db_context(user_id=1, user_role="admin") as db:
                self.assertEqual(db, self.mock_db)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Test that close was called
        self.mock_db.close.assert_called_once()

class TestWithSecureDbDecorator(unittest.TestCase):
    """Test the with_secure_db decorator."""

    def setUp(self):
        """Set up the test case."""
        # Create a mock for secure_db_context
        self.secure_db_context_patcher = patch('db.secure_access.secure_db_context')
        self.mock_secure_db_context = self.secure_db_context_patcher.start()

        # Create a mock context manager
        self.mock_context = MagicMock()
        self.mock_secure_db_context.return_value = self.mock_context

        # Create a mock SecureDatabase
        self.mock_db = MagicMock()
        self.mock_context.__enter__.return_value = self.mock_db

    def tearDown(self):
        """Tear down the test case."""
        # Stop the patchers
        self.secure_db_context_patcher.stop()

    def test_with_secure_db(self):
        """Test the with_secure_db decorator."""
        # Define a test function
        @with_secure_db()
        def test_func(db, user_id=None, user_role=None):
            return db, user_id, user_role

        # Test the decorated function
        db, user_id, user_role = test_func(user_id=1, user_role="admin")

        # Test that secure_db_context was called
        self.mock_secure_db_context.assert_called_with(1, "admin")

        # Test that the result is correct
        self.assertEqual(db, self.mock_db)
        self.assertEqual(user_id, 1)
        self.assertEqual(user_role, "admin")

    def test_with_secure_db_custom_args(self):
        """Test the with_secure_db decorator with custom argument names."""
        # Define a test function
        @with_secure_db(user_id_arg="uid", user_role_arg="role")
        def test_func(db, uid=None, role=None):
            return db, uid, role

        # Test the decorated function
        db, uid, role = test_func(uid=1, role="admin")

        # Test that secure_db_context was called
        self.mock_secure_db_context.assert_called_with(1, "admin")

        # Test that the result is correct
        self.assertEqual(db, self.mock_db)
        self.assertEqual(uid, 1)
        self.assertEqual(role, "admin")

if __name__ == "__main__":
    unittest.main()

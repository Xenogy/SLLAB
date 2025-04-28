"""
Integration tests for user database connection.
"""

import pytest
import psycopg2
from db.user_connection import (
    get_user_db_connection, get_user_db_connection_with_retries,
    get_user_connection_info, set_rls_context, clear_rls_context
)

@pytest.mark.integration
@pytest.mark.db
class TestUserConnection:
    """Tests for user database connection."""
    
    def test_get_user_db_connection(self):
        """Test get_user_db_connection context manager."""
        # Use the context manager
        with get_user_db_connection(user_id=1, user_role="admin") as conn:
            # Check that the connection is valid
            assert conn is not None
            assert isinstance(conn, psycopg2.extensions.connection)
            assert not conn.closed
            
            # Check that the RLS context was set
            cursor = conn.cursor()
            cursor.execute("SELECT current_setting('app.current_user_id', TRUE)")
            user_id = cursor.fetchone()[0]
            cursor.execute("SELECT current_setting('app.current_user_role', TRUE)")
            user_role = cursor.fetchone()[0]
            cursor.close()
            
            # Check the RLS context
            assert user_id == "1"
            assert user_role == "admin"
        
        # Check that the connection was returned
        assert conn.closed
    
    def test_get_user_db_connection_with_retries(self):
        """Test get_user_db_connection_with_retries context manager."""
        # Use the context manager
        with get_user_db_connection_with_retries(user_id=1, user_role="admin", max_retries=3, retry_interval=1) as conn:
            # Check that the connection is valid
            assert conn is not None
            assert isinstance(conn, psycopg2.extensions.connection)
            assert not conn.closed
            
            # Check that the RLS context was set
            cursor = conn.cursor()
            cursor.execute("SELECT current_setting('app.current_user_id', TRUE)")
            user_id = cursor.fetchone()[0]
            cursor.execute("SELECT current_setting('app.current_user_role', TRUE)")
            user_role = cursor.fetchone()[0]
            cursor.close()
            
            # Check the RLS context
            assert user_id == "1"
            assert user_role == "admin"
        
        # Check that the connection was returned
        assert conn.closed
    
    def test_get_user_connection_info(self):
        """Test get_user_connection_info function."""
        # Use the context manager
        with get_user_db_connection(user_id=1, user_role="admin") as conn:
            # Get the user connection info
            info = get_user_connection_info(conn)
            
            # Check the info
            assert info is not None
            assert isinstance(info, dict)
            assert info["user_id"] == "1"
            assert info["user_role"] == "admin"
    
    def test_set_rls_context(self):
        """Test set_rls_context function."""
        # Get a connection
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="accountdb",
            user="postgres",
            password="postgres"
        )
        
        try:
            # Set the RLS context
            set_rls_context(conn, 1, "admin")
            
            # Check that the RLS context was set
            cursor = conn.cursor()
            cursor.execute("SELECT current_setting('app.current_user_id', TRUE)")
            user_id = cursor.fetchone()[0]
            cursor.execute("SELECT current_setting('app.current_user_role', TRUE)")
            user_role = cursor.fetchone()[0]
            cursor.close()
            
            # Check the RLS context
            assert user_id == "1"
            assert user_role == "admin"
            
            # Clear the RLS context
            clear_rls_context(conn)
            
            # Check that the RLS context was cleared
            cursor = conn.cursor()
            cursor.execute("SELECT current_setting('app.current_user_id', TRUE)")
            user_id = cursor.fetchone()[0]
            cursor.execute("SELECT current_setting('app.current_user_role', TRUE)")
            user_role = cursor.fetchone()[0]
            cursor.close()
            
            # Check the RLS context
            assert user_id == "0"
            assert user_role == "none"
        finally:
            # Close the connection
            conn.close()

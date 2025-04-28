"""
Integration tests for database connection.
"""

import pytest
import psycopg2
from db.connection import (
    create_connection_pool, get_connection, return_connection,
    get_db_connection, get_connection_with_retries, get_db_connection_with_retries,
    get_pool_stats, close_all_connections
)

@pytest.mark.integration
@pytest.mark.db
class TestDbConnection:
    """Tests for database connection."""
    
    def test_create_connection_pool(self):
        """Test create_connection_pool function."""
        # Create a connection pool
        pool = create_connection_pool(min_connections=1, max_connections=5)
        
        # Check that the pool was created
        assert pool is not None
        assert pool.minconn == 1
        assert pool.maxconn == 5
        
        # Clean up
        pool.closeall()
    
    def test_get_connection(self):
        """Test get_connection function."""
        # Get a connection
        conn = get_connection()
        
        # Check that the connection is valid
        assert conn is not None
        assert isinstance(conn, psycopg2.extensions.connection)
        assert not conn.closed
        
        # Return the connection
        return_connection(conn)
    
    def test_get_db_connection(self):
        """Test get_db_connection context manager."""
        # Use the context manager
        with get_db_connection() as conn:
            # Check that the connection is valid
            assert conn is not None
            assert isinstance(conn, psycopg2.extensions.connection)
            assert not conn.closed
            
            # Execute a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            # Check the result
            assert result == (1,)
        
        # Check that the connection was returned
        assert conn.closed
    
    def test_get_connection_with_retries(self):
        """Test get_connection_with_retries function."""
        # Get a connection with retries
        conn = get_connection_with_retries(max_retries=3, retry_interval=1)
        
        # Check that the connection is valid
        assert conn is not None
        assert isinstance(conn, psycopg2.extensions.connection)
        assert not conn.closed
        
        # Return the connection
        return_connection(conn)
    
    def test_get_db_connection_with_retries(self):
        """Test get_db_connection_with_retries context manager."""
        # Use the context manager
        with get_db_connection_with_retries(max_retries=3, retry_interval=1) as conn:
            # Check that the connection is valid
            assert conn is not None
            assert isinstance(conn, psycopg2.extensions.connection)
            assert not conn.closed
            
            # Execute a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            # Check the result
            assert result == (1,)
        
        # Check that the connection was returned
        assert conn.closed
    
    def test_get_pool_stats(self):
        """Test get_pool_stats function."""
        # Get the pool stats
        stats = get_pool_stats()
        
        # Check that the stats are valid
        assert stats is not None
        assert isinstance(stats, dict)
        assert "created_connections" in stats
        assert "returned_connections" in stats
        assert "failed_connections" in stats
        assert "max_connections_used" in stats
    
    def test_close_all_connections(self):
        """Test close_all_connections function."""
        # Get a connection
        conn = get_connection()
        
        # Check that the connection is valid
        assert conn is not None
        assert isinstance(conn, psycopg2.extensions.connection)
        assert not conn.closed
        
        # Close all connections
        close_all_connections()
        
        # Check that the connection was closed
        assert conn.closed

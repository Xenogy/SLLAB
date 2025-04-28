"""
Database connection management module.

This module provides functions for managing database connections, including
connection pooling, connection creation, and connection closing.
"""

import psycopg2
import psycopg2.pool
import psycopg2.extensions
import time
import logging
from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Connection pool configuration
DEFAULT_MIN_CONNECTIONS = 1
DEFAULT_MAX_CONNECTIONS = 20
DEFAULT_CONNECTION_TIMEOUT = 30  # seconds
DEFAULT_IDLE_TIMEOUT = 600  # seconds (10 minutes)
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_INTERVAL = 1  # seconds

# Connection pool statistics
pool_stats = {
    "created_connections": 0,
    "returned_connections": 0,
    "failed_connections": 0,
    "max_connections_used": 0,
}

# Create a connection pool
def create_connection_pool(
    min_connections: int = None,
    max_connections: int = None,
    connection_timeout: int = None,
    **kwargs
) -> Optional[psycopg2.pool.AbstractConnectionPool]:
    """
    Create a database connection pool.

    Args:
        min_connections (int, optional): Minimum number of connections. Defaults to Config.DB_MIN_CONNECTIONS or DEFAULT_MIN_CONNECTIONS.
        max_connections (int, optional): Maximum number of connections. Defaults to Config.DB_MAX_CONNECTIONS or DEFAULT_MAX_CONNECTIONS.
        connection_timeout (int, optional): Connection timeout in seconds. Defaults to Config.DB_CONNECTION_TIMEOUT or DEFAULT_CONNECTION_TIMEOUT.
        **kwargs: Additional arguments to pass to the connection pool.

    Returns:
        Optional[psycopg2.pool.AbstractConnectionPool]: A connection pool or None if creation fails.
    """
    # Get configuration values
    min_conn = min_connections or getattr(Config, 'DB_MIN_CONNECTIONS', DEFAULT_MIN_CONNECTIONS)
    max_conn = max_connections or getattr(Config, 'DB_MAX_CONNECTIONS', DEFAULT_MAX_CONNECTIONS)
    timeout = connection_timeout or getattr(Config, 'DB_CONNECTION_TIMEOUT', DEFAULT_CONNECTION_TIMEOUT)

    # Validate configuration values
    min_conn = max(1, min_conn)  # Minimum of 1 connection
    max_conn = max(min_conn, max_conn)  # Maximum must be at least minimum
    timeout = max(1, timeout)  # Minimum timeout of 1 second

    try:
        # Create the connection pool
        pool = psycopg2.pool.ThreadedConnectionPool(
            min_conn,
            max_conn,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASS,
            connect_timeout=timeout,
            target_session_attrs="read-write",
            **kwargs
        )
        logger.info(f"Database connection pool created successfully (min={min_conn}, max={max_conn})")
        return pool
    except Exception as e:
        logger.error(f"Error creating database connection pool: {e}")
        return None

# Initialize the connection pool
connection_pool = create_connection_pool()

# Get a connection from the pool
def get_connection() -> Optional[psycopg2.extensions.connection]:
    """
    Get a connection from the pool.

    Returns:
        Optional[psycopg2.extensions.connection]: A database connection or None if not available.
    """
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            pool_stats["created_connections"] += 1
            pool_stats["max_connections_used"] = max(
                pool_stats["max_connections_used"],
                pool_stats["created_connections"] - pool_stats["returned_connections"]
            )
            return conn
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            pool_stats["failed_connections"] += 1
            return None
    else:
        logger.warning("Connection pool not available")
        return None

# Return a connection to the pool
def return_connection(conn: Optional[psycopg2.extensions.connection]) -> None:
    """
    Return a connection to the pool.

    Args:
        conn (Optional[psycopg2.extensions.connection]): The connection to return.
    """
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
            pool_stats["returned_connections"] += 1
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")

# Context manager for database connections
@contextmanager
def get_db_connection() -> Generator[Optional[psycopg2.extensions.connection], None, None]:
    """
    Context manager for database connections.

    Yields:
        Generator[Optional[psycopg2.extensions.connection], None, None]: A database connection or None if not available.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        if conn:
            return_connection(conn)

# Get a connection with retries
def get_connection_with_retries(
    max_retries: int = None,
    retry_interval: int = None
) -> Optional[psycopg2.extensions.connection]:
    """
    Get a connection from the pool with retries.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to Config.DB_MAX_RETRIES or DEFAULT_MAX_RETRIES.
        retry_interval (int, optional): Retry interval in seconds. Defaults to Config.DB_RETRY_INTERVAL or DEFAULT_RETRY_INTERVAL.

    Returns:
        Optional[psycopg2.extensions.connection]: A database connection or None if not available after retries.
    """
    # Get configuration values
    retries = max_retries or getattr(Config, 'DB_MAX_RETRIES', DEFAULT_MAX_RETRIES)
    interval = retry_interval or getattr(Config, 'DB_RETRY_INTERVAL', DEFAULT_RETRY_INTERVAL)

    # Validate configuration values
    retries = max(1, retries)  # Minimum of 1 retry
    interval = max(0.1, interval)  # Minimum interval of 0.1 seconds

    for i in range(retries):
        conn = get_connection()
        if conn:
            return conn

        if i < retries - 1:
            logger.warning(f"Failed to get connection (attempt {i+1}/{retries}), retrying in {interval} seconds...")
            time.sleep(interval)

    logger.error(f"Failed to get connection after {retries} attempts")
    return None

# Context manager for database connections with retries
@contextmanager
def get_db_connection_with_retries(
    max_retries: int = None,
    retry_interval: int = None
) -> Generator[Optional[psycopg2.extensions.connection], None, None]:
    """
    Context manager for database connections with retries.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to Config.DB_MAX_RETRIES or DEFAULT_MAX_RETRIES.
        retry_interval (int, optional): Retry interval in seconds. Defaults to Config.DB_RETRY_INTERVAL or DEFAULT_RETRY_INTERVAL.

    Yields:
        Generator[Optional[psycopg2.extensions.connection], None, None]: A database connection or None if not available after retries.
    """
    conn = get_connection_with_retries(max_retries, retry_interval)
    try:
        yield conn
    finally:
        if conn:
            return_connection(conn)

# Get connection pool statistics
def get_pool_stats() -> Dict[str, Any]:
    """
    Get connection pool statistics.

    Returns:
        Dict[str, Any]: A dictionary with connection pool statistics.
    """
    stats = pool_stats.copy()

    # Add current pool status if available
    if connection_pool:
        stats["min_connections"] = connection_pool.minconn
        stats["max_connections"] = connection_pool.maxconn

        # Calculate current connections
        current_connections = pool_stats["created_connections"] - pool_stats["returned_connections"]
        stats["current_connections"] = current_connections

        # Calculate available connections
        available_connections = connection_pool.maxconn - current_connections
        stats["available_connections"] = max(0, available_connections)

        # Calculate pool utilization
        if connection_pool.maxconn > 0:
            stats["pool_utilization"] = round((current_connections / connection_pool.maxconn) * 100, 2)
        else:
            stats["pool_utilization"] = 0

        # Add pool size for compatibility with health check
        stats["pool_size"] = connection_pool.maxconn
        stats["used_connections"] = current_connections
    else:
        # Set default values if pool is not available
        stats["min_connections"] = 0
        stats["max_connections"] = 0
        stats["current_connections"] = 0
        stats["available_connections"] = 0
        stats["pool_utilization"] = 0
        stats["pool_size"] = 0
        stats["used_connections"] = 0

    return stats

# Check database health
def check_database_health() -> Dict[str, Any]:
    """
    Check database health.

    Returns:
        Dict[str, Any]: A dictionary with database health information.
    """
    health = {
        "healthy": True,
        "connection_health": {},
        "pool_health": {},
        "query_performance": {}
    }

    try:
        # Check if we can get a connection
        with get_db_connection() as conn:
            if not conn:
                health["healthy"] = False
                health["connection_health"]["can_connect"] = False
                return health

            health["connection_health"]["can_connect"] = True

            # Check if we can execute a query
            cursor = conn.cursor()

            # Check connection info
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            health["connection_health"]["version"] = version

            # Check current connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]
            health["connection_health"]["active_connections"] = connections

            # Check pool health
            pool_stats = get_pool_stats()
            health["pool_health"] = pool_stats

            # Check if pool is overloaded
            if pool_stats.get("pool_utilization", 0) > 80:
                health["healthy"] = False
                health["pool_health"]["overloaded"] = True

            # Check query performance
            start_time = time.time()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            query_time = time.time() - start_time
            health["query_performance"]["simple_query_time"] = query_time

            # Check if query is too slow
            if query_time > 0.1:
                health["healthy"] = False
                health["query_performance"]["slow_query"] = True

            # Close cursor
            cursor.close()
    except Exception as e:
        health["healthy"] = False
        health["error"] = str(e)

    return health

# Reset connection pool statistics
def reset_pool_stats() -> None:
    """
    Reset connection pool statistics.
    """
    global pool_stats
    pool_stats = {
        "created_connections": 0,
        "returned_connections": 0,
        "failed_connections": 0,
        "max_connections_used": 0,
    }

# Close all connections in the pool
def close_all_connections() -> None:
    """
    Close all connections in the pool.
    """
    if connection_pool:
        try:
            connection_pool.closeall()
            logger.info("All connections in the pool closed")
        except Exception as e:
            logger.error(f"Error closing all connections in the pool: {e}")

# Check if a connection is alive
def is_connection_alive(conn: psycopg2.extensions.connection) -> bool:
    """
    Check if a connection is alive.

    Args:
        conn (psycopg2.extensions.connection): The connection to check.

    Returns:
        bool: True if the connection is alive, False otherwise.
    """
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True
    except Exception:
        return False

# Create a new connection pool
def recreate_connection_pool(
    min_connections: int = None,
    max_connections: int = None,
    connection_timeout: int = None,
    **kwargs
) -> Optional[psycopg2.pool.AbstractConnectionPool]:
    """
    Create a new connection pool and replace the existing one.

    Args:
        min_connections (int, optional): Minimum number of connections. Defaults to Config.DB_MIN_CONNECTIONS or DEFAULT_MIN_CONNECTIONS.
        max_connections (int, optional): Maximum number of connections. Defaults to Config.DB_MAX_CONNECTIONS or DEFAULT_MAX_CONNECTIONS.
        connection_timeout (int, optional): Connection timeout in seconds. Defaults to Config.DB_CONNECTION_TIMEOUT or DEFAULT_CONNECTION_TIMEOUT.
        **kwargs: Additional arguments to pass to the connection pool.

    Returns:
        Optional[psycopg2.pool.AbstractConnectionPool]: A connection pool or None if creation fails.
    """
    global connection_pool

    # Close all connections in the existing pool
    if connection_pool:
        close_all_connections()

    # Create a new connection pool
    connection_pool = create_connection_pool(
        min_connections,
        max_connections,
        connection_timeout,
        **kwargs
    )

    # Reset pool statistics
    reset_pool_stats()

    return connection_pool

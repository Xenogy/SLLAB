"""
Database health check module.

This module provides functions for checking the health of the database, including
connection health, pool health, and query performance.
"""

import logging
import time
from typing import Dict, Any, Optional
import psycopg2
import psycopg2.extensions

from .connection import get_db_connection, get_pool_stats
from .utils import execute_query

# Configure logging
logger = logging.getLogger(__name__)

def check_connection_health(conn: psycopg2.extensions.connection) -> Dict[str, Any]:
    """
    Check the health of a database connection.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Dict[str, Any]: A dictionary with connection health information.
    """
    health = {
        "status": "unknown",
        "message": "",
        "response_time_ms": None,
        "timestamp": time.time()
    }

    if not conn:
        health["status"] = "error"
        health["message"] = "No database connection available"
        return health

    try:
        # Measure response time
        start_time = time.time()
        
        # Execute a simple query
        result = execute_query(conn, "SELECT 1", fetch='one')
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        if result and result[0] == 1:
            health["status"] = "healthy"
            health["message"] = "Database connection is healthy"
            health["response_time_ms"] = response_time_ms
        else:
            health["status"] = "warning"
            health["message"] = "Database connection returned unexpected result"
            health["response_time_ms"] = response_time_ms
    except Exception as e:
        health["status"] = "error"
        health["message"] = f"Database connection error: {str(e)}"

    return health

def check_pool_health() -> Dict[str, Any]:
    """
    Check the health of the connection pool.

    Returns:
        Dict[str, Any]: A dictionary with pool health information.
    """
    health = {
        "status": "unknown",
        "message": "",
        "pool_stats": get_pool_stats(),
        "timestamp": time.time()
    }

    # Get a connection from the pool
    with get_db_connection() as conn:
        # Check connection health
        conn_health = check_connection_health(conn)
        
        if conn_health["status"] == "healthy":
            health["status"] = "healthy"
            health["message"] = "Connection pool is healthy"
        elif conn_health["status"] == "warning":
            health["status"] = "warning"
            health["message"] = conn_health["message"]
        else:
            health["status"] = "error"
            health["message"] = conn_health["message"]
        
        health["connection_health"] = conn_health

    return health

def check_query_performance(
    conn: psycopg2.extensions.connection,
    query: str,
    params: Optional[tuple] = None
) -> Dict[str, Any]:
    """
    Check the performance of a database query.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (str): The query to execute.
        params (Optional[tuple], optional): The query parameters. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary with query performance information.
    """
    performance = {
        "status": "unknown",
        "message": "",
        "query": query,
        "params": params,
        "execution_time_ms": None,
        "timestamp": time.time()
    }

    if not conn:
        performance["status"] = "error"
        performance["message"] = "No database connection available"
        return performance

    try:
        # Measure execution time
        start_time = time.time()
        
        # Execute the query
        execute_query(conn, query, params)
        
        # Calculate execution time
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        
        performance["status"] = "success"
        performance["message"] = "Query executed successfully"
        performance["execution_time_ms"] = execution_time_ms
    except Exception as e:
        performance["status"] = "error"
        performance["message"] = f"Query execution error: {str(e)}"

    return performance

def check_database_health() -> Dict[str, Any]:
    """
    Check the health of the database.

    Returns:
        Dict[str, Any]: A dictionary with database health information.
    """
    health = {
        "status": "unknown",
        "message": "",
        "timestamp": time.time()
    }

    # Check pool health
    pool_health = check_pool_health()
    health["pool_health"] = pool_health
    
    if pool_health["status"] == "healthy":
        health["status"] = "healthy"
        health["message"] = "Database is healthy"
    elif pool_health["status"] == "warning":
        health["status"] = "warning"
        health["message"] = pool_health["message"]
    else:
        health["status"] = "error"
        health["message"] = pool_health["message"]

    return health

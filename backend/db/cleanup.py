"""
Database cleanup module.

This module provides functions for cleaning up the database, including
closing connections, vacuuming tables, and analyzing tables.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import psycopg2
import psycopg2.extensions

from .connection import get_db_connection, close_all_connections
from .utils import execute_query, execute_query_with_transaction

# Configure logging
logger = logging.getLogger(__name__)

def vacuum_table(
    conn: psycopg2.extensions.connection,
    table_name: str,
    full: bool = False,
    analyze: bool = True
) -> bool:
    """
    Vacuum a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        full (bool, optional): Whether to perform a full vacuum. Defaults to False.
        analyze (bool, optional): Whether to analyze the table. Defaults to True.

    Returns:
        bool: True if the vacuum was successful, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Build the vacuum command
        vacuum_cmd = "VACUUM"
        if full:
            vacuum_cmd += " FULL"
        if analyze:
            vacuum_cmd += " ANALYZE"
        vacuum_cmd += f" {table_name}"
        
        # Execute the vacuum command
        execute_query(conn, vacuum_cmd)
        logger.info(f"Vacuumed table {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error vacuuming table {table_name}: {e}")
        return False

def analyze_table(
    conn: psycopg2.extensions.connection,
    table_name: str
) -> bool:
    """
    Analyze a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.

    Returns:
        bool: True if the analyze was successful, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Execute the analyze command
        execute_query(conn, f"ANALYZE {table_name}")
        logger.info(f"Analyzed table {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error analyzing table {table_name}: {e}")
        return False

def reindex_table(
    conn: psycopg2.extensions.connection,
    table_name: str
) -> bool:
    """
    Reindex a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.

    Returns:
        bool: True if the reindex was successful, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Execute the reindex command
        execute_query(conn, f"REINDEX TABLE {table_name}")
        logger.info(f"Reindexed table {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error reindexing table {table_name}: {e}")
        return False

def truncate_table(
    conn: psycopg2.extensions.connection,
    table_name: str
) -> bool:
    """
    Truncate a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.

    Returns:
        bool: True if the truncate was successful, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Execute the truncate command
        execute_query_with_transaction(conn, f"TRUNCATE TABLE {table_name}")
        logger.info(f"Truncated table {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error truncating table {table_name}: {e}")
        return False

def get_table_names(
    conn: psycopg2.extensions.connection,
    schema: str = 'public'
) -> Optional[List[str]]:
    """
    Get the names of all tables in a schema.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        schema (str, optional): The schema name. Defaults to 'public'.

    Returns:
        Optional[List[str]]: A list of table names or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the table names
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        results = execute_query(conn, query, (schema,), 'all')
        if not results:
            return None
        
        return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Error getting table names: {e}")
        return None

def vacuum_all_tables(
    conn: psycopg2.extensions.connection,
    full: bool = False,
    analyze: bool = True
) -> Dict[str, Any]:
    """
    Vacuum all tables in the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        full (bool, optional): Whether to perform a full vacuum. Defaults to False.
        analyze (bool, optional): Whether to analyze the tables. Defaults to True.

    Returns:
        Dict[str, Any]: A dictionary with vacuum results.
    """
    results = {
        "success": True,
        "tables": {},
        "timestamp": time.time()
    }

    if not conn:
        logger.warning("No database connection available")
        results["success"] = False
        results["error"] = "No database connection available"
        return results

    try:
        # Get the table names
        table_names = get_table_names(conn)
        if not table_names:
            results["success"] = False
            results["error"] = "No tables found"
            return results
        
        # Vacuum each table
        for table_name in table_names:
            table_result = vacuum_table(conn, table_name, full, analyze)
            results["tables"][table_name] = {
                "success": table_result
            }
            
            if not table_result:
                results["success"] = False
        
        return results
    except Exception as e:
        logger.error(f"Error vacuuming all tables: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results

def analyze_all_tables(
    conn: psycopg2.extensions.connection
) -> Dict[str, Any]:
    """
    Analyze all tables in the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Dict[str, Any]: A dictionary with analyze results.
    """
    results = {
        "success": True,
        "tables": {},
        "timestamp": time.time()
    }

    if not conn:
        logger.warning("No database connection available")
        results["success"] = False
        results["error"] = "No database connection available"
        return results

    try:
        # Get the table names
        table_names = get_table_names(conn)
        if not table_names:
            results["success"] = False
            results["error"] = "No tables found"
            return results
        
        # Analyze each table
        for table_name in table_names:
            table_result = analyze_table(conn, table_name)
            results["tables"][table_name] = {
                "success": table_result
            }
            
            if not table_result:
                results["success"] = False
        
        return results
    except Exception as e:
        logger.error(f"Error analyzing all tables: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results

def reindex_all_tables(
    conn: psycopg2.extensions.connection
) -> Dict[str, Any]:
    """
    Reindex all tables in the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Dict[str, Any]: A dictionary with reindex results.
    """
    results = {
        "success": True,
        "tables": {},
        "timestamp": time.time()
    }

    if not conn:
        logger.warning("No database connection available")
        results["success"] = False
        results["error"] = "No database connection available"
        return results

    try:
        # Get the table names
        table_names = get_table_names(conn)
        if not table_names:
            results["success"] = False
            results["error"] = "No tables found"
            return results
        
        # Reindex each table
        for table_name in table_names:
            table_result = reindex_table(conn, table_name)
            results["tables"][table_name] = {
                "success": table_result
            }
            
            if not table_result:
                results["success"] = False
        
        return results
    except Exception as e:
        logger.error(f"Error reindexing all tables: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results

def cleanup_database() -> Dict[str, Any]:
    """
    Clean up the database.

    Returns:
        Dict[str, Any]: A dictionary with cleanup results.
    """
    results = {
        "success": True,
        "timestamp": time.time()
    }

    try:
        # Close all connections
        close_all_connections()
        results["connections_closed"] = True
        
        # Get a new connection
        with get_db_connection() as conn:
            if conn:
                # Vacuum all tables
                vacuum_results = vacuum_all_tables(conn)
                results["vacuum_results"] = vacuum_results
                
                if not vacuum_results["success"]:
                    results["success"] = False
                
                # Analyze all tables
                analyze_results = analyze_all_tables(conn)
                results["analyze_results"] = analyze_results
                
                if not analyze_results["success"]:
                    results["success"] = False
            else:
                results["success"] = False
                results["error"] = "No database connection available"
        
        return results
    except Exception as e:
        logger.error(f"Error cleaning up database: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results

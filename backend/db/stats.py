"""
Database statistics module.

This module provides functions for collecting and analyzing database statistics,
including query performance, connection usage, and table sizes.
"""

import logging
import time
from typing import Dict, Any, Optional, List
import psycopg2
import psycopg2.extensions

from .connection import get_db_connection, get_pool_stats
from .utils import execute_query

# Configure logging
logger = logging.getLogger(__name__)

def get_database_size(conn: psycopg2.extensions.connection) -> Optional[Dict[str, Any]]:
    """
    Get the size of the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[Dict[str, Any]]: A dictionary with database size information or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the database size
        query = """
            SELECT
                pg_database.datname AS database_name,
                pg_size_pretty(pg_database_size(pg_database.datname)) AS pretty_size,
                pg_database_size(pg_database.datname) AS size_bytes
            FROM pg_database
            WHERE pg_database.datname = current_database()
        """
        
        result = execute_query(conn, query, fetch='one')
        if not result:
            return None
        
        return {
            "database_name": result[0],
            "pretty_size": result[1],
            "size_bytes": result[2],
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting database size: {e}")
        return None

def get_table_sizes(conn: psycopg2.extensions.connection) -> Optional[List[Dict[str, Any]]]:
    """
    Get the sizes of all tables in the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries with table size information or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the table sizes
        query = """
            SELECT
                table_schema,
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) AS pretty_total_size,
                pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) AS total_size_bytes,
                pg_size_pretty(pg_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) AS pretty_table_size,
                pg_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) AS table_size_bytes,
                pg_size_pretty(pg_indexes_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) AS pretty_indexes_size,
                pg_indexes_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) AS indexes_size_bytes
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY total_size_bytes DESC
        """
        
        results = execute_query(conn, query, fetch='all')
        if not results:
            return None
        
        table_sizes = []
        for row in results:
            table_sizes.append({
                "table_schema": row[0],
                "table_name": row[1],
                "pretty_total_size": row[2],
                "total_size_bytes": row[3],
                "pretty_table_size": row[4],
                "table_size_bytes": row[5],
                "pretty_indexes_size": row[6],
                "indexes_size_bytes": row[7],
                "timestamp": time.time()
            })
        
        return table_sizes
    except Exception as e:
        logger.error(f"Error getting table sizes: {e}")
        return None

def get_table_row_counts(conn: psycopg2.extensions.connection) -> Optional[List[Dict[str, Any]]]:
    """
    Get the row counts of all tables in the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries with table row count information or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the table names
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        results = execute_query(conn, query, fetch='all')
        if not results:
            return None
        
        table_row_counts = []
        for row in results:
            table_name = row[0]
            
            # Get the row count for the table
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = execute_query(conn, count_query, fetch='one')
            
            if count_result:
                table_row_counts.append({
                    "table_name": table_name,
                    "row_count": count_result[0],
                    "timestamp": time.time()
                })
        
        return table_row_counts
    except Exception as e:
        logger.error(f"Error getting table row counts: {e}")
        return None

def get_index_usage_stats(conn: psycopg2.extensions.connection) -> Optional[List[Dict[str, Any]]]:
    """
    Get the index usage statistics.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries with index usage statistics or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the index usage statistics
        query = """
            SELECT
                schemaname,
                relname AS table_name,
                indexrelname AS index_name,
                idx_scan AS index_scans,
                idx_tup_read AS tuples_read,
                idx_tup_fetch AS tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) AS pretty_index_size,
                pg_relation_size(indexrelid) AS index_size_bytes
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
        """
        
        results = execute_query(conn, query, fetch='all')
        if not results:
            return None
        
        index_usage_stats = []
        for row in results:
            index_usage_stats.append({
                "schema_name": row[0],
                "table_name": row[1],
                "index_name": row[2],
                "index_scans": row[3],
                "tuples_read": row[4],
                "tuples_fetched": row[5],
                "pretty_index_size": row[6],
                "index_size_bytes": row[7],
                "timestamp": time.time()
            })
        
        return index_usage_stats
    except Exception as e:
        logger.error(f"Error getting index usage statistics: {e}")
        return None

def get_table_bloat(conn: psycopg2.extensions.connection) -> Optional[List[Dict[str, Any]]]:
    """
    Get the table bloat statistics.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries with table bloat statistics or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the table bloat statistics
        query = """
            SELECT
                schemaname,
                tablename,
                reltuples::bigint AS row_estimate,
                pg_size_pretty(relpages::bigint * 8192) AS pretty_table_size,
                relpages::bigint * 8192 AS table_size_bytes,
                pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS pretty_actual_size,
                pg_relation_size(schemaname || '.' || tablename) AS actual_size_bytes,
                CASE WHEN relpages > 0
                    THEN round(100 * (relpages::bigint * 8192 - pg_relation_size(schemaname || '.' || tablename)) / (relpages::bigint * 8192))
                    ELSE 0
                END AS bloat_percentage
            FROM pg_catalog.pg_stats
            JOIN pg_catalog.pg_class ON pg_class.relname = tablename
            JOIN pg_catalog.pg_namespace ON pg_namespace.oid = pg_class.relnamespace AND pg_namespace.nspname = schemaname
            WHERE schemaname = 'public'
            GROUP BY schemaname, tablename, reltuples, relpages
            ORDER BY bloat_percentage DESC
        """
        
        results = execute_query(conn, query, fetch='all')
        if not results:
            return None
        
        table_bloat = []
        for row in results:
            table_bloat.append({
                "schema_name": row[0],
                "table_name": row[1],
                "row_estimate": row[2],
                "pretty_table_size": row[3],
                "table_size_bytes": row[4],
                "pretty_actual_size": row[5],
                "actual_size_bytes": row[6],
                "bloat_percentage": row[7],
                "timestamp": time.time()
            })
        
        return table_bloat
    except Exception as e:
        logger.error(f"Error getting table bloat statistics: {e}")
        return None

def get_database_stats() -> Dict[str, Any]:
    """
    Get comprehensive database statistics.

    Returns:
        Dict[str, Any]: A dictionary with database statistics.
    """
    stats = {
        "timestamp": time.time(),
        "pool_stats": get_pool_stats()
    }

    with get_db_connection() as conn:
        if conn:
            # Get database size
            db_size = get_database_size(conn)
            if db_size:
                stats["database_size"] = db_size
            
            # Get table sizes
            table_sizes = get_table_sizes(conn)
            if table_sizes:
                stats["table_sizes"] = table_sizes
            
            # Get table row counts
            table_row_counts = get_table_row_counts(conn)
            if table_row_counts:
                stats["table_row_counts"] = table_row_counts
            
            # Get index usage statistics
            index_usage_stats = get_index_usage_stats(conn)
            if index_usage_stats:
                stats["index_usage_stats"] = index_usage_stats
            
            # Get table bloat statistics
            table_bloat = get_table_bloat(conn)
            if table_bloat:
                stats["table_bloat"] = table_bloat
        else:
            stats["error"] = "No database connection available"

    return stats

"""
Database initialization module.

This module provides functions for initializing the database, including
creating tables, indexes, and constraints.
"""

import logging
import time
from typing import Optional, List, Dict, Any, Tuple
import psycopg2
import psycopg2.extensions

from config import Config
from .connection import get_db_connection_with_retries
from .utils import execute_query, table_exists, column_exists

# Configure logging
logger = logging.getLogger(__name__)

def init_database(
    max_retries: int = 5,
    retry_interval: int = 2
) -> bool:
    """
    Initialize the database.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    logger.info("Initializing database...")

    # Get a database connection with retries
    with get_db_connection_with_retries(max_retries, retry_interval) as conn:
        if not conn:
            logger.error("Failed to get database connection for initialization")
            return False

        try:
            # Check if required tables exist
            required_tables = ["users", "accounts", "hardware", "cards"]
            missing_tables = []

            for table in required_tables:
                if not table_exists(conn, table):
                    missing_tables.append(table)

            if missing_tables:
                logger.warning(f"Missing required tables: {', '.join(missing_tables)}")
                return False

            # Check if RLS is enabled
            rls_enabled = check_rls_enabled(conn)
            if not rls_enabled:
                logger.warning("Row-Level Security is not enabled")
                return False

            logger.info("Database initialization successful")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

def check_rls_enabled(conn: psycopg2.extensions.connection) -> bool:
    """
    Check if Row-Level Security is enabled.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        bool: True if RLS is enabled, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Check if RLS is enabled for required tables
        required_tables = ["accounts", "hardware", "cards"]
        tables_without_rls = []

        for table in required_tables:
            query = """
                SELECT relrowsecurity
                FROM pg_class
                WHERE relname = %s
                AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            """

            result = execute_query(conn, query, (table,), 'one')
            if not result or not result[0]:
                tables_without_rls.append(table)

        if tables_without_rls:
            logger.warning(f"RLS not enabled for tables: {', '.join(tables_without_rls)}")
            return False

        # Check if owner_id column exists in required tables
        tables_without_owner_id = []

        for table in required_tables:
            if not column_exists(conn, table, "owner_id"):
                tables_without_owner_id.append(table)

        if tables_without_owner_id:
            logger.warning(f"owner_id column missing in tables: {', '.join(tables_without_owner_id)}")
            return False

        # Check if RLS policies exist
        tables_without_policies = []

        for table in required_tables:
            query = """
                SELECT COUNT(*)
                FROM pg_policy
                WHERE polrelid = %s::regclass
            """

            result = execute_query(conn, query, (f"public.{table}",), 'one')
            if not result or result[0] < 1:
                tables_without_policies.append(table)

        if tables_without_policies:
            logger.warning(f"RLS policies missing for tables: {', '.join(tables_without_policies)}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error checking RLS: {e}")
        return False

def init_database_with_retries(
    max_retries: int = 5,
    retry_interval: int = 2
) -> bool:
    """
    Initialize the database with retries.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    for i in range(max_retries):
        logger.info(f"Initializing database (attempt {i+1}/{max_retries})...")

        if init_database(max_retries, retry_interval):
            return True

        if i < max_retries - 1:
            logger.info(f"Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)

    logger.error("Failed to initialize database after multiple attempts")
    return False

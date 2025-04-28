"""
Database migrations module.

This module provides functions for managing database migrations, including
running migrations and tracking migration history.
"""

import logging
import os
import time
from typing import Optional, List, Dict, Any, Tuple
import psycopg2
import psycopg2.extensions

from config import Config
from .connection import get_db_connection_with_retries
from .utils import execute_query, execute_query_with_transaction, table_exists

# Configure logging
logger = logging.getLogger(__name__)

def create_migrations_table(conn: psycopg2.extensions.connection) -> bool:
    """
    Create the migrations table if it doesn't exist.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        bool: True if the table was created or already exists, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Check if the migrations table exists
        if table_exists(conn, "migrations"):
            logger.debug("Migrations table already exists")
            return True

        # Create the migrations table
        query = """
            CREATE TABLE migrations (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            )
        """

        execute_query_with_transaction(conn, query)
        logger.info("Migrations table created")
        return True
    except Exception as e:
        logger.error(f"Error creating migrations table: {e}")
        return False

def get_applied_migrations(conn: psycopg2.extensions.connection) -> Optional[List[str]]:
    """
    Get the list of applied migrations.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[List[str]]: A list of applied migration names or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Check if the migrations table exists
        if not table_exists(conn, "migrations"):
            logger.debug("Migrations table doesn't exist")
            return []

        # Get the list of applied migrations
        query = """
            SELECT name
            FROM migrations
            ORDER BY id
        """

        results = execute_query(conn, query, fetch='all')
        if not results:
            return []

        return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Error getting applied migrations: {e}")
        return None

def record_migration(conn: psycopg2.extensions.connection, name: str) -> bool:
    """
    Record a migration as applied.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        name (str): The name of the migration.

    Returns:
        bool: True if the migration was recorded, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Insert the migration record
        query = """
            INSERT INTO migrations (name)
            VALUES (%s)
        """

        execute_query_with_transaction(conn, query, (name,))
        logger.info(f"Migration recorded: {name}")
        return True
    except Exception as e:
        logger.error(f"Error recording migration: {e}")
        return False

def run_migration_file(conn: psycopg2.extensions.connection, file_path: str) -> bool:
    """
    Run a migration file.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        file_path (str): The path to the migration file.

    Returns:
        bool: True if the migration was successful, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Read the migration file
        with open(file_path, 'r') as f:
            sql = f.read()

        # Execute the migration
        execute_query_with_transaction(conn, sql)
        logger.info(f"Migration executed: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        logger.error(f"Error running migration {file_path}: {e}")
        return False

def run_migrations(
    migrations_dir: str = None,
    max_retries: int = 5,
    retry_interval: int = 2
) -> bool:
    """
    Run all pending migrations.

    Args:
        migrations_dir (str, optional): The directory containing migration files. Defaults to None.
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if all migrations were successful, False otherwise.
    """
    logger.info("Running migrations...")

    # Get the migrations directory
    if not migrations_dir:
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")

    # Check if the migrations directory exists
    if not os.path.exists(migrations_dir):
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return False

    # Get a database connection with retries
    with get_db_connection_with_retries(max_retries, retry_interval) as conn:
        if not conn:
            logger.error("Failed to get database connection for migrations")
            return False

        try:
            # Create the migrations table if it doesn't exist
            if not create_migrations_table(conn):
                logger.error("Failed to create migrations table")
                return False

            # Get the list of applied migrations
            applied_migrations = get_applied_migrations(conn)
            if applied_migrations is None:
                logger.error("Failed to get applied migrations")
                return False

            # Get the list of migration files
            migration_files = []
            for file_name in os.listdir(migrations_dir):
                if file_name.endswith('.sql'):
                    migration_files.append(file_name)

            # Sort migration files by name
            migration_files.sort()

            # Run pending migrations
            for file_name in migration_files:
                if file_name not in applied_migrations:
                    file_path = os.path.join(migrations_dir, file_name)
                    logger.info(f"Running migration: {file_name}")

                    if run_migration_file(conn, file_path):
                        if not record_migration(conn, file_name):
                            logger.error(f"Failed to record migration: {file_name}")
                            return False
                    else:
                        logger.error(f"Failed to run migration: {file_name}")
                        return False

            logger.info("Migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            return False

def run_migrations_with_retries(
    migrations_dir: str = None,
    max_retries: int = 5,
    retry_interval: int = 2
) -> bool:
    """
    Run all pending migrations with retries.

    Args:
        migrations_dir (str, optional): The directory containing migration files. Defaults to None.
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if all migrations were successful, False otherwise.
    """
    for i in range(max_retries):
        logger.info(f"Running migrations (attempt {i+1}/{max_retries})...")

        if run_migrations(migrations_dir, max_retries, retry_interval):
            return True

        if i < max_retries - 1:
            logger.info(f"Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)

    logger.error("Failed to run migrations after multiple attempts")
    return False

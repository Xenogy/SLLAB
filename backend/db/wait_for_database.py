"""
Wait for database module.

This module provides functions for waiting for the database to be available.
"""

import logging
import time
import psycopg2
from typing import Optional, Dict, Any
from contextlib import contextmanager

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

def wait_for_database(
    max_retries: int = 30,
    retry_interval: int = 2
) -> bool:
    """
    Wait for the database to be available.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to 30.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if the database is available, False otherwise.
    """
    logger.info(f"Waiting for database to be available (max {max_retries} attempts, {retry_interval}s interval)...")
    
    for i in range(max_retries):
        try:
            # Try to connect to the database
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                connect_timeout=5
            )
            
            # Check if connection is valid
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            logger.info(f"Database is available after {i+1} attempts")
            return True
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(f"Database not available (attempt {i+1}/{max_retries}): {e}")
                time.sleep(retry_interval)
            else:
                logger.error(f"Database not available after {max_retries} attempts: {e}")
                return False
    
    return False

def initialize_connection_pool():
    """
    Initialize the connection pool after waiting for the database.
    
    This function should be called during application startup to ensure
    the connection pool is created after the database is available.
    """
    from .connection import recreate_connection_pool
    
    # Wait for the database to be available
    if wait_for_database():
        # Create the connection pool
        pool = recreate_connection_pool()
        if pool:
            logger.info("Connection pool initialized successfully")
            return True
        else:
            logger.error("Failed to initialize connection pool")
            return False
    else:
        logger.error("Failed to wait for database")
        return False

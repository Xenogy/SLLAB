#!/usr/bin/env python3
"""
Script to run the performance indexes migration.

This script runs the migration to add performance indexes to the database.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import from the backend package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the performance indexes migration."""
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "db",
        "migrations",
        "004_performance_indexes.sql"
    )

    if not os.path.exists(migration_file):
        logger.error(f"Migration file not found: {migration_file}")
        return False

    # Read the migration file
    with open(migration_file, "r") as f:
        migration_sql = f.read()

    # Run the migration
    with get_db_connection() as conn:
        if not conn:
            logger.error("Failed to get database connection")
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(migration_sql)
            conn.commit()
            cursor.close()
            logger.info("Performance indexes migration completed successfully")
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error running performance indexes migration: {e}")
            return False

if __name__ == "__main__":
    logger.info("Running performance indexes migration...")
    success = run_migration()
    if success:
        logger.info("Performance indexes migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Performance indexes migration failed")
        sys.exit(1)

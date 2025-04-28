"""
Script to run database improvements during application startup.

This script is designed to be imported and run during application startup.
It checks if the database needs improvements and applies them if necessary.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from db.migration_manager import get_migration_status, upgrade_to_latest
from db.add_indexes import add_all_indexes
from db.standardize_rls_policies import standardize_all_policies
from db.check_database import check_database

# Configure logging
logger = logging.getLogger(__name__)

def should_run_improvements() -> bool:
    """
    Check if database improvements should be run.
    
    Returns:
        bool: True if improvements should be run, False otherwise
    """
    # Check environment variable
    env_var = os.environ.get("AUTO_IMPROVE_DATABASE", "false").lower()
    return env_var in ("true", "1", "yes", "y")

def run_startup_improvements() -> Dict[str, Any]:
    """
    Run database improvements during application startup.
    
    Returns:
        Dict[str, Any]: A dictionary with results
    """
    if not should_run_improvements():
        logger.info("Automatic database improvements are disabled")
        return {"skipped": True}
    
    logger.info("Running database improvements during startup...")
    
    # Check database status
    status = check_database()
    
    # If we can't connect to the database, we can't do any improvements
    if not status.get("connection", {}).get("connected", False):
        logger.error("Cannot connect to database, skipping improvements")
        return {"error": "Cannot connect to database"}
    
    results = {}
    
    # Check if migrations need to be run
    migration_status = status.get("migrations", {})
    if not migration_status.get("is_up_to_date", False):
        logger.info("Database needs migration, upgrading...")
        migration_success, migration_message = upgrade_to_latest()
        results["migrations"] = {
            "success": migration_success,
            "message": migration_message
        }
    else:
        logger.info("Database is up to date, skipping migrations")
        results["migrations"] = {"skipped": True}
    
    # Check if indexes need to be added
    index_status = status.get("indexes", {})
    tables_with_missing_indexes = [table for table, status in index_status.items() if not status.get("has_all_indexes", False)]
    
    if tables_with_missing_indexes:
        logger.info(f"Database has {len(tables_with_missing_indexes)} tables with missing indexes, adding...")
        index_results = add_all_indexes()
        results["indexes"] = index_results
    else:
        logger.info("Database has all required indexes, skipping")
        results["indexes"] = {"skipped": True}
    
    # Check if RLS policies need to be standardized
    rls_status = status.get("rls", {})
    tables_with_missing_policies = [table for table, status in rls_status.items() if not status.get("has_all_policies", False)]
    
    if tables_with_missing_policies:
        logger.info(f"Database has {len(tables_with_missing_policies)} tables with missing RLS policies, standardizing...")
        rls_results = standardize_all_policies()
        results["rls"] = rls_results
    else:
        logger.info("Database has all required RLS policies, skipping")
        results["rls"] = {"skipped": True}
    
    logger.info("Database improvements completed")
    return results

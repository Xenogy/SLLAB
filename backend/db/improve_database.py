"""
Script to improve database performance and security.

This script runs all the database improvements in one go:
1. Upgrades the database to the latest migration
2. Adds indexes to improve performance
3. Standardizes RLS policies
"""

import logging
import argparse
from typing import Dict, Any, List, Optional
from db.migration_manager import upgrade_to_latest, get_migration_status
from db.add_indexes import add_all_indexes
from db.standardize_rls_policies import standardize_all_policies

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def improve_database(skip_migrations: bool = False, skip_indexes: bool = False, skip_rls: bool = False) -> Dict[str, Any]:
    """
    Improve database performance and security.
    
    Args:
        skip_migrations (bool, optional): Whether to skip migrations. Defaults to False.
        skip_indexes (bool, optional): Whether to skip adding indexes. Defaults to False.
        skip_rls (bool, optional): Whether to skip standardizing RLS policies. Defaults to False.
        
    Returns:
        Dict[str, Any]: A dictionary with results
    """
    results = {}
    
    # Upgrade the database to the latest migration
    if not skip_migrations:
        logger.info("Upgrading database to latest migration...")
        migration_success, migration_message = upgrade_to_latest()
        results["migrations"] = {
            "success": migration_success,
            "message": migration_message
        }
        
        if migration_success:
            logger.info("Database upgraded successfully")
        else:
            logger.error(f"Error upgrading database: {migration_message}")
    else:
        logger.info("Skipping migrations")
    
    # Add indexes to improve performance
    if not skip_indexes:
        logger.info("Adding indexes to improve performance...")
        index_results = add_all_indexes()
        results["indexes"] = index_results
        
        # Count total indexes added
        total_added = sum(stats["added"] for stats in index_results.values())
        total_skipped = sum(stats["skipped"] for stats in index_results.values())
        total_failed = sum(stats["failed"] for stats in index_results.values())
        
        logger.info(f"Added {total_added} indexes, skipped {total_skipped}, failed {total_failed}")
    else:
        logger.info("Skipping indexes")
    
    # Standardize RLS policies
    if not skip_rls:
        logger.info("Standardizing RLS policies...")
        rls_results = standardize_all_policies()
        results["rls"] = rls_results
        
        # Count successful and failed tables
        successful_tables = sum(1 for success in rls_results.values() if success)
        failed_tables = sum(1 for success in rls_results.values() if not success)
        
        logger.info(f"Standardized RLS policies for {successful_tables} tables, failed for {failed_tables} tables")
    else:
        logger.info("Skipping RLS policies")
    
    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Improve database performance and security.')
    parser.add_argument('--skip-migrations', action='store_true', help='Skip database migrations')
    parser.add_argument('--skip-indexes', action='store_true', help='Skip adding indexes')
    parser.add_argument('--skip-rls', action='store_true', help='Skip standardizing RLS policies')
    args = parser.parse_args()
    
    # Check migration status
    migration_status = get_migration_status()
    if not args.skip_migrations and migration_status.get("is_up_to_date", False):
        logger.info("Database is already up to date, skipping migrations")
        args.skip_migrations = True
    
    # Improve database
    results = improve_database(
        skip_migrations=args.skip_migrations,
        skip_indexes=args.skip_indexes,
        skip_rls=args.skip_rls
    )
    
    # Print summary
    logger.info("Database improvement summary:")
    
    if "migrations" in results:
        migration_result = results["migrations"]
        logger.info(f"  Migrations: {'Success' if migration_result['success'] else 'Failed'}")
        if not migration_result['success']:
            logger.info(f"    Error: {migration_result['message']}")
    
    if "indexes" in results:
        index_results = results["indexes"]
        total_added = sum(stats["added"] for stats in index_results.values())
        total_skipped = sum(stats["skipped"] for stats in index_results.values())
        total_failed = sum(stats["failed"] for stats in index_results.values())
        logger.info(f"  Indexes: {total_added} added, {total_skipped} skipped, {total_failed} failed")
    
    if "rls" in results:
        rls_results = results["rls"]
        successful_tables = sum(1 for success in rls_results.values() if success)
        failed_tables = sum(1 for success in rls_results.values() if not success)
        logger.info(f"  RLS Policies: {successful_tables} tables successful, {failed_tables} tables failed")

if __name__ == "__main__":
    main()

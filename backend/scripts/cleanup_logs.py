"""
Script to clean up old logs based on retention policies.

This script is designed to be run as a scheduled task to clean up old logs
based on the configured retention policies.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.repositories.logs import LogRepository
from utils.log_utils import log_info, log_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'cleanup_logs.log'))
    ]
)
logger = logging.getLogger(__name__)

def cleanup_logs(dry_run: bool = False) -> int:
    """
    Clean up old logs based on retention policies.

    Args:
        dry_run (bool, optional): If True, only show what would be deleted without actually deleting. Defaults to False.

    Returns:
        int: Number of deleted log entries
    """
    try:
        # Create log repository with admin context to bypass RLS
        log_repo = LogRepository(user_id=1, user_role="admin")
        
        # Get retention policies
        policies = log_repo.get_retention_policies()
        
        logger.info(f"Found {len(policies)} retention policies")
        
        # Log the policies
        for policy in policies:
            logger.info(f"Policy: category={policy.get('category_name')}, "
                       f"source={policy.get('source_name')}, "
                       f"level={policy.get('level_name')}, "
                       f"retention_days={policy.get('retention_days')}")
        
        if dry_run:
            logger.info("Dry run mode - no logs will be deleted")
            return 0
        
        # Clean up logs
        deleted_count = log_repo.cleanup_old_logs()
        
        logger.info(f"Deleted {deleted_count} log entries")
        
        # Log the cleanup
        log_info(
            message=f"Cleaned up {deleted_count} old log entries",
            category="system",
            source="cleanup_logs",
            details={"deleted_count": deleted_count},
            async_log=False
        )
        
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        
        # Log the error
        log_error(
            message=f"Error cleaning up logs: {e}",
            category="system",
            source="cleanup_logs",
            exception=e,
            async_log=False
        )
        
        return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Clean up old logs based on retention policies')
    parser.add_argument('--dry-run', action='store_true', help='Only show what would be deleted without actually deleting')
    args = parser.parse_args()
    
    logger.info(f"Starting log cleanup at {datetime.now().isoformat()}")
    
    deleted_count = cleanup_logs(args.dry_run)
    
    logger.info(f"Log cleanup completed at {datetime.now().isoformat()}")
    logger.info(f"Deleted {deleted_count} log entries")

if __name__ == '__main__':
    main()

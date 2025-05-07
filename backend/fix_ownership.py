"""
Fix ownership for existing accounts.

This module provides functions for fixing ownership for existing accounts.
"""

import logging
from typing import Dict, Any, Optional, List

from db import get_db_connection_with_retries

# Configure logging
logger = logging.getLogger(__name__)

def fix_ownership(max_retries: int = 5, retry_interval: int = 2) -> bool:
    """
    Fix ownership for existing accounts.

    This function assigns ownership to existing accounts that don't have an owner.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if ownership was fixed successfully, False otherwise
    """
    try:
        # Get a database connection with retries
        with get_db_connection_with_retries(max_retries=max_retries, retry_interval=retry_interval) as conn:
            cursor = conn.cursor()

            # Find accounts without an owner
            cursor.execute("""
                SELECT acc_id
                FROM accounts
                WHERE owner_id IS NULL
            """)

            accounts = cursor.fetchall()

            if not accounts:
                logger.info("No accounts without an owner found")
                return True

            logger.info(f"Found {len(accounts)} accounts without an owner")

            # Get admin user ID
            cursor.execute("""
                SELECT id
                FROM users
                WHERE role = 'admin'
                LIMIT 1
            """)

            admin = cursor.fetchone()

            if not admin:
                logger.warning("No admin user found")
                return False

            admin_id = admin[0]

            # Assign ownership to admin
            for account in accounts:
                acc_id = account[0]
                cursor.execute("""
                    UPDATE accounts
                    SET owner_id = %s
                    WHERE acc_id = %s
                """, (admin_id, acc_id))

            # Commit the changes
            conn.commit()

            logger.info(f"Fixed ownership for {len(accounts)} accounts")

            return True
    except Exception as e:
        logger.error(f"Error fixing ownership: {e}", exc_info=True)
        return False

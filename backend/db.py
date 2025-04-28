"""
Database module for the AccountDB application.

This module provides functions for managing database connections, including
connection pooling, connection creation, and connection closing.

IMPORTANT: This module is deprecated and will be removed in a future version.
Use the new db.connection and db.user_connection modules instead.
"""

import logging
import warnings
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Import the new connection management modules
from .db.connection import (
    get_connection, return_connection, get_db_connection,
    get_connection_with_retries, get_db_connection_with_retries,
    get_pool_stats, close_all_connections
)

from .db.user_connection import (
    get_user_db_connection, get_user_db_connection_with_retries,
    get_user_connection_info
)

# Show deprecation warning
warnings.warn(
    "The db module is deprecated and will be removed in a future version. "
    "Use the new db.connection and db.user_connection modules instead.",
    DeprecationWarning,
    stacklevel=2
)

# Legacy global connection for backward compatibility
# This should be replaced with the context managers in all routers
conn = get_connection()

# Log a warning about the global connection
logger.warning(
    "Using the global database connection is deprecated and will be removed in a future version. "
    "Use the get_db_connection() or get_user_db_connection() context managers instead."
)

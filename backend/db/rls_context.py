"""
Centralized module for RLS context setting.

This module provides functions and context managers for setting and managing
Row-Level Security (RLS) context in PostgreSQL.

It includes enhanced security features such as:
- Parameterized queries to prevent SQL injection
- Comprehensive validation of user input
- Detailed logging for security auditing
- Context managers for safe RLS context handling
"""

import logging
import time
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator, Union, List, Tuple
import psycopg2
import psycopg2.extensions

# Configure logging
logger = logging.getLogger(__name__)

# Thread-local storage for RLS context
_local = threading.local()

# Constants
DEFAULT_RLS_TIMEOUT = 300  # 5 minutes in seconds

def set_rls_context(cursor, user_id: Union[int, str], user_role: str) -> bool:
    """
    Set RLS context in the database.

    This function sets the app.current_user_id and app.current_user_role session variables
    in the database, which are used by RLS policies to filter rows.

    Args:
        cursor: Database cursor
        user_id (Union[int, str]): User ID (must be a valid integer or string representation of an integer)
        user_role (str): User role (must be 'admin' or 'user')

    Returns:
        bool: True if the context was set successfully, False otherwise
    """
    # Validate inputs
    if cursor is None:
        logger.error("Cannot set RLS context: cursor is None")
        return False

    # Validate user_id
    try:
        # Convert to string to ensure it's a valid representation
        user_id_str = str(user_id)
        # Try to convert to int to validate it's a number
        int(user_id_str)
    except (ValueError, TypeError):
        logger.error(f"Invalid user_id for RLS context: {user_id}")
        return False

    # Validate user_role
    if not isinstance(user_role, str) or user_role not in ['admin', 'user']:
        logger.error(f"Invalid user_role for RLS context: {user_role}")
        return False

    try:
        # Store the context in thread-local storage
        _local.current_user_id = user_id_str
        _local.current_user_role = user_role
        _local.context_set_time = time.time()

        # Set the session variables for RLS using parameterized queries
        cursor.execute("SET app.current_user_id = %s", (user_id_str,))
        cursor.execute("SET app.current_user_role = %s", (user_role,))

        # Verify the session variables were set correctly
        cursor.execute("SELECT current_setting('app.current_user_id', TRUE), current_setting('app.current_user_role', TRUE)")
        result = cursor.fetchone()

        if result and result[0] == user_id_str and result[1] == user_role:
            # Single log message at debug level for normal operation
            logger.debug(f"RLS context set: user_id={result[0]}, role={result[1]}")

            # Only log at INFO level for security audit if it's not the system user (admin)
            if user_id != 1 or user_role != 'admin':
                logger.info(f"RLS context set for user_id={user_id_str}, role={user_role}")

            return True
        else:
            logger.warning(f"RLS context verification failed: expected user_id={user_id_str}, role={user_role}, got {result}")
            return False
    except Exception as e:
        logger.error(f"Error setting RLS context: {e}")
        return False

def clear_rls_context(cursor) -> bool:
    """
    Clear RLS context in the database.

    This function resets the app.current_user_id and app.current_user_role session variables
    in the database, which effectively disables RLS filtering.

    Args:
        cursor: Database cursor

    Returns:
        bool: True if the context was cleared successfully, False otherwise
    """
    # Validate inputs
    if cursor is None:
        logger.error("Cannot clear RLS context: cursor is None")
        return False

    try:
        # Get the current context for logging
        previous_user_id = getattr(_local, 'current_user_id', None)
        previous_user_role = getattr(_local, 'current_user_role', None)

        # Clear the context from thread-local storage
        if hasattr(_local, 'current_user_id'):
            delattr(_local, 'current_user_id')
        if hasattr(_local, 'current_user_role'):
            delattr(_local, 'current_user_role')
        if hasattr(_local, 'context_set_time'):
            delattr(_local, 'context_set_time')

        # Reset the session variables for RLS
        cursor.execute("RESET app.current_user_id")
        cursor.execute("RESET app.current_user_role")

        # Verify the session variables were reset
        cursor.execute("SELECT current_setting('app.current_user_id', TRUE), current_setting('app.current_user_role', TRUE)")
        result = cursor.fetchone()

        if result and (result[0] is None or result[0] == '') and (result[1] is None or result[1] == ''):
            logger.debug("RLS context cleared")

            # Log for security audit
            if previous_user_id and previous_user_role:
                logger.debug(f"RLS context cleared for previous user_id={previous_user_id}, role={previous_user_role}")
            else:
                logger.debug("RLS context cleared (no previous context)")

            return True
        else:
            logger.warning(f"RLS context clearing verification failed: {result}")
            return False
    except Exception as e:
        logger.error(f"Error clearing RLS context: {e}")
        return False

@contextmanager
def rls_context(conn, user_id: Union[int, str], user_role: str, timeout: int = DEFAULT_RLS_TIMEOUT) -> Generator[Optional[Dict[str, Any]], None, None]:
    """
    Context manager for RLS context.

    This context manager sets the RLS context for the duration of the context,
    and automatically clears it when the context exits. It also enforces a timeout
    to prevent long-running operations from keeping the context active for too long.

    Args:
        conn: Database connection
        user_id (Union[int, str]): User ID
        user_role (str): User role
        timeout (int, optional): Maximum time in seconds to keep the context active. Defaults to DEFAULT_RLS_TIMEOUT.

    Yields:
        Generator[Optional[Dict[str, Any]], None, None]: A dictionary with context information or None if not available

    Example:
        ```python
        with rls_context(conn, user_id=1, user_role='admin') as ctx:
            if ctx:
                # RLS context is set, perform operations
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM accounts")
                # ...
            else:
                # Failed to set RLS context
                logger.error("Failed to set RLS context")
        # RLS context is automatically cleared when the context exits
        ```
    """
    cursor = None
    context_info = None

    try:
        # Validate inputs
        if conn is None:
            logger.error("Cannot set RLS context: connection is None")
            yield None
            return

        # Create cursor
        cursor = conn.cursor()

        # Set RLS context
        success = set_rls_context(cursor, user_id, user_role)

        if success:
            # Create context information
            context_info = {
                "success": True,
                "user_id": user_id,
                "user_role": user_role,
                "start_time": time.time(),
                "timeout": timeout
            }

            # Check if the context has expired during yield
            if hasattr(_local, 'context_set_time') and (time.time() - _local.context_set_time) > timeout:
                logger.warning(f"RLS context timeout exceeded ({timeout}s), clearing context")
                clear_rls_context(cursor)
                yield None
                return

            # Yield context information
            yield context_info
        else:
            logger.warning(f"Failed to set RLS context for user_id={user_id}, role={user_role}")
            yield None
    except Exception as e:
        logger.error(f"Error in RLS context: {e}")
        yield None
    finally:
        # Always clear the context and close the cursor
        if cursor:
            # Check if the context has expired
            if context_info and (time.time() - context_info["start_time"]) > timeout:
                logger.warning(f"RLS context timeout exceeded ({timeout}s) during operation")

            # Clear the context
            clear_rls_context(cursor)
            cursor.close()

def get_current_rls_context() -> Optional[Dict[str, Any]]:
    """
    Get the current RLS context from thread-local storage.

    This function returns the current RLS context if it exists and has not expired.

    Returns:
        Optional[Dict[str, Any]]: A dictionary with the current RLS context or None if not available
    """
    if not hasattr(_local, 'current_user_id') or not hasattr(_local, 'current_user_role'):
        return None

    # Check if the context has expired
    if hasattr(_local, 'context_set_time'):
        elapsed = time.time() - _local.context_set_time
        if elapsed > DEFAULT_RLS_TIMEOUT:
            logger.warning(f"RLS context has expired ({elapsed:.2f}s > {DEFAULT_RLS_TIMEOUT}s)")
            return None

    return {
        "user_id": _local.current_user_id,
        "user_role": _local.current_user_role,
        "set_time": getattr(_local, 'context_set_time', None),
        "elapsed": time.time() - getattr(_local, 'context_set_time', time.time())
    }

def is_rls_context_set() -> bool:
    """
    Check if the RLS context is set in thread-local storage.

    Returns:
        bool: True if the RLS context is set and has not expired, False otherwise
    """
    return get_current_rls_context() is not None

def get_user_tables_with_rls() -> List[Dict[str, str]]:
    """
    Get a list of tables with RLS views.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with table and view names.
    """
    return [
        {"table": "accounts", "view": "accounts_with_rls"},
        {"table": "hardware", "view": "hardware_with_rls"},
        {"table": "cards", "view": "cards_with_rls"},
        {"table": "hardware_profiles", "view": "hardware_profiles_with_rls"},
        {"table": "vms", "view": "vms_with_rls"},
        {"table": "proxmox_nodes", "view": "proxmox_nodes_with_rls"}
    ]

def verify_rls_setup(conn) -> Dict[str, Any]:
    """
    Verify that RLS is set up correctly.

    This function checks if RLS is properly set up in the database by verifying:
    - If tables exist and have RLS enabled
    - If owner_id columns exist
    - If RLS policies exist
    - If RLS views exist
    - If app schema exists
    - If set_rls_context function exists

    Args:
        conn: Database connection

    Returns:
        Dict[str, Any]: A dictionary with verification results
    """
    results = {
        "success": True,
        "tables": {},
        "views": {},
        "policies": {},
        "timestamp": time.time()
    }

    if not conn:
        logger.warning("No database connection available")
        results["success"] = False
        return results

    cursor = conn.cursor()
    try:
        # Check if tables exist and have RLS enabled
        tables = ["accounts", "hardware", "cards", "vms", "proxmox_nodes"]
        for table in tables:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """, (table,))
            table_exists = cursor.fetchone()[0]
            results["tables"][table] = {"exists": table_exists}

            if table_exists:
                # Check if RLS is enabled
                cursor.execute("""
                    SELECT relrowsecurity, relforcerowsecurity
                    FROM pg_class
                    WHERE relname = %s AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
                """, (table,))
                rls_result = cursor.fetchone()
                if rls_result:
                    results["tables"][table]["rls_enabled"] = rls_result[0]
                    results["tables"][table]["rls_forced"] = rls_result[1]
                else:
                    results["tables"][table]["rls_enabled"] = False
                    results["tables"][table]["rls_forced"] = False

                # Check if owner_id column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = %s
                        AND column_name = 'owner_id'
                    );
                """, (table,))
                owner_id_exists = cursor.fetchone()[0]
                results["tables"][table]["owner_id_exists"] = owner_id_exists

                # Check if RLS policies exist
                cursor.execute("""
                    SELECT polname, polcmd, polpermissive
                    FROM pg_policy
                    WHERE polrelid = %s::regclass;
                """, (table,))
                policies = cursor.fetchall()
                results["policies"][table] = {
                    "count": len(policies),
                    "policies": [
                        {
                            "name": policy[0],
                            "command": policy[1],
                            "permissive": policy[2]
                        }
                        for policy in policies
                    ]
                }

                # Check if RLS view exists
                view_name = f"{table}_with_rls"
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.views
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    );
                """, (view_name,))
                view_exists = cursor.fetchone()[0]
                results["views"][table] = {"exists": view_exists}

        # Check if app schema exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.schemata
                WHERE schema_name = 'app'
            );
        """)
        app_schema_exists = cursor.fetchone()[0]
        results["app_schema_exists"] = app_schema_exists

        # Check if set_rls_context function exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc
                WHERE proname = 'set_rls_context'
            );
        """)
        set_rls_context_exists = cursor.fetchone()[0]
        results["set_rls_context_exists"] = set_rls_context_exists

        return results
    except Exception as e:
        logger.error(f"Error verifying RLS setup: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results
    finally:
        cursor.close()

def test_rls_policies(conn, user_id: Union[int, str], user_role: str) -> Dict[str, Any]:
    """
    Test RLS policies for a specific user.

    This function tests if RLS policies are working correctly by:
    1. Setting the RLS context for the specified user
    2. Querying each table to see what rows are visible
    3. Comparing the results with the expected behavior

    Args:
        conn: Database connection
        user_id (Union[int, str]): User ID to test
        user_role (str): User role to test

    Returns:
        Dict[str, Any]: A dictionary with test results
    """
    results = {
        "success": True,
        "tables": {},
        "timestamp": time.time(),
        "user_id": user_id,
        "user_role": user_role
    }

    if not conn:
        logger.warning("No database connection available")
        results["success"] = False
        return results

    cursor = None
    try:
        cursor = conn.cursor()

        # Set RLS context
        success = set_rls_context(cursor, user_id, user_role)
        if not success:
            logger.warning(f"Failed to set RLS context for user_id={user_id}, role={user_role}")
            results["success"] = False
            results["error"] = "Failed to set RLS context"
            return results

        # Test each table
        tables = get_user_tables_with_rls()
        for table_info in tables:
            table = table_info["table"]
            view = table_info["view"]

            # Test direct table access
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                table_count = cursor.fetchone()[0]

                # Test view access
                cursor.execute(f"SELECT COUNT(*) FROM {view}")
                view_count = cursor.fetchone()[0]

                # Get owner_id counts
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE owner_id = %s", (user_id,))
                owned_count = cursor.fetchone()[0]

                # Store results
                results["tables"][table] = {
                    "table_count": table_count,
                    "view_count": view_count,
                    "owned_count": owned_count,
                    "rls_working": (user_role == 'admin' and table_count == view_count) or
                                  (user_role != 'admin' and view_count == owned_count)
                }
            except Exception as e:
                logger.error(f"Error testing RLS for table {table}: {e}")
                results["tables"][table] = {
                    "error": str(e)
                }
                results["success"] = False

        return results
    except Exception as e:
        logger.error(f"Error testing RLS policies: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results
    finally:
        if cursor:
            clear_rls_context(cursor)
            cursor.close()

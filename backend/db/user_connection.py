"""
User-specific database connection management module.

This module provides functions for managing database connections with user context,
including setting and clearing Row-Level Security (RLS) context.
"""

import logging
from typing import Optional, Dict, Any, Generator, Union
from contextlib import contextmanager
import psycopg2
import psycopg2.extensions

from .connection import get_connection, return_connection, get_connection_with_retries
from .rls_context import set_rls_context, clear_rls_context

# Configure logging
logger = logging.getLogger(__name__)

@contextmanager
def get_user_db_connection(
    user_id: Optional[Union[int, str]] = None,
    user_role: Optional[str] = None
) -> Generator[Optional[psycopg2.extensions.connection], None, None]:
    """
    Context manager for database connections with user context.

    Args:
        user_id (Optional[Union[int, str]], optional): The ID of the user. Defaults to None.
        user_role (Optional[str], optional): The role of the user. Defaults to None.

    Yields:
        Generator[Optional[psycopg2.extensions.connection], None, None]: A database connection with RLS context set.
    """
    conn = get_connection()
    try:
        if conn:
            if user_id is not None and user_role is not None:
                # Convert user_id to int if it's a string
                if isinstance(user_id, str):
                    try:
                        user_id = int(user_id)
                    except ValueError:
                        logger.warning(f"Invalid user_id: {user_id}, cannot convert to int")
                        user_id = None

                # Set RLS context
                if user_id is not None:
                    logger.debug(f"Setting RLS context: user_id={user_id}, role={user_role}")
                    cursor = conn.cursor()
                    try:
                        success = set_rls_context(cursor, user_id, user_role)
                        if not success:
                            logger.warning(f"Failed to set RLS context: user_id={user_id}, role={user_role}")
                    finally:
                        cursor.close()
                else:
                    logger.warning("Cannot set RLS context: user_id is None")
            else:
                logger.warning("Missing user_id or user_role for RLS context")
        else:
            logger.warning("No database connection available")

        yield conn
    finally:
        if conn:
            # Clear RLS context
            if user_id is not None and user_role is not None:
                cursor = conn.cursor()
                try:
                    success = clear_rls_context(cursor)
                    if not success:
                        logger.warning(f"Failed to clear RLS context: user_id={user_id}, role={user_role}")
                finally:
                    cursor.close()

            # Return connection to pool
            return_connection(conn)

@contextmanager
def get_user_db_connection_with_retries(
    user_id: Optional[Union[int, str]] = None,
    user_role: Optional[str] = None,
    max_retries: Optional[int] = None,
    retry_interval: Optional[int] = None
) -> Generator[Optional[psycopg2.extensions.connection], None, None]:
    """
    Context manager for database connections with user context and retries.

    Args:
        user_id (Optional[Union[int, str]], optional): The ID of the user. Defaults to None.
        user_role (Optional[str], optional): The role of the user. Defaults to None.
        max_retries (Optional[int], optional): Maximum number of retries. Defaults to None.
        retry_interval (Optional[int], optional): Retry interval in seconds. Defaults to None.

    Yields:
        Generator[Optional[psycopg2.extensions.connection], None, None]: A database connection with RLS context set.
    """
    conn = get_connection_with_retries(max_retries, retry_interval)
    try:
        if conn:
            if user_id is not None and user_role is not None:
                # Convert user_id to int if it's a string
                if isinstance(user_id, str):
                    try:
                        user_id = int(user_id)
                    except ValueError:
                        logger.warning(f"Invalid user_id: {user_id}, cannot convert to int")
                        user_id = None

                # Set RLS context
                if user_id is not None:
                    logger.debug(f"Setting RLS context: user_id={user_id}, role={user_role}")
                    cursor = conn.cursor()
                    try:
                        success = set_rls_context(cursor, user_id, user_role)
                        if not success:
                            logger.warning(f"Failed to set RLS context: user_id={user_id}, role={user_role}")
                    finally:
                        cursor.close()
                else:
                    logger.warning("Cannot set RLS context: user_id is None")
            else:
                logger.warning("Missing user_id or user_role for RLS context")
        else:
            logger.warning("No database connection available after retries")

        yield conn
    finally:
        if conn:
            # Clear RLS context
            if user_id is not None and user_role is not None:
                cursor = conn.cursor()
                try:
                    success = clear_rls_context(cursor)
                    if not success:
                        logger.warning(f"Failed to clear RLS context: user_id={user_id}, role={user_role}")
                finally:
                    cursor.close()

            # Return connection to pool
            return_connection(conn)

def get_user_connection_info(
    conn: psycopg2.extensions.connection,
    user_id: Optional[Union[int, str]] = None,
    user_role: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get information about a user connection.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        user_id (Optional[Union[int, str]], optional): The ID of the user. Defaults to None.
        user_role (Optional[str], optional): The role of the user. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary with connection information.
    """
    info = {
        "connection": bool(conn),
        "user_id": user_id,
        "user_role": user_role,
        "rls_context_set": False,
        "connection_status": None
    }

    if conn:
        # Check if connection is alive
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            info["connection_status"] = "alive"
        except Exception as e:
            info["connection_status"] = f"error: {str(e)}"

        # Check if RLS context is set
        if user_id is not None and user_role is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT current_setting('app.current_user_id', TRUE), current_setting('app.current_user_role', TRUE)")
                result = cursor.fetchone()
                cursor.close()

                if result and result[0] and result[1]:
                    info["rls_context_set"] = True
                    info["current_user_id"] = result[0]
                    info["current_user_role"] = result[1]
            except Exception as e:
                logger.warning(f"Error checking RLS context: {e}")

    return info

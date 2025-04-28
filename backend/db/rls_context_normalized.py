"""
Row-Level Security (RLS) context management for the normalized database schema.

This module provides functions for setting and clearing the RLS context in PostgreSQL.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extensions import connection as pg_connection

# Configure logging
logger = logging.getLogger(__name__)

def get_user_tables_with_rls() -> list:
    """
    Get a list of tables with RLS views.

    Returns:
        list: A list of dictionaries with table and view names.
    """
    return [
        {"table": "accounts_normalized", "view": "accounts_normalized_with_rls"},
        {"table": "hardware_normalized", "view": "hardware_normalized_with_rls"},
        {"table": "cards_normalized", "view": "cards_normalized_with_rls"},
        {"table": "email_accounts", "view": "email_accounts_with_rls"},
        {"table": "vault_accounts", "view": "vault_accounts_with_rls"},
        {"table": "steamguard_data", "view": "steamguard_data_with_rls"},
        # Legacy tables (kept for backward compatibility)
        {"table": "accounts", "view": "accounts_with_rls"},
        {"table": "hardware", "view": "hardware_with_rls"},
        {"table": "cards", "view": "cards_with_rls"},
        {"table": "vms", "view": "vms_with_rls"},
        {"table": "proxmox_nodes", "view": "proxmox_nodes_with_rls"}
    ]

def set_rls_context(conn: pg_connection, user_id: int, user_role: str) -> None:
    """
    Set the RLS context for the current database session.

    Args:
        conn: Database connection
        user_id: User ID to set in the RLS context
        user_role: User role to set in the RLS context
    """
    if not conn:
        logger.warning("No database connection available")
        return

    cursor = conn.cursor()
    try:
        # Set the user ID and role in the RLS context
        cursor.execute(f"SET app.current_user_id = '{user_id}';")
        cursor.execute(f"SET app.current_user_role = '{user_role}';")
        logger.debug(f"RLS context set: user_id={user_id}, user_role={user_role}")
    except Exception as e:
        logger.error(f"Error setting RLS context: {e}")
    finally:
        cursor.close()

def clear_rls_context(conn: pg_connection) -> None:
    """
    Clear the RLS context for the current database session.

    Args:
        conn: Database connection
    """
    if not conn:
        logger.warning("No database connection available")
        return

    cursor = conn.cursor()
    try:
        # Clear the user ID and role from the RLS context
        cursor.execute("RESET app.current_user_id;")
        cursor.execute("RESET app.current_user_role;")
        logger.debug("RLS context cleared")
    except Exception as e:
        logger.error(f"Error clearing RLS context: {e}")
    finally:
        cursor.close()

@contextmanager
def rls_context(conn: pg_connection, user_id: int, user_role: str):
    """
    Context manager for setting and clearing the RLS context.

    Args:
        conn: Database connection
        user_id: User ID to set in the RLS context
        user_role: User role to set in the RLS context
    """
    try:
        set_rls_context(conn, user_id, user_role)
        yield
    finally:
        clear_rls_context(conn)

@contextmanager
def get_user_db_connection(conn_func, user_id: int, user_role: str):
    """
    Context manager for getting a database connection with RLS context.

    Args:
        conn_func: Function to get a database connection
        user_id: User ID to set in the RLS context
        user_role: User role to set in the RLS context
    """
    conn = conn_func()
    try:
        set_rls_context(conn, user_id, user_role)
        yield conn
    finally:
        clear_rls_context(conn)
        if conn:
            conn.close()

def verify_rls_setup(conn: pg_connection) -> Dict[str, Any]:
    """
    Verify that RLS is set up correctly.

    Args:
        conn: Database connection

    Returns:
        Dict[str, Any]: A dictionary with verification results
    """
    results = {
        "success": True,
        "tables": {},
        "views": {},
        "policies": {}
    }

    if not conn:
        logger.warning("No database connection available")
        results["success"] = False
        return results

    cursor = conn.cursor()
    try:
        # Get a list of tables with RLS
        tables = [table["table"] for table in get_user_tables_with_rls()]

        for table in tables:
            # Check if table exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """)
            table_exists = cursor.fetchone()[0]
            results["tables"][table] = {"exists": table_exists}

            if table_exists:
                # Check if RLS is enabled
                cursor.execute(f"""
                    SELECT relrowsecurity
                    FROM pg_class
                    WHERE relname = '{table}' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
                """)
                rls_enabled = cursor.fetchone()[0]
                results["tables"][table]["rls_enabled"] = rls_enabled

                # Check if owner_id column exists
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = '{table}'
                        AND column_name = 'owner_id'
                    );
                """)
                owner_id_exists = cursor.fetchone()[0]
                results["tables"][table]["owner_id_exists"] = owner_id_exists

                # Check if RLS policies exist
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM pg_policy
                    WHERE polrelid = '{table}'::regclass;
                """)
                policy_count = cursor.fetchone()[0]
                results["policies"][table] = {"count": policy_count}

                # Check if RLS view exists
                view_name = f"{table}_with_rls"
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.views
                        WHERE table_schema = 'public'
                        AND table_name = '{view_name}'
                    );
                """)
                view_exists = cursor.fetchone()[0]
                results["views"][table] = {"exists": view_exists}
    except Exception as e:
        logger.error(f"Error verifying RLS setup: {e}")
        results["success"] = False
        results["error"] = str(e)
    finally:
        cursor.close()

    return results

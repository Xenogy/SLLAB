"""
Helper functions for Row-Level Security (RLS).
"""

from contextlib import contextmanager
from .db import get_db_connection

@contextmanager
def rls_context(user_id, user_role):
    """
    Context manager for setting RLS context.
    
    Args:
        user_id (int): The ID of the user.
        user_role (str): The role of the user (admin or user).
        
    Yields:
        connection: A database connection with RLS context set.
    """
    conn = get_db_connection()
    try:
        if conn:
            cursor = conn.cursor()
            try:
                print(f"Setting RLS context: user_id={user_id}, role={user_role}")
                
                # Set the session variables for RLS
                cursor.execute("SET app.current_user_id = %s", (str(user_id),))
                cursor.execute("SET app.current_user_role = %s", (str(user_role),))
                
                # Verify the session variables were set correctly
                cursor.execute("SELECT current_setting('app.current_user_id'), current_setting('app.current_user_role')")
                result = cursor.fetchone()
                if result:
                    print(f"RLS context verified: user_id={result[0]}, role={result[1]}")
                else:
                    print("Warning: Could not verify RLS context")
            except Exception as e:
                print(f"Error setting RLS context: {e}")
            finally:
                cursor.close()
        else:
            print("Warning: No database connection available")
            
        yield conn
    finally:
        if conn:
            conn.close()

def get_user_tables_with_rls():
    """
    Get a list of tables with RLS views.
    
    Returns:
        list: A list of dictionaries with table and view names.
    """
    tables = [
        {"table": "accounts", "view": "accounts_with_rls"},
        {"table": "cards", "view": "cards_with_rls"},
        {"table": "hardware_profiles", "view": "hardware_profiles_with_rls"}
    ]
    
    # Filter out tables that don't exist
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor()
            try:
                existing_tables = []
                for table in tables:
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table["view"]}'
                        );
                    """)
                    exists = cursor.fetchone()[0]
                    if exists:
                        existing_tables.append(table)
                return existing_tables
            except Exception as e:
                print(f"Error getting tables with RLS: {e}")
                return []
            finally:
                cursor.close()
        else:
            print("Warning: No database connection available")
            return []

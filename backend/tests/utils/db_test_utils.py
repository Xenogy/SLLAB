"""
Database utility functions for testing.
"""

import os
import psycopg2
import subprocess
import time
from typing import Dict, Any, List, Optional, Union, Generator
from psycopg2.extensions import connection as PsycopgConnection

from config import Config

def setup_test_database() -> None:
    """
    Set up a test database.
    """
    # Get test database configuration
    test_db_host = os.getenv('TEST_DB_HOST', Config.DB_HOST)
    test_db_port = os.getenv('TEST_DB_PORT', Config.DB_PORT)
    test_db_name = os.getenv('TEST_DB_NAME', 'accountdb_test')
    test_db_user = os.getenv('TEST_DB_USER', Config.DB_USER)
    test_db_pass = os.getenv('TEST_DB_PASS', Config.DB_PASS)
    
    # Connect to the default database
    conn = psycopg2.connect(
        host=test_db_host,
        port=test_db_port,
        dbname="postgres",
        user=test_db_user,
        password=test_db_pass
    )
    conn.autocommit = True
    
    # Create the test database if it doesn't exist
    cursor = conn.cursor()
    try:
        # Check if the test database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{test_db_name}'")
        if cursor.fetchone() is None:
            # Create the test database
            cursor.execute(f"CREATE DATABASE {test_db_name}")
            print(f"Created test database: {test_db_name}")
        else:
            print(f"Test database already exists: {test_db_name}")
    finally:
        cursor.close()
        conn.close()
    
    # Connect to the test database
    conn = psycopg2.connect(
        host=test_db_host,
        port=test_db_port,
        dbname=test_db_name,
        user=test_db_user,
        password=test_db_pass
    )
    conn.autocommit = True
    
    # Initialize the test database
    cursor = conn.cursor()
    try:
        # Check if the users table exists
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'users'
        """)
        
        if cursor.fetchone() is None:
            # Initialize the database schema
            initialize_test_database_schema(conn)
            print("Initialized test database schema")
        else:
            print("Test database schema already initialized")
    finally:
        cursor.close()
        conn.close()

def initialize_test_database_schema(conn: PsycopgConnection) -> None:
    """
    Initialize the test database schema.
    
    Args:
        conn (PsycopgConnection): A database connection
    """
    # Get the SQL initialization scripts
    sql_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sql')
    
    # Execute the SQL scripts
    cursor = conn.cursor()
    try:
        # Execute the initialization scripts
        for script_name in sorted(os.listdir(sql_dir)):
            if script_name.endswith('.sql'):
                script_path = os.path.join(sql_dir, script_name)
                with open(script_path, 'r') as f:
                    sql = f.read()
                    cursor.execute(sql)
                    print(f"Executed SQL script: {script_name}")
    finally:
        cursor.close()

def teardown_test_database() -> None:
    """
    Tear down the test database.
    """
    # Get test database configuration
    test_db_host = os.getenv('TEST_DB_HOST', Config.DB_HOST)
    test_db_port = os.getenv('TEST_DB_PORT', Config.DB_PORT)
    test_db_name = os.getenv('TEST_DB_NAME', 'accountdb_test')
    test_db_user = os.getenv('TEST_DB_USER', Config.DB_USER)
    test_db_pass = os.getenv('TEST_DB_PASS', Config.DB_PASS)
    
    # Connect to the default database
    conn = psycopg2.connect(
        host=test_db_host,
        port=test_db_port,
        dbname="postgres",
        user=test_db_user,
        password=test_db_pass
    )
    conn.autocommit = True
    
    # Drop the test database
    cursor = conn.cursor()
    try:
        # Terminate all connections to the test database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{test_db_name}'
            AND pid <> pg_backend_pid()
        """)
        
        # Drop the test database
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        print(f"Dropped test database: {test_db_name}")
    finally:
        cursor.close()
        conn.close()

def get_test_db_connection() -> PsycopgConnection:
    """
    Get a connection to the test database.
    
    Returns:
        PsycopgConnection: A database connection
    """
    # Get test database configuration
    test_db_host = os.getenv('TEST_DB_HOST', Config.DB_HOST)
    test_db_port = os.getenv('TEST_DB_PORT', Config.DB_PORT)
    test_db_name = os.getenv('TEST_DB_NAME', 'accountdb_test')
    test_db_user = os.getenv('TEST_DB_USER', Config.DB_USER)
    test_db_pass = os.getenv('TEST_DB_PASS', Config.DB_PASS)
    
    # Connect to the test database
    conn = psycopg2.connect(
        host=test_db_host,
        port=test_db_port,
        dbname=test_db_name,
        user=test_db_user,
        password=test_db_pass
    )
    
    return conn

def execute_query(
    conn: PsycopgConnection,
    query: str,
    params: Optional[Union[List[Any], Dict[str, Any], tuple]] = None,
    fetch: Optional[str] = None
) -> Optional[Union[List[tuple], tuple, Any]]:
    """
    Execute a database query.
    
    Args:
        conn (PsycopgConnection): A database connection
        query (str): The query to execute
        params (Optional[Union[List[Any], Dict[str, Any], tuple]], optional): The query parameters. Defaults to None.
        fetch (Optional[str], optional): The fetch mode ('one', 'all', 'many', None). Defaults to None.
        
    Returns:
        Optional[Union[List[tuple], tuple, Any]]: The query results or None if not available
    """
    cursor = conn.cursor()
    try:
        # Execute the query
        cursor.execute(query, params)
        
        # Fetch the results
        if fetch == 'one':
            return cursor.fetchone()
        elif fetch == 'all':
            return cursor.fetchall()
        elif fetch == 'many':
            return cursor.fetchmany()
        else:
            return None
    finally:
        cursor.close()

def count_rows(conn: PsycopgConnection, table: str, where: Optional[str] = None, params: Optional[tuple] = None) -> int:
    """
    Count the number of rows in a table.
    
    Args:
        conn (PsycopgConnection): A database connection
        table (str): The table name
        where (Optional[str], optional): The WHERE clause. Defaults to None.
        params (Optional[tuple], optional): The query parameters. Defaults to None.
        
    Returns:
        int: The number of rows
    """
    # Build the query
    query = f"SELECT COUNT(*) FROM {table}"
    if where:
        query += f" WHERE {where}"
    
    # Execute the query
    result = execute_query(conn, query, params, fetch='one')
    
    # Return the count
    return result[0] if result else 0

def table_exists(conn: PsycopgConnection, table: str) -> bool:
    """
    Check if a table exists.
    
    Args:
        conn (PsycopgConnection): A database connection
        table (str): The table name
        
    Returns:
        bool: Whether the table exists
    """
    # Execute the query
    result = execute_query(
        conn,
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table,),
        fetch='one'
    )
    
    # Return whether the table exists
    return result is not None

def column_exists(conn: PsycopgConnection, table: str, column: str) -> bool:
    """
    Check if a column exists.
    
    Args:
        conn (PsycopgConnection): A database connection
        table (str): The table name
        column (str): The column name
        
    Returns:
        bool: Whether the column exists
    """
    # Execute the query
    result = execute_query(
        conn,
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        """,
        (table, column),
        fetch='one'
    )
    
    # Return whether the column exists
    return result is not None

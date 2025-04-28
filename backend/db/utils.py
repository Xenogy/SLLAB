"""
Database utility functions.

This module provides utility functions for working with databases, including
executing queries, handling transactions, and managing cursors.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple, Union, Generator
from contextlib import contextmanager
import psycopg2
import psycopg2.extensions
from psycopg2 import sql

# Configure logging
logger = logging.getLogger(__name__)

@contextmanager
def get_cursor(
    conn: psycopg2.extensions.connection,
    cursor_factory: Optional[Any] = None
) -> Generator[Optional[psycopg2.extensions.cursor], None, None]:
    """
    Context manager for database cursors.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        cursor_factory (Optional[Any], optional): The cursor factory to use. Defaults to None.

    Yields:
        Generator[Optional[psycopg2.extensions.cursor], None, None]: A database cursor or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        yield None
        return

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=cursor_factory) if cursor_factory else conn.cursor()
        yield cursor
    finally:
        if cursor:
            cursor.close()

@contextmanager
def transaction(
    conn: psycopg2.extensions.connection,
    isolation_level: Optional[int] = None
) -> Generator[Optional[psycopg2.extensions.connection], None, None]:
    """
    Context manager for database transactions.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        isolation_level (Optional[int], optional): The isolation level to use. Defaults to None.

    Yields:
        Generator[Optional[psycopg2.extensions.connection], None, None]: A database connection or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        yield None
        return

    # Save the current isolation level
    old_isolation_level = conn.isolation_level

    try:
        # Set the new isolation level if specified
        if isolation_level is not None:
            conn.set_isolation_level(isolation_level)

        # Start a transaction
        yield conn

        # Commit the transaction
        conn.commit()
    except Exception as e:
        # Rollback the transaction on error
        logger.error(f"Transaction error: {e}")
        conn.rollback()
        raise
    finally:
        # Restore the original isolation level
        if isolation_level is not None:
            conn.set_isolation_level(old_isolation_level)

def execute_query(
    conn: psycopg2.extensions.connection,
    query: Union[str, sql.Composed],
    params: Optional[Union[Tuple, List, Dict]] = None,
    fetch: Optional[str] = None,
    cursor_factory: Optional[Any] = None
) -> Optional[Union[List, Dict, Any]]:
    """
    Execute a database query.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (Union[str, sql.Composed]): The query to execute.
        params (Optional[Union[Tuple, List, Dict]], optional): The query parameters. Defaults to None.
        fetch (Optional[str], optional): The fetch mode ('one', 'all', 'many', None). Defaults to None.
        cursor_factory (Optional[Any], optional): The cursor factory to use. Defaults to None.

    Returns:
        Optional[Union[List, Dict, Any]]: The query results or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    with get_cursor(conn, cursor_factory) as cursor:
        if not cursor:
            return None

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
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

def execute_query_with_transaction(
    conn: psycopg2.extensions.connection,
    query: Union[str, sql.Composed],
    params: Optional[Union[Tuple, List, Dict]] = None,
    fetch: Optional[str] = None,
    cursor_factory: Optional[Any] = None,
    isolation_level: Optional[int] = None
) -> Optional[Union[List, Dict, Any]]:
    """
    Execute a database query within a transaction.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (Union[str, sql.Composed]): The query to execute.
        params (Optional[Union[Tuple, List, Dict]], optional): The query parameters. Defaults to None.
        fetch (Optional[str], optional): The fetch mode ('one', 'all', 'many', None). Defaults to None.
        cursor_factory (Optional[Any], optional): The cursor factory to use. Defaults to None.
        isolation_level (Optional[int], optional): The isolation level to use. Defaults to None.

    Returns:
        Optional[Union[List, Dict, Any]]: The query results or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    with transaction(conn, isolation_level) as tx_conn:
        if not tx_conn:
            return None

        return execute_query(tx_conn, query, params, fetch, cursor_factory)

def execute_batch(
    conn: psycopg2.extensions.connection,
    query: Union[str, sql.Composed],
    params_list: List[Union[Tuple, List, Dict]],
    page_size: int = 100
) -> Optional[int]:
    """
    Execute a batch of database queries.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (Union[str, sql.Composed]): The query to execute.
        params_list (List[Union[Tuple, List, Dict]]): The list of query parameters.
        page_size (int, optional): The number of queries to execute in each batch. Defaults to 100.

    Returns:
        Optional[int]: The number of rows affected or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    with get_cursor(conn) as cursor:
        if not cursor:
            return None

        try:
            # Execute the batch
            from psycopg2.extras import execute_batch
            execute_batch(cursor, query, params_list, page_size)
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Batch execution error: {e}")
            raise

def execute_batch_with_transaction(
    conn: psycopg2.extensions.connection,
    query: Union[str, sql.Composed],
    params_list: List[Union[Tuple, List, Dict]],
    page_size: int = 100,
    isolation_level: Optional[int] = None
) -> Optional[int]:
    """
    Execute a batch of database queries within a transaction.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (Union[str, sql.Composed]): The query to execute.
        params_list (List[Union[Tuple, List, Dict]]): The list of query parameters.
        page_size (int, optional): The number of queries to execute in each batch. Defaults to 100.
        isolation_level (Optional[int], optional): The isolation level to use. Defaults to None.

    Returns:
        Optional[int]: The number of rows affected or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    with transaction(conn, isolation_level) as tx_conn:
        if not tx_conn:
            return None

        return execute_batch(tx_conn, query, params_list, page_size)

def execute_values(
    conn: psycopg2.extensions.connection,
    query: Union[str, sql.Composed],
    values: List[Union[Tuple, List, Dict]],
    template: Optional[str] = None,
    page_size: int = 100,
    fetch: Optional[str] = None
) -> Optional[Union[List, Dict, Any]]:
    """
    Execute a query with multiple values.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (Union[str, sql.Composed]): The query to execute.
        values (List[Union[Tuple, List, Dict]]): The list of values.
        template (Optional[str], optional): The template for the values. Defaults to None.
        page_size (int, optional): The number of values to execute in each batch. Defaults to 100.
        fetch (Optional[str], optional): The fetch mode ('one', 'all', 'many', None). Defaults to None.

    Returns:
        Optional[Union[List, Dict, Any]]: The query results or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    with get_cursor(conn) as cursor:
        if not cursor:
            return None

        try:
            # Execute the values
            from psycopg2.extras import execute_values
            execute_values(cursor, query, values, template, page_size)

            # Fetch the results
            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'many':
                return cursor.fetchmany()
            else:
                return None
        except Exception as e:
            logger.error(f"Values execution error: {e}")
            raise

def execute_values_with_transaction(
    conn: psycopg2.extensions.connection,
    query: Union[str, sql.Composed],
    values: List[Union[Tuple, List, Dict]],
    template: Optional[str] = None,
    page_size: int = 100,
    fetch: Optional[str] = None,
    isolation_level: Optional[int] = None
) -> Optional[Union[List, Dict, Any]]:
    """
    Execute a query with multiple values within a transaction.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        query (Union[str, sql.Composed]): The query to execute.
        values (List[Union[Tuple, List, Dict]]): The list of values.
        template (Optional[str], optional): The template for the values. Defaults to None.
        page_size (int, optional): The number of values to execute in each batch. Defaults to 100.
        fetch (Optional[str], optional): The fetch mode ('one', 'all', 'many', None). Defaults to None.
        isolation_level (Optional[int], optional): The isolation level to use. Defaults to None.

    Returns:
        Optional[Union[List, Dict, Any]]: The query results or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    with transaction(conn, isolation_level) as tx_conn:
        if not tx_conn:
            return None

        return execute_values(tx_conn, query, values, template, page_size, fetch)

def table_exists(
    conn: psycopg2.extensions.connection,
    table_name: str,
    schema: str = 'public'
) -> bool:
    """
    Check if a table exists.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        schema (str, optional): The schema of the table. Defaults to 'public'.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = %s
        )
    """
    
    result = execute_query(conn, query, (schema, table_name), 'one')
    return result[0] if result else False

def column_exists(
    conn: psycopg2.extensions.connection,
    table_name: str,
    column_name: str,
    schema: str = 'public'
) -> bool:
    """
    Check if a column exists.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        column_name (str): The name of the column.
        schema (str, optional): The schema of the table. Defaults to 'public'.

    Returns:
        bool: True if the column exists, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = %s 
            AND table_name = %s 
            AND column_name = %s
        )
    """
    
    result = execute_query(conn, query, (schema, table_name, column_name), 'one')
    return result[0] if result else False

def get_table_columns(
    conn: psycopg2.extensions.connection,
    table_name: str,
    schema: str = 'public'
) -> Optional[List[Dict[str, Any]]]:
    """
    Get the columns of a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        schema (str, optional): The schema of the table. Defaults to 'public'.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of column information or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s
        AND table_name = %s
        ORDER BY ordinal_position
    """
    
    results = execute_query(conn, query, (schema, table_name), 'all')
    if not results:
        return None
    
    columns = []
    for row in results:
        columns.append({
            'name': row[0],
            'type': row[1],
            'nullable': row[2] == 'YES',
            'default': row[3]
        })
    
    return columns

def get_table_primary_key(
    conn: psycopg2.extensions.connection,
    table_name: str,
    schema: str = 'public'
) -> Optional[List[str]]:
    """
    Get the primary key columns of a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        schema (str, optional): The schema of the table. Defaults to 'public'.

    Returns:
        Optional[List[str]]: A list of primary key column names or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    query = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass
        AND i.indisprimary
    """
    
    results = execute_query(conn, query, (f"{schema}.{table_name}",), 'all')
    if not results:
        return None
    
    return [row[0] for row in results]

def get_table_foreign_keys(
    conn: psycopg2.extensions.connection,
    table_name: str,
    schema: str = 'public'
) -> Optional[List[Dict[str, Any]]]:
    """
    Get the foreign key constraints of a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        schema (str, optional): The schema of the table. Defaults to 'public'.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of foreign key constraint information or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    query = """
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = %s
        AND tc.table_name = %s
    """
    
    results = execute_query(conn, query, (schema, table_name), 'all')
    if not results:
        return None
    
    foreign_keys = []
    for row in results:
        foreign_keys.append({
            'constraint_name': row[0],
            'column_name': row[1],
            'foreign_table_schema': row[2],
            'foreign_table_name': row[3],
            'foreign_column_name': row[4]
        })
    
    return foreign_keys

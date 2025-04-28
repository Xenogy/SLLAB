"""
Database access layer with RLS support.

This module provides a base class for database access with Row-Level Security (RLS) support.
It ensures that all database operations respect RLS policies and provides a consistent
interface for database operations.

It also includes query analysis and caching for improved performance and monitoring.
"""

import logging
import time
from typing import Optional, Dict, Any, List, Tuple, Union
from contextlib import contextmanager

from .connection import get_db_connection
from .user_connection import get_user_db_connection
from .query_analyzer import query_analyzer
from .query_cache import cached_query, invalidate_cache_by_table

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseAccess:
    """Base class for database access with RLS support."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the DatabaseAccess instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        self.user_id = user_id
        self.user_role = user_role

    @contextmanager
    def get_connection(self, with_rls: bool = True):
        """
        Get a database connection with or without RLS context.

        Args:
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Yields:
            A database connection with or without RLS context.
        """
        if with_rls and self.user_id and self.user_role:
            with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
                yield conn
        else:
            with get_db_connection() as conn:
                yield conn

    @cached_query()
    def execute_query(self, query: str, params: Tuple = None, with_rls: bool = True) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results as a list of dictionaries.

        This method is decorated with @cached_query() to cache the results of read-only queries.
        It also uses the query_analyzer context manager to track query performance.

        Args:
            query (str): The SQL query to execute.
            params (Tuple, optional): The parameters for the query. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the query results.
        """
        with self.get_connection(with_rls) as conn:
            if not conn:
                logger.error("No database connection available")
                return []

            cursor = conn.cursor()
            try:
                # Use query analyzer to track query performance
                with query_analyzer(query, params):
                    cursor.execute(query, params or ())

                if not cursor.description:
                    return []

                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                logger.debug(f"Query: {query}")
                logger.debug(f"Params: {params}")
                return []
            finally:
                cursor.close()

    def execute_command(self, query: str, params: Tuple = None, with_rls: bool = True) -> int:
        """
        Execute a command and return the number of affected rows.

        This method uses the query_analyzer context manager to track query performance.
        It also invalidates the cache for the affected table.

        Args:
            query (str): The SQL command to execute.
            params (Tuple, optional): The parameters for the command. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            int: The number of affected rows.
        """
        with self.get_connection(with_rls) as conn:
            if not conn:
                logger.error("No database connection available")
                return 0

            cursor = conn.cursor()
            try:
                # Use query analyzer to track query performance
                with query_analyzer(query, params):
                    cursor.execute(query, params or ())

                # Invalidate cache for the affected table
                # This is a simple implementation that invalidates the entire cache
                # For a more sophisticated implementation, you would parse the query
                # and determine which tables are affected
                if query.upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    from .query_analyzer import get_tables_from_query
                    tables = get_tables_from_query(query)
                    for table in tables:
                        invalidate_cache_by_table(table)

                conn.commit()
                return cursor.rowcount
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                logger.debug(f"Query: {query}")
                logger.debug(f"Params: {params}")
                conn.rollback()
                return 0
            finally:
                cursor.close()

    def execute_query_single(self, query: str, params: Tuple = None, with_rls: bool = True) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return the first result as a dictionary.

        Args:
            query (str): The SQL query to execute.
            params (Tuple, optional): The parameters for the query. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the first result or None if no results.
        """
        results = self.execute_query(query, params, with_rls)
        return results[0] if results else None

    def execute_insert(self, query: str, params: Tuple = None, with_rls: bool = True, returning: bool = True) -> Optional[Dict[str, Any]]:
        """
        Execute an INSERT command and return the inserted row if RETURNING clause is used.

        Args:
            query (str): The SQL INSERT command to execute.
            params (Tuple, optional): The parameters for the command. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.
            returning (bool, optional): Whether the query has a RETURNING clause. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the inserted row or None if no RETURNING clause.
        """
        with self.get_connection(with_rls) as conn:
            if not conn:
                logger.error("No database connection available")
                return None

            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())

                if returning:
                    if not cursor.description:
                        conn.commit()
                        return None

                    columns = [desc[0] for desc in cursor.description]
                    result = cursor.fetchone()

                    if result:
                        conn.commit()
                        return dict(zip(columns, result))
                    else:
                        conn.commit()
                        return None
                else:
                    conn.commit()
                    return {"rowcount": cursor.rowcount}
            except Exception as e:
                logger.error(f"Error executing insert: {e}")
                logger.debug(f"Query: {query}")
                logger.debug(f"Params: {params}")
                conn.rollback()
                return None
            finally:
                cursor.close()

    def execute_update(self, query: str, params: Tuple = None, with_rls: bool = True, returning: bool = False) -> Union[int, Optional[Dict[str, Any]]]:
        """
        Execute an UPDATE command and return the number of affected rows or the updated row if RETURNING clause is used.

        Args:
            query (str): The SQL UPDATE command to execute.
            params (Tuple, optional): The parameters for the command. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.
            returning (bool, optional): Whether the query has a RETURNING clause. Defaults to False.

        Returns:
            Union[int, Optional[Dict[str, Any]]]: The number of affected rows or a dictionary with the updated row.
        """
        with self.get_connection(with_rls) as conn:
            if not conn:
                logger.error("No database connection available")
                return 0 if not returning else None

            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())

                if returning:
                    if not cursor.description:
                        conn.commit()
                        return None

                    columns = [desc[0] for desc in cursor.description]
                    result = cursor.fetchone()

                    if result:
                        conn.commit()
                        return dict(zip(columns, result))
                    else:
                        conn.commit()
                        return None
                else:
                    conn.commit()
                    return cursor.rowcount
            except Exception as e:
                logger.error(f"Error executing update: {e}")
                logger.debug(f"Query: {query}")
                logger.debug(f"Params: {params}")
                conn.rollback()
                return 0 if not returning else None
            finally:
                cursor.close()

    def execute_delete(self, query: str, params: Tuple = None, with_rls: bool = True) -> int:
        """
        Execute a DELETE command and return the number of affected rows.

        Args:
            query (str): The SQL DELETE command to execute.
            params (Tuple, optional): The parameters for the command. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            int: The number of affected rows.
        """
        return self.execute_command(query, params, with_rls)

    def execute_transaction(self, queries: List[Tuple[str, Tuple]], with_rls: bool = True) -> bool:
        """
        Execute multiple queries in a transaction.

        Args:
            queries (List[Tuple[str, Tuple]]): A list of tuples with queries and their parameters.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        with self.get_connection(with_rls) as conn:
            if not conn:
                logger.error("No database connection available")
                return False

            cursor = conn.cursor()
            try:
                for query, params in queries:
                    cursor.execute(query, params or ())

                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error executing transaction: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()

    def get_count(self, table: str, condition: str = "", params: Tuple = None, with_rls: bool = True) -> int:
        """
        Get the count of rows in a table.

        Args:
            table (str): The table name.
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            int: The count of rows.
        """
        query = f"SELECT COUNT(*) FROM {table}"
        if condition:
            query += f" WHERE {condition}"

        result = self.execute_query_single(query, params, with_rls)
        return result["count"] if result else 0

    def get_by_id(self, table: str, id_column: str, id_value: Any, columns: str = "*", with_rls: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a row by its ID.

        Args:
            table (str): The table name.
            id_column (str): The ID column name.
            id_value (Any): The ID value.
            columns (str, optional): The columns to select. Defaults to "*".
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the row or None if not found.
        """
        query = f"SELECT {columns} FROM {table} WHERE {id_column} = %s"
        return self.execute_query_single(query, (id_value,), with_rls)

    def get_all(self, table: str, condition: str = "", params: Tuple = None, columns: str = "*",
                order_by: str = "", limit: int = 0, offset: int = 0, with_rls: bool = True) -> List[Dict[str, Any]]:
        """
        Get all rows from a table.

        Args:
            table (str): The table name.
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            columns (str, optional): The columns to select. Defaults to "*".
            order_by (str, optional): The ORDER BY clause. Defaults to "".
            limit (int, optional): The LIMIT clause. Defaults to 0 (no limit).
            offset (int, optional): The OFFSET clause. Defaults to 0.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the rows.
        """
        query = f"SELECT {columns} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit > 0:
            query += f" LIMIT {limit}"
        if offset > 0:
            query += f" OFFSET {offset}"

        return self.execute_query(query, params, with_rls)

    def insert(self, table: str, data: Dict[str, Any], returning: bool = True, with_rls: bool = True) -> Optional[Dict[str, Any]]:
        """
        Insert a row into a table.

        Args:
            table (str): The table name.
            data (Dict[str, Any]): The data to insert.
            returning (bool, optional): Whether to return the inserted row. Defaults to True.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the inserted row or None if not returning.
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ["%s"] * len(columns)

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        if returning:
            query += " RETURNING *"

        return self.execute_insert(query, tuple(values), with_rls, returning)

    def update(self, table: str, data: Dict[str, Any], condition: str, params: Tuple = None,
               returning: bool = False, with_rls: bool = True) -> Union[int, Optional[Dict[str, Any]]]:
        """
        Update rows in a table.

        Args:
            table (str): The table name.
            data (Dict[str, Any]): The data to update.
            condition (str): The WHERE condition.
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            returning (bool, optional): Whether to return the updated row. Defaults to False.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Union[int, Optional[Dict[str, Any]]]: The number of affected rows or a dictionary with the updated row.
        """
        set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
        values = list(data.values())

        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        if returning:
            query += " RETURNING *"

        all_params = tuple(values) + (params or ())
        return self.execute_update(query, all_params, with_rls, returning)

    def delete(self, table: str, condition: str, params: Tuple = None, with_rls: bool = True) -> int:
        """
        Delete rows from a table.

        Args:
            table (str): The table name.
            condition (str): The WHERE condition.
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            int: The number of affected rows.
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_delete(query, params, with_rls)

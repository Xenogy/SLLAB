"""
Secure database access layer with RLS enforcement.

This module provides a unified database access layer that enforces Row-Level Security (RLS)
for all database operations. It ensures that all database operations respect RLS policies
and provides a consistent interface for database operations.
"""

import logging
import time
import functools
from typing import Optional, Dict, Any, List, Tuple, Union, Callable
from contextlib import contextmanager

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from .connection import get_db_connection, get_connection_with_retries
from .rls_context import set_rls_context, clear_rls_context, rls_context, is_rls_context_set, get_current_rls_context

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_QUERY_TIMEOUT = 30  # seconds

class SecureDatabase:
    """
    Secure database access class with RLS enforcement.
    
    This class provides methods for executing database operations with RLS enforcement.
    It ensures that all database operations respect RLS policies by setting the appropriate
    RLS context before executing the operation.
    """
    
    def __init__(self, user_id: Optional[Union[int, str]] = None, user_role: Optional[str] = None):
        """
        Initialize the SecureDatabase instance.
        
        Args:
            user_id (Optional[Union[int, str]], optional): User ID for RLS context. Defaults to None.
            user_role (Optional[str], optional): User role for RLS context. Defaults to None.
        """
        self.user_id = user_id
        self.user_role = user_role
        self.conn = None
        self._cursor = None
        self._in_transaction = False
        self._transaction_start_time = None
        
        # Validate user_role if provided
        if user_role is not None and user_role not in ['admin', 'user']:
            logger.warning(f"Invalid user_role: {user_role}, must be 'admin' or 'user'")
            self.user_role = None
    
    def __enter__(self):
        """
        Enter context manager.
        
        Returns:
            SecureDatabase: The SecureDatabase instance
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.close()
    
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            bool: True if the connection was successful, False otherwise
        """
        if self.conn is not None:
            return True
        
        try:
            # Get a database connection
            self.conn = get_connection_with_retries()
            
            if self.conn is None:
                logger.error("Failed to get database connection")
                return False
            
            # Set RLS context if user_id and user_role are provided
            if self.user_id is not None and self.user_role is not None:
                cursor = self.conn.cursor()
                try:
                    success = set_rls_context(cursor, self.user_id, self.user_role)
                    if not success:
                        logger.warning(f"Failed to set RLS context: user_id={self.user_id}, role={self.user_role}")
                        self.close()
                        return False
                finally:
                    cursor.close()
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            self.close()
            return False
    
    def close(self) -> None:
        """
        Close the database connection.
        """
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception as e:
                logger.error(f"Error closing cursor: {e}")
            finally:
                self._cursor = None
        
        if self.conn is not None:
            try:
                # Clear RLS context if user_id and user_role are provided
                if self.user_id is not None and self.user_role is not None:
                    cursor = self.conn.cursor()
                    try:
                        clear_rls_context(cursor)
                    finally:
                        cursor.close()
                
                # Close the connection
                self.conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.conn = None
        
        self._in_transaction = False
        self._transaction_start_time = None
    
    def begin_transaction(self) -> bool:
        """
        Begin a database transaction.
        
        Returns:
            bool: True if the transaction was started successfully, False otherwise
        """
        if self._in_transaction:
            logger.warning("Transaction already in progress")
            return True
        
        if not self.connect():
            return False
        
        try:
            self._in_transaction = True
            self._transaction_start_time = time.time()
            return True
        except Exception as e:
            logger.error(f"Error beginning transaction: {e}")
            return False
    
    def commit(self) -> bool:
        """
        Commit the current transaction.
        
        Returns:
            bool: True if the transaction was committed successfully, False otherwise
        """
        if not self._in_transaction:
            logger.warning("No transaction in progress")
            return False
        
        if self.conn is None:
            logger.error("No database connection available")
            return False
        
        try:
            self.conn.commit()
            
            # Log transaction duration
            if self._transaction_start_time is not None:
                duration = time.time() - self._transaction_start_time
                logger.debug(f"Transaction committed in {duration:.6f}s")
            
            self._in_transaction = False
            self._transaction_start_time = None
            return True
        except Exception as e:
            logger.error(f"Error committing transaction: {e}")
            return False
    
    def rollback(self) -> bool:
        """
        Rollback the current transaction.
        
        Returns:
            bool: True if the transaction was rolled back successfully, False otherwise
        """
        if not self._in_transaction:
            logger.warning("No transaction in progress")
            return False
        
        if self.conn is None:
            logger.error("No database connection available")
            return False
        
        try:
            self.conn.rollback()
            
            # Log transaction duration
            if self._transaction_start_time is not None:
                duration = time.time() - self._transaction_start_time
                logger.debug(f"Transaction rolled back after {duration:.6f}s")
            
            self._in_transaction = False
            self._transaction_start_time = None
            return True
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            return False
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Yields:
            SecureDatabase: The SecureDatabase instance
        
        Example:
            ```python
            with db.transaction():
                db.execute_command("INSERT INTO accounts (name, owner_id) VALUES (%s, %s)", ("Account 1", 1))
                db.execute_command("INSERT INTO accounts (name, owner_id) VALUES (%s, %s)", ("Account 2", 1))
            # Transaction is automatically committed if no exception is raised
            # or rolled back if an exception is raised
            ```
        """
        try:
            self.begin_transaction()
            yield self
            self.commit()
        except Exception as e:
            logger.error(f"Error in transaction: {e}")
            self.rollback()
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, timeout: int = DEFAULT_QUERY_TIMEOUT) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results as a list of dictionaries.
        
        Args:
            query (str): The SQL query to execute
            params (Optional[Tuple], optional): The parameters for the query. Defaults to None.
            timeout (int, optional): Query timeout in seconds. Defaults to DEFAULT_QUERY_TIMEOUT.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the query results
        """
        if not self.connect():
            return []
        
        # Validate query
        if not query or not isinstance(query, str):
            logger.error(f"Invalid query: {query}")
            return []
        
        # Set statement timeout
        cursor = None
        try:
            # Use DictCursor to return results as dictionaries
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Set statement timeout
            cursor.execute(f"SET statement_timeout = {timeout * 1000}")
            
            # Execute the query
            start_time = time.time()
            cursor.execute(query, params or ())
            duration = time.time() - start_time
            
            # Log slow queries
            if duration > 1.0:
                logger.warning(f"Slow query ({duration:.6f}s): {query}")
            else:
                logger.debug(f"Query executed in {duration:.6f}s: {query}")
            
            # Return results
            if not cursor.description:
                return []
            
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def execute_command(self, query: str, params: Optional[Tuple] = None, timeout: int = DEFAULT_QUERY_TIMEOUT) -> int:
        """
        Execute a command and return the number of affected rows.
        
        Args:
            query (str): The SQL command to execute
            params (Optional[Tuple], optional): The parameters for the command. Defaults to None.
            timeout (int, optional): Query timeout in seconds. Defaults to DEFAULT_QUERY_TIMEOUT.
        
        Returns:
            int: The number of affected rows
        """
        if not self.connect():
            return 0
        
        # Validate query
        if not query or not isinstance(query, str):
            logger.error(f"Invalid query: {query}")
            return 0
        
        # Set statement timeout
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            # Set statement timeout
            cursor.execute(f"SET statement_timeout = {timeout * 1000}")
            
            # Execute the command
            start_time = time.time()
            cursor.execute(query, params or ())
            duration = time.time() - start_time
            
            # Log slow commands
            if duration > 1.0:
                logger.warning(f"Slow command ({duration:.6f}s): {query}")
            else:
                logger.debug(f"Command executed in {duration:.6f}s: {query}")
            
            # Commit if not in a transaction
            if not self._in_transaction:
                self.conn.commit()
            
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            
            # Rollback if not in a transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            
            return 0
        finally:
            if cursor:
                cursor.close()
    
    def get_by_id(self, table: str, id_column: str, id_value: Any) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            table (str): The table name
            id_column (str): The ID column name
            id_value (Any): The ID value
        
        Returns:
            Optional[Dict[str, Any]]: The record as a dictionary, or None if not found
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return None
        
        if not id_column or not isinstance(id_column, str):
            logger.error(f"Invalid ID column name: {id_column}")
            return None
        
        # Execute query
        query = f"SELECT * FROM {table} WHERE {id_column} = %s"
        results = self.execute_query(query, (id_value,))
        
        if not results:
            return None
        
        return results[0]
    
    def get_all(self, table: str, where: Optional[str] = None, params: Optional[Tuple] = None, order_by: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all records from a table.
        
        Args:
            table (str): The table name
            where (Optional[str], optional): The WHERE clause. Defaults to None.
            params (Optional[Tuple], optional): The parameters for the WHERE clause. Defaults to None.
            order_by (Optional[str], optional): The ORDER BY clause. Defaults to None.
            limit (Optional[int], optional): The LIMIT clause. Defaults to None.
            offset (Optional[int], optional): The OFFSET clause. Defaults to None.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the query results
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return []
        
        # Build query
        query = f"SELECT * FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit is not None:
            query += f" LIMIT {limit}"
        
        if offset is not None:
            query += f" OFFSET {offset}"
        
        # Execute query
        return self.execute_query(query, params)
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a record into a table.
        
        Args:
            table (str): The table name
            data (Dict[str, Any]): The data to insert
        
        Returns:
            Optional[int]: The number of affected rows, or None if the operation failed
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return None
        
        if not data or not isinstance(data, dict):
            logger.error(f"Invalid data: {data}")
            return None
        
        # Build query
        columns = list(data.keys())
        placeholders = [f"%s" for _ in columns]
        values = [data[column] for column in columns]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # Execute command
        return self.execute_command(query, tuple(values))
    
    def update(self, table: str, data: Dict[str, Any], where: str, params: Optional[Tuple] = None) -> Optional[int]:
        """
        Update records in a table.
        
        Args:
            table (str): The table name
            data (Dict[str, Any]): The data to update
            where (str): The WHERE clause
            params (Optional[Tuple], optional): The parameters for the WHERE clause. Defaults to None.
        
        Returns:
            Optional[int]: The number of affected rows, or None if the operation failed
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return None
        
        if not data or not isinstance(data, dict):
            logger.error(f"Invalid data: {data}")
            return None
        
        if not where or not isinstance(where, str):
            logger.error(f"Invalid WHERE clause: {where}")
            return None
        
        # Build query
        set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
        values = list(data.values())
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        # Combine data values and where params
        all_params = tuple(values) + (params or ())
        
        # Execute command
        return self.execute_command(query, all_params)
    
    def delete(self, table: str, where: str, params: Optional[Tuple] = None) -> Optional[int]:
        """
        Delete records from a table.
        
        Args:
            table (str): The table name
            where (str): The WHERE clause
            params (Optional[Tuple], optional): The parameters for the WHERE clause. Defaults to None.
        
        Returns:
            Optional[int]: The number of affected rows, or None if the operation failed
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return None
        
        if not where or not isinstance(where, str):
            logger.error(f"Invalid WHERE clause: {where}")
            return None
        
        # Build query
        query = f"DELETE FROM {table} WHERE {where}"
        
        # Execute command
        return self.execute_command(query, params)
    
    def count(self, table: str, where: Optional[str] = None, params: Optional[Tuple] = None) -> int:
        """
        Count records in a table.
        
        Args:
            table (str): The table name
            where (Optional[str], optional): The WHERE clause. Defaults to None.
            params (Optional[Tuple], optional): The parameters for the WHERE clause. Defaults to None.
        
        Returns:
            int: The number of records
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return 0
        
        # Build query
        query = f"SELECT COUNT(*) FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        
        # Execute query
        results = self.execute_query(query, params)
        
        if not results:
            return 0
        
        return results[0]["count"]
    
    def exists(self, table: str, where: str, params: Optional[Tuple] = None) -> bool:
        """
        Check if records exist in a table.
        
        Args:
            table (str): The table name
            where (str): The WHERE clause
            params (Optional[Tuple], optional): The parameters for the WHERE clause. Defaults to None.
        
        Returns:
            bool: True if records exist, False otherwise
        """
        # Validate inputs
        if not table or not isinstance(table, str):
            logger.error(f"Invalid table name: {table}")
            return False
        
        if not where or not isinstance(where, str):
            logger.error(f"Invalid WHERE clause: {where}")
            return False
        
        # Build query
        query = f"SELECT EXISTS (SELECT 1 FROM {table} WHERE {where})"
        
        # Execute query
        results = self.execute_query(query, params)
        
        if not results:
            return False
        
        return results[0]["exists"]

def get_secure_db(user_id: Optional[Union[int, str]] = None, user_role: Optional[str] = None) -> SecureDatabase:
    """
    Get a SecureDatabase instance.
    
    Args:
        user_id (Optional[Union[int, str]], optional): User ID for RLS context. Defaults to None.
        user_role (Optional[str], optional): User role for RLS context. Defaults to None.
    
    Returns:
        SecureDatabase: A SecureDatabase instance
    """
    return SecureDatabase(user_id, user_role)

@contextmanager
def secure_db_context(user_id: Optional[Union[int, str]] = None, user_role: Optional[str] = None):
    """
    Context manager for SecureDatabase.
    
    Args:
        user_id (Optional[Union[int, str]], optional): User ID for RLS context. Defaults to None.
        user_role (Optional[str], optional): User role for RLS context. Defaults to None.
    
    Yields:
        SecureDatabase: A SecureDatabase instance
    
    Example:
        ```python
        with secure_db_context(user_id=1, user_role='admin') as db:
            accounts = db.get_all('accounts')
            # ...
        # Database connection is automatically closed when the context exits
        ```
    """
    db = None
    try:
        db = get_secure_db(user_id, user_role)
        yield db
    finally:
        if db:
            db.close()

def with_secure_db(user_id_arg: str = 'user_id', user_role_arg: str = 'user_role'):
    """
    Decorator for functions that need a SecureDatabase instance.
    
    Args:
        user_id_arg (str, optional): The argument name for user_id. Defaults to 'user_id'.
        user_role_arg (str, optional): The argument name for user_role. Defaults to 'user_role'.
    
    Returns:
        Callable: The decorated function
    
    Example:
        ```python
        @with_secure_db()
        def get_accounts(db, user_id=None, user_role=None):
            return db.get_all('accounts')
        ```
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get(user_id_arg)
            user_role = kwargs.get(user_role_arg)
            
            with secure_db_context(user_id, user_role) as db:
                return func(db=db, *args, **kwargs)
        
        return wrapper
    
    return decorator

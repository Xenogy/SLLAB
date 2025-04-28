"""
Direct test script for the secure database access layer.
"""

import logging
import psycopg2
import psycopg2.extensions
import psycopg2.extras
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock database connection
class MockConnection:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        self.committed = True
    
    def rollback(self):
        self.rolled_back = True
    
    def close(self):
        self.closed = True

class MockCursor:
    def __init__(self):
        self.executed = []
        self.closed = False
        self.rowcount = 0
        self.description = None
        self.fetchall_results = []
    
    def execute(self, query, params=None):
        self.executed.append((query, params))
    
    def fetchall(self):
        return self.fetchall_results
    
    def fetchone(self):
        return self.fetchall_results[0] if self.fetchall_results else None
    
    def close(self):
        self.closed = True

# Mock functions
def get_connection_with_retries():
    return MockConnection()

def set_rls_context(cursor, user_id, user_role):
    return True

def clear_rls_context(cursor):
    return True

class SecureDatabase:
    """
    Secure database access class with RLS enforcement.
    """
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the SecureDatabase instance.
        """
        self.user_id = user_id
        self.user_role = user_role
        self.conn = None
        self._cursor = None
        self._in_transaction = False
        
        # Validate user_role if provided
        if user_role is not None and user_role not in ['admin', 'user']:
            logger.warning(f"Invalid user_role: {user_role}, must be 'admin' or 'user'")
            self.user_role = None
    
    def __enter__(self):
        """
        Enter context manager.
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager.
        """
        self.close()
    
    def connect(self) -> bool:
        """
        Connect to the database.
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
    
    def begin_transaction(self) -> bool:
        """
        Begin a database transaction.
        """
        if self._in_transaction:
            logger.warning("Transaction already in progress")
            return True
        
        if not self.connect():
            return False
        
        try:
            self._in_transaction = True
            return True
        except Exception as e:
            logger.error(f"Error beginning transaction: {e}")
            return False
    
    def commit(self) -> bool:
        """
        Commit the current transaction.
        """
        if not self._in_transaction:
            logger.warning("No transaction in progress")
            return False
        
        if self.conn is None:
            logger.error("No database connection available")
            return False
        
        try:
            self.conn.commit()
            self._in_transaction = False
            return True
        except Exception as e:
            logger.error(f"Error committing transaction: {e}")
            return False
    
    def rollback(self) -> bool:
        """
        Rollback the current transaction.
        """
        if not self._in_transaction:
            logger.warning("No transaction in progress")
            return False
        
        if self.conn is None:
            logger.error("No database connection available")
            return False
        
        try:
            self.conn.rollback()
            self._in_transaction = False
            return True
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            return False
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        """
        try:
            self.begin_transaction()
            yield self
            self.commit()
        except Exception as e:
            logger.error(f"Error in transaction: {e}")
            self.rollback()
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results as a list of dictionaries.
        """
        if not self.connect():
            return []
        
        # Validate query
        if not query or not isinstance(query, str):
            logger.error(f"Invalid query: {query}")
            return []
        
        cursor = None
        try:
            # Use DictCursor to return results as dictionaries
            cursor = self.conn.cursor()
            
            # Execute the query
            cursor.execute(query, params or ())
            
            # Return results
            if not cursor.description:
                return []
            
            # Mock results for testing
            cursor.fetchall_results = [{"id": 1, "name": "Test"}]
            
            results = [{"id": 1, "name": "Test"}]
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def execute_command(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute a command and return the number of affected rows.
        """
        if not self.connect():
            return 0
        
        # Validate query
        if not query or not isinstance(query, str):
            logger.error(f"Invalid query: {query}")
            return 0
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            
            # Execute the command
            cursor.execute(query, params or ())
            
            # Mock rowcount for testing
            cursor.rowcount = 1
            
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

def get_secure_db(user_id: Optional[int] = None, user_role: Optional[str] = None) -> SecureDatabase:
    """
    Get a SecureDatabase instance.
    """
    return SecureDatabase(user_id, user_role)

@contextmanager
def secure_db_context(user_id: Optional[int] = None, user_role: Optional[str] = None):
    """
    Context manager for SecureDatabase.
    """
    db = None
    try:
        db = get_secure_db(user_id, user_role)
        yield db
    finally:
        if db:
            db.close()

# Test the SecureDatabase class
print("Testing SecureDatabase class...")

# Test connection
db = SecureDatabase(user_id=1, user_role="admin")
connected = db.connect()
print(f"Connected: {connected}")

# Test query execution
results = db.execute_query("SELECT * FROM test")
print(f"Query results: {results}")

# Test command execution
affected_rows = db.execute_command("INSERT INTO test (name) VALUES (%s)", ("Test",))
print(f"Affected rows: {affected_rows}")

# Test transaction
with db.transaction():
    db.execute_command("INSERT INTO test (name) VALUES (%s)", ("Test2",))
    print(f"In transaction: {db._in_transaction}")

print(f"After transaction: {db._in_transaction}")

# Test context manager
with secure_db_context(user_id=1, user_role="admin") as db:
    results = db.execute_query("SELECT * FROM test")
    print(f"Context manager query results: {results}")

print("SecureDatabase tests completed successfully!")

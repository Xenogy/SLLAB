# Connection Management

## Overview

This document describes the connection management approach used in the AccountDB project. Connection management is a critical feature that ensures that database connections are properly created, used, and closed, and that the application can handle connection failures gracefully.

## Implementation

### Connection Module

The project uses a centralized connection module (`db/connection.py`) to handle all database connection management. This module provides functions for:

- Creating connection pools
- Getting connections from the pool
- Returning connections to the pool
- Getting connections with retries
- Closing all connections

```python
# Example connection pool creation
def create_connection_pool(
    min_connections: int = None,
    max_connections: int = None,
    connection_timeout: int = None,
    **kwargs
) -> Optional[psycopg2.pool.AbstractConnectionPool]:
    """
    Create a database connection pool.
    
    Args:
        min_connections (int, optional): Minimum number of connections. Defaults to Config.DB_MIN_CONNECTIONS or DEFAULT_MIN_CONNECTIONS.
        max_connections (int, optional): Maximum number of connections. Defaults to Config.DB_MAX_CONNECTIONS or DEFAULT_MAX_CONNECTIONS.
        connection_timeout (int, optional): Connection timeout in seconds. Defaults to Config.DB_CONNECTION_TIMEOUT or DEFAULT_CONNECTION_TIMEOUT.
        **kwargs: Additional arguments to pass to the connection pool.
        
    Returns:
        Optional[psycopg2.pool.AbstractConnectionPool]: A connection pool or None if creation fails.
    """
    # Get configuration values
    min_conn = min_connections or getattr(Config, 'DB_MIN_CONNECTIONS', DEFAULT_MIN_CONNECTIONS)
    max_conn = max_connections or getattr(Config, 'DB_MAX_CONNECTIONS', DEFAULT_MAX_CONNECTIONS)
    timeout = connection_timeout or getattr(Config, 'DB_CONNECTION_TIMEOUT', DEFAULT_CONNECTION_TIMEOUT)
    
    # Validate configuration values
    min_conn = max(1, min_conn)  # Minimum of 1 connection
    max_conn = max(min_conn, max_conn)  # Maximum must be at least minimum
    timeout = max(1, timeout)  # Minimum timeout of 1 second
    
    try:
        # Create the connection pool
        pool = psycopg2.pool.ThreadedConnectionPool(
            min_conn,
            max_conn,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASS,
            connect_timeout=timeout,
            target_session_attrs="read-write",
            **kwargs
        )
        logger.info(f"Database connection pool created successfully (min={min_conn}, max={max_conn})")
        return pool
    except Exception as e:
        logger.error(f"Error creating database connection pool: {e}")
        return None
```

### User Connection Module

The project uses a user connection module (`db/user_connection.py`) to handle database connections with user context. This module provides functions for:

- Getting connections with user context
- Setting and clearing RLS context
- Getting user connection information

```python
# Example user connection context manager
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
                    set_rls_context(conn, user_id, user_role)
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
                clear_rls_context(conn)
            
            # Return connection to pool
            return_connection(conn)
```

### Database Utilities Module

The project uses a database utilities module (`db/utils.py`) to provide utility functions for working with databases. This module provides functions for:

- Executing queries
- Handling transactions
- Managing cursors
- Checking table and column existence
- Getting table information

```python
# Example query execution function
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
```

### Health Check Module

The project uses a health check module (`db/health.py`) to provide functions for checking the health of the database. This module provides functions for:

- Checking connection health
- Checking pool health
- Checking query performance
- Checking database health

```python
# Example connection health check function
def check_connection_health(conn: psycopg2.extensions.connection) -> Dict[str, Any]:
    """
    Check the health of a database connection.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Dict[str, Any]: A dictionary with connection health information.
    """
    health = {
        "status": "unknown",
        "message": "",
        "response_time_ms": None,
        "timestamp": time.time()
    }

    if not conn:
        health["status"] = "error"
        health["message"] = "No database connection available"
        return health

    try:
        # Measure response time
        start_time = time.time()
        
        # Execute a simple query
        result = execute_query(conn, "SELECT 1", fetch='one')
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        if result and result[0] == 1:
            health["status"] = "healthy"
            health["message"] = "Database connection is healthy"
            health["response_time_ms"] = response_time_ms
        else:
            health["status"] = "warning"
            health["message"] = "Database connection returned unexpected result"
            health["response_time_ms"] = response_time_ms
    except Exception as e:
        health["status"] = "error"
        health["message"] = f"Database connection error: {str(e)}"

    return health
```

### Statistics Module

The project uses a statistics module (`db/stats.py`) to provide functions for collecting and analyzing database statistics. This module provides functions for:

- Getting database size
- Getting table sizes
- Getting table row counts
- Getting index usage statistics
- Getting table bloat statistics
- Getting comprehensive database statistics

```python
# Example database size function
def get_database_size(conn: psycopg2.extensions.connection) -> Optional[Dict[str, Any]]:
    """
    Get the size of the database.

    Args:
        conn (psycopg2.extensions.connection): The database connection.

    Returns:
        Optional[Dict[str, Any]]: A dictionary with database size information or None if not available.
    """
    if not conn:
        logger.warning("No database connection available")
        return None

    try:
        # Get the database size
        query = """
            SELECT
                pg_database.datname AS database_name,
                pg_size_pretty(pg_database_size(pg_database.datname)) AS pretty_size,
                pg_database_size(pg_database.datname) AS size_bytes
            FROM pg_database
            WHERE pg_database.datname = current_database()
        """
        
        result = execute_query(conn, query, fetch='one')
        if not result:
            return None
        
        return {
            "database_name": result[0],
            "pretty_size": result[1],
            "size_bytes": result[2],
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting database size: {e}")
        return None
```

### Cleanup Module

The project uses a cleanup module (`db/cleanup.py`) to provide functions for cleaning up the database. This module provides functions for:

- Vacuuming tables
- Analyzing tables
- Reindexing tables
- Truncating tables
- Getting table names
- Cleaning up the database

```python
# Example vacuum function
def vacuum_table(
    conn: psycopg2.extensions.connection,
    table_name: str,
    full: bool = False,
    analyze: bool = True
) -> bool:
    """
    Vacuum a table.

    Args:
        conn (psycopg2.extensions.connection): The database connection.
        table_name (str): The name of the table.
        full (bool, optional): Whether to perform a full vacuum. Defaults to False.
        analyze (bool, optional): Whether to analyze the table. Defaults to True.

    Returns:
        bool: True if the vacuum was successful, False otherwise.
    """
    if not conn:
        logger.warning("No database connection available")
        return False

    try:
        # Build the vacuum command
        vacuum_cmd = "VACUUM"
        if full:
            vacuum_cmd += " FULL"
        if analyze:
            vacuum_cmd += " ANALYZE"
        vacuum_cmd += f" {table_name}"
        
        # Execute the vacuum command
        execute_query(conn, vacuum_cmd)
        logger.info(f"Vacuumed table {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error vacuuming table {table_name}: {e}")
        return False
```

### Initialization Module

The project uses an initialization module (`db/init.py`) to provide functions for initializing the database. This module provides functions for:

- Initializing the database
- Checking if RLS is enabled
- Initializing the database with retries

```python
# Example initialization function
def init_database(
    max_retries: int = 5,
    retry_interval: int = 2
) -> bool:
    """
    Initialize the database.

    Args:
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    logger.info("Initializing database...")

    # Get a database connection with retries
    with get_db_connection_with_retries(max_retries, retry_interval) as conn:
        if not conn:
            logger.error("Failed to get database connection for initialization")
            return False

        try:
            # Check if required tables exist
            required_tables = ["users", "accounts", "hardware", "cards"]
            missing_tables = []

            for table in required_tables:
                if not table_exists(conn, table):
                    missing_tables.append(table)

            if missing_tables:
                logger.warning(f"Missing required tables: {', '.join(missing_tables)}")
                return False

            # Check if RLS is enabled
            rls_enabled = check_rls_enabled(conn)
            if not rls_enabled:
                logger.warning("Row-Level Security is not enabled")
                return False

            logger.info("Database initialization successful")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
```

### Migrations Module

The project uses a migrations module (`db/migrations.py`) to provide functions for managing database migrations. This module provides functions for:

- Creating the migrations table
- Getting applied migrations
- Recording migrations
- Running migration files
- Running all pending migrations
- Running migrations with retries

```python
# Example migration function
def run_migrations(
    migrations_dir: str = None,
    max_retries: int = 5,
    retry_interval: int = 2
) -> bool:
    """
    Run all pending migrations.

    Args:
        migrations_dir (str, optional): The directory containing migration files. Defaults to None.
        max_retries (int, optional): Maximum number of retries. Defaults to 5.
        retry_interval (int, optional): Retry interval in seconds. Defaults to 2.

    Returns:
        bool: True if all migrations were successful, False otherwise.
    """
    logger.info("Running migrations...")

    # Get the migrations directory
    if not migrations_dir:
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")

    # Check if the migrations directory exists
    if not os.path.exists(migrations_dir):
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return False

    # Get a database connection with retries
    with get_db_connection_with_retries(max_retries, retry_interval) as conn:
        if not conn:
            logger.error("Failed to get database connection for migrations")
            return False

        try:
            # Create the migrations table if it doesn't exist
            if not create_migrations_table(conn):
                logger.error("Failed to create migrations table")
                return False

            # Get the list of applied migrations
            applied_migrations = get_applied_migrations(conn)
            if applied_migrations is None:
                logger.error("Failed to get applied migrations")
                return False

            # Get the list of migration files
            migration_files = []
            for file_name in os.listdir(migrations_dir):
                if file_name.endswith('.sql'):
                    migration_files.append(file_name)

            # Sort migration files by name
            migration_files.sort()

            # Run pending migrations
            for file_name in migration_files:
                if file_name not in applied_migrations:
                    file_path = os.path.join(migrations_dir, file_name)
                    logger.info(f"Running migration: {file_name}")
                    
                    if run_migration_file(conn, file_path):
                        if not record_migration(conn, file_name):
                            logger.error(f"Failed to record migration: {file_name}")
                            return False
                    else:
                        logger.error(f"Failed to run migration: {file_name}")
                        return False

            logger.info("Migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            return False
```

## Usage

### Getting a Database Connection

To get a database connection, use the `get_db_connection()` context manager:

```python
from db.connection import get_db_connection

with get_db_connection() as conn:
    if conn:
        # Use the connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(result)
    else:
        print("No database connection available")
```

### Getting a User Database Connection

To get a database connection with user context, use the `get_user_db_connection()` context manager:

```python
from db.user_connection import get_user_db_connection

with get_user_db_connection(user_id=123, user_role="admin") as conn:
    if conn:
        # Use the connection
        cursor = conn.cursor()
        cursor.execute("SELECT current_setting('app.current_user_id', TRUE)")
        result = cursor.fetchone()
        print(result)
    else:
        print("No database connection available")
```

### Executing a Query

To execute a query, use the `execute_query()` function:

```python
from db.connection import get_db_connection
from db.utils import execute_query

with get_db_connection() as conn:
    if conn:
        # Execute a query
        result = execute_query(conn, "SELECT * FROM users WHERE id = %s", (123,), fetch='one')
        print(result)
    else:
        print("No database connection available")
```

### Executing a Query with a Transaction

To execute a query within a transaction, use the `execute_query_with_transaction()` function:

```python
from db.connection import get_db_connection
from db.utils import execute_query_with_transaction

with get_db_connection() as conn:
    if conn:
        # Execute a query within a transaction
        result = execute_query_with_transaction(
            conn,
            "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
            ("john", "john@example.com"),
            fetch='one'
        )
        print(result)
    else:
        print("No database connection available")
```

### Checking Database Health

To check the health of the database, use the `check_database_health()` function:

```python
from db.health import check_database_health

health = check_database_health()
print(health)
```

### Getting Database Statistics

To get comprehensive database statistics, use the `get_database_stats()` function:

```python
from db.stats import get_database_stats

stats = get_database_stats()
print(stats)
```

### Cleaning Up the Database

To clean up the database, use the `cleanup_database()` function:

```python
from db.cleanup import cleanup_database

results = cleanup_database()
print(results)
```

### Running Database Migrations

To run all pending database migrations, use the `run_migrations()` function:

```python
from db.migrations import run_migrations

success = run_migrations()
print(success)
```

## Configuration

The connection management modules use the following configuration values from the `Config` class:

- `DB_HOST`: The database host
- `DB_PORT`: The database port
- `DB_NAME`: The database name
- `DB_USER`: The database user
- `DB_PASS`: The database password
- `DB_MIN_CONNECTIONS`: The minimum number of connections in the pool
- `DB_MAX_CONNECTIONS`: The maximum number of connections in the pool
- `DB_CONNECTION_TIMEOUT`: The connection timeout in seconds
- `DB_MAX_RETRIES`: The maximum number of retries for getting a connection
- `DB_RETRY_INTERVAL`: The retry interval in seconds

## Benefits

The connection management approach provides several benefits:

1. **Improved Reliability**: Connection pooling and retries improve the reliability of database connections.
2. **Better Resource Management**: Connections are properly closed and returned to the pool.
3. **Better Error Handling**: Errors are properly logged and handled.
4. **Better Monitoring**: Connection health and statistics are available for monitoring.
5. **Better Maintenance**: Database cleanup and maintenance functions are available.
6. **Better Migration Management**: Database migrations are properly tracked and applied.
7. **Better Configuration**: Connection parameters are configurable.
8. **Better Documentation**: Comprehensive documentation is available.
9. **Better Testing**: Connection management functions are testable.
10. **Better Security**: User context is properly set and cleared.

## Next Steps

1. **Update Application Code**: Update the application code to use the new connection management modules.
2. **Add Connection Monitoring**: Add monitoring for connection health and statistics.
3. **Add Connection Logging**: Add logging for connection usage and errors.
4. **Add Connection Metrics**: Add metrics for connection usage and performance.
5. **Add Connection Tracing**: Add tracing for connection usage and queries.
6. **Add Connection Testing**: Add tests for connection management functions.
7. **Add Connection Documentation**: Add more documentation for connection management.
8. **Add Connection Examples**: Add more examples for connection management.
9. **Add Connection Troubleshooting**: Add troubleshooting guides for connection issues.
10. **Add Connection Best Practices**: Add best practices for connection management.

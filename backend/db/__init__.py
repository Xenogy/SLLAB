"""
Database package for the AccountDB application.

This package provides modules for managing database connections, including
connection pooling, connection creation, and connection closing.
"""

from .connection import (
    get_connection, return_connection, get_db_connection,
    get_connection_with_retries, get_db_connection_with_retries,
    get_pool_stats, close_all_connections, recreate_connection_pool
)

from .user_connection import (
    get_user_db_connection, get_user_db_connection_with_retries,
    get_user_connection_info
)

from .wait_for_database import (
    wait_for_database, initialize_connection_pool
)

from .utils import (
    get_cursor, transaction, execute_query, execute_query_with_transaction,
    execute_batch, execute_batch_with_transaction, execute_values,
    execute_values_with_transaction, table_exists, column_exists,
    get_table_columns, get_table_primary_key, get_table_foreign_keys
)

from .health import (
    check_connection_health, check_pool_health, check_query_performance,
    check_database_health
)

from .stats import (
    get_database_size, get_table_sizes, get_table_row_counts,
    get_index_usage_stats, get_table_bloat, get_database_stats
)

from .cleanup import (
    vacuum_table, analyze_table, reindex_table, truncate_table,
    get_table_names, vacuum_all_tables, analyze_all_tables,
    reindex_all_tables, cleanup_database
)

from .init import (
    init_database, check_rls_enabled, init_database_with_retries
)

from .migrations import (
    create_migrations_table, get_applied_migrations, record_migration,
    run_migration_file, run_migrations, run_migrations_with_retries
)

__all__ = [
    # Connection management
    'get_connection', 'return_connection', 'get_db_connection',
    'get_connection_with_retries', 'get_db_connection_with_retries',
    'get_pool_stats', 'close_all_connections',

    # User connection management
    'get_user_db_connection', 'get_user_db_connection_with_retries',
    'get_user_connection_info',

    # Database utilities
    'get_cursor', 'transaction', 'execute_query', 'execute_query_with_transaction',
    'execute_batch', 'execute_batch_with_transaction', 'execute_values',
    'execute_values_with_transaction', 'table_exists', 'column_exists',
    'get_table_columns', 'get_table_primary_key', 'get_table_foreign_keys',

    # Health checks
    'check_connection_health', 'check_pool_health', 'check_query_performance',
    'check_database_health',

    # Statistics
    'get_database_size', 'get_table_sizes', 'get_table_row_counts',
    'get_index_usage_stats', 'get_table_bloat', 'get_database_stats',

    # Cleanup
    'vacuum_table', 'analyze_table', 'reindex_table', 'truncate_table',
    'get_table_names', 'vacuum_all_tables', 'analyze_all_tables',
    'reindex_all_tables', 'cleanup_database',

    # Initialization
    'init_database', 'check_rls_enabled', 'init_database_with_retries',

    # Migrations
    'create_migrations_table', 'get_applied_migrations', 'record_migration',
    'run_migration_file', 'run_migrations', 'run_migrations_with_retries'
]
